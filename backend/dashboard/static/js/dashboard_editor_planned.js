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
    const NUM_RE = "\\d+(?:[.,]\\d+)?";
    const MULT_RANGE_PAREN_RE = new RegExp(`(${NUM_RE})\\s*-\\s*(${NUM_RE})\\s*[x×]\\s*\\(([^)]*)\\)`, "gi");
    const MULT_PAREN_WITH_TAIL_SERIES_RE = new RegExp(`(${NUM_RE})\\s*[x×]\\s*\\(([^)]*)\\)\\s*(?:mk|mch)?\\s*(\\d{3,4}(?:\\s*-\\s*\\d{3,4})+)m\\b`, "gi");
    const MULT_SINGLE_PAREN_RE = new RegExp(`(${NUM_RE})\\s*[x×]\\s*\\(([^)]*)\\)`, "gi");
    const MULT_CHAIN_DIST_RANGE_RE = new RegExp(`(${NUM_RE})\\s*-\\s*(${NUM_RE})\\s*[x×]\\s*(${NUM_RE})\\s*[x×]\\s*(${NUM_RE})\\s*(km|m)\\b`, "gi");
    const MULT_CHAIN_DIST_SINGLE_RE = new RegExp(`(${NUM_RE})\\s*[x×]\\s*(${NUM_RE})\\s*[x×]\\s*(${NUM_RE})\\s*(km|m)\\b`, "gi");
    const MULT_DIST_RANGE_RE = new RegExp(`(${NUM_RE})\\s*-\\s*(${NUM_RE})\\s*[x×]\\s*(${NUM_RE})\\s*(km|m)\\b`, "gi");
    const MULT_DIST_SINGLE_RE = new RegExp(`(${NUM_RE})\\s*[x×]\\s*(${NUM_RE})\\s*(km|m)\\b`, "gi");
    const RV_KM_RE = new RegExp(`(?<!\\w)(${NUM_RE})\\s*([RV])(?=$|[\\s,;+()/-])`, "g");
    const RANGE_UNIT_RE = new RegExp(`(${NUM_RE})\\s*-\\s*(${NUM_RE})\\s*(km|m)\\b`, "gi");
    const SINGLE_UNIT_RE = new RegExp(`(${NUM_RE})\\s*(km|m)\\b`, "gi");
    const BARE_M_SERIES_RE = /\b(\d{3,4}(?:\s*-\s*\d{3,4}){1,})\b/gi;
    const BARE_M_TOKEN_RE = /(?<!\d)(\d{3,4})(?!\d)/g;
    const WALK_RE = /(chuze|mch|walk|walking|hike)/i;
    const PAUSE_MIN_RE = /(?:\bp\s*=\s*|\bpo\s*serii\s*)(\d+(?:[.,]\d+)?)\s*['´’]/gi;

    function toNum(value) {
      const parsed = Number.parseFloat(String(value || "").replace(",", "."));
      return Number.isFinite(parsed) ? parsed : null;
    }

    function isWalkContext(text, start, end) {
      const separators = "+,;/|";
      let segLeft = start;
      while (segLeft > 0 && !separators.includes(text[segLeft - 1])) segLeft -= 1;
      let segRight = end;
      while (segRight < text.length && !separators.includes(text[segRight])) segRight += 1;
      const segment = text.slice(segLeft, segRight).toLowerCase();
      const relStart = start - segLeft;
      const relEnd = end - segLeft;
      const keywords = ["chuze", "mch", "walk", "walking", "hike"];
      for (const keyword of keywords) {
        let pos = segment.indexOf(keyword);
        while (pos !== -1) {
          let distance = 0;
          if (pos < relStart) distance = relStart - (pos + keyword.length);
          else if (pos > relEnd) distance = pos - relEnd;
          if (distance <= 3) return true;
          pos = segment.indexOf(keyword, pos + 1);
        }
      }
      return false;
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
      if (!text) return 0;
      let total = 0;
      PAUSE_MIN_RE.lastIndex = 0;
      let match = PAUSE_MIN_RE.exec(text);
      while (match) {
        const mins = toNum(match[1]);
        if (mins !== null && mins >= 0) total += mins * 0.15;
        match = PAUSE_MIN_RE.exec(text);
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

      let out = consumeRegex(mutable, MULT_RANGE_PAREN_RE, (m) => {
        const a = toNum(m[1]);
        const b = toNum(m[2]);
        if (a === null || b === null || a < 0 || b < 0) return 0;
        const mult = (a + b) / 2;
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
        return ((a1 + a2) / 2) * b * toKm(d, m[5]);
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
        return ((a + b) / 2) * toKm(d, m[4]);
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

      out = consumeRegex(mutable, RV_KM_RE, (m, src) => {
        const start = m.index;
        const end = start + m[0].length;
        if (isWalkContext(src, start, end)) return 0;
        const value = toNum(m[1]);
        if (value === null || value < 0) return 0;
        return value;
      });
      total += out.total;
      mutable = out.text;

      out = consumeRegex(mutable, RANGE_UNIT_RE, (m, src) => {
        const start = m.index;
        const end = start + m[0].length;
        if (isWalkContext(src, start, end)) return 0;
        const a = toNum(m[1]);
        const b = toNum(m[2]);
        if (a === null || b === null || a < 0 || b < 0) return 0;
        return toKm((a + b) / 2, m[3]);
      });
      total += out.total;
      mutable = out.text;

      out = consumeRegex(mutable, SINGLE_UNIT_RE, (m, src) => {
        const start = m.index;
        const end = start + m[0].length;
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

    function recalcPlannedWeekTotals(widget) {
      const languageCode = resolveLanguageCode();
      const weekRows = Array.from(widget.querySelectorAll(".eb-week-row"));
      weekRows.forEach((weekRow) => {
        const trainingCells = Array.from(weekRow.querySelectorAll(".eb-col-planned tbody td.eb-planned-training-col"));
        const totalNode = weekRow.querySelector(".eb-planned-week-total-km");
        if (!totalNode) return;
        const totalKm = trainingCells.reduce((sum, cell) => sum + estimateRunningKmFromText(cell.textContent || ""), 0);
        totalNode.textContent = formatWeekKmText(totalKm, languageCode);
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

    function initCoachInlineEditing(widget, scheduleEqualize) {
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
            <td class="eb-planned-training-col"><div class="eb-inline-edit" contenteditable="true" data-training-id="${newPlannedId}" data-field="title"></div></td>
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
