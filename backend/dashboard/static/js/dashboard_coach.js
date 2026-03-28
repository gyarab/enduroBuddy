(function () {
  window.EB = window.EB || {};

  function createCoachController(deps) {
    const metrics = (window.EB && window.EB.metrics) || {};
    const metricStart = metrics.start || (() => null);
    const metricEnd = metrics.end || (() => null);
    const getNotifications = () => (window.EB && window.EB.notifications) || null;
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
      if (!response.ok) throw new Error(`Požadavek selhal se stavem ${response.status}`);
      return response.json();
    });
    const postForm = (deps && deps.postForm) || (async (url, formData, csrfToken) => {
      const response = await fetch(url, {
        method: "POST",
        body: formData,
        headers: {
          "X-Requested-With": "XMLHttpRequest",
          "X-CSRFToken": csrfToken || "",
        },
        credentials: "same-origin",
      });
      if (!response.ok) throw new Error(`Požadavek selhal se stavem ${response.status}`);
      return response;
    });
    const getHtml = (deps && deps.getHtml) || (async (url) => {
      const response = await fetch(url, {
        method: "GET",
        headers: { "X-Requested-With": "XMLHttpRequest" },
        credentials: "same-origin",
      });
      if (!response.ok) throw new Error(`Požadavek selhal se stavem ${response.status}`);
      return response.text();
    });
    const initCoachMainContent = (deps && deps.initCoachMainContent) || (() => {});
    const ui = (window.EB && window.EB.ui) || {};
    const setButtonBusy = ui.setButtonBusy || (() => {});
    const mobileAthletePickerMedia = window.matchMedia ? window.matchMedia("(max-width: 991.98px)") : null;
    const mobilePlanRevealKey = "eb_coach_mobile_show_plan_once";

    function initCoachAthleteFocus() {
      const input = document.getElementById("coachAthleteFocusInput");
      if (!input) return;

      const updateUrl = input.getAttribute("data-focus-update-url");
      const athleteId = Number(input.getAttribute("data-athlete-id"));
      if (!updateUrl || !athleteId) return;

      const csrfToken = getCsrfToken();
      input.dataset.savedValue = input.value || "";

      function applyFocusToSidebar(value) {
        const summaryNode = document.querySelector(`.eb-athlete-item[data-athlete-id="${athleteId}"] [data-athlete-summary]`);
        if (!summaryNode) return;
        const athleteName = summaryNode.getAttribute("data-athlete-name") || "";
        const emptyFocusLabelAttr = summaryNode.getAttribute("data-empty-focus-label");
        const emptyFocusLabel = emptyFocusLabelAttr === null ? "" : emptyFocusLabelAttr;
        const suffix = value ? String(value) : emptyFocusLabel;
        const combined = suffix ? `${athleteName} - ${suffix}` : athleteName;
        summaryNode.textContent = combined.slice(0, 31);
      }

      async function saveFocus() {
        const raw = (input.value || "").slice(0, 10);
        if (input.value !== raw) {
          input.value = raw;
        }
        if (raw === (input.dataset.savedValue || "")) return;

        input.classList.add("is-saving");
        try {
          const payload = await postJson(
            updateUrl,
            {
              athlete_id: athleteId,
              focus: raw,
            },
            csrfToken
          );
          if (!payload.ok) {
            throw new Error(payload.error || "Uložení fokusu selhalo.");
          }

          input.dataset.savedValue = payload.focus || "";
          input.value = payload.focus || "";
          input.classList.remove("is-error");
          applyFocusToSidebar(payload.focus || "");
          } catch (err) {
            input.classList.add("is-error");
            input.value = input.dataset.savedValue || "";
            const notifications = getNotifications();
            if (notifications) {
              notifications.addNotification({
                id: `coach-focus-error-${athleteId}`,
                text: (err && err.message) || "Uložení zaměření selhalo.",
                tone: "danger",
                unread: true,
              });
            }
            console.error(err);
          } finally {
            input.classList.remove("is-saving");
          }
        }

      let timerId = null;
      input.addEventListener("input", () => {
        if ((input.value || "").length > 10) {
          input.value = (input.value || "").slice(0, 10);
        }
        if (timerId) clearTimeout(timerId);
        timerId = setTimeout(() => {
          timerId = null;
          saveFocus();
        }, 450);
      });

      input.addEventListener("blur", () => {
        if (timerId) {
          clearTimeout(timerId);
          timerId = null;
        }
        saveFocus();
      });

      input.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
          event.preventDefault();
          input.blur();
        }
      });
    }

    function initCoachLegendModal() {
      const legendModal = document.getElementById("coachLegendModal");
      if (!legendModal) return;
      if (legendModal.dataset.initialized === "1") return;
      legendModal.dataset.initialized = "1";

      const athleteIdNode = legendModal.querySelector("[data-legend-athlete-id]");
      const athleteId = athleteIdNode ? String(athleteIdNode.getAttribute("data-legend-athlete-id") || "") : "";
      if (!athleteId) return;
      const isCs = (document.documentElement.lang || "").toLowerCase().startsWith("cs");
      const zoneTableBody = legendModal.querySelector("[data-legend-zone-table-body]");
      const aerobicDisplay = legendModal.querySelector("[data-legend-threshold-display='aerobic']");
      const anaerobicDisplay = legendModal.querySelector("[data-legend-threshold-display='anaerobic']");
      const prBody = legendModal.querySelector("[data-legend-pr-body]");
      const prEmptyRow = legendModal.querySelector("[data-legend-pr-empty-row]");
      const prModal = document.getElementById("coachLegendPrModal");
      const prSelect = prModal ? prModal.querySelector("[data-legend-pr-select]") : null;
      const prTimeInput = prModal ? prModal.querySelector("[data-legend-pr-time-input]") : null;
      const prAddButton = prModal ? prModal.querySelector("[data-legend-pr-add]") : null;
      const zonesModal = document.getElementById("coachLegendZonesModal");
      const thresholdsModal = document.getElementById("coachLegendThresholdModal");
      const zonesSaveButton = zonesModal ? zonesModal.querySelector("[data-legend-zones-modal-save]") : null;
      const thresholdSaveButton = thresholdsModal ? thresholdsModal.querySelector("[data-legend-threshold-modal-save]") : null;
      const thresholdEditAerobic = thresholdsModal ? thresholdsModal.querySelector("[data-legend-threshold-edit='aerobic']") : null;
      const thresholdEditAnaerobic = thresholdsModal ? thresholdsModal.querySelector("[data-legend-threshold-edit='anaerobic']") : null;
      const legendEditable = athleteIdNode.getAttribute("data-legend-editable") === "1";
      const legendSaveUrl = athleteIdNode.getAttribute("data-legend-save-url") || "";
      if (
        !zoneTableBody ||
        !aerobicDisplay ||
        !anaerobicDisplay ||
        !prBody ||
        (legendEditable && !prModal) ||
        (legendEditable && !prSelect) ||
        (legendEditable && !prTimeInput) ||
        (legendEditable && !prAddButton) ||
        (legendEditable && !zonesModal) ||
        (legendEditable && !thresholdsModal) ||
        (legendEditable && !zonesSaveButton) ||
        (legendEditable && !thresholdSaveButton) ||
        (legendEditable && !thresholdEditAerobic) ||
        (legendEditable && !thresholdEditAnaerobic)
      ) return;

      const childOpenButtons = Array.from(legendModal.querySelectorAll("[data-legend-open-modal]"));
      const initialStateRaw = athleteIdNode.getAttribute("data-legend-state") || "{}";
      const prOrderMap = {
        "800m": 1,
        "1000m": 2,
        "1 mile": 3,
        "1500m": 4,
        "2 miles": 5,
        "3000m": 6,
        "3k": 7,
        "5000m": 8,
        "5k": 9,
        "10000m": 10,
        "10k": 11,
        "half marathon": 12,
        "půlmaraton": 12,
        "marathon": 13,
        "maraton": 13,
      };
      const legacyPrFieldToDistance = {
        pr_800m: "800m",
        pr_1000m: "1000m",
        pr_1_mile: "1 mile",
        pr_1500m: "1500m",
        pr_2_miles: "2 miles",
        pr_3000m: "3000m",
        pr_3k: "3k",
        pr_5000m: "5000m",
        pr_5k: "5k",
        pr_10000m: "10000m",
        pr_10k: "10k",
        pr_half_marathon: "Half marathon",
        pr_marathon: "Marathon",
      };
      let currentState = {};

      function readInitialState() {
        try {
          const parsed = JSON.parse(initialStateRaw);
          return parsed && typeof parsed === "object" ? parsed : {};
        } catch (_) {
          return {};
        }
      }

      function normalizeState(savedState) {
        const source = savedState && typeof savedState === "object" ? savedState : {};
        const next = {};

        const zones = source.zones && typeof source.zones === "object" ? source.zones : {};
        const normalizedZones = {};
        for (let zone = 1; zone <= 5; zone += 1) {
          const direct = zones[String(zone)];
          const from = direct && typeof direct === "object"
            ? String(direct.from || "").trim()
            : String(source[`hr_z${zone}_from`] || "").trim();
          const to = direct && typeof direct === "object"
            ? String(direct.to || "").trim()
            : String(source[`hr_z${zone}_to`] || "").trim();
          if (from && to) {
            normalizedZones[String(zone)] = { from, to };
          }
        }
        if (Object.keys(normalizedZones).length) {
          next.zones = normalizedZones;
        }

        const aerobic = String(source.aerobic_threshold || "").trim();
        const anaerobic = String(source.anaerobic_threshold || "").trim();
        if (aerobic) next.aerobic_threshold = aerobic;
        if (anaerobic) next.anaerobic_threshold = anaerobic;

        const prs = Array.isArray(source.prs) ? source.prs : [];
        if (prs.length) {
          next.prs = prs
            .map((item) => {
              if (!item || typeof item !== "object") return null;
              return {
                distance: normalizeDistance(item.distance),
                time: String(item.time || "").trim(),
              };
            })
            .filter((item) => !!item && item.distance);
        } else {
          const fallback = [];
          Object.keys(legacyPrFieldToDistance).forEach((legacyField) => {
            const legacyValue = String(source[legacyField] || "").trim();
            if (!legacyValue) return;
            fallback.push({
              distance: legacyPrFieldToDistance[legacyField],
              time: legacyValue,
            });
          });
          if (fallback.length) next.prs = fallback;
        }

        return next;
      }

      async function writeSavedState(nextState, options) {
        if (!legendEditable || !legendSaveUrl) return;
        const opts = options || {};
        try {
          await postJson(
            legendSaveUrl,
            { state: nextState || {} },
            getCsrfToken()
          );
          const notifications = getNotifications();
          if (notifications && opts.successText) {
            notifications.addNotification({
              id: `legend-save-${athleteId}`,
              text: opts.successText,
              tone: "success",
              unread: true,
            });
          }
        } catch (err) {
          const notifications = getNotifications();
          if (notifications) {
            notifications.addNotification({
              id: `legend-save-error-${athleteId}`,
              text: (err && err.message) || "Ulozeni legendy selhalo.",
              tone: "danger",
              unread: true,
            });
          }
          console.error(err);
        }
      }

      function getPrRows() {
        return Array.from(prBody.querySelectorAll("tr[data-legend-pr-row='1']"));
      }

      function updatePrEmptyState() {
        if (!prEmptyRow) return;
        prEmptyRow.classList.toggle("d-none", getPrRows().length > 0);
      }

      function clearPrRows() {
        getPrRows().forEach((row) => row.remove());
        updatePrEmptyState();
      }

      function getPrSortOrder(distance) {
        const normalized = normalizeDistanceKey(distance);
        return Object.prototype.hasOwnProperty.call(prOrderMap, normalized) ? prOrderMap[normalized] : 999;
      }

      function getTimeFormatForDistance(distance) {
        const normalized = normalizeDistanceKey(distance);
        if (normalized === "10000m" || normalized === "10k" || normalized === "half marathon" || normalized === "půlmaraton" || normalized === "marathon" || normalized === "maraton") {
          return "hhmmss";
        }
        return "mmss";
      }

      function formatDigitsAsTime(digitsInput, format, keepTrailingColon) {
        const digits = String(digitsInput || "").replace(/\D/g, "");
        if (format === "hhmmss") {
          const limited = digits.slice(0, 6);
          const hh = limited.slice(0, 2);
          const mm = limited.slice(2, 4);
          const ss = limited.slice(4, 6);
          if (limited.length <= 2) {
            if (keepTrailingColon && limited.length === 2) return `${hh}:`;
            return hh;
          }
          if (limited.length <= 4) {
            const partial = `${hh}:${mm}`;
            if (keepTrailingColon && limited.length === 4) return `${partial}:`;
            return partial;
          }
          return `${hh}:${mm}:${ss}`;
        }

        const limited = digits.slice(0, 4);
        const mm = limited.slice(0, 2);
        const ss = limited.slice(2, 4);
        if (limited.length <= 2) {
          if (keepTrailingColon && limited.length === 2) return `${mm}:`;
          return mm;
        }
        return `${mm}:${ss}`;
      }

      function normalizeFinalTime(value, format) {
        const keepTrailing = false;
        return formatDigitsAsTime(value, format, keepTrailing);
      }

      function renderZoneTable() {
        zoneTableBody.innerHTML = "";
        const zones = (currentState && currentState.zones && typeof currentState.zones === "object") ? currentState.zones : {};
        for (let zone = 1; zone <= 5; zone += 1) {
          const data = zones[String(zone)] || {};
          const from = String(data.from || "").trim();
          const to = String(data.to || "").trim();
          const range = from && to ? `${from}-${to}` : "-";
          const tr = document.createElement("tr");
          tr.innerHTML = `<td>Z${zone}</td><td>${range}</td>`;
          zoneTableBody.appendChild(tr);
        }
      }

      function renderThresholdDisplays() {
        const aerobicValue = String((currentState && currentState.aerobic_threshold) || "").trim();
        const anaerobicValue = String((currentState && currentState.anaerobic_threshold) || "").trim();
        aerobicDisplay.textContent = aerobicValue || "-";
        anaerobicDisplay.textContent = anaerobicValue || "-";
      }

      function normalizeDistance(distance) {
        return String(distance || "").trim();
      }

      function normalizeDistanceKey(distance) {
        return normalizeDistance(distance)
          .toLowerCase()
          .normalize("NFD")
          .replace(/[\u0300-\u036f]/g, "");
      }

      function hasPrDistance(distance) {
        const normalized = normalizeDistanceKey(distance);
        if (!normalized) return false;
        return getPrRows().some((row) => {
          const rowDistance = normalizeDistanceKey(row.getAttribute("data-distance"));
          return rowDistance === normalized;
        });
      }

      function createPrRow(distance, timeValue) {
        const normalizedDistance = normalizeDistance(distance);
        if (!normalizedDistance || hasPrDistance(normalizedDistance)) return null;

        const row = document.createElement("tr");
        row.setAttribute("data-legend-pr-row", "1");
        row.setAttribute("data-distance", normalizedDistance);

        const distanceCell = document.createElement("td");
        distanceCell.className = "eb-legend-pr-distance";
        distanceCell.textContent = normalizedDistance;

        const timeCell = document.createElement("td");
        const timeFormat = getTimeFormatForDistance(normalizedDistance);
        if (legendEditable) {
          const timeInput = document.createElement("input");
          timeInput.className = "form-control form-control-sm";
          timeInput.type = "text";
          timeInput.maxLength = 20;
          timeInput.placeholder = timeFormat === "hhmmss" ? "hh:mm:ss" : "mm:ss";
          timeInput.value = normalizeFinalTime(String(timeValue || ""), timeFormat);
          timeInput.setAttribute("data-legend-pr-time", "1");
          timeInput.addEventListener("input", () => {
            timeInput.value = formatDigitsAsTime(timeInput.value, timeFormat, true);
            saveStateFromInputs();
          });
          timeInput.addEventListener("blur", () => {
            timeInput.value = normalizeFinalTime(timeInput.value, timeFormat);
            saveStateFromInputs();
          });
          timeCell.appendChild(timeInput);
        } else {
          timeCell.textContent = normalizeFinalTime(String(timeValue || ""), timeFormat) || "-";
        }

        row.appendChild(distanceCell);
        row.appendChild(timeCell);
        let inserted = false;
        const nextOrder = getPrSortOrder(normalizedDistance);
        getPrRows().forEach((existingRow) => {
          if (inserted) return;
          const existingDistance = normalizeDistance(existingRow.getAttribute("data-distance"));
          const existingOrder = getPrSortOrder(existingDistance);
          if (nextOrder < existingOrder || (nextOrder === existingOrder && normalizedDistance.localeCompare(existingDistance, "cs", { sensitivity: "base" }) < 0)) {
            prBody.insertBefore(row, existingRow);
            inserted = true;
          }
        });
        if (!inserted) {
          prBody.appendChild(row);
        }
        updatePrEmptyState();
        return row;
      }

      function loadStateIntoInputs() {
        currentState = normalizeState(readInitialState());
        renderZoneTable();
        renderThresholdDisplays();
        clearPrRows();
        const parsedPrs = Array.isArray(currentState.prs) ? currentState.prs : [];
        if (parsedPrs.length) {
          parsedPrs.forEach((item) => {
            if (!item || typeof item !== "object") return;
            createPrRow(item.distance, item.time || "");
          });
        }
      }

      function saveStateFromInputs() {
        const prs = getPrRows()
          .map((row) => {
            const distance = normalizeDistance(row.getAttribute("data-distance"));
            const timeInput = row.querySelector("[data-legend-pr-time='1']");
            const time = timeInput && "value" in timeInput ? String(timeInput.value || "").trim() : "";
            if (!distance) return null;
            return { distance, time };
          })
          .filter((item) => !!item);
        if (prs.length) {
          currentState.prs = prs;
        } else {
          delete currentState.prs;
        }
        writeSavedState(currentState);
      }

      legendModal.addEventListener("show.bs.modal", loadStateIntoInputs);
      if (legendEditable) {
        childOpenButtons.forEach((button) => {
          if (button.dataset.legendOpenInit === "1") return;
          button.dataset.legendOpenInit = "1";
          button.addEventListener("click", (event) => {
            event.preventDefault();
            const targetSelector = button.getAttribute("data-legend-open-modal") || "";
            if (!targetSelector) return;
            const targetModal = document.querySelector(targetSelector);
            if (!targetModal || !(window.bootstrap && window.bootstrap.Modal)) return;
            const instance = window.bootstrap.Modal.getOrCreateInstance(targetModal, { backdrop: false });
            instance.show();
          });
        });
        zonesModal.addEventListener("show.bs.modal", () => {
          const zones = currentState && currentState.zones ? currentState.zones : {};
          for (let z = 1; z <= 5; z += 1) {
            const fromInput = zonesModal.querySelector(`[data-legend-zone-edit-from='${z}']`);
            const toInput = zonesModal.querySelector(`[data-legend-zone-edit-to='${z}']`);
            if (!fromInput || !toInput) continue;
            fromInput.value = zones[String(z)] ? String(zones[String(z)].from || "") : "";
            toInput.value = zones[String(z)] ? String(zones[String(z)].to || "") : "";
          }
        });
        zonesSaveButton.addEventListener("click", () => {
          const nextZones = {};
          for (let z = 1; z <= 5; z += 1) {
            const fromInput = zonesModal.querySelector(`[data-legend-zone-edit-from='${z}']`);
            const toInput = zonesModal.querySelector(`[data-legend-zone-edit-to='${z}']`);
            if (!fromInput || !toInput) continue;
            const from = String(fromInput.value || "").trim();
            const to = String(toInput.value || "").trim();
            if (!from && !to) continue;
            const fromNum = Number(from);
            const toNum = Number(to);
            if (!Number.isFinite(fromNum) || !Number.isFinite(toNum) || fromNum > toNum) continue;
            nextZones[String(z)] = { from, to };
          }
          if (Object.keys(nextZones).length) {
            currentState.zones = nextZones;
          } else {
            delete currentState.zones;
          }
          writeSavedState(currentState, { successText: "Zóny byly uloženy." });
          renderZoneTable();
          const modal = window.bootstrap && window.bootstrap.Modal ? window.bootstrap.Modal.getInstance(zonesModal) : null;
          if (modal) modal.hide();
        });

        thresholdsModal.addEventListener("show.bs.modal", () => {
          thresholdEditAerobic.value = currentState && currentState.aerobic_threshold ? String(currentState.aerobic_threshold) : "";
          thresholdEditAnaerobic.value = currentState && currentState.anaerobic_threshold ? String(currentState.anaerobic_threshold) : "";
        });
        thresholdSaveButton.addEventListener("click", () => {
          const aerobic = String(thresholdEditAerobic.value || "").trim();
          const anaerobic = String(thresholdEditAnaerobic.value || "").trim();
          if (aerobic) currentState.aerobic_threshold = aerobic;
          else delete currentState.aerobic_threshold;
          if (anaerobic) currentState.anaerobic_threshold = anaerobic;
          else delete currentState.anaerobic_threshold;
          writeSavedState(currentState, { successText: "Prahy byly uloženy." });
          renderThresholdDisplays();
          const modal = window.bootstrap && window.bootstrap.Modal ? window.bootstrap.Modal.getInstance(thresholdsModal) : null;
          if (modal) modal.hide();
        });

        [thresholdEditAerobic, thresholdEditAnaerobic].forEach((input) => {
          input.addEventListener("keydown", (event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              thresholdSaveButton.click();
            }
          });
        });
        prModal.addEventListener("show.bs.modal", () => {
          prTimeInput.value = "";
          const selectedDistance = normalizeDistance(prSelect.value);
          prTimeInput.placeholder = getTimeFormatForDistance(selectedDistance) === "hhmmss" ? "hh:mm:ss" : "mm:ss";
        });
        prSelect.addEventListener("change", () => {
          const selectedDistance = normalizeDistance(prSelect.value);
          const format = getTimeFormatForDistance(selectedDistance);
          prTimeInput.placeholder = format === "hhmmss" ? "hh:mm:ss" : "mm:ss";
          prTimeInput.value = normalizeFinalTime(prTimeInput.value, format);
        });
        prTimeInput.addEventListener("input", () => {
          const selectedDistance = normalizeDistance(prSelect.value);
          const format = getTimeFormatForDistance(selectedDistance);
          prTimeInput.value = formatDigitsAsTime(prTimeInput.value, format, true);
        });
        prTimeInput.addEventListener("blur", () => {
          const selectedDistance = normalizeDistance(prSelect.value);
          const format = getTimeFormatForDistance(selectedDistance);
          prTimeInput.value = normalizeFinalTime(prTimeInput.value, format);
        });
        prAddButton.addEventListener("click", () => {
          const distance = normalizeDistance(prSelect.value);
          const format = getTimeFormatForDistance(distance);
          const timeValue = normalizeFinalTime(prTimeInput.value, format);
          if (!distance || hasPrDistance(distance)) return;
          const newRow = createPrRow(distance, timeValue);
          if (newRow) {
            saveStateFromInputs();
            prTimeInput.value = "";
            const notifications = getNotifications();
            if (notifications) {
              notifications.addNotification({
                id: `legend-pr-${athleteId}`,
                text: "Osobní rekord byl uložen.",
                tone: "success",
                unread: true,
              });
            }
            const modal = window.bootstrap && window.bootstrap.Modal ? window.bootstrap.Modal.getInstance(prModal) : null;
            if (modal) modal.hide();
          }
        });
      }

      loadStateIntoInputs();
    }

    function initCoachAthleteReorder() {
      const list = document.getElementById("coachAthleteList");
      if (!list) return;

      const reorderUrl = list.getAttribute("data-reorder-url");
      if (!reorderUrl) return;
      const csrfToken = getCsrfToken();

      let draggedItem = null;
      let hasOrderChanged = false;
      const getReorderableItems = () => Array.from(list.querySelectorAll(".eb-athlete-item[data-reorderable='1']"));

      list.querySelectorAll(".eb-athlete-item[data-reorderable='1'] a").forEach((anchor) => {
        anchor.addEventListener("dragstart", (event) => {
          event.preventDefault();
        });
      });

      function getDragAfterElement(container, y) {
        const candidates = getReorderableItems().filter((item) => !item.classList.contains("is-dragging"));
        let closest = { offset: Number.NEGATIVE_INFINITY, element: null };
        candidates.forEach((item) => {
          const box = item.getBoundingClientRect();
          const offset = y - box.top - box.height / 2;
          if (offset < 0 && offset > closest.offset) {
            closest = { offset, element: item };
          }
        });
        return closest.element;
      }

      async function persistOrder() {
        const ids = getReorderableItems()
          .map((item) => Number(item.getAttribute("data-athlete-id")))
          .filter((id) => !!id);

        try {
          await postJson(reorderUrl, { athlete_ids: ids }, csrfToken);
          const notifications = getNotifications();
          if (notifications) {
            notifications.addNotification({
              id: "coach-reorder-success",
              text: "Pořadí svěřenců bylo uloženo.",
              tone: "success",
              unread: true,
            });
          }
        } catch (err) {
          const notifications = getNotifications();
          if (notifications) {
            notifications.addNotification({
              id: "coach-reorder-error",
              text: (err && err.message) || "Uložení pořadí svěřenců selhalo.",
              tone: "danger",
              unread: true,
            });
          }
          console.error(err);
        }
      }

      list.querySelectorAll(".eb-athlete-item[data-reorderable='1']").forEach((item) => {
        item.addEventListener("dragstart", (event) => {
          draggedItem = item;
          hasOrderChanged = false;
          item.classList.add("is-dragging");
          if (event.dataTransfer) {
            event.dataTransfer.effectAllowed = "move";
            event.dataTransfer.setData("text/plain", item.getAttribute("data-athlete-id") || "");
          }
        });

        item.addEventListener("dragend", () => {
          item.classList.remove("is-dragging");
          const changed = hasOrderChanged;
          draggedItem = null;
          if (changed) {
            persistOrder();
          }
        });
      });

      list.addEventListener("dragover", (event) => {
        if (!draggedItem) return;
        event.preventDefault();
        const afterElement = getDragAfterElement(list, event.clientY);
        if (!afterElement) {
          const reorderables = getReorderableItems();
          const lastReorderable = reorderables.length ? reorderables[reorderables.length - 1] : null;
          if (lastReorderable && lastReorderable !== draggedItem) {
            lastReorderable.insertAdjacentElement("afterend", draggedItem);
            hasOrderChanged = true;
          }
        } else {
          if (afterElement !== draggedItem.nextElementSibling) {
            list.insertBefore(draggedItem, afterElement);
            hasOrderChanged = true;
          }
        }
      });
    }

    function initCoachSidebarToggle() {
      const shell = document.getElementById("coachShell");
      if (!shell) return;
      const toggleButtons = Array.from(document.querySelectorAll("[data-athlete-sidebar-toggle='1']"));
      if (!toggleButtons.length) return;

      const storageKey = "eb_coach_athletes_collapsed";
      const state = {
        desktopCollapsed: window.localStorage.getItem(storageKey) === "1",
        mobilePickerOpen: false,
        mobileSelectionRequired: false,
        mobilePlanVisible: false,
      };

      function isMobileViewport() {
        return !!(mobileAthletePickerMedia && mobileAthletePickerMedia.matches);
      }

      function consumeMobilePlanRevealFlag() {
        try {
          if (window.sessionStorage.getItem(mobilePlanRevealKey) === "1") {
            window.sessionStorage.removeItem(mobilePlanRevealKey);
            return true;
          }
        } catch (_err) {
          return false;
        }
        return false;
      }

      function setMobilePlanRevealFlag() {
        try {
          window.sessionStorage.setItem(mobilePlanRevealKey, "1");
        } catch (_err) {
          // Ignore storage failures; navigation will still work.
        }
      }

      function syncMobileState() {
        if (!isMobileViewport()) {
          state.mobilePickerOpen = false;
          state.mobileSelectionRequired = false;
          state.mobilePlanVisible = false;
          return;
        }
        const shouldRevealPlan = consumeMobilePlanRevealFlag();
        state.mobilePickerOpen = false;
        state.mobileSelectionRequired = false;
        state.mobilePlanVisible = true;
        if (shouldRevealPlan) {
          state.mobileSelectionRequired = false;
          state.mobilePlanVisible = true;
        }
      }

      function applyState(isCollapsed) {
        const mobileSelectionRequired = isMobileViewport() && state.mobileSelectionRequired;
        const mobilePickerOpen = isMobileViewport() && state.mobilePickerOpen;
        const mobilePlanVisible = isMobileViewport() && state.mobilePlanVisible;
        shell.classList.toggle("is-athletes-collapsed", isCollapsed);
        shell.classList.toggle("is-mobile-athlete-selection-required", mobileSelectionRequired);
        shell.classList.toggle("is-mobile-athlete-picker-open", mobilePickerOpen);
        shell.classList.toggle("is-mobile-plan-visible", mobilePlanVisible);
        toggleButtons.forEach((button) => {
          button.setAttribute("aria-expanded", isCollapsed ? "false" : "true");
          const expandedTitle = button.getAttribute("data-title-expand") || "Hide athletes";
          const collapsedTitle = button.getAttribute("data-title-collapse") || "Show athletes";
          const nextTitle = isCollapsed ? collapsedTitle : expandedTitle;
          button.setAttribute("title", nextTitle);
          button.setAttribute("aria-label", nextTitle);
        });
      }

      syncMobileState();
      applyState(isMobileViewport() ? !state.mobilePickerOpen : state.desktopCollapsed);

      toggleButtons.forEach((button) => {
        if (button.dataset.toggleSidebarInit === "1") return;
        button.dataset.toggleSidebarInit = "1";
        button.addEventListener("click", () => {
          if (isMobileViewport()) {
            state.mobilePickerOpen = !state.mobilePickerOpen;
            state.mobileSelectionRequired = false;
            state.mobilePlanVisible = true;
            applyState(!state.mobilePickerOpen);
            return;
          }
          state.desktopCollapsed = !shell.classList.contains("is-athletes-collapsed");
          applyState(state.desktopCollapsed);
          window.localStorage.setItem(storageKey, state.desktopCollapsed ? "1" : "0");
        });
      });

      if (mobileAthletePickerMedia && shell.dataset.mobileSidebarListenerInit !== "1") {
        shell.dataset.mobileSidebarListenerInit = "1";
        const handleViewportChange = () => {
          syncMobileState();
          applyState(isMobileViewport() ? !state.mobilePickerOpen : state.desktopCollapsed);
        };
        if (typeof mobileAthletePickerMedia.addEventListener === "function") {
          mobileAthletePickerMedia.addEventListener("change", handleViewportChange);
        } else if (typeof mobileAthletePickerMedia.addListener === "function") {
          mobileAthletePickerMedia.addListener(handleViewportChange);
        }
      }

      shell._coachRevealPlanAfterSelection = () => {
        if (!isMobileViewport()) return;
        setMobilePlanRevealFlag();
      };
    }

    function updateCoachSidebarActiveState(targetUrl) {
      const list = document.getElementById("coachAthleteList");
      if (!list) return;

      let normalizedTarget = "";
      try {
        const parsedTarget = new URL(targetUrl, window.location.origin);
        normalizedTarget = `${parsedTarget.pathname}${parsedTarget.search}`;
      } catch (_) {
        normalizedTarget = String(targetUrl || "");
      }

      const items = Array.from(list.querySelectorAll(".eb-athlete-switch-item[href]"));
      items.forEach((item) => {
        let normalizedItem = "";
        try {
          const parsedItem = new URL(item.href, window.location.origin);
          normalizedItem = `${parsedItem.pathname}${parsedItem.search}`;
        } catch (_) {
          normalizedItem = item.getAttribute("href") || "";
        }

        const isActive = normalizedItem === normalizedTarget;
        item.classList.toggle("active", isActive);
        item.classList.toggle("btn-dark", isActive);
        item.classList.toggle("btn-outline-dark", !isActive);
      });
    }

    function initCoachAthleteKeyboardSwitch() {
      if (document.body.dataset.ebCoachKeyboardInit === "1") return;
      document.body.dataset.ebCoachKeyboardInit = "1";

      function getItems() {
        return Array.from(document.querySelectorAll(".eb-athlete-switch-item[href]"));
      }

      function getCurrentIndex(items) {
        const activeIndex = items.findIndex((item) => item.classList.contains("active"));
        return activeIndex >= 0 ? activeIndex : 0;
      }

      function shouldIgnoreShortcut() {
        const activeElement = document.activeElement;
        if (!activeElement) return false;
        if (activeElement.isContentEditable) return true;
        const tag = (activeElement.tagName || "").toLowerCase();
        return tag === "input" || tag === "textarea" || tag === "select";
      }

      async function softNavigateToCoachAthlete(url) {
        const metricToken = metricStart("athlete-switch");
        let metricClosed = false;
        const closeMetric = (meta) => {
          if (metricClosed) return;
          metricClosed = true;
          metricEnd(metricToken, meta);
        };
        const shell = document.getElementById("coachShell");
        if (!shell) {
          window.location.href = url;
          closeMetric({ target: url, fallback: "hard_nav_no_shell" });
          return;
        }
        if (shell.dataset.loading === "1") return;

        const currentLegendModal = document.getElementById("coachLegendModal");
        const legendWasOpen = !!(currentLegendModal && currentLegendModal.classList.contains("show"));

        shell.dataset.loading = "1";
        shell.classList.add("is-loading");
        try {
          const html = await getHtml(url);
          const parser = new DOMParser();
          const doc = parser.parseFromString(html, "text/html");
          const replacement = doc.getElementById("coachShell");
          if (!replacement) throw new Error("Replacement shell not found.");
          const replacementSidebar = replacement.querySelector(".eb-coach-sidebar");
          const replacementMain = replacement.querySelector(".eb-coach-main");
          const currentSidebar = shell.querySelector(".eb-coach-sidebar");
          const currentMain = shell.querySelector(".eb-coach-main");
          if (!replacementSidebar || !currentSidebar || !replacementMain || !currentMain) {
            throw new Error("Replacement coach content not found.");
          }

          currentSidebar.replaceWith(replacementSidebar);
          currentMain.replaceWith(replacementMain);
          ["coachLegendModal", "coachLegendZonesModal", "coachLegendThresholdModal", "coachLegendPrModal"].forEach((modalId) => {
            const currentModal = document.getElementById(modalId);
            const nextModal = doc.getElementById(modalId);
            if (currentModal && nextModal) {
              currentModal.replaceWith(nextModal);
            } else if (currentModal && !nextModal) {
              currentModal.remove();
            } else if (!currentModal && nextModal) {
              document.body.appendChild(nextModal);
            }
          });
          if (window.location.href !== url) {
            window.history.pushState({}, "", url);
          }
          if (doc.title) {
            document.title = doc.title;
          }
          initCoachShellContent();
          if (legendWasOpen && window.bootstrap && window.bootstrap.Modal) {
            const nextLegendModal = document.getElementById("coachLegendModal");
            if (nextLegendModal) {
              window.bootstrap.Modal.getOrCreateInstance(nextLegendModal).show();
            }
          }
        } catch (err) {
          console.error(err);
          closeMetric({ target: url, fallback: "hard_nav_error" });
          window.location.href = url;
        } finally {
          const activeShell = document.getElementById("coachShell");
          if (activeShell) {
            activeShell.dataset.loading = "0";
            activeShell.classList.remove("is-loading");
          }
          closeMetric({ target: url, soft: true });
        }
      }

      document.addEventListener("keydown", (event) => {
        if (!event.ctrlKey || event.altKey || event.metaKey) return;
        if (event.key !== "ArrowUp" && event.key !== "ArrowDown") return;
        if (shouldIgnoreShortcut()) return;

        const items = getItems();
        if (!items.length) return;

        event.preventDefault();
        const currentIndex = getCurrentIndex(items);
        const direction = event.key === "ArrowDown" ? 1 : -1;
        const nextIndex = (currentIndex + direction + items.length) % items.length;
        const target = items[nextIndex];
        if (!target || !target.href) return;
        softNavigateToCoachAthlete(target.href);
      });

      document.addEventListener("click", (event) => {
        const target = event.target && typeof event.target.closest === "function"
          ? event.target.closest(".eb-athlete-switch-item[href]")
          : null;
        if (!target) return;
        if (event.defaultPrevented) return;
        if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
        const href = target.getAttribute("href") || target.href;
        if (!href) return;

        const shell = document.getElementById("coachShell");
        if (shell && typeof shell._coachRevealPlanAfterSelection === "function") {
          shell._coachRevealPlanAfterSelection();
        }

        event.preventDefault();
        softNavigateToCoachAthlete(href);
      });
    }

    function initCoachAthleteRemovalModal() {
      const removeModal = document.getElementById("coachRemoveAthleteModal");
      if (!removeModal) return;
      if (removeModal.dataset.initialized === "1") return;
      removeModal.dataset.initialized = "1";

      const athleteIdInput = document.getElementById("coachRemoveAthleteIdInput");
      const expectedNameNode = document.getElementById("coachRemoveAthleteExpectedName");
      const confirmInput = document.getElementById("coachRemoveAthleteConfirmInput");
      const submitBtn = document.getElementById("coachRemoveAthleteSubmitBtn");
      if (!athleteIdInput || !expectedNameNode || !confirmInput || !submitBtn) return;

      let expectedName = "";

      function refreshSubmitState() {
        submitBtn.disabled = (confirmInput.value || "").trim() !== expectedName;
      }

      removeModal.addEventListener("show.bs.modal", (event) => {
        const trigger = event.relatedTarget;
        const button = trigger && typeof trigger.getAttribute === "function" ? trigger : null;
        const athleteId = button ? button.getAttribute("data-remove-athlete-id") || "" : "";
        expectedName = button ? (button.getAttribute("data-remove-athlete-name") || "").trim() : "";
        athleteIdInput.value = athleteId;
        expectedNameNode.textContent = expectedName;
        confirmInput.value = "";
        refreshSubmitState();
        window.setTimeout(() => {
          confirmInput.focus();
        }, 80);
      });

      confirmInput.addEventListener("input", refreshSubmitState);
    }

    function initCoachAthleteVisibilityToggle() {
      const manageModal = document.getElementById("coachManageModal");
      if (!manageModal) return;
      if (manageModal.dataset.visibilityToggleInitialized === "1") return;
      manageModal.dataset.visibilityToggleInitialized = "1";

      const eyeIcon = `
      <svg class="eb-icon-svg" viewBox="0 0 16 16" aria-hidden="true" focusable="false">
        <path d="M1.2 8s2.4-4 6.8-4 6.8 4 6.8 4-2.4 4-6.8 4-6.8-4-6.8-4Z" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"></path>
        <circle cx="8" cy="8" r="1.8" fill="none" stroke="currentColor" stroke-width="1.3"></circle>
      </svg>
    `;
      const eyeSlashIcon = `
      <svg class="eb-icon-svg" viewBox="0 0 16 16" aria-hidden="true" focusable="false">
        <path d="M1.2 8s2.4-4 6.8-4 6.8 4 6.8 4-2.4 4-6.8 4-6.8-4-6.8-4Z" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"></path>
        <circle cx="8" cy="8" r="1.8" fill="none" stroke="currentColor" stroke-width="1.3"></circle>
        <path d="M3 13 13 3" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"></path>
      </svg>
    `;

      manageModal.addEventListener("submit", async (event) => {
        const form = event.target;
        if (!(form instanceof HTMLFormElement)) return;
        if (form.getAttribute("data-athlete-visibility-form") !== "1") return;

        event.preventDefault();
        const actionInput = form.querySelector("input[name='action']");
        const button = form.querySelector("button[type='submit']");
        if (!actionInput || !button) {
          form.submit();
          return;
        }

        setButtonBusy(button, true, { label: "" });
        try {
          const response = await postForm(form.getAttribute("action") || window.location.href, new FormData(form), getCsrfToken() || "");
          const payload = await response.json();
          if (!payload || !payload.ok) throw new Error("Přepnutí viditelnosti selhalo.");

          const isHidden = !!payload.hidden;
          const row = form.closest(".eb-manage-athlete-row");
          if (row) {
            row.classList.toggle("is-hidden", isHidden);
          }
          actionInput.value = isHidden ? "show_athlete" : "hide_athlete";

          const showLabel = button.getAttribute("data-label-show") || "Show";
          const hideLabel = button.getAttribute("data-label-hide") || "Hide";
            const nextLabel = isHidden ? showLabel : hideLabel;
            button.setAttribute("title", nextLabel);
            button.setAttribute("aria-label", nextLabel);
            button.innerHTML = isHidden ? eyeSlashIcon : eyeIcon;
            const notifications = getNotifications();
            if (notifications) {
              notifications.addNotification({
                id: `coach-visibility-${payload.athlete_id}`,
                text: isHidden ? "Svěřenec byl skryt z plánu." : "Svěřenec byl znovu zobrazen v plánech.",
                tone: "success",
                unread: true,
              });
            }
          } catch (err) {
            const notifications = getNotifications();
            if (notifications) {
              notifications.addNotification({
                id: "coach-visibility-error",
                text: (err && err.message) || "Prepnuti viditelnosti selhalo.",
                tone: "danger",
                unread: true,
              });
            }
            console.error(err);
            form.submit();
          } finally {
          setButtonBusy(button, false);
        }
      });
    }

    function initCoachShellContent() {
      initCoachMainContent(document);
      initCoachAthleteFocus();
      initCoachLegendModal();
      initCoachAthleteReorder();
      initCoachSidebarToggle();
      initCoachAthleteRemovalModal();
      initCoachAthleteVisibilityToggle();
    }

    return {
      initCoachShellContent,
      initCoachAthleteKeyboardSwitch,
    };
  }

  window.EB.coach = {
    createCoachController,
  };
})();
