(function () {
  function initFitImportQuickAction() {
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
        form.submit();
      }
    });
  }

  window.EB = window.EB || {};
  window.EB.dashboardApp = Object.assign(window.EB.dashboardApp || {}, {
    initFitImportQuickAction,
  });
})();
