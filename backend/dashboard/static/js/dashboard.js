(function () {
  function getCookie(name) {
    const cookieValue = document.cookie
      .split(";")
      .map((c) => c.trim())
      .find((c) => c.startsWith(`${name}=`));
    if (!cookieValue) return null;
    return decodeURIComponent(cookieValue.substring(name.length + 1));
  }

  function getCsrfToken() {
    return (
      getCookie("endurobuddy_csrftoken") ||
      getCookie("csrftoken") ||
      (document.querySelector("input[name='csrfmiddlewaretoken']") || {}).value ||
      ""
    );
  }

  function showMonth(widget, monthId) {
    widget.querySelectorAll(".month-container").forEach((el) => {
      el.classList.remove("is-active");
    });

    const target = widget.querySelector(`.month-container[data-month-id="${monthId}"]`);
    if (target) target.classList.add("is-active");

    widget.querySelectorAll(".month-btn").forEach((btn) => {
      const isActive = btn.getAttribute("data-month-id") === String(monthId);
      btn.classList.toggle("is-active", isActive);
      btn.classList.toggle("btn-outline-dark", !isActive);
      btn.classList.toggle("btn-dark", isActive);
    });

    equalizeMonthColumns(widget, monthId);
  }

  function equalizeMonthColumns(widget, monthId) {
    const month = widget.querySelector(`.month-container[data-month-id="${monthId}"]`);
    if (!month) return;

    const plannedCols = Array.from(month.querySelectorAll(".eb-col-planned"));
    const completedCols = Array.from(month.querySelectorAll(".eb-col-completed"));
    if (!plannedCols.length || !completedCols.length) return;

    plannedCols.forEach((col) => {
      col.style.width = "";
      col.style.minWidth = "";
      col.style.flexBasis = "";
    });
    completedCols.forEach((col) => {
      col.style.width = "";
      col.style.minWidth = "";
      col.style.flexBasis = "";
    });

    month.style.removeProperty("--eb-planned-training-col-width");
    month.style.removeProperty("--eb-planned-notes-col-width");

    const trainingNodes = Array.from(
      month.querySelectorAll(".eb-col-planned th.eb-planned-training-col, .eb-col-planned td.eb-planned-training-col")
    );
    const notesNodes = Array.from(
      month.querySelectorAll(".eb-col-planned th.eb-planned-notes-col, .eb-col-planned td.eb-planned-notes-col")
    );

    const measureNodesMaxWidth = (nodes, minWidth) => {
      if (!nodes.length) return minWidth;
      const measured = nodes.map((node) => Math.max(node.scrollWidth, node.offsetWidth));
      return Math.max(minWidth, ...measured);
    };

    const trainingWidth = Math.ceil(measureNodesMaxWidth(trainingNodes, 320));
    const notesWidth = Math.ceil(measureNodesMaxWidth(notesNodes, 180));
    month.style.setProperty("--eb-planned-training-col-width", `${trainingWidth}px`);
    month.style.setProperty("--eb-planned-notes-col-width", `${notesWidth}px`);

    const plannedWidth = Math.max(...plannedCols.map((col) => Math.max(col.scrollWidth, col.offsetWidth)));
    const completedWidth = Math.max(...completedCols.map((col) => Math.max(col.scrollWidth, col.offsetWidth)));

    plannedCols.forEach((col) => {
      const px = `${plannedWidth}px`;
      col.style.width = px;
      col.style.minWidth = px;
      col.style.flexBasis = px;
    });
    completedCols.forEach((col) => {
      const px = `${completedWidth}px`;
      col.style.width = px;
      col.style.minWidth = px;
      col.style.flexBasis = px;
    });

    // Keep planned/completed table rows visually aligned within each week.
    const weekRows = Array.from(month.querySelectorAll(".eb-week-row"));
    weekRows.forEach((weekRow) => {
      const plannedBodyRows = Array.from(weekRow.querySelectorAll(".eb-col-planned tbody tr"));
      const completedBodyRows = Array.from(weekRow.querySelectorAll(".eb-col-completed tbody tr"));
      plannedBodyRows.forEach((row) => {
        row.style.height = "";
      });
      completedBodyRows.forEach((row) => {
        row.style.height = "";
      });

      const bodyRowCount = Math.max(plannedBodyRows.length, completedBodyRows.length);
      for (let i = 0; i < bodyRowCount; i += 1) {
        const plannedRow = plannedBodyRows[i] || null;
        const completedRow = completedBodyRows[i] || null;
        const plannedHeight = plannedRow ? Math.max(plannedRow.offsetHeight, plannedRow.scrollHeight) : 0;
        const completedHeight = completedRow ? Math.max(completedRow.offsetHeight, completedRow.scrollHeight) : 0;
        const targetHeight = Math.max(plannedHeight, completedHeight);
        if (!targetHeight) continue;
        if (plannedRow) plannedRow.style.height = `${targetHeight}px`;
        if (completedRow) completedRow.style.height = `${targetHeight}px`;
      }

      const plannedFooterRow = weekRow.querySelector(".eb-col-planned tfoot tr");
      const completedFooterRow = weekRow.querySelector(".eb-col-completed tfoot tr");
      if (plannedFooterRow && completedFooterRow) {
        plannedFooterRow.style.height = "";
        completedFooterRow.style.height = "";
        const plannedFooterHeight = Math.max(plannedFooterRow.offsetHeight, plannedFooterRow.scrollHeight);
        const completedFooterHeight = Math.max(completedFooterRow.offsetHeight, completedFooterRow.scrollHeight);
        const targetFooterHeight = Math.max(plannedFooterHeight, completedFooterHeight);
        if (targetFooterHeight) {
          plannedFooterRow.style.height = `${targetFooterHeight}px`;
          completedFooterRow.style.height = `${targetFooterHeight}px`;
        }
      }
    });
  }

  function scheduleEqualize(widget) {
    if (widget.__ebEqRaf) {
      window.cancelAnimationFrame(widget.__ebEqRaf);
    }
    widget.__ebEqRaf = window.requestAnimationFrame(() => {
      widget.__ebEqRaf = null;
      const activeMonth = widget.querySelector(".month-container.is-active");
      if (!activeMonth) return;
      const monthId = activeMonth.getAttribute("data-month-id");
      if (!monthId) return;
      equalizeMonthColumns(widget, monthId);
    });
  }

  function initMonthWidget(widget) {
    const buttons = Array.from(widget.querySelectorAll(".month-btn"));
    const months = Array.from(widget.querySelectorAll(".month-container"));
    if (!months.length) return;

    const stateKeyRaw = widget.getAttribute("data-month-state-key");
    const storageKey = stateKeyRaw ? `eb_month_${stateKeyRaw}` : null;
    const savedMonthId = storageKey ? window.localStorage.getItem(storageKey) : null;

    const firstId = buttons.length
      ? buttons[0].getAttribute("data-month-id")
      : months[0].getAttribute("data-month-id");

    const useSaved = savedMonthId && months.some((m) => m.getAttribute("data-month-id") === savedMonthId);
    const activeMonthId = useSaved ? savedMonthId : firstId;

    showMonth(widget, activeMonthId);

    buttons.forEach((btn) => {
      btn.addEventListener("click", () => {
        const monthId = btn.getAttribute("data-month-id");
        showMonth(widget, monthId);
        if (storageKey) {
          window.localStorage.setItem(storageKey, monthId);
        }
      });
    });
  }

  function initMonthSwitcherScroll(widget) {
    const track = widget.querySelector(".eb-month-switcher-track");
    if (!track) return;

    let wheelDeltaBuffer = 0;
    let wheelRafId = null;

    function normalizeWheelDelta(event) {
      // DOM_DELTA_PIXEL = 0, DOM_DELTA_LINE = 1, DOM_DELTA_PAGE = 2
      const raw = Math.abs(event.deltaX) > 0 ? event.deltaX : event.deltaY;
      if (!raw) return 0;
      if (event.deltaMode === 1) return raw * 16;
      if (event.deltaMode === 2) return raw * track.clientWidth;
      return raw;
    }

    function flushWheelDelta() {
      wheelRafId = null;
      if (!wheelDeltaBuffer) return;
      track.scrollLeft += wheelDeltaBuffer;
      wheelDeltaBuffer = 0;
    }

    track.addEventListener(
      "wheel",
      (event) => {
        if (track.scrollWidth <= track.clientWidth) return;
        const delta = normalizeWheelDelta(event);
        if (!delta) return;

        // Slightly dampen wheel movement to avoid jumpy stepping on classic mouse wheels.
        wheelDeltaBuffer += delta * 0.65;
        if (!wheelRafId) {
          wheelRafId = window.requestAnimationFrame(flushWheelDelta);
        }
        event.preventDefault();
      },
      { passive: false }
    );
  }

  async function saveInlineField(node, updateUrl, csrfToken, widget) {
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
      const response = await fetch(updateUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken || "",
          "X-Requested-With": "XMLHttpRequest",
        },
        body: JSON.stringify({
          planned_id: trainingId,
          field,
          value: currentValue,
        }),
      });

      if (!response.ok) {
        throw new Error(`Save failed with status ${response.status}`);
      }

      const payload = await response.json();
      if (!payload.ok) {
        throw new Error(payload.error || "Save failed.");
      }

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
        saveInlineField(node, updateUrl, csrfToken, widget);
      }
      scheduleEqualize(widget);
    }
  }

  function initCoachInlineEditing(widget) {
    const updateUrl = widget.getAttribute("data-plan-update-url");
    if (!updateUrl) return;

    const csrfToken = getCsrfToken();
    const editableNodes = Array.from(widget.querySelectorAll(".eb-inline-edit[contenteditable='true']"));
    let inlineSelection = null;
    const undoStack = [];
    const redoStack = [];
    const historyLimit = 100;

    function placeCaretToEnd(el) {
      const selection = window.getSelection();
      if (!selection) return;
      const range = document.createRange();
      range.selectNodeContents(el);
      range.collapse(false);
      selection.removeAllRanges();
      selection.addRange(range);
    }

    function focusNextEditableInColumn(currentNode) {
      const field = currentNode.getAttribute("data-field");
      const month = currentNode.closest(".month-container");
      if (!field || !month) return false;

      const allInColumn = Array.from(month.querySelectorAll(`.eb-inline-edit[data-field="${field}"]`));
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

      const allInColumn = Array.from(month.querySelectorAll(`.eb-inline-edit[data-field="${field}"]`));
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

    function getMonthGrid(month) {
      if (!month) return { rows: [] };
      const titleNodes = Array.from(month.querySelectorAll(".eb-inline-edit[data-field='title'][contenteditable='true']"));
      const rows = titleNodes.map((titleNode) => {
        const row = titleNode.closest("tr");
        const notesNode = row ? row.querySelector(".eb-inline-edit[data-field='notes'][contenteditable='true']") : null;
        return { title: titleNode, notes: notesNode };
      });
      return { rows };
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
          cols.push(node ? (node.textContent || "") : "");
        }
        lines.push(cols.join("\t"));
      }
      return lines.join("\n");
    }

    function applyPastedMatrix(startNode, text) {
      const startPos = getNodePosition(startNode);
      if (!startPos) return [];

      const normalized = String(text || "").replace(/\r/g, "");
      const rawRows = normalized.split("\n");
      if (rawRows.length && rawRows[rawRows.length - 1] === "") {
        rawRows.pop();
      }
      if (!rawRows.length) return [];

      const matrix = rawRows.map((line) => line.split("\t"));
      const changes = [];
      matrix.forEach((rowValues, rOffset) => {
        rowValues.forEach((value, cOffset) => {
          const target = getNodeAt(startPos.month, startPos.rowIndex + rOffset, startPos.colIndex + cOffset);
          if (!target) return;
          const before = target.textContent || "";
          if (before === value) return;
          target.textContent = value;
          changes.push({ node: target, before, after: value });
          saveInlineField(target, updateUrl, csrfToken, widget);
        });
      });
      scheduleEqualize(widget);
      return changes;
    }

    function pushHistory(changes) {
      if (!changes || !changes.length) return;
      undoStack.push(changes);
      if (undoStack.length > historyLimit) {
        undoStack.shift();
      }
      redoStack.length = 0;
    }

    function applyHistory(changes, direction) {
      if (!changes || !changes.length) return;
      changes.forEach((change) => {
        if (!change.node) return;
        const nextValue = direction === "undo" ? change.before : change.after;
        change.node.textContent = nextValue;
        saveInlineField(change.node, updateUrl, csrfToken, widget);
      });
      scheduleEqualize(widget);
    }

    function runUndo() {
      const action = undoStack.pop();
      if (!action) return;
      applyHistory(action, "undo");
      redoStack.push(action);
    }

    function runRedo() {
      const action = redoStack.pop();
      if (!action) return;
      applyHistory(action, "redo");
      undoStack.push(action);
    }

    function clearSelectedCellsIfAny() {
      if (!inlineSelection || !inlineSelection.cells || inlineSelection.cells.length < 2) return false;
      const changes = [];
      inlineSelection.cells.forEach((selectedNode) => {
        const before = selectedNode.textContent || "";
        if (!before) return;
        selectedNode.textContent = "";
        changes.push({ node: selectedNode, before, after: "" });
        saveInlineField(selectedNode, updateUrl, csrfToken, widget);
      });
      pushHistory(changes);
      clearInlineSelection();
      scheduleEqualize(widget);
      return true;
    }

    function focusNextEditableInRowOrder(currentNode) {
      const month = currentNode.closest(".month-container");
      if (!month) return false;
      const allEditables = Array.from(month.querySelectorAll(".eb-inline-edit[contenteditable='true']"));
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
      const allEditables = Array.from(month.querySelectorAll(".eb-inline-edit[contenteditable='true']"));
      const currentIndex = allEditables.indexOf(currentNode);
      if (currentIndex <= 0) return false;

      const prevEditable = allEditables[currentIndex - 1];
      prevEditable.focus();
      placeCaretToEnd(prevEditable);
      return true;
    }

    editableNodes.forEach((node) => {
      node.dataset.originalValue = node.textContent || "";

      node.addEventListener("copy", (event) => {
        if (hasActiveSelectionForNode(node)) {
          const text = getSelectionAsTsv();
          if (event.clipboardData) {
            event.preventDefault();
            event.clipboardData.setData("text/plain", text);
            return;
          }
          if (navigator.clipboard && navigator.clipboard.writeText) {
            event.preventDefault();
            navigator.clipboard.writeText(text).catch(() => {});
            return;
          }
        }

        const text = node.textContent || "";
        if (event.clipboardData) {
          event.preventDefault();
          event.clipboardData.setData("text/plain", text);
          return;
        }
        if (navigator.clipboard && navigator.clipboard.writeText) {
          event.preventDefault();
          navigator.clipboard.writeText(text).catch(() => {});
        }
      });

      node.addEventListener("focus", () => {
        node.dataset.originalValue = node.textContent || "";
        if (!hasActiveSelectionForNode(node)) {
          clearInlineSelection();
        }
      });

      node.addEventListener("paste", (event) => {
        const text = event.clipboardData ? event.clipboardData.getData("text/plain") : "";
        if (typeof text !== "string") return;
        event.preventDefault();
        const changes = applyPastedMatrix(node, text);
        pushHistory(changes);
        clearInlineSelection();
      });

      node.addEventListener("keydown", (event) => {
        const isCtrlOrMeta = event.ctrlKey || event.metaKey;
        if (isCtrlOrMeta && (event.key === "z" || event.key === "Z")) {
          event.preventDefault();
          if (event.shiftKey) {
            runRedo();
          } else {
            runUndo();
          }
          clearInlineSelection();
          return;
        }

        if (isCtrlOrMeta && (event.key === "y" || event.key === "Y")) {
          event.preventDefault();
          runRedo();
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
          saveInlineField(node, updateUrl, csrfToken, widget);
          if (!focusNextEditableInColumn(node)) {
            node.blur();
          }
          return;
        }

        if (event.key === "Tab") {
          event.preventDefault();
          clearInlineSelection();
          saveInlineField(node, updateUrl, csrfToken, widget);
          const moved = event.shiftKey
            ? focusPrevEditableInRowOrder(node)
            : focusNextEditableInRowOrder(node);
          if (!moved) {
            node.blur();
          }
          return;
        }

        if (event.key === "Delete") {
          event.preventDefault();
          if (!clearSelectedCellsIfAny()) {
            const before = node.textContent || "";
            if (!before) return;
            node.textContent = "";
            saveInlineField(node, updateUrl, csrfToken, widget);
            pushHistory([{ node, before, after: "" }]);
            scheduleEqualize(widget);
          }
          return;
        }

        if (event.key === "Backspace") {
          if (clearSelectedCellsIfAny()) {
            event.preventDefault();
            return;
          }
        }

        if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) {
          return;
        }

        if (event.key === "ArrowDown") {
          event.preventDefault();
          clearInlineSelection();
          saveInlineField(node, updateUrl, csrfToken, widget);
          focusNextEditableInColumn(node);
          return;
        }

        if (event.key === "ArrowUp") {
          event.preventDefault();
          clearInlineSelection();
          saveInlineField(node, updateUrl, csrfToken, widget);
          focusPrevEditableInColumn(node);
          return;
        }

        if (event.key === "ArrowRight") {
          if (node.getAttribute("data-field") === "title") {
            event.preventDefault();
            clearInlineSelection();
            saveInlineField(node, updateUrl, csrfToken, widget);
            focusSiblingFieldInRow(node, "notes");
          }
          return;
        }

        if (event.key === "ArrowLeft") {
          if (node.getAttribute("data-field") === "notes") {
            event.preventDefault();
            clearInlineSelection();
            saveInlineField(node, updateUrl, csrfToken, widget);
            focusSiblingFieldInRow(node, "title");
          }
        }
      });

      let timerId = null;
      node.addEventListener("input", () => {
        if (timerId) clearTimeout(timerId);
        timerId = setTimeout(() => {
          timerId = null;
          saveInlineField(node, updateUrl, csrfToken, widget);
        }, 500);
        scheduleEqualize(widget);
      });

      node.addEventListener("blur", () => {
        if (timerId) {
          clearTimeout(timerId);
          timerId = null;
        }
        saveInlineField(node, updateUrl, csrfToken, widget);
      });
    });
  }

  function initCompletedInlineEditing(widget) {
    const updateUrl = widget.getAttribute("data-completed-update-url");
    if (!updateUrl) return;

    const csrfToken = getCsrfToken();
    const editableNodes = Array.from(widget.querySelectorAll(".eb-completed-inline-edit[contenteditable='true']"));
    if (!editableNodes.length) return;

    let inlineSelection = null;
    const undoStack = [];
    const redoStack = [];
    const historyLimit = 100;

    function placeCaretToEnd(el) {
      const selection = window.getSelection();
      if (!selection) return;
      const range = document.createRange();
      range.selectNodeContents(el);
      range.collapse(false);
      selection.removeAllRanges();
      selection.addRange(range);
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
        const response = await fetch(updateUrl, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken || "",
            "X-Requested-With": "XMLHttpRequest",
          },
          body: JSON.stringify({
            planned_id: trainingId,
            field,
            value: currentValue,
          }),
        });

        if (!response.ok) {
          throw new Error(`Save failed with status ${response.status}`);
        }

        const payload = await response.json();
        if (!payload.ok) {
          throw new Error(payload.error || "Save failed.");
        }

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
        scheduleEqualize(widget);
      }
    }

    function getTableRows(month) {
      if (!month) return [];
      const rows = Array.from(month.querySelectorAll(".eb-col-completed tbody tr"));
      return rows
        .map((row) => Array.from(row.querySelectorAll(".eb-completed-inline-edit[contenteditable='true']")))
        .filter((cells) => cells.length > 0);
    }

    function getNodePosition(node) {
      const month = node.closest(".month-container");
      const tableRows = getTableRows(month);
      for (let r = 0; r < tableRows.length; r += 1) {
        const c = tableRows[r].indexOf(node);
        if (c !== -1) {
          return { month, rowIndex: r, colIndex: c };
        }
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

    function pushHistory(changes) {
      if (!changes || !changes.length) return;
      undoStack.push(changes);
      if (undoStack.length > historyLimit) undoStack.shift();
      redoStack.length = 0;
    }

    function applyHistory(changes, direction) {
      if (!changes || !changes.length) return;
      changes.forEach((change) => {
        const next = direction === "undo" ? change.before : change.after;
        change.node.textContent = next;
        saveCompletedField(change.node);
      });
      scheduleEqualize(widget);
    }

    function runUndo() {
      const action = undoStack.pop();
      if (!action) return;
      applyHistory(action, "undo");
      redoStack.push(action);
    }

    function runRedo() {
      const action = redoStack.pop();
      if (!action) return;
      applyHistory(action, "redo");
      undoStack.push(action);
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
      pushHistory(changes);
      clearInlineSelection();
      scheduleEqualize(widget);
      return true;
    }

    function applyPastedMatrix(startNode, text) {
      const startPos = getNodePosition(startNode);
      if (!startPos) return [];
      const normalized = String(text || "").replace(/\r/g, "");
      const rawRows = normalized.split("\n");
      if (rawRows.length && rawRows[rawRows.length - 1] === "") rawRows.pop();
      if (!rawRows.length) return [];

      const matrix = rawRows.map((line) => line.split("\t"));
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
      scheduleEqualize(widget);
      return changes;
    }

    editableNodes.forEach((node) => {
      node.dataset.originalValue = node.textContent || "";

      node.addEventListener("copy", (event) => {
        if (hasActiveSelectionForNode(node)) {
          const text = getSelectionAsTsv();
          if (event.clipboardData) {
            event.preventDefault();
            event.clipboardData.setData("text/plain", text);
            return;
          }
        }
        const text = node.textContent || "";
        if (event.clipboardData) {
          event.preventDefault();
          event.clipboardData.setData("text/plain", text);
        }
      });

      node.addEventListener("focus", () => {
        node.dataset.originalValue = node.textContent || "";
        if (!hasActiveSelectionForNode(node)) clearInlineSelection();
      });

      node.addEventListener("paste", (event) => {
        const text = event.clipboardData ? event.clipboardData.getData("text/plain") : "";
        event.preventDefault();
        const changes = applyPastedMatrix(node, text);
        pushHistory(changes);
        clearInlineSelection();
      });

      node.addEventListener("keydown", (event) => {
        const isCtrlOrMeta = event.ctrlKey || event.metaKey;
        if (isCtrlOrMeta && (event.key === "z" || event.key === "Z")) {
          event.preventDefault();
          if (event.shiftKey) runRedo();
          else runUndo();
          clearInlineSelection();
          return;
        }
        if (isCtrlOrMeta && (event.key === "y" || event.key === "Y")) {
          event.preventDefault();
          runRedo();
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
            pushHistory([{ node, before, after: "" }]);
            scheduleEqualize(widget);
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

      let timerId = null;
      node.addEventListener("input", () => {
        if (timerId) clearTimeout(timerId);
        timerId = setTimeout(() => {
          timerId = null;
          saveCompletedField(node);
        }, 500);
        scheduleEqualize(widget);
      });

      node.addEventListener("blur", () => {
        if (timerId) {
          clearTimeout(timerId);
          timerId = null;
        }
        saveCompletedField(node);
      });
    });
  }

  function initCoachAthleteFocus() {
    const input = document.getElementById("coachAthleteFocusInput");
    if (!input) return;

    const updateUrl = input.getAttribute("data-focus-update-url");
    const athleteId = Number(input.getAttribute("data-athlete-id"));
    if (!updateUrl || !athleteId) return;

    const csrfToken = getCsrfToken();
    input.dataset.savedValue = input.value || "";

    function applyFocusToSidebar(value) {
      const row = document.querySelector(`.eb-athlete-item[data-athlete-id="${athleteId}"] [data-athlete-focus]`);
      if (!row) return;
      row.textContent = value ? `- ${value}` : "";
    }

    async function saveFocus() {
      const raw = (input.value || "").slice(0, 30);
      if (input.value !== raw) {
        input.value = raw;
      }
      if (raw === (input.dataset.savedValue || "")) return;

      input.classList.add("is-saving");
      try {
        const response = await fetch(updateUrl, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken || "",
            "X-Requested-With": "XMLHttpRequest",
          },
          body: JSON.stringify({
            athlete_id: athleteId,
            focus: raw,
          }),
        });

        if (!response.ok) {
          throw new Error(`Focus save failed with status ${response.status}`);
        }
        const payload = await response.json();
        if (!payload.ok) {
          throw new Error(payload.error || "Focus save failed.");
        }

        input.dataset.savedValue = payload.focus || "";
        input.value = payload.focus || "";
        input.classList.remove("is-error");
        applyFocusToSidebar(payload.focus || "");
      } catch (err) {
        input.classList.add("is-error");
        input.value = input.dataset.savedValue || "";
        console.error(err);
      } finally {
        input.classList.remove("is-saving");
      }
    }

    let timerId = null;
    input.addEventListener("input", () => {
      if ((input.value || "").length > 30) {
        input.value = (input.value || "").slice(0, 30);
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
        const response = await fetch(reorderUrl, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken || "",
            "X-Requested-With": "XMLHttpRequest",
          },
          body: JSON.stringify({ athlete_ids: ids }),
        });
        if (!response.ok) {
          throw new Error(`Reorder failed with status ${response.status}`);
        }
      } catch (err) {
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

  function init() {
    function enhanceAddMonthForms(widget) {
      const addMonthForms = Array.from(widget.querySelectorAll(".eb-add-month-form"));
      addMonthForms.forEach((form) => {
        if (form.dataset.enhanced === "1") return;
        form.dataset.enhanced = "1";
        form.addEventListener("submit", async (event) => {
          event.preventDefault();
          const submitBtn = form.querySelector("button[type='submit']");
          if (submitBtn) submitBtn.disabled = true;
          form.classList.add("is-loading");

          try {
            const formData = new FormData(form);
            const postUrl = form.getAttribute("action") || window.location.href;
            const response = await fetch(postUrl, {
              method: "POST",
              body: formData,
              headers: {
                "X-Requested-With": "XMLHttpRequest",
              },
              credentials: "same-origin",
            });

            const html = await response.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, "text/html");
            const replacement = doc.querySelector(".eb-month-widget");
            if (!replacement) {
              window.location.reload();
              return;
            }

            const currentWidget = form.closest(".eb-month-widget");
            if (!currentWidget) {
              window.location.reload();
              return;
            }

            currentWidget.replaceWith(replacement);
            initSingleMonthWidget(replacement);
            enhanceAddMonthForms(replacement);
          } catch (err) {
            console.error(err);
            window.location.reload();
          }
        });
      });
    }

    function initSingleMonthWidget(widget) {
      initMonthWidget(widget);
      initMonthSwitcherScroll(widget);
      if (widget.getAttribute("data-inline-editable") === "1") {
        initCoachInlineEditing(widget);
      }
      if (widget.getAttribute("data-completed-inline-editable") === "1") {
        initCompletedInlineEditing(widget);
      }
    }

    const widgets = Array.from(document.querySelectorAll(".eb-month-widget"));
    widgets.forEach((widget) => {
      initSingleMonthWidget(widget);
      enhanceAddMonthForms(widget);
    });
    initCoachAthleteFocus();
    initCoachAthleteReorder();

    const importLink = document.getElementById("fitImportLink");
    const fileInput = document.getElementById("fitFileInput");
    const form = document.getElementById("fitImportForm");
    const importSourceInput = document.getElementById("importSourceInput");

    if (importLink && fileInput && form && importSourceInput) {
      importLink.addEventListener("click", (event) => {
        event.preventDefault();
        importSourceInput.value = "fit_upload";
        fileInput.click();
      });

      fileInput.addEventListener("change", () => {
        if (fileInput.files && fileInput.files.length > 0) {
          importSourceInput.value = "fit_upload";
          form.submit();
        }
      });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
