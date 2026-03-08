(function () {
  window.EB = window.EB || {};

  function createPlannedEditor(deps) {
    const metrics = (window.EB && window.EB.metrics) || {};
    const metricMeasureAsync = metrics.measureAsync || (async (_name, fn) => fn());
    const getCsrfToken = (deps && deps.getCsrfToken) || (() => "");
    const postJson = (deps && deps.postJson) || (async (url, payload, csrfToken) => {
      const response = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken || "",
          "X-Requested-With": "XMLHttpRequest",
        },
        body: JSON.stringify(payload || {}),
        credentials: "same-origin",
      });
      if (!response.ok) throw new Error(`Request failed with status ${response.status}`);
      return response.json();
    });
    const placeCaretToEnd = (deps && deps.placeCaretToEnd) || (() => {});
    const setClipboardText = (deps && deps.setClipboardText) || (() => false);
    const parsePasteMatrix = (deps && deps.parsePasteMatrix) || (() => []);
    const createHistoryManager = (deps && deps.createHistoryManager) || (() => ({ push() {}, undo() {}, redo() {} }));
    const RULES_ONBOARDING_KEY = "eb_planned_rules_onboarding_dismissed_v1";
    const NUM_RE = "\\d+(?:[.,]\\d+)?";
    const MULT_RANGE_PAREN_RE = new RegExp(`(${NUM_RE})\\s*-\\s*(${NUM_RE})\\s*[xX×]\\s*\\(([^)]*)\\)`, "gi");
    const MULT_PAREN_WITH_TAIL_SERIES_RE = new RegExp(`(${NUM_RE})\\s*[xX×]\\s*\\(([^)]*)\\)\\s*(?:mk|mch)?\\s*(\\d{3,4}(?:\\s*-\\s*\\d{3,4})+)m\\b`, "gi");
    const MULT_SINGLE_PAREN_RE = new RegExp(`(${NUM_RE})\\s*[xX×]\\s*\\(([^)]*)\\)`, "gi");
    const MULT_CHAIN_DIST_RANGE_RE = new RegExp(`(${NUM_RE})\\s*-\\s*(${NUM_RE})\\s*[xX×]\\s*(${NUM_RE})\\s*[xX×]\\s*(${NUM_RE})\\s*(km|m)\\b`, "gi");
    const MULT_CHAIN_DIST_SINGLE_RE = new RegExp(`(${NUM_RE})\\s*[xX×]\\s*(${NUM_RE})\\s*[xX×]\\s*(${NUM_RE})\\s*(km|m)\\b`, "gi");
    const MULT_DIST_RANGE_RE = new RegExp(`(${NUM_RE})\\s*-\\s*(${NUM_RE})\\s*[xX×]\\s*(${NUM_RE})\\s*(km|m)\\b`, "gi");
    const MULT_DIST_SINGLE_RE = new RegExp(`(${NUM_RE})\\s*[xX×]\\s*(${NUM_RE})\\s*(km|m)\\b`, "gi");
    const RV_RANGE_KM_RE = new RegExp(`(?<!\\w)(${NUM_RE})\\s*-\\s*(${NUM_RE})\\s*([RVrv])(?=$|[\\s,;+()/-])`, "g");
    const RV_KM_RE = new RegExp(`(?<!\\w)(${NUM_RE})\\s*([RVrv])(?=$|[\\s,;+()/-])`, "g");
    const RANGE_UNIT_RE = new RegExp(`(${NUM_RE})\\s*-\\s*(${NUM_RE})\\s*(km|m)\\b`, "gi");
    const SINGLE_UNIT_RE = new RegExp(`(${NUM_RE})\\s*(km|m)\\b`, "gi");
    const BARE_M_SERIES_RE = /\b(\d{3,4}(?:\s*-\s*\d{3,4}){1,})\b/gi;
    const BARE_M_TOKEN_RE = /(?<!\d)(\d{3,4})(?!\d)/g;
    const WALK_RE = /(chuze|chůze|mch|walk|walking|hike)/i;
    const PAUSE_MIN_RE = /\bp\s*=\s*(\d+(?:[.,]\d+)?)\s*['´’]/gi;
    const KLUS_MIN_RE = /(?:(po\s*serii)\s*)?(\d+(?:[.,]\d+)?)\s*(?:min|m(?:in)?)\s*klus/gi;
    const RUN_HINT_RE = /\b(km|m|klus|fartlek|tempo|kopec|kopce|beh|běh|run|interval|rovinky)\b/i;
    const MAX_RV_TOKEN = 30;

    function toNum(value) {
      const parsed = Number.parseFloat(String(value || "").replace(",", "."));
      return Number.isFinite(parsed) ? parsed : null;
    }

    function stripAccents(value) {
      return String(value || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "");
    }

    function isWalkContext(text, start, end) {
      const normalized = String(text || "").toLowerCase();
      const left = Math.max(0, start - 24);
      const right = Math.min(normalized.length, end + 24);
      const around = normalized.slice(left, right);
      const relStart = start - left;
      const relEnd = end - left;
      const before = around.slice(0, relStart);
      const after = around.slice(relEnd);
      const marker = "(?:mch|chuze|walk|walking|hike)";
      const beforeRe = new RegExp(`\\b${marker}\\s*$`);
      const afterRe = new RegExp(`^\\s*${marker}\\b`);
      return beforeRe.test(before) || afterRe.test(after);
    }

    function isTempoContext(text, start) {
      const normalized = stripAccents(text).toLowerCase();
      const left = Math.max(0, start - 20);
      const before = normalized.slice(left, start);
      return /(?:tempo|tempu)\s*$/i.test(before);
    }

    function toKm(value, unit) {
      if (String(unit || "").toLowerCase() === "km") {
        if (value > 60) return 0;
        return value;
      }
      if (value < 100 || value > 5000) return 0;
      return value / 1000;
    }

    function tailSeriesKm(raw) {
      const values = String(raw || "")
        .split("-")
        .map((part) => toNum(part.trim()));
      if (!values.length || values.some((v) => v === null || v < 100 || v > 5000)) return 0;
      const sum = values.reduce((acc, v) => acc + v, 0);
      return sum / 1000;
    }

    function estimatePauseMinutesKm(text) {
      return 0;
    }

    function outerSeriesMultiplier(text) {
      const match = /\b(\d+(?:[.,]\d+)?)\s*[xX×]\s*\d/i.exec(stripAccents(text));
      if (!match) return 1;
      const value = toNum(match[1]);
      if (value === null || value <= 0 || value > 10) return 1;
      return value;
    }

    function estimateKlusMinutesKm(text) {
      if (!text) return 0;
      let total = 0;
      const normalized = stripAccents(text).toLowerCase();
      const seriesMult = outerSeriesMultiplier(normalized);
      KLUS_MIN_RE.lastIndex = 0;
      let match = KLUS_MIN_RE.exec(normalized);
      while (match) {
        const mins = toNum(match[2]);
        if (mins !== null && mins > 0) {
          const mult = match[1] ? seriesMult : 1;
          total += mins * 0.25 * mult;
        }
        match = KLUS_MIN_RE.exec(normalized);
      }
      return total;
    }

    function bareMTokensKm(text) {
      if (!text) return 0;
      let total = 0;
      BARE_M_TOKEN_RE.lastIndex = 0;
      let match = BARE_M_TOKEN_RE.exec(text);
      while (match) {
        const value = toNum(match[1]);
        if (value !== null && value >= 100 && value <= 5000) total += value / 1000;
        match = BARE_M_TOKEN_RE.exec(text);
      }
      return total;
    }

    function consumeRegex(text, pattern, handler) {
      pattern.lastIndex = 0;
      let mutable = text;
      let total = 0;
      let match = pattern.exec(mutable);
      while (match) {
        total += handler(match, mutable);
        const start = match.index;
        const end = start + match[0].length;
        mutable = `${mutable.slice(0, start)}${" ".repeat(end - start)}${mutable.slice(end)}`;
        pattern.lastIndex = 0;
        match = pattern.exec(mutable);
      }
      return { total, text: mutable };
    }

    function estimateRunningKmFromText(text) {
      if (!text) return 0;
      let mutable = String(text);
      let total = 0;
      const pauseKm = estimatePauseMinutesKm(mutable);
      const klusMinutesKm = estimateKlusMinutesKm(mutable);

      let out = consumeRegex(mutable, MULT_RANGE_PAREN_RE, (m) => {
        const a = toNum(m[1]);
        const b = toNum(m[2]);
        if (a === null || b === null || a < 0 || b < 0) return 0;
        const mult = Math.max(a, b);
        let bodyKm = estimateRunningKmFromText(m[3] || "");
        if (bodyKm === 0) bodyKm = bareMTokensKm(m[3] || "");
        return mult * bodyKm;
      });
      total += out.total;
      mutable = out.text;

      out = consumeRegex(mutable, MULT_PAREN_WITH_TAIL_SERIES_RE, (m, src) => {
        const start = m.index;
        const end = start + m[0].length;
        if (isWalkContext(src, start, end)) return 0;
        const mult = toNum(m[1]);
        if (mult === null || mult < 0) return 0;
        const bodyKm = estimateRunningKmFromText(m[2] || "");
        const tailKm = tailSeriesKm(m[3] || "");
        return mult * (bodyKm + tailKm);
      });
      total += out.total;
      mutable = out.text;

      out = consumeRegex(mutable, MULT_SINGLE_PAREN_RE, (m) => {
        const mult = toNum(m[1]);
        if (mult === null || mult < 0) return 0;
        let bodyKm = estimateRunningKmFromText(m[2] || "");
        if (bodyKm === 0) bodyKm = bareMTokensKm(m[2] || "");
        return mult * bodyKm;
      });
      total += out.total;
      mutable = out.text;

      out = consumeRegex(mutable, MULT_CHAIN_DIST_RANGE_RE, (m, src) => {
        const start = m.index;
        const end = start + m[0].length;
        if (isWalkContext(src, start, end)) return 0;
        const a1 = toNum(m[1]);
        const a2 = toNum(m[2]);
        const b = toNum(m[3]);
        const d = toNum(m[4]);
        if (a1 === null || a2 === null || b === null || d === null || a1 < 0 || a2 < 0 || b < 0 || d < 0) return 0;
        return Math.max(a1, a2) * b * toKm(d, m[5]);
      });
      total += out.total;
      mutable = out.text;

      out = consumeRegex(mutable, MULT_CHAIN_DIST_SINGLE_RE, (m, src) => {
        const start = m.index;
        const end = start + m[0].length;
        if (isWalkContext(src, start, end)) return 0;
        const a = toNum(m[1]);
        const b = toNum(m[2]);
        const d = toNum(m[3]);
        if (a === null || b === null || d === null || a < 0 || b < 0 || d < 0) return 0;
        return a * b * toKm(d, m[4]);
      });
      total += out.total;
      mutable = out.text;

      out = consumeRegex(mutable, MULT_DIST_RANGE_RE, (m, src) => {
        const start = m.index;
        const end = start + m[0].length;
        if (isWalkContext(src, start, end)) return 0;
        const a = toNum(m[1]);
        const b = toNum(m[2]);
        const d = toNum(m[3]);
        if (a === null || b === null || d === null || a < 0 || b < 0 || d < 0) return 0;
        return Math.max(a, b) * toKm(d, m[4]);
      });
      total += out.total;
      mutable = out.text;

      out = consumeRegex(mutable, MULT_DIST_SINGLE_RE, (m, src) => {
        const start = m.index;
        const end = start + m[0].length;
        if (isWalkContext(src, start, end)) return 0;
        const mult = toNum(m[1]);
        const d = toNum(m[2]);
        if (mult === null || d === null || mult < 0 || d < 0) return 0;
        return mult * toKm(d, m[3]);
      });
      total += out.total;
      mutable = out.text;

      out = consumeRegex(mutable, RV_RANGE_KM_RE, (m, src) => {
        const a = toNum(m[1]);
        const b = toNum(m[2]);
        if (a === null || b === null || a < 0 || b < 0) return 0;
        if (a > MAX_RV_TOKEN || b > MAX_RV_TOKEN) return 0;
        return Math.max(a, b);
      });
      total += out.total;
      mutable = out.text;

      out = consumeRegex(mutable, RV_KM_RE, (m, src) => {
        const value = toNum(m[1]);
        if (value === null || value < 0) return 0;
        if (value > MAX_RV_TOKEN) return 0;
        return value;
      });
      total += out.total;
      mutable = out.text;

      out = consumeRegex(mutable, RANGE_UNIT_RE, (m, src) => {
        const start = m.index;
        const end = start + m[0].length;
        if (String(m[3] || "").toLowerCase() === "m" && isTempoContext(src, start)) return 0;
        if (isWalkContext(src, start, end)) return 0;
        const a = toNum(m[1]);
        const b = toNum(m[2]);
        if (a === null || b === null || a < 0 || b < 0) return 0;
        return toKm(Math.max(a, b), m[3]);
      });
      total += out.total;
      mutable = out.text;

      out = consumeRegex(mutable, SINGLE_UNIT_RE, (m, src) => {
        const start = m.index;
        const end = start + m[0].length;
        if (String(m[2] || "").toLowerCase() === "m" && isTempoContext(src, start)) return 0;
        if (isWalkContext(src, start, end)) return 0;
        const value = toNum(m[1]);
        if (value === null || value < 0) return 0;
        return toKm(value, m[2]);
      });
      total += out.total;
      mutable = out.text;

      out = consumeRegex(mutable, BARE_M_SERIES_RE, (m, src) => {
        const start = m.index;
        const end = start + m[0].length;
        if (isTempoContext(src, start)) return 0;
        if (isWalkContext(src, start, end)) return 0;
        const values = String(m[1] || "")
          .split("-")
          .map((part) => toNum(part.trim()));
        if (!values.length || values.some((v) => v === null || v < 100 || v > 5000)) return 0;
        const sum = values.reduce((acc, v) => acc + v, 0);
        return sum / 1000;
      });
      total += out.total;
      total += pauseKm;
      total += klusMinutesKm;
      if (total === 0) {
        const normalized = String(text).toLowerCase();
        const longByFeel =
          (normalized.includes("delsi klus") || normalized.includes("dlouhy klus") || normalized.includes("long run"))
          && (normalized.includes("na pocit") || normalized.includes("by feel"));
        const looseLongByFeel = normalized.includes("klus") && normalized.includes("na pocit") && normalized.includes("del");
        if (looseLongByFeel || longByFeel) {
          return 15;
        }
      }
      return total;
    }

    function resolveLanguageCode() {
      const lang = (document.documentElement.getAttribute("lang") || "").toLowerCase();
      return lang.startsWith("cs") ? "cs" : "en";
    }

    function formatWeekKmText(totalKm, languageCode) {
      const safeTotal = Number.isFinite(totalKm) ? totalKm : 0;
      const rounded = (Math.round(safeTotal * 10) / 10).toFixed(1);
      if (languageCode === "cs") return `${rounded.replace(".", ",")} km/týden`;
      return `${rounded} km/week`;
    }

    function formatRowKmText(totalKm, languageCode) {
      const safeTotal = Number.isFinite(totalKm) ? totalKm : 0;
      const rounded = (Math.round(safeTotal * 10) / 10).toFixed(1);
      if (languageCode === "cs") return `≈ ${rounded.replace(".", ",")} km`;
      return `≈ ${rounded} km`;
    }

    function warningTextFor(warningKey, languageCode) {
      const isCs = languageCode === "cs";
      const warningMap = {
        run_hint_but_no_distance: isCs ? "Nejasný zápis: chybí konkrétní vzdálenost (např. 8 km, 6x300m, 2R/2V)." : "Ambiguous input: missing concrete distance (e.g. 8 km, 6x300m, 2R/2V).",
        long_run_by_feel_heuristic_used: isCs ? "Použit odhad pro běh na pocit." : "Heuristic used for by-feel long run.",
        klus_minutes_estimate_used: isCs ? "Do součtu je započítán odhad z času klusu (min klus)." : "Estimated distance from jogging minutes (min klus) included.",
        pause_minutes_estimate_used: isCs ? "Do součtu je započítán odhad z pauz." : "Estimated distance from pause markers included.",
      };
      return warningMap[warningKey] || "";
    }

    function extractWarningFragment(rawText, warningKey) {
      const raw = String(rawText || "");
      if (warningKey === "run_hint_but_no_distance") {
        const m = /\b(klus|beh|běh|run|fartlek|tempo|kopec|kopce|interval)\b/i.exec(raw);
        return m ? m[0] : raw.slice(0, 24).trim();
      }
      if (warningKey === "dropped_large_km_token") {
        const re = /(\d+(?:[.,]\d+)?)\s*km\b/gi;
        let m = re.exec(raw);
        while (m) {
          const val = toNum(m[1]);
          if (val !== null && val > 60) return m[0];
          m = re.exec(raw);
        }
      }
      if (warningKey === "dropped_invalid_m_token") {
        const re = /(\d{2,5})\s*m\b/gi;
        let m = re.exec(raw);
        while (m) {
          const val = Number.parseInt(m[1], 10);
          if (Number.isFinite(val) && (val < 100 || val > 5000)) return m[0];
          m = re.exec(raw);
        }
      }
      if (warningKey === "pause_minutes_estimate_used") {
        const m = /(p\s*=\s*\d+(?:[.,]\d+)?\s*['´’]|po\s*s[ée]rii\s*\d+(?:[.,]\d+)?\s*(?:min|m(?:in)?))/i.exec(raw);
        return m ? m[0] : "";
      }
      if (warningKey === "klus_minutes_estimate_used") {
        const m = /(?:(?:po\s*s[ée]rii)\s*)?\d+(?:[.,]\d+)?\s*(?:min|m(?:in)?)\s*klus/i.exec(raw);
        return m ? m[0] : "";
      }
      if (warningKey === "long_run_by_feel_heuristic_used") {
        const m = /(na pocit|by feel)/i.exec(raw);
        return m ? m[0] : "";
      }
      return "";
    }

    function estimateRowDetails(text) {
      const raw = String(text || "").trim();
      if (!raw) {
        return { totalKm: 0, confidence: "low", warnings: [], isEmpty: true };
      }
      const normalized = raw.toLowerCase();
      const isRest = normalized === "volno" || normalized === "rest" || normalized === "rest day";
      if (isRest) {
        return { totalKm: 0, confidence: "high", warnings: [], isEmpty: false, isRest: true, raw };
      }
      const totalKm = estimateRunningKmFromText(raw);
      const warnings = [];
      const hasRunHint = RUN_HINT_RE.test(normalized);
      const hasDistanceToken = /(\d+(?:[.,]\d+)?\s*(km|m)\b|\d+\s*[rv]\b|\d{3,4}\s*-\s*\d{3,4})/i.test(normalized);
      const hasKlusMinutes = /(?:(?:po\s*s[ée]rii)\s*)?\d+(?:[.,]\d+)?\s*(?:min|m(?:in)?)\s*klus/i.test(normalized);
      const hasLongByFeel =
        ((normalized.includes("delsi klus") || normalized.includes("dlouhy klus") || normalized.includes("long run"))
          && (normalized.includes("na pocit") || normalized.includes("by feel")))
        || (normalized.includes("klus") && normalized.includes("na pocit") && normalized.includes("del"));

      if (hasRunHint && !hasDistanceToken && totalKm === 0) warnings.push("run_hint_but_no_distance");
      if (hasKlusMinutes && totalKm > 0) warnings.push("klus_minutes_estimate_used");
      if (hasLongByFeel && totalKm === 15) warnings.push("long_run_by_feel_heuristic_used");
      if (!warnings.length && totalKm === 0) warnings.push("run_hint_but_no_distance");

      let confidence = "high";
      if (totalKm === 0) confidence = "low";
      else if (warnings.length) confidence = warnings.includes("run_hint_but_no_distance") ? "low" : "medium";

      return { totalKm, confidence, warnings, isEmpty: false, isRest: false, raw };
    }

    function applyRowKmHint(row, details, languageCode) {
      if (!row || !details) return;
      let hintWrap = row.querySelector(".eb-planned-row-km-indicator-wrap");
      if (details.isEmpty) {
        if (hintWrap) hintWrap.remove();
        return;
      }
      if (!hintWrap) {
        hintWrap = document.createElement("div");
        hintWrap.className = "eb-planned-row-km-indicator-wrap";
        const trainingCell = row.querySelector(".eb-planned-training-col");
        if (!trainingCell) return;
        const dot = document.createElement("button");
        dot.type = "button";
        dot.className = "eb-planned-row-km-dot";
        dot.setAttribute("aria-label", languageCode === "cs" ? "Detail odhadu km" : "Planned km detail");
        const pop = document.createElement("div");
        pop.className = "eb-planned-row-km-popover d-none";
        const head = document.createElement("div");
        head.className = "eb-planned-row-km-popover-head";
        head.textContent = languageCode === "cs" ? "Kontrola km" : "Planned km check";
        const body = document.createElement("div");
        body.className = "eb-planned-row-km-popover-body";
        pop.appendChild(head);
        pop.appendChild(body);
        hintWrap.appendChild(dot);
        hintWrap.appendChild(pop);
        trainingCell.appendChild(hintWrap);
      }
      hintWrap.classList.remove("eb-km-confidence-high", "eb-km-confidence-medium", "eb-km-confidence-low");
      hintWrap.classList.add(`eb-km-confidence-${details.confidence}`);
      const popover = hintWrap.querySelector(".eb-planned-row-km-popover");
      if (!popover) return;
      const popoverBody = popover.querySelector(".eb-planned-row-km-popover-body");
      if (!popoverBody) return;
      const kmLabel = languageCode === "cs" ? "Km:" : "Km:";
      const reasonLabel = languageCode === "cs" ? "Důvod:" : "Reason:";
      const whereLabel = languageCode === "cs" ? "Kde:" : "Where:";
      const setBodyLines = (kmText, reasonText, whereText) => {
        popoverBody.innerHTML = `
          <div class="eb-planned-km-line"><strong>${kmLabel}</strong> ${kmText || "-"}</div>
          <div class="eb-planned-km-line"><strong>${reasonLabel}</strong> ${reasonText || "-"}</div>
          <div class="eb-planned-km-line"><strong>${whereLabel}</strong> ${whereText || "-"}</div>
        `;
      };
      if (details.isRest) {
        setBodyLines(
          formatRowKmText(details.totalKm, languageCode),
          languageCode === "cs" ? "V pořádku (volno)." : "OK (rest day).",
          ""
        );
        return;
      }
      const warningText = details.warnings.length ? warningTextFor(details.warnings[0], languageCode) : "";
      if (!warningText) {
        if (details.confidence !== "high") {
          setBodyLines(
            formatRowKmText(details.totalKm, languageCode),
            languageCode === "cs"
              ? "Nejasný zápis, doplň konkrétní vzdálenosti."
              : "Ambiguous input, add explicit distances.",
            ""
          );
        } else {
          setBodyLines(formatRowKmText(details.totalKm, languageCode), languageCode === "cs" ? "V pořádku." : "OK.", "");
        }
        return;
      }
      const fragment = extractWarningFragment(details.raw, details.warnings[0]);
      if (fragment) {
        setBodyLines(formatRowKmText(details.totalKm, languageCode), warningText, fragment);
      } else {
        setBodyLines(formatRowKmText(details.totalKm, languageCode), warningText, "");
      }
    }

    function recalcPlannedWeekTotals(widget) {
      const languageCode = resolveLanguageCode();
      const weekRows = Array.from(widget.querySelectorAll(".eb-week-row"));
      weekRows.forEach((weekRow) => {
        const plannedRows = Array.from(weekRow.querySelectorAll(".eb-col-planned tbody tr"));
        const totalNode = weekRow.querySelector(".eb-planned-week-total-km");
        if (!totalNode) return;
        const totalKm = plannedRows.reduce((sum, row) => {
          const titleNode = row.querySelector(".eb-inline-edit[data-field='title']");
          const sourceText = titleNode ? titleNode.textContent || "" : (row.querySelector(".eb-planned-training-col")?.textContent || "");
          const details = estimateRowDetails(sourceText);
          applyRowKmHint(row, details, languageCode);
          return sum + details.totalKm;
        }, 0);
        totalNode.textContent = formatWeekKmText(totalKm, languageCode);
      });
    }

    function initRulesOnboarding(widget) {
      const onboarding = widget.querySelector(".eb-plan-rules-onboarding");
      if (!onboarding) return;
      let dismissed = false;
      try {
        dismissed = window.localStorage.getItem(RULES_ONBOARDING_KEY) === "1";
      } catch (_err) {
        dismissed = false;
      }
      if (!dismissed) onboarding.classList.remove("d-none");

      const dismissBtn = onboarding.querySelector(".eb-plan-rules-dismiss");
      if (!dismissBtn || dismissBtn.dataset.ebBound === "1") return;
      dismissBtn.dataset.ebBound = "1";
      dismissBtn.addEventListener("click", () => {
        onboarding.classList.add("d-none");
        try {
          window.localStorage.setItem(RULES_ONBOARDING_KEY, "1");
        } catch (_err) {}
      });
    }

    async function saveInlineField(node, updateUrl, csrfToken, widget, scheduleEqualize) {
      if (node.dataset.saving === "1") {
        node.dataset.queued = "1";
        return;
      }

      const trainingId = Number(node.getAttribute("data-training-id"));
      const field = node.getAttribute("data-field");
      const currentValue = node.textContent || "";
      const originalValue = node.dataset.originalValue || "";
      if (!trainingId || !field || currentValue === originalValue) return;

      node.dataset.saving = "1";
      node.classList.add("is-saving");
      try {
        const payload = await metricMeasureAsync(
          "inline-save-planned",
          () =>
            postJson(
              updateUrl,
              {
                planned_id: trainingId,
                field,
                value: currentValue,
              },
              csrfToken
            ),
          { field, training_id: trainingId }
        );
        if (!payload.ok) throw new Error(payload.error || "Save failed.");
        node.dataset.originalValue = payload.value || "";
        node.classList.remove("is-error");
      } catch (err) {
        node.textContent = originalValue;
        node.classList.add("is-error");
        console.error(err);
      } finally {
        node.dataset.saving = "0";
        node.classList.remove("is-saving");
        if (node.dataset.queued === "1") {
          node.dataset.queued = "0";
          saveInlineField(node, updateUrl, csrfToken, widget, scheduleEqualize);
        }
        recalcPlannedWeekTotals(widget);
        scheduleEqualize(widget, { dirty: true });
      }
    }

    async function saveSelectField(selectNode, updateUrl, csrfToken, widget, scheduleEqualize) {
      if (selectNode.dataset.saving === "1") {
        selectNode.dataset.queued = "1";
        return;
      }
      const trainingId = Number(selectNode.getAttribute("data-training-id"));
      const field = selectNode.getAttribute("data-field");
      const currentValue = selectNode.value || "";
      const originalValue = selectNode.dataset.originalValue || "";
      if (!trainingId || !field || currentValue === originalValue) return;

      selectNode.dataset.saving = "1";
      selectNode.classList.add("is-saving");
      try {
        const payload = await metricMeasureAsync(
          "inline-save-planned-select",
          () =>
            postJson(
              updateUrl,
              {
                planned_id: trainingId,
                field,
                value: currentValue,
              },
              csrfToken
            ),
          { field, training_id: trainingId }
        );
        if (!payload.ok) throw new Error(payload.error || "Save failed.");
        selectNode.dataset.originalValue = payload.value || "";
        selectNode.classList.remove("is-error");
        // Completed rendering depends on server-side month card build; refresh to reflect new mode immediately.
        window.location.reload();
      } catch (err) {
        selectNode.value = originalValue;
        selectNode.classList.add("is-error");
        console.error(err);
      } finally {
        selectNode.dataset.saving = "0";
        selectNode.classList.remove("is-saving");
        if (selectNode.dataset.queued === "1") {
          selectNode.dataset.queued = "0";
          saveSelectField(selectNode, updateUrl, csrfToken, widget, scheduleEqualize);
        }
        scheduleEqualize(widget, { dirty: true });
      }
    }

    function initCoachInlineEditing(widget, scheduleEqualize) {
      initRulesOnboarding(widget);
      if (widget.dataset.ebKmDotClickInit !== "1") {
        widget.dataset.ebKmDotClickInit = "1";
        widget.addEventListener("click", (event) => {
          const target = event && event.target ? event.target : null;
          if (!target || typeof target.closest !== "function") return;
          const dot = target.closest(".eb-planned-row-km-dot");
          if (dot && widget.contains(dot)) {
            const wrap = dot.closest(".eb-planned-row-km-indicator-wrap");
            const pop = wrap ? wrap.querySelector(".eb-planned-row-km-popover") : null;
            if (!pop) return;
            const all = Array.from(widget.querySelectorAll(".eb-planned-row-km-popover"));
            all.forEach((node) => {
              if (node !== pop) node.classList.add("d-none");
            });
            pop.classList.toggle("d-none");
            return;
          }
          const insidePopover = target.closest(".eb-planned-row-km-popover");
          if (insidePopover) return;
          const all = Array.from(widget.querySelectorAll(".eb-planned-row-km-popover"));
          all.forEach((node) => node.classList.add("d-none"));
        });
      }
      const updateUrl = widget.getAttribute("data-plan-update-url");
      const addPhaseUrl = widget.getAttribute("data-add-phase-url");
      const removePhaseUrl = widget.getAttribute("data-remove-phase-url");
      if (!updateUrl) return;

      const csrfToken = getCsrfToken();
      const editableNodes = Array.from(widget.querySelectorAll(".eb-inline-edit[contenteditable='true']"));
      let inlineSelection = null;
      const history = createHistoryManager({
        limit: 100,
        apply(changes, direction) {
          if (!changes || !changes.length) return;
          changes.forEach((change) => {
            if (!change.node) return;
            const nextValue = direction === "undo" ? change.before : change.after;
            change.node.textContent = nextValue;
            saveInlineField(change.node, updateUrl, csrfToken, widget, scheduleEqualize);
          });
          scheduleEqualize(widget, { dirty: true });
        },
      });
      const monthGridCache = new WeakMap();

      async function addSecondPhase(node) {
        if (!addPhaseUrl) return false;
        if (node.dataset.addingPhase === "1") return false;
        const trainingId = Number(node.getAttribute("data-training-id"));
        if (!trainingId) return false;

        const sourcePlannedRow = node.closest("tr");
        const weekRow = sourcePlannedRow ? sourcePlannedRow.closest(".eb-week-row") : null;
        if (!sourcePlannedRow || !weekRow) return false;

        const plannedBody = weekRow.querySelector(".eb-col-planned tbody");
        const completedBody = weekRow.querySelector(".eb-col-completed tbody");
        if (!plannedBody || !completedBody) return false;

        node.dataset.addingPhase = "1";
        node.classList.add("is-saving");
        try {
          const payload = await postJson(
            addPhaseUrl,
            {
              planned_id: trainingId,
            },
            csrfToken
          );
          if (!payload || !payload.ok || !payload.second_phase_planned_id) {
            throw new Error((payload && payload.error) || "Add second phase failed.");
          }

          const newPlannedId = Number(payload.second_phase_planned_id);
          if (!newPlannedId) throw new Error("Invalid second phase id.");

          const plannedRows = Array.from(plannedBody.querySelectorAll("tr"));
          const rowIndex = plannedRows.indexOf(sourcePlannedRow);
          if (rowIndex === -1) return false;

          const newPlannedRow = document.createElement("tr");
          newPlannedRow.innerHTML = `
            <td class="eb-planned-date-col"></td>
            <td class="eb-planned-day-col"></td>
            <td class="eb-planned-type-col">
              <select class="form-select form-select-sm eb-inline-select" data-training-id="${newPlannedId}" data-field="session_type">
                <option value="RUN" selected>Run</option>
                <option value="WORKOUT">Workout</option>
              </select>
            </td>
            <td class="eb-planned-training-col">
              <div class="eb-inline-edit" contenteditable="true" data-training-id="${newPlannedId}" data-field="title"></div>
            </td>
            <td class="eb-planned-notes-col"><div class="eb-inline-edit" contenteditable="true" data-training-id="${newPlannedId}" data-field="notes"></div></td>
          `;
          sourcePlannedRow.insertAdjacentElement("afterend", newPlannedRow);

          const completedRows = Array.from(completedBody.querySelectorAll("tr"));
          const anchorCompletedRow = completedRows[rowIndex] || null;
          const newCompletedRow = document.createElement("tr");
          newCompletedRow.innerHTML = `
            <td><div class="eb-completed-inline-edit" contenteditable="true" data-training-id="${newPlannedId}" data-field="km">-</div></td>
            <td><div class="eb-completed-inline-edit" contenteditable="true" data-training-id="${newPlannedId}" data-field="min">-</div></td>
            <td><div class="eb-completed-inline-edit" contenteditable="true" data-training-id="${newPlannedId}" data-field="third">-</div></td>
            <td><div class="eb-completed-inline-edit" contenteditable="true" data-training-id="${newPlannedId}" data-field="avg_hr">-</div></td>
            <td><div class="eb-completed-inline-edit" contenteditable="true" data-training-id="${newPlannedId}" data-field="max_hr">-</div></td>
          `;
          if (anchorCompletedRow) anchorCompletedRow.insertAdjacentElement("afterend", newCompletedRow);
          else completedBody.appendChild(newCompletedRow);

          const month = node.closest(".month-container");
          if (month) {
            monthGridCache.delete(month);
            widget.dispatchEvent(new CustomEvent("eb:rows-changed", { detail: { month } }));
          }
          recalcPlannedWeekTotals(widget);
          scheduleEqualize(widget, { dirty: true });

          const targetField = node.getAttribute("data-field") === "notes" ? "notes" : "title";
          const nextNode = newPlannedRow.querySelector(`.eb-inline-edit[data-field="${targetField}"]`);
          if (nextNode) {
            nextNode.focus();
            placeCaretToEnd(nextNode);
          }
          return true;
        } catch (err) {
          console.error(err);
          node.classList.add("is-error");
          return false;
        } finally {
          node.dataset.addingPhase = "0";
          node.classList.remove("is-saving");
        }
      }

      async function removeSecondPhase(node) {
        if (!removePhaseUrl) return false;
        if (node.dataset.removingPhase === "1") return false;
        const trainingId = Number(node.getAttribute("data-training-id"));
        if (!trainingId) return false;

        const weekRow = node.closest(".eb-week-row");
        if (!weekRow) return false;
        const plannedBody = weekRow.querySelector(".eb-col-planned tbody");
        const completedBody = weekRow.querySelector(".eb-col-completed tbody");
        if (!plannedBody || !completedBody) return false;

        node.dataset.removingPhase = "1";
        node.classList.add("is-saving");
        try {
          const payload = await postJson(
            removePhaseUrl,
            {
              planned_id: trainingId,
            },
            csrfToken
          );
          if (!payload || !payload.ok || !payload.removed_planned_id) {
            throw new Error((payload && payload.error) || "Remove second phase failed.");
          }

          const removedId = Number(payload.removed_planned_id);
          if (!removedId) throw new Error("Invalid removed phase id.");

          const plannedRemovedNode = plannedBody.querySelector(`.eb-inline-edit[data-training-id="${removedId}"]`);
          const plannedRemovedRow = plannedRemovedNode ? plannedRemovedNode.closest("tr") : null;
          if (plannedRemovedRow) plannedRemovedRow.remove();

          const completedRemovedNode = completedBody.querySelector(`.eb-completed-inline-edit[data-training-id="${removedId}"]`);
          const completedRemovedRow = completedRemovedNode ? completedRemovedNode.closest("tr") : null;
          if (completedRemovedRow) completedRemovedRow.remove();

          const month = node.closest(".month-container");
          if (month) {
            monthGridCache.delete(month);
            widget.dispatchEvent(new CustomEvent("eb:rows-changed", { detail: { month } }));
          }
          recalcPlannedWeekTotals(widget);
          scheduleEqualize(widget, { dirty: true });

          const field = node.getAttribute("data-field") || "title";
          const fallback = plannedBody.querySelector(`.eb-inline-edit[data-training-id="${trainingId}"][data-field="${field}"]`)
            || plannedBody.querySelector(`.eb-inline-edit[data-training-id="${trainingId}"]`);
          if (fallback) {
            fallback.focus();
            placeCaretToEnd(fallback);
          }
          return true;
        } catch (err) {
          console.error(err);
          node.classList.add("is-error");
          return false;
        } finally {
          node.dataset.removingPhase = "0";
          node.classList.remove("is-saving");
        }
      }

      function getColumnNodes(month, field) {
        const grid = getMonthGrid(month);
        if (!field || !grid.rows.length) return [];
        if (field === "title") return grid.rows.map((row) => row.title).filter((node) => !!node);
        if (field === "notes") return grid.rows.map((row) => row.notes).filter((node) => !!node);
        return [];
      }

      function focusNextEditableInColumn(currentNode) {
        const field = currentNode.getAttribute("data-field");
        const month = currentNode.closest(".month-container");
        if (!field || !month) return false;
        const allInColumn = getColumnNodes(month, field);
        const currentIndex = allInColumn.indexOf(currentNode);
        if (currentIndex === -1 || currentIndex + 1 >= allInColumn.length) return false;
        const nextEditable = allInColumn[currentIndex + 1];
        nextEditable.focus();
        placeCaretToEnd(nextEditable);
        return true;
      }

      function focusPrevEditableInColumn(currentNode) {
        const field = currentNode.getAttribute("data-field");
        const month = currentNode.closest(".month-container");
        if (!field || !month) return false;
        const allInColumn = getColumnNodes(month, field);
        const currentIndex = allInColumn.indexOf(currentNode);
        if (currentIndex <= 0) return false;
        const prevEditable = allInColumn[currentIndex - 1];
        prevEditable.focus();
        placeCaretToEnd(prevEditable);
        return true;
      }

      function focusSiblingFieldInRow(currentNode, targetField) {
        const row = currentNode.closest("tr");
        if (!row) return false;
        const target = row.querySelector(`.eb-inline-edit[data-field="${targetField}"]`);
        if (!target) return false;
        target.focus();
        placeCaretToEnd(target);
        return true;
      }

      function buildMonthGrid(month) {
        if (!month) return { rows: [] };
        const titleNodes = Array.from(month.querySelectorAll(".eb-inline-edit[data-field='title'][contenteditable='true']"));
        const rows = titleNodes.map((titleNode) => {
          const row = titleNode.closest("tr");
          const notesNode = row ? row.querySelector(".eb-inline-edit[data-field='notes'][contenteditable='true']") : null;
          return { title: titleNode, notes: notesNode };
        });
        return { rows };
      }

      function getMonthGrid(month) {
        if (!month) return { rows: [] };
        const cached = monthGridCache.get(month);
        if (cached) return cached;
        const built = buildMonthGrid(month);
        monthGridCache.set(month, built);
        return built;
      }

      function getNodePosition(node) {
        const month = node.closest(".month-container");
        const grid = getMonthGrid(month);
        const rowIndex = grid.rows.findIndex((row) => row.title === node || row.notes === node);
        if (rowIndex === -1) return null;
        const colIndex = grid.rows[rowIndex].notes === node ? 1 : 0;
        return { month, rowIndex, colIndex };
      }

      function getNodeAt(month, rowIndex, colIndex) {
        const grid = getMonthGrid(month);
        if (rowIndex < 0 || rowIndex >= grid.rows.length) return null;
        if (colIndex < 0 || colIndex > 1) return null;
        const row = grid.rows[rowIndex];
        return colIndex === 0 ? row.title : row.notes;
      }

      function clearInlineSelection() {
        const selected = widget.querySelectorAll(".eb-inline-edit.is-selected, .eb-inline-edit.is-selection-anchor");
        selected.forEach((el) => {
          el.classList.remove("is-selected");
          el.classList.remove("is-selection-anchor");
        });
        inlineSelection = null;
      }

      function updateInlineSelection(anchorNode, focusNode) {
        const anchorPos = getNodePosition(anchorNode);
        const focusPos = getNodePosition(focusNode);
        if (!anchorPos || !focusPos) return;
        if (anchorPos.month !== focusPos.month) return;

        clearInlineSelection();
        const rowStart = Math.min(anchorPos.rowIndex, focusPos.rowIndex);
        const rowEnd = Math.max(anchorPos.rowIndex, focusPos.rowIndex);
        const colStart = Math.min(anchorPos.colIndex, focusPos.colIndex);
        const colEnd = Math.max(anchorPos.colIndex, focusPos.colIndex);

        const cells = [];
        for (let row = rowStart; row <= rowEnd; row += 1) {
          for (let col = colStart; col <= colEnd; col += 1) {
            const cell = getNodeAt(anchorPos.month, row, col);
            if (cell) {
              cell.classList.add("is-selected");
              cells.push(cell);
            }
          }
        }

        anchorNode.classList.add("is-selection-anchor");
        inlineSelection = {
          month: anchorPos.month,
          anchorNode,
          focusNode,
          rowStart,
          rowEnd,
          colStart,
          colEnd,
          cells,
        };
      }

      function moveByArrow(node, key) {
        const pos = getNodePosition(node);
        if (!pos) return null;
        let nextRow = pos.rowIndex;
        let nextCol = pos.colIndex;
        if (key === "ArrowUp") nextRow -= 1;
        if (key === "ArrowDown") nextRow += 1;
        if (key === "ArrowLeft") nextCol -= 1;
        if (key === "ArrowRight") nextCol += 1;
        const target = getNodeAt(pos.month, nextRow, nextCol);
        return target || null;
      }

      function hasActiveSelectionForNode(node) {
        if (!inlineSelection || !inlineSelection.cells || inlineSelection.cells.length < 2) return false;
        return inlineSelection.cells.includes(node);
      }

      function getSelectionAsTsv() {
        if (!inlineSelection || !inlineSelection.cells || !inlineSelection.cells.length) return "";
        const lines = [];
        for (let row = inlineSelection.rowStart; row <= inlineSelection.rowEnd; row += 1) {
          const cols = [];
          for (let col = inlineSelection.colStart; col <= inlineSelection.colEnd; col += 1) {
            const node = getNodeAt(inlineSelection.month, row, col);
            cols.push(node ? node.textContent || "" : "");
          }
          lines.push(cols.join("\t"));
        }
        return lines.join("\n");
      }

      function applyPastedMatrix(startNode, text) {
        const startPos = getNodePosition(startNode);
        if (!startPos) return [];
        const matrix = parsePasteMatrix(text);
        if (!matrix.length) return [];
        const changes = [];
        matrix.forEach((rowValues, rOffset) => {
          rowValues.forEach((value, cOffset) => {
            const target = getNodeAt(startPos.month, startPos.rowIndex + rOffset, startPos.colIndex + cOffset);
            if (!target) return;
            const before = target.textContent || "";
            if (before === value) return;
            target.textContent = value;
            changes.push({ node: target, before, after: value });
            saveInlineField(target, updateUrl, csrfToken, widget, scheduleEqualize);
          });
        });
        recalcPlannedWeekTotals(widget);
        scheduleEqualize(widget, { dirty: true });
        return changes;
      }

      function clearSelectedCellsIfAny() {
        if (!inlineSelection || !inlineSelection.cells || inlineSelection.cells.length < 2) return false;
        const changes = [];
        inlineSelection.cells.forEach((selectedNode) => {
          const before = selectedNode.textContent || "";
          if (!before) return;
          selectedNode.textContent = "";
          changes.push({ node: selectedNode, before, after: "" });
          saveInlineField(selectedNode, updateUrl, csrfToken, widget, scheduleEqualize);
        });
        history.push(changes);
        clearInlineSelection();
        recalcPlannedWeekTotals(widget);
        scheduleEqualize(widget, { dirty: true });
        return true;
      }

      function focusNextEditableInRowOrder(currentNode) {
        const month = currentNode.closest(".month-container");
        if (!month) return false;
        const allEditables = getMonthGrid(month).rows.flatMap((row) => [row.title, row.notes]).filter((node) => !!node);
        const currentIndex = allEditables.indexOf(currentNode);
        if (currentIndex === -1 || currentIndex + 1 >= allEditables.length) return false;
        const nextEditable = allEditables[currentIndex + 1];
        nextEditable.focus();
        placeCaretToEnd(nextEditable);
        return true;
      }

      function focusPrevEditableInRowOrder(currentNode) {
        const month = currentNode.closest(".month-container");
        if (!month) return false;
        const allEditables = getMonthGrid(month).rows.flatMap((row) => [row.title, row.notes]).filter((node) => !!node);
        const currentIndex = allEditables.indexOf(currentNode);
        if (currentIndex <= 0) return false;
        const prevEditable = allEditables[currentIndex - 1];
        prevEditable.focus();
        placeCaretToEnd(prevEditable);
        return true;
      }

      const inputTimers = new WeakMap();
      editableNodes.forEach((node) => {
        node.dataset.originalValue = node.textContent || "";
      });
      const selectNodes = Array.from(widget.querySelectorAll(".eb-inline-select[data-field='session_type']"));
      selectNodes.forEach((node) => {
        node.dataset.originalValue = node.value || "";
      });
      recalcPlannedWeekTotals(widget);
      if (widget.dataset.ebPlannedDelegatedInit === "1") return;
      widget.dataset.ebPlannedDelegatedInit = "1";

      const getNodeFromEvent = (event) => {
        const target = event && event.target ? event.target : null;
        if (!target || typeof target.closest !== "function") return null;
        const node = target.closest(".eb-inline-edit[contenteditable='true']");
        if (!node) return null;
        if (!widget.contains(node)) return null;
        return node;
      };

      widget.addEventListener("copy", (event) => {
        const node = getNodeFromEvent(event);
        if (!node) return;
        if (hasActiveSelectionForNode(node)) {
          const text = getSelectionAsTsv();
          if (setClipboardText(event, text)) return;
          if (navigator.clipboard && navigator.clipboard.writeText) {
            event.preventDefault();
            navigator.clipboard.writeText(text).catch(() => {});
            return;
          }
        }
        const text = node.textContent || "";
        if (setClipboardText(event, text)) return;
        if (navigator.clipboard && navigator.clipboard.writeText) {
          event.preventDefault();
          navigator.clipboard.writeText(text).catch(() => {});
        }
      });

      widget.addEventListener("focusin", (event) => {
        const node = getNodeFromEvent(event);
        if (!node) return;
        node.dataset.originalValue = node.textContent || "";
        if (!hasActiveSelectionForNode(node)) clearInlineSelection();
      });

      widget.addEventListener("paste", (event) => {
        const node = getNodeFromEvent(event);
        if (!node) return;
        const text = event.clipboardData ? event.clipboardData.getData("text/plain") : "";
        if (typeof text !== "string") return;
        event.preventDefault();
        const changes = applyPastedMatrix(node, text);
        history.push(changes);
        clearInlineSelection();
        recalcPlannedWeekTotals(widget);
      });

      widget.addEventListener("keydown", (event) => {
        const node = getNodeFromEvent(event);
        if (!node) return;
        const isCtrlOrMeta = event.ctrlKey || event.metaKey;
        if (isCtrlOrMeta && event.shiftKey && event.key === "Enter") {
          event.preventDefault();
          clearInlineSelection();
          saveInlineField(node, updateUrl, csrfToken, widget, scheduleEqualize);
          removeSecondPhase(node);
          return;
        }
        if (isCtrlOrMeta && event.key === "Enter") {
          event.preventDefault();
          clearInlineSelection();
          saveInlineField(node, updateUrl, csrfToken, widget, scheduleEqualize);
          addSecondPhase(node);
          return;
        }
        if (isCtrlOrMeta && (event.key === "z" || event.key === "Z")) {
          event.preventDefault();
          if (event.shiftKey) history.redo();
          else history.undo();
          clearInlineSelection();
          return;
        }
        if (isCtrlOrMeta && (event.key === "y" || event.key === "Y")) {
          event.preventDefault();
          history.redo();
          clearInlineSelection();
          return;
        }

        if (event.shiftKey && (event.key === "ArrowUp" || event.key === "ArrowDown" || event.key === "ArrowLeft" || event.key === "ArrowRight")) {
          event.preventDefault();
          const selectionAnchor = inlineSelection && inlineSelection.anchorNode ? inlineSelection.anchorNode : node;
          const baseFocus = inlineSelection && inlineSelection.focusNode ? inlineSelection.focusNode : node;
          const nextFocus = moveByArrow(baseFocus, event.key);
          if (!nextFocus) return;
          updateInlineSelection(selectionAnchor, nextFocus);
          nextFocus.focus();
          placeCaretToEnd(nextFocus);
          return;
        }

        if (event.key === "Enter") {
          event.preventDefault();
          clearInlineSelection();
          saveInlineField(node, updateUrl, csrfToken, widget, scheduleEqualize);
          if (!focusNextEditableInColumn(node)) node.blur();
          return;
        }

        if (event.key === "Tab") {
          event.preventDefault();
          clearInlineSelection();
          saveInlineField(node, updateUrl, csrfToken, widget, scheduleEqualize);
          const moved = event.shiftKey ? focusPrevEditableInRowOrder(node) : focusNextEditableInRowOrder(node);
          if (!moved) node.blur();
          return;
        }

        if (event.key === "Delete") {
          event.preventDefault();
          if (!clearSelectedCellsIfAny()) {
            const before = node.textContent || "";
            if (!before) return;
            node.textContent = "";
            saveInlineField(node, updateUrl, csrfToken, widget, scheduleEqualize);
            history.push([{ node, before, after: "" }]);
            recalcPlannedWeekTotals(widget);
            scheduleEqualize(widget, { dirty: true });
          }
          return;
        }

        if (event.key === "Backspace") {
          if (clearSelectedCellsIfAny()) {
            event.preventDefault();
            return;
          }
        }

        if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;

        if (event.key === "ArrowDown") {
          event.preventDefault();
          clearInlineSelection();
          saveInlineField(node, updateUrl, csrfToken, widget, scheduleEqualize);
          focusNextEditableInColumn(node);
          return;
        }

        if (event.key === "ArrowUp") {
          event.preventDefault();
          clearInlineSelection();
          saveInlineField(node, updateUrl, csrfToken, widget, scheduleEqualize);
          focusPrevEditableInColumn(node);
          return;
        }

        if (event.key === "ArrowRight") {
          if (node.getAttribute("data-field") === "title") {
            event.preventDefault();
            clearInlineSelection();
            saveInlineField(node, updateUrl, csrfToken, widget, scheduleEqualize);
            focusSiblingFieldInRow(node, "notes");
          }
          return;
        }

        if (event.key === "ArrowLeft") {
          if (node.getAttribute("data-field") === "notes") {
            event.preventDefault();
            clearInlineSelection();
            saveInlineField(node, updateUrl, csrfToken, widget, scheduleEqualize);
            focusSiblingFieldInRow(node, "title");
          }
        }
      });

      widget.addEventListener("input", (event) => {
        const node = getNodeFromEvent(event);
        if (!node) return;
        const timerId = inputTimers.get(node);
        if (timerId) clearTimeout(timerId);
        const nextTimerId = setTimeout(() => {
          inputTimers.delete(node);
          saveInlineField(node, updateUrl, csrfToken, widget, scheduleEqualize);
        }, 500);
        inputTimers.set(node, nextTimerId);
        recalcPlannedWeekTotals(widget);
        scheduleEqualize(widget, { dirty: true });
      });

      widget.addEventListener("focusout", (event) => {
        const node = getNodeFromEvent(event);
        if (!node) return;
        const timerId = inputTimers.get(node);
        if (timerId) {
          clearTimeout(timerId);
          inputTimers.delete(node);
        }
        saveInlineField(node, updateUrl, csrfToken, widget, scheduleEqualize);
      });

      widget.addEventListener("change", (event) => {
        const target = event && event.target ? event.target : null;
        if (!target || typeof target.closest !== "function") return;
        const selectNode = target.closest(".eb-inline-select[data-field='session_type']");
        if (!selectNode || !widget.contains(selectNode)) return;
        saveSelectField(selectNode, updateUrl, csrfToken, widget, scheduleEqualize);
      });

      widget.addEventListener("focusout", (event) => {
        const target = event && event.target ? event.target : null;
        if (!target || typeof target.closest !== "function") return;
        const selectNode = target.closest(".eb-inline-select[data-field='session_type']");
        if (!selectNode || !widget.contains(selectNode)) return;
        saveSelectField(selectNode, updateUrl, csrfToken, widget, scheduleEqualize);
      });

      widget.addEventListener("eb:rows-changed", (event) => {
        const month = event && event.detail ? event.detail.month : null;
        if (!month) return;
        monthGridCache.delete(month);
      });
    }

    return {
      initCoachInlineEditing,
    };
  }

  window.EB.editorPlanned = {
    createPlannedEditor,
  };
})();
