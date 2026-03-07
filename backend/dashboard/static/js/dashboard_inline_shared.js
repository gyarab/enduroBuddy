(function () {
  window.EB = window.EB || {};

  function placeCaretToEnd(el) {
    const selection = window.getSelection();
    if (!selection) return;
    const range = document.createRange();
    range.selectNodeContents(el);
    range.collapse(false);
    selection.removeAllRanges();
    selection.addRange(range);
  }

  function setClipboardText(event, text) {
    if (!event || !event.clipboardData) return false;
    event.preventDefault();
    event.clipboardData.setData("text/plain", String(text || ""));
    return true;
  }

  function parsePasteMatrix(text) {
    const normalized = String(text || "").replace(/\r/g, "");
    const rawRows = normalized.split("\n");
    if (rawRows.length && rawRows[rawRows.length - 1] === "") {
      rawRows.pop();
    }
    if (!rawRows.length) return [];
    return rawRows.map((line) => line.split("\t"));
  }

  function createHistoryManager(options) {
    const apply = options && typeof options.apply === "function" ? options.apply : () => {};
    const limit = options && typeof options.limit === "number" ? options.limit : 100;
    const undoStack = [];
    const redoStack = [];

    function push(changes) {
      if (!changes || !changes.length) return;
      undoStack.push(changes);
      if (undoStack.length > limit) undoStack.shift();
      redoStack.length = 0;
    }

    function undo() {
      const action = undoStack.pop();
      if (!action) return false;
      apply(action, "undo");
      redoStack.push(action);
      return true;
    }

    function redo() {
      const action = redoStack.pop();
      if (!action) return false;
      apply(action, "redo");
      undoStack.push(action);
      return true;
    }

    return { push, undo, redo };
  }

  window.EB.inlineShared = {
    placeCaretToEnd,
    setClipboardText,
    parsePasteMatrix,
    createHistoryManager,
  };
})();
