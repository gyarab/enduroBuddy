(function () {
  console.log("[dashboard.js] loaded ✅"); // <- tohle musíš vidět v console

  function ready(fn) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", fn);
    } else {
      fn();
    }
  }

  ready(() => {
    console.log("[dashboard.js] DOM ready ✅");

    const monthButtons = Array.from(document.querySelectorAll(".month-btn"));
    const monthContainers = Array.from(document.querySelectorAll(".month-container"));
    const contentArea = document.getElementById("monthContentArea");

    console.log("[dashboard.js] buttons:", monthButtons.length, "containers:", monthContainers.length);

    function setActive(monthId) {
      monthContainers.forEach((c) => c.classList.remove("active"));
      monthButtons.forEach((b) => b.classList.remove("active"));

      const selected = document.querySelector(`.month-container[data-month-id="${monthId}"]`);
      if (selected) selected.classList.add("active");

      const btn = document.querySelector(`.month-btn[data-month-id="${monthId}"]`);
      if (btn) btn.classList.add("active");

      try { localStorage.setItem("selectedMonthId", String(monthId)); } catch (e) {}

      if (contentArea) contentArea.scrollTop = 0;
    }

    monthButtons.forEach((btn) => {
      btn.addEventListener("click", () => {
        const id = btn.getAttribute("data-month-id");
        console.log("[dashboard.js] click month:", id);
        if (id) setActive(id);
      });
    });

    // init
    if (monthButtons.length === 0 || monthContainers.length === 0) return;

    let startId = monthButtons[0].getAttribute("data-month-id");
    try {
      const saved = localStorage.getItem("selectedMonthId");
      if (saved && document.querySelector(`.month-container[data-month-id="${saved}"]`)) {
        startId = saved;
      }
    } catch (e) {}

    if (startId) setActive(startId);
  });
})();
