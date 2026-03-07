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

    editableNodes.forEach((node) => {
      node.dataset.originalValue = node.textContent || "";

      node.addEventListener("copy", (event) => {
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
      });

      node.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
          event.preventDefault();
          saveInlineField(node, updateUrl, csrfToken, widget);
          if (!focusNextEditableInColumn(node)) {
            node.blur();
          }
          return;
        }

        if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) {
          return;
        }

        if (event.key === "ArrowDown") {
          event.preventDefault();
          saveInlineField(node, updateUrl, csrfToken, widget);
          focusNextEditableInColumn(node);
          return;
        }

        if (event.key === "ArrowUp") {
          event.preventDefault();
          saveInlineField(node, updateUrl, csrfToken, widget);
          focusPrevEditableInColumn(node);
          return;
        }

        if (event.key === "ArrowRight") {
          if (node.getAttribute("data-field") === "title") {
            event.preventDefault();
            saveInlineField(node, updateUrl, csrfToken, widget);
            focusSiblingFieldInRow(node, "notes");
          }
          return;
        }

        if (event.key === "ArrowLeft") {
          if (node.getAttribute("data-field") === "notes") {
            event.preventDefault();
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

    list.querySelectorAll(".eb-athlete-item a").forEach((anchor) => {
      anchor.addEventListener("dragstart", (event) => {
        event.preventDefault();
      });
    });

    function getDragAfterElement(container, y) {
      const candidates = Array.from(container.querySelectorAll(".eb-athlete-item:not(.is-dragging)"));
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
      const ids = Array.from(list.querySelectorAll(".eb-athlete-item"))
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

    list.querySelectorAll(".eb-athlete-item").forEach((item) => {
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
        if (list.lastElementChild !== draggedItem) {
          list.appendChild(draggedItem);
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
    const widgets = Array.from(document.querySelectorAll(".eb-month-widget"));
    widgets.forEach((widget) => {
      initMonthWidget(widget);
      initMonthSwitcherScroll(widget);
      if (widget.getAttribute("data-inline-editable") === "1") {
        initCoachInlineEditing(widget);
      }
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
