(function () {
  window.EB = window.EB || {};

  function createMonthController(deps) {
    const metrics = (window.EB && window.EB.metrics) || {};
    const metricStart = metrics.start || (() => null);
    const metricEnd = metrics.end || (() => null);
    const getNotifications = () => (window.EB && window.EB.notifications) || null;
    const getWidgetState = (deps && deps.getWidgetState) || ((widget) => widget || {});
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
    const ui = (window.EB && window.EB.ui) || {};
    const setButtonBusy = ui.setButtonBusy || (() => {});

    function getActiveMonthId(widget) {
      const activeMonth = widget.querySelector(".month-container.is-active");
      if (!activeMonth) return null;
      return activeMonth.getAttribute("data-month-id");
    }

    function getMonthRevisions(widget) {
      const state = getWidgetState(widget);
      if (!state.monthRevisions) state.monthRevisions = {};
      return state.monthRevisions;
    }

    function markMonthDirty(widget, monthId) {
      if (!monthId) return;
      const revisions = getMonthRevisions(widget);
      revisions[monthId] = (revisions[monthId] || 0) + 1;
    }

    function getMonthRevision(widget, monthId) {
      if (!monthId) return 0;
      const revisions = getMonthRevisions(widget);
      return revisions[monthId] || 0;
    }

    function equalizeMonthColumns(widget, monthId, options = {}) {
      const metricToken = metricStart("month-equalize");
      const month = widget.querySelector(`.month-container[data-month-id="${monthId}"]`);
      if (!month) {
        metricEnd(metricToken, { month_id: monthId, skipped: true, reason: "month_missing" });
        return;
      }
      const force = !!options.force;

      const state = getWidgetState(widget);
      const layoutCache = state.monthLayoutCache || {};
      const cache = layoutCache[monthId] || null;
      const monthWidth = month.clientWidth || 0;
      const revision = getMonthRevision(widget, monthId);
      if (!force && cache && cache.monthWidth === monthWidth && cache.revision === revision) {
        metricEnd(metricToken, { month_id: monthId, skipped: true, reason: "cache_hit" });
        return;
      }

      const plannedCols = Array.from(month.querySelectorAll(".eb-col-planned"));
      const completedCols = Array.from(month.querySelectorAll(".eb-col-completed"));
      if (!plannedCols.length || !completedCols.length) {
        metricEnd(metricToken, { month_id: monthId, skipped: true, reason: "missing_columns" });
        return;
      }

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

      layoutCache[monthId] = { monthWidth, revision };
      state.monthLayoutCache = layoutCache;
      metricEnd(metricToken, { month_id: monthId, force, revision });
    }

    function scheduleEqualize(widget, options = {}) {
      const monthId = getActiveMonthId(widget);
      if (!monthId) return;

      if (options.dirty) {
        markMonthDirty(widget, monthId);
      }

      const state = getWidgetState(widget);
      if (state.eqTimer) window.clearTimeout(state.eqTimer);
      if (state.eqRaf) window.cancelAnimationFrame(state.eqRaf);

      const delayMs = typeof options.delayMs === "number" ? options.delayMs : 140;
      state.eqTimer = window.setTimeout(() => {
        state.eqTimer = null;
        state.eqRaf = window.requestAnimationFrame(() => {
          state.eqRaf = null;
          const latestMonthId = getActiveMonthId(widget);
          if (!latestMonthId) return;
          equalizeMonthColumns(widget, latestMonthId, { force: !!options.force });
        });
      }, delayMs);
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

      equalizeMonthColumns(widget, monthId, { force: true });
    }

    function initMonthWidget(widget) {
      const state = getWidgetState(widget);
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

      if (!state.resizeBound) {
        state.resizeBound = true;
        window.addEventListener("resize", () => {
          scheduleEqualize(widget, { force: true, delayMs: 40 });
        });
      }

      if ("ResizeObserver" in window && !state.resizeObserver) {
        const observedMonth = widget.querySelector(".month-container.is-active");
        if (observedMonth) {
          state.resizeObserver = new ResizeObserver(() => {
            scheduleEqualize(widget, { force: true, delayMs: 40 });
          });
          state.resizeObserver.observe(observedMonth);
        }
      }

      buttons.forEach((btn) => {
        btn.addEventListener("click", () => {
          const monthId = btn.getAttribute("data-month-id");
          showMonth(widget, monthId);
          if (state.resizeObserver) {
            state.resizeObserver.disconnect();
            const activeMonth = widget.querySelector(".month-container.is-active");
            if (activeMonth) state.resizeObserver.observe(activeMonth);
          }
          if (storageKey) window.localStorage.setItem(storageKey, monthId);
        });
      });
    }

    function initMonthSwitcherScroll(widget) {
      const track = widget.querySelector(".eb-month-switcher-track");
      if (!track) return;

      let wheelDeltaBuffer = 0;
      let wheelRafId = null;

      function normalizeWheelDelta(event) {
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
          wheelDeltaBuffer += delta * 0.65;
          if (!wheelRafId) wheelRafId = window.requestAnimationFrame(flushWheelDelta);
          event.preventDefault();
        },
        { passive: false }
      );
    }

    function enhanceAddMonthForms(widget, onWidgetReady) {
      const addMonthForms = Array.from(widget.querySelectorAll(".eb-add-month-form"));
      addMonthForms.forEach((form) => {
        if (form.dataset.enhanced === "1") return;
        form.dataset.enhanced = "1";
        form.addEventListener("submit", async (event) => {
          event.preventDefault();
          const submitBtn = form.querySelector("button[type='submit']");
          if (submitBtn) {
            setButtonBusy(submitBtn, true, { label: "" });
          }
          form.classList.add("is-loading");

          try {
            const formData = new FormData(form);
            const postUrl = form.getAttribute("action") || window.location.href;
            const response = await postForm(postUrl, formData, "");
            const html = await response.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, "text/html");
            const notifications = getNotifications();
            if (notifications && typeof notifications.ingestNotificationsFromDocument === "function") {
              notifications.ingestNotificationsFromDocument(doc);
            }
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
            if (typeof onWidgetReady === "function") onWidgetReady(replacement);
            enhanceAddMonthForms(replacement, onWidgetReady);
          } catch (err) {
            const notifications = getNotifications();
            if (notifications) {
              notifications.addNotification({
                id: "add-month-error",
                text: (err && err.message) || "Přidání dalšího měsíce selhalo.",
                tone: "danger",
                unread: true,
              });
            }
            console.error(err);
            window.location.reload();
          } finally {
            if (submitBtn) {
              setButtonBusy(submitBtn, false);
            }
          }
        });
      });
    }

    return {
      scheduleEqualize,
      initMonthWidget,
      initMonthSwitcherScroll,
      enhanceAddMonthForms,
    };
  }

  window.EB.month = {
    createMonthController,
  };
})();
