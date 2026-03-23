document.querySelectorAll(".eb-shell input").forEach((el) => {
  if (el.type === "checkbox") return;
  el.classList.add("form-control", "eb-input");
});

document.querySelectorAll('.eb-shell input[type="checkbox"]').forEach((el) => {
  el.classList.add("form-check-input");
});

document.querySelectorAll(".eb-shell select").forEach((el) => {
  el.classList.add("form-select", "eb-input");
});
