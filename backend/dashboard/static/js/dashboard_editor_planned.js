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
        scheduleEqualize(widget, { dirty: true });
      }
    }

    function initCoachInlineEditing(widget, scheduleEqualize) {
      const updateUrl = widget.getAttribute("data-plan-update-url");
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
      });

      widget.addEventListener("keydown", (event) => {
        const node = getNodeFromEvent(event);
        if (!node) return;
        const isCtrlOrMeta = event.ctrlKey || event.metaKey;
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
    }

    return {
      initCoachInlineEditing,
    };
  }

  window.EB.editorPlanned = {
    createPlannedEditor,
  };
})();
