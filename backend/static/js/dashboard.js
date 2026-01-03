document.addEventListener("DOMContentLoaded", () => {
  const modalEl = document.getElementById("analysisModal");
  if (!modalEl) return;

  modalEl.addEventListener("show.bs.modal", (event) => {
    const trigger = event.relatedTarget; // <tr> that opened the modal
    if (!trigger) return;

    const title = trigger.getAttribute("data-title") || "Analysis detail";
    const desc = trigger.getAttribute("data-desc") || "";

    const titleEl = document.getElementById("analysisModalTitle");
    const descEl = document.getElementById("analysisModalDesc");

    if (titleEl) titleEl.textContent = title;
    if (descEl) descEl.textContent = desc;
  });
});
