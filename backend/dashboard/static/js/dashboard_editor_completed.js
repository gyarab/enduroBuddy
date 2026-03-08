(function () {
  window.EB = window.EB || {};

  function createCompletedEditor(deps) {
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

    function parseNum(text) {
      if (text == null) return null;
      const normalized = String(text).trim().replace(",", ".");
      if (!normalized || normalized === "-") return null;
      const value = Number.parseFloat(normalized);
      return Number.isFinite(value) ? value : null;
    }

    function recalcCompletedWeekTotals(widget) {
      const weekRows = Array.from(widget.querySelectorAll(".eb-week-row"));
      weekRows.forEach((weekRow) => {
        const table = weekRow.querySelector(".eb-col-completed table");
        if (!table) return;
        const bodyRows = Array.from(table.querySelectorAll("tbody tr"));
        let totalKm = 0;
        let totalMin = 0;
        let hrNum = 0;
        let hrDen = 0;
        let maxHr = null;

        bodyRows.forEach((row) => {
          const cells = row.querySelectorAll("td");
          if (!cells || cells.length < 5) return;
          const kmVal = parseNum(cells[0].textContent);
          const minVal = parseNum(cells[1].textContent);
          const avgHrVal = parseNum(cells[3].textContent);
          const maxHrVal = parseNum(cells[4].textContent);

          if (kmVal !== null) totalKm += kmVal;
          if (minVal !== null) totalMin += minVal;
          if (avgHrVal !== null && minVal !== null && minVal > 0) {
            hrNum += avgHrVal * minVal;
            hrDen += minVal;
          }
          if (maxHrVal !== null) {
            maxHr = maxHr === null ? maxHrVal : Math.max(maxHr, maxHrVal);
          }
        });

        const foot = table.querySelector("tfoot tr");
        if (!foot) return;
        const footCells = foot.querySelectorAll("th");
        if (!footCells || footCells.length < 5) return;
        footCells[0].textContent = totalKm > 0 ? totalKm.toFixed(2) : "-";
        footCells[1].textContent = totalMin > 0 ? String(Math.round(totalMin)) : "-";
        footCells[3].textContent = hrDen > 0 ? String(Math.round(hrNum / hrDen)) : "-";
        footCells[4].textContent = maxHr !== null ? String(Math.round(maxHr)) : "-";
      });
    }

    function initCompletedInlineEditing(widget, scheduleEqualize) {
      const updateUrl = widget.getAttribute("data-completed-update-url");
      const addPhaseUrl = widget.getAttribute("data-add-phase-url");
      const removePhaseUrl = widget.getAttribute("data-remove-phase-url");
      if (!updateUrl) return;

      const csrfToken = getCsrfToken();
      const editableNodes = Array.from(widget.querySelectorAll(".eb-completed-inline-edit[contenteditable='true']"));
      if (!editableNodes.length) return;

      let inlineSelection = null;
      const history = createHistoryManager({
        limit: 100,
        apply(changes, direction) {
          if (!changes || !changes.length) return;
          changes.forEach((change) => {
            const next = direction === "undo" ? change.before : change.after;
            change.node.textContent = next;
            saveCompletedField(change.node);
          });
          scheduleEqualize(widget, { dirty: true });
        },
      });
      const monthTableCache = new WeakMap();

      async function addSecondPhase(node) {
        if (!addPhaseUrl) return false;
        if (node.dataset.addingPhase === "1") return false;
        const trainingId = Number(node.getAttribute("data-training-id"));
        if (!trainingId) return false;

        const sourceCompletedRow = node.closest("tr");
        const weekRow = sourceCompletedRow ? sourceCompletedRow.closest(".eb-week-row") : null;
        if (!sourceCompletedRow || !weekRow) return false;

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

          const completedRows = Array.from(completedBody.querySelectorAll("tr"));
          const rowIndex = completedRows.indexOf(sourceCompletedRow);
          if (rowIndex === -1) return false;

          const plannedRows = Array.from(plannedBody.querySelectorAll("tr"));
          const anchorPlannedRow = plannedRows[rowIndex] || null;
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
            <td class="eb-planned-training-col"><div class="eb-inline-edit" contenteditable="true" data-training-id="${newPlannedId}" data-field="title"></div></td>
            <td class="eb-planned-notes-col"><div class="eb-inline-edit" contenteditable="true" data-training-id="${newPlannedId}" data-field="notes"></div></td>
          `;
          if (anchorPlannedRow) anchorPlannedRow.insertAdjacentElement("afterend", newPlannedRow);
          else plannedBody.appendChild(newPlannedRow);

          const newCompletedRow = document.createElement("tr");
          newCompletedRow.innerHTML = `
            <td><div class="eb-completed-inline-edit" contenteditable="true" data-training-id="${newPlannedId}" data-field="km">-</div></td>
            <td><div class="eb-completed-inline-edit" contenteditable="true" data-training-id="${newPlannedId}" data-field="min">-</div></td>
            <td><div class="eb-completed-inline-edit" contenteditable="true" data-training-id="${newPlannedId}" data-field="third">-</div></td>
            <td><div class="eb-completed-inline-edit" contenteditable="true" data-training-id="${newPlannedId}" data-field="avg_hr">-</div></td>
            <td><div class="eb-completed-inline-edit" contenteditable="true" data-training-id="${newPlannedId}" data-field="max_hr">-</div></td>
          `;
          sourceCompletedRow.insertAdjacentElement("afterend", newCompletedRow);

          const month = node.closest(".month-container");
          if (month) {
            monthTableCache.delete(month);
            widget.dispatchEvent(new CustomEvent("eb:rows-changed", { detail: { month } }));
          }
          recalcCompletedWeekTotals(widget);
          scheduleEqualize(widget, { dirty: true });

          const field = node.getAttribute("data-field") || "km";
          const nextNode = newCompletedRow.querySelector(`.eb-completed-inline-edit[data-field="${field}"]`);
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

          const completedRemovedNode = completedBody.querySelector(`.eb-completed-inline-edit[data-training-id="${removedId}"]`);
          const completedRemovedRow = completedRemovedNode ? completedRemovedNode.closest("tr") : null;
          if (completedRemovedRow) completedRemovedRow.remove();

          const plannedRemovedNode = plannedBody.querySelector(`.eb-inline-edit[data-training-id="${removedId}"]`);
          const plannedRemovedRow = plannedRemovedNode ? plannedRemovedNode.closest("tr") : null;
          if (plannedRemovedRow) plannedRemovedRow.remove();

          const month = node.closest(".month-container");
          if (month) {
            monthTableCache.delete(month);
            widget.dispatchEvent(new CustomEvent("eb:rows-changed", { detail: { month } }));
          }
          recalcCompletedWeekTotals(widget);
          scheduleEqualize(widget, { dirty: true });

          const field = node.getAttribute("data-field") || "km";
          const fallback = completedBody.querySelector(`.eb-completed-inline-edit[data-training-id="${trainingId}"][data-field="${field}"]`)
            || completedBody.querySelector(`.eb-completed-inline-edit[data-training-id="${trainingId}"]`);
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

      async function saveCompletedField(node) {
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
            "inline-save-completed",
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

          const normalized = payload.value == null ? "-" : String(payload.value);
          node.textContent = normalized;
          node.dataset.originalValue = normalized;
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
            saveCompletedField(node);
          }
          recalcCompletedWeekTotals(widget);
          scheduleEqualize(widget, { dirty: true });
        }
      }

      function buildTableRows(month) {
        if (!month) return [];
        const rows = Array.from(month.querySelectorAll(".eb-col-completed tbody tr"));
        return rows
          .map((row) => Array.from(row.querySelectorAll(".eb-completed-inline-edit[contenteditable='true']")))
          .filter((cells) => cells.length > 0);
      }

      function getTableRows(month) {
        if (!month) return [];
        const cached = monthTableCache.get(month);
        if (cached) return cached;
        const built = buildTableRows(month);
        monthTableCache.set(month, built);
        return built;
      }

      function getNodePosition(node) {
        const month = node.closest(".month-container");
        const tableRows = getTableRows(month);
        for (let r = 0; r < tableRows.length; r += 1) {
          const c = tableRows[r].indexOf(node);
          if (c !== -1) return { month, rowIndex: r, colIndex: c };
        }
        return null;
      }

      function getNodeAt(month, rowIndex, colIndex) {
        const tableRows = getTableRows(month);
        if (rowIndex < 0 || rowIndex >= tableRows.length) return null;
        if (colIndex < 0 || colIndex >= tableRows[rowIndex].length) return null;
        return tableRows[rowIndex][colIndex];
      }

      function clearInlineSelection() {
        const selected = widget.querySelectorAll(".eb-completed-inline-edit.is-selected, .eb-completed-inline-edit.is-selection-anchor");
        selected.forEach((el) => {
          el.classList.remove("is-selected");
          el.classList.remove("is-selection-anchor");
        });
        inlineSelection = null;
      }

      function updateInlineSelection(anchorNode, focusNode) {
        const anchorPos = getNodePosition(anchorNode);
        const focusPos = getNodePosition(focusNode);
        if (!anchorPos || !focusPos || anchorPos.month !== focusPos.month) return;

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
        inlineSelection = { month: anchorPos.month, anchorNode, focusNode, rowStart, rowEnd, colStart, colEnd, cells };
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
        return getNodeAt(pos.month, nextRow, nextCol);
      }

      function getLinearOrder(month) {
        return getTableRows(month).flat();
      }

      function focusLinear(node, direction) {
        const month = node.closest(".month-container");
        const all = getLinearOrder(month);
        const idx = all.indexOf(node);
        if (idx === -1) return false;
        const nextIdx = idx + direction;
        if (nextIdx < 0 || nextIdx >= all.length) return false;
        all[nextIdx].focus();
        placeCaretToEnd(all[nextIdx]);
        return true;
      }

      function focusInColumn(node, direction) {
        const pos = getNodePosition(node);
        if (!pos) return false;
        const target = getNodeAt(pos.month, pos.rowIndex + direction, pos.colIndex);
        if (!target) return false;
        target.focus();
        placeCaretToEnd(target);
        return true;
      }

      function hasActiveSelectionForNode(node) {
        return !!(inlineSelection && inlineSelection.cells && inlineSelection.cells.length > 1 && inlineSelection.cells.includes(node));
      }

      function getSelectionAsTsv() {
        if (!inlineSelection || !inlineSelection.cells || !inlineSelection.cells.length) return "";
        const lines = [];
        for (let row = inlineSelection.rowStart; row <= inlineSelection.rowEnd; row += 1) {
          const cols = [];
          for (let col = inlineSelection.colStart; col <= inlineSelection.colEnd; col += 1) {
            const node = getNodeAt(inlineSelection.month, row, col);
            cols.push(node ? (node.textContent || "") : "");
          }
          lines.push(cols.join("\t"));
        }
        return lines.join("\n");
      }

      function clearSelectedCellsIfAny() {
        if (!inlineSelection || !inlineSelection.cells || inlineSelection.cells.length < 2) return false;
        const changes = [];
        inlineSelection.cells.forEach((selectedNode) => {
          const before = selectedNode.textContent || "";
          if (!before || before === "-") return;
          selectedNode.textContent = "";
          changes.push({ node: selectedNode, before, after: "" });
          saveCompletedField(selectedNode);
        });
        history.push(changes);
        clearInlineSelection();
        scheduleEqualize(widget, { dirty: true });
        recalcCompletedWeekTotals(widget);
        return true;
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
            saveCompletedField(target);
          });
        });
        scheduleEqualize(widget, { dirty: true });
        recalcCompletedWeekTotals(widget);
        return changes;
      }

      const inputTimers = new WeakMap();
      editableNodes.forEach((node) => {
        node.dataset.originalValue = node.textContent || "";
      });
      recalcCompletedWeekTotals(widget);
      if (widget.dataset.ebCompletedDelegatedInit === "1") return;
      widget.dataset.ebCompletedDelegatedInit = "1";

      const getNodeFromEvent = (event) => {
        const target = event && event.target ? event.target : null;
        if (!target || typeof target.closest !== "function") return null;
        const node = target.closest(".eb-completed-inline-edit[contenteditable='true']");
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
        }
        const text = node.textContent || "";
        setClipboardText(event, text);
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
        event.preventDefault();
        const changes = applyPastedMatrix(node, text);
        history.push(changes);
        clearInlineSelection();
      });

      widget.addEventListener("keydown", (event) => {
        const node = getNodeFromEvent(event);
        if (!node) return;
        const isCtrlOrMeta = event.ctrlKey || event.metaKey;
        if (isCtrlOrMeta && event.shiftKey && event.key === "Enter") {
          event.preventDefault();
          clearInlineSelection();
          saveCompletedField(node);
          removeSecondPhase(node);
          return;
        }
        if (isCtrlOrMeta && event.key === "Enter") {
          event.preventDefault();
          clearInlineSelection();
          saveCompletedField(node);
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
          const anchor = inlineSelection && inlineSelection.anchorNode ? inlineSelection.anchorNode : node;
          const baseFocus = inlineSelection && inlineSelection.focusNode ? inlineSelection.focusNode : node;
          const nextFocus = moveByArrow(baseFocus, event.key);
          if (!nextFocus) return;
          updateInlineSelection(anchor, nextFocus);
          nextFocus.focus();
          placeCaretToEnd(nextFocus);
          return;
        }

        if (event.key === "Enter") {
          event.preventDefault();
          clearInlineSelection();
          saveCompletedField(node);
          if (!focusInColumn(node, 1)) node.blur();
          return;
        }

        if (event.key === "Tab") {
          event.preventDefault();
          clearInlineSelection();
          saveCompletedField(node);
          const moved = event.shiftKey ? focusLinear(node, -1) : focusLinear(node, 1);
          if (!moved) node.blur();
          return;
        }

        if (event.key === "Delete") {
          event.preventDefault();
          if (!clearSelectedCellsIfAny()) {
            const before = node.textContent || "";
            if (!before || before === "-") return;
            node.textContent = "";
            saveCompletedField(node);
            history.push([{ node, before, after: "" }]);
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
          saveCompletedField(node);
          focusInColumn(node, 1);
          return;
        }

        if (event.key === "ArrowUp") {
          event.preventDefault();
          clearInlineSelection();
          saveCompletedField(node);
          focusInColumn(node, -1);
          return;
        }

        if (event.key === "ArrowRight") {
          event.preventDefault();
          clearInlineSelection();
          saveCompletedField(node);
          focusLinear(node, 1);
          return;
        }

        if (event.key === "ArrowLeft") {
          event.preventDefault();
          clearInlineSelection();
          saveCompletedField(node);
          focusLinear(node, -1);
        }
      });

      widget.addEventListener("input", (event) => {
        const node = getNodeFromEvent(event);
        if (!node) return;
        const timerId = inputTimers.get(node);
        if (timerId) clearTimeout(timerId);
        const nextTimerId = setTimeout(() => {
          inputTimers.delete(node);
          saveCompletedField(node);
        }, 500);
        inputTimers.set(node, nextTimerId);
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
        saveCompletedField(node);
      });

      widget.addEventListener("eb:rows-changed", (event) => {
        const month = event && event.detail ? event.detail.month : null;
        if (!month) return;
        monthTableCache.delete(month);
      });
    }

    return {
      initCompletedInlineEditing,
    };
  }

  window.EB.editorCompleted = {
    createCompletedEditor,
  };
})();
