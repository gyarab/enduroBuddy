(function () {
  function px(n) {
    return `${Math.ceil(n)}px`;
  }

  function measureAndNormalizeMonth(monthEl) {
    if (!monthEl) return;

    const plannedCards = Array.from(monthEl.querySelectorAll(".eb-planned-card"));
    const completedCards = Array.from(monthEl.querySelectorAll(".eb-completed-card"));

    // reset explicit widths (abychom změřili "natural" obsah)
    plannedCards.forEach(c => (c.style.width = ""));
    completedCards.forEach(c => (c.style.width = ""));

    // změř šířku obsahu uvnitř každé karty
    const plannedMax = plannedCards.reduce((max, card) => {
      const table = card.querySelector("table");
      const w = table ? table.scrollWidth : card.scrollWidth;
      return Math.max(max, w);
    }, 0);

    const completedMax = completedCards.reduce((max, card) => {
      const table = card.querySelector("table");
      const w = table ? table.scrollWidth : card.scrollWidth;
      return Math.max(max, w);
    }, 0);

    // nastav všem v měsíci stejnou šířku (pokud něco naměříme)
    if (plannedMax > 0) {
      plannedCards.forEach(card => (card.style.width = px(plannedMax)));
    }

    if (completedMax > 0) {
      completedCards.forEach(card => (card.style.width = px(completedMax)));
    }
  }

  function showMonth(monthId) {
    const months = Array.from(document.querySelectorAll(".month-container"));
    const buttons = Array.from(document.querySelectorAll(".month-btn"));

    months.forEach(m => m.classList.remove("is-active"));
    buttons.forEach(b => b.classList.remove("is-active"));

    const active = document.querySelector(`.month-container[data-month-id="${monthId}"]`);
    if (active) {
      active.classList.add("is-active");
      // až bude vidět, změř a srovnej šířky karet
      requestAnimationFrame(() => measureAndNormalizeMonth(active));
    }

    const btn = document.querySelector(`.month-btn[data-month-id="${monthId}"]`);
    if (btn) btn.classList.add("is-active");
  }

  function init() {
    const buttons = Array.from(document.querySelectorAll(".month-btn"));
    const months = Array.from(document.querySelectorAll(".month-container"));
    if (!months.length) return;

    // první měsíc
    const first = months[0].getAttribute("data-month-id");
    showMonth(first);

    buttons.forEach(btn => {
      btn.addEventListener("click", () => {
        const id = btn.getAttribute("data-month-id");
        showMonth(id);
      });
    });

    // když resize okna → přepočítej aktivní měsíc (kvůli fontům, scrollbars, atd.)
    window.addEventListener("resize", () => {
      const active = document.querySelector(".month-container.is-active");
      if (active) measureAndNormalizeMonth(active);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
