(function () {
  window.EB = window.EB || {};

  function createCoachController(deps) {
    const metrics = (window.EB && window.EB.metrics) || {};
    const metricStart = metrics.start || (() => null);
    const metricEnd = metrics.end || (() => null);
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
      if (!response.ok) throw new Error(`Request failed with status ${response.status}`);
      return response;
    });
    const getHtml = (deps && deps.getHtml) || (async (url) => {
      const response = await fetch(url, {
        method: "GET",
        headers: { "X-Requested-With": "XMLHttpRequest" },
        credentials: "same-origin",
      });
      if (!response.ok) throw new Error(`Request failed with status ${response.status}`);
      return response.text();
    });
    const initCoachMainContent = (deps && deps.initCoachMainContent) || (() => {});

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

    function initCoachSidebarToggle() {
      const shell = document.getElementById("coachShell");
      if (!shell) return;
      const toggleButtons = Array.from(document.querySelectorAll("[data-athlete-sidebar-toggle='1']"));
      if (!toggleButtons.length) return;

      const storageKey = "eb_coach_athletes_collapsed";

      function applyState(isCollapsed) {
        shell.classList.toggle("is-athletes-collapsed", isCollapsed);
        toggleButtons.forEach((button) => {
          button.setAttribute("aria-expanded", isCollapsed ? "false" : "true");
          const expandedTitle = button.getAttribute("data-title-expand") || "Hide athletes";
          const collapsedTitle = button.getAttribute("data-title-collapse") || "Show athletes";
          const nextTitle = isCollapsed ? collapsedTitle : expandedTitle;
          button.setAttribute("title", nextTitle);
          button.setAttribute("aria-label", nextTitle);
        });
      }

      applyState(window.localStorage.getItem(storageKey) === "1");

      toggleButtons.forEach((button) => {
        if (button.dataset.toggleSidebarInit === "1") return;
        button.dataset.toggleSidebarInit = "1";
        button.addEventListener("click", () => {
          const nextCollapsed = !shell.classList.contains("is-athletes-collapsed");
          applyState(nextCollapsed);
          window.localStorage.setItem(storageKey, nextCollapsed ? "1" : "0");
        });
      });
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

        shell.dataset.loading = "1";
        shell.classList.add("is-loading");
        try {
          const html = await getHtml(url);
          const parser = new DOMParser();
          const doc = parser.parseFromString(html, "text/html");
          const replacement = doc.getElementById("coachShell");
          if (!replacement) throw new Error("Replacement shell not found.");
          const replacementMain = replacement.querySelector(".eb-coach-main");
          const currentMain = shell.querySelector(".eb-coach-main");
          if (!replacementMain || !currentMain) throw new Error("Replacement main content not found.");

          currentMain.replaceWith(replacementMain);
          if (window.location.href !== url) {
            window.history.pushState({}, "", url);
          }
          if (doc.title) {
            document.title = doc.title;
          }
          updateCoachSidebarActiveState(url);
          initCoachMainContent(document.getElementById("coachShell") || document);
          initCoachSidebarToggle();
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

        button.disabled = true;
        try {
          const response = await postForm(form.getAttribute("action") || window.location.href, new FormData(form), getCsrfToken() || "");
          const payload = await response.json();
          if (!payload || !payload.ok) throw new Error("Visibility toggle failed.");

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
        } catch (err) {
          console.error(err);
          form.submit();
        } finally {
          button.disabled = false;
        }
      });
    }

    function initCoachShellContent() {
      initCoachMainContent(document);
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
