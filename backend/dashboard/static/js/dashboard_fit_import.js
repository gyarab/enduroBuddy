(function () {
  function getCsrfTokenFromForm(form) {
    if (!(form instanceof HTMLFormElement)) return "";
    const tokenInput = form.querySelector("input[name='csrfmiddlewaretoken']");
    return tokenInput instanceof HTMLInputElement ? tokenInput.value : "";
  }

  async function fetchCurrentDocument() {
    const response = await fetch(window.location.pathname + window.location.search, {
      method: "GET",
      headers: { "X-Requested-With": "XMLHttpRequest" },
      credentials: "same-origin",
    });
    if (!response.ok) throw new Error(`Pozadavek selhal se stavem ${response.status}`);
    const html = await response.text();
    return new DOMParser().parseFromString(html, "text/html");
  }

  async function refreshImportModalContent(options) {
    const opts = options || {};
    const currentModal = document.getElementById("importActivitiesModal");
    if (!currentModal) return;
    const doc = await fetchCurrentDocument();
    const nextModal = doc.getElementById("importActivitiesModal");
    if (nextModal) {
      const currentContent = currentModal.querySelector(".modal-content");
      const nextContent = nextModal.querySelector(".modal-content");
      if (currentContent && nextContent) {
        currentContent.replaceWith(nextContent);
      }
    }
    initFitImportQuickAction();
    const dashboardApp = (window.EB && window.EB.dashboardApp) || {};
    const initGarminBackgroundSync = dashboardApp.initGarminBackgroundSync || (() => {});
    initGarminBackgroundSync();
    if (opts.keepOpen !== false && window.bootstrap && window.bootstrap.Modal) {
      window.bootstrap.Modal.getOrCreateInstance(currentModal).show();
    }
  }

  function initFitImportQuickAction() {
    if (document.body.dataset.ebImportAjaxInit !== "1") {
      document.body.dataset.ebImportAjaxInit = "1";
      document.addEventListener("submit", async (event) => {
        const form = event.target;
        if (!(form instanceof HTMLFormElement)) return;
        if (form.getAttribute("data-import-ajax") !== "1") return;

        event.preventDefault();
        const submitter = event.submitter instanceof HTMLElement
          ? event.submitter
          : form.querySelector("button[type='submit'], input[type='submit']");
        const notifications = (window.EB && window.EB.notifications) || null;
        const ui = (window.EB && window.EB.ui) || {};
        const setButtonBusy = ui.setButtonBusy || (() => {});
        if (submitter instanceof HTMLElement) {
          setButtonBusy(submitter, true);
        }

        try {
          const response = await fetch(form.getAttribute("action") || window.location.href, {
            method: "POST",
            headers: {
              "X-Requested-With": "XMLHttpRequest",
              "X-CSRFToken": getCsrfTokenFromForm(form),
            },
            body: new FormData(form),
            credentials: "same-origin",
          });
          const payload = await response.json();
          const message = (payload && (payload.message || payload.error)) || "Import akce selhala.";
          const tone = (payload && payload.tone) || (response.ok ? "success" : "danger");
          if (notifications) {
            notifications.addNotification({
              id: `import-${Date.now()}`,
              text: message,
              tone,
              unread: true,
            });
          }
          if (!response.ok || !payload || !payload.ok) return;

          const dashboardApp = (window.EB && window.EB.dashboardApp) || {};
          const refreshDashboardMonthCards = dashboardApp.refreshDashboardMonthCards || (async () => {});
          if (payload.refresh_month_cards) {
            await refreshDashboardMonthCards();
          }
          if (payload.refresh_import_modal) {
            await refreshImportModalContent({ keepOpen: true });
          }
        } catch (error) {
          if (notifications) {
            notifications.addNotification({
              id: `import-error-${Date.now()}`,
              text: (error && error.message) || "Import akcí se nepodařilo dokončit.",
              tone: "danger",
              unread: true,
            });
          }
        } finally {
          if (submitter instanceof HTMLElement) {
            setButtonBusy(submitter, false);
          }
        }
      });
    }

    const importLink = document.getElementById("fitImportLink");
    const fileInput = document.getElementById("fitFileInput");
    const form = document.getElementById("fitImportForm");
    const importSourceInput = document.getElementById("importSourceInput");
    if (!importLink || !fileInput || !form || !importSourceInput) return;

    importLink.addEventListener("click", (event) => {
      event.preventDefault();
      importSourceInput.value = "fit_upload";
      fileInput.click();
    });

    fileInput.addEventListener("change", () => {
      if (fileInput.files && fileInput.files.length > 0) {
        importSourceInput.value = "fit_upload";
        if (typeof form.requestSubmit === "function") form.requestSubmit();
        else form.submit();
      }
    });
  }

  window.EB = window.EB || {};
  window.EB.dashboardApp = Object.assign(window.EB.dashboardApp || {}, {
    initFitImportQuickAction,
  });
})();
