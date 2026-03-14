(function () {
  function initLegendKeyboardShortcut() {
    if (document.body.dataset.ebLegendShortcutInit === "1") return;
    document.body.dataset.ebLegendShortcutInit = "1";

    document.addEventListener("keydown", (event) => {
      if (!event.altKey || event.ctrlKey || event.metaKey) return;
      if ((event.key || "").toLowerCase() !== "l") return;

      const legendModal = document.getElementById("coachLegendModal");
      if (!legendModal || !(window.bootstrap && window.bootstrap.Modal)) return;
      event.preventDefault();

      const childModalIds = ["coachLegendZonesModal", "coachLegendThresholdModal", "coachLegendPrModal"];
      childModalIds.forEach((id) => {
        const child = document.getElementById(id);
        if (!child || !child.classList.contains("show")) return;
        const childInstance = window.bootstrap.Modal.getInstance(child);
        if (childInstance) childInstance.hide();
      });

      const instance = window.bootstrap.Modal.getOrCreateInstance(legendModal);
      if (legendModal.classList.contains("show")) {
        instance.hide();
      } else {
        instance.show();
      }
    });
  }

  window.EB = window.EB || {};
  window.EB.dashboardApp = Object.assign(window.EB.dashboardApp || {}, {
    initLegendKeyboardShortcut,
  });
})();
