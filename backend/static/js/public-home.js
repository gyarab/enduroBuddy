(function () {
  const revealItems = Array.from(document.querySelectorAll(".eb-reveal"));
  if (!revealItems.length) return;

  const showItem = (item) => {
    item.classList.add("eb-is-visible");
  };

  if (!("IntersectionObserver" in window)) {
    revealItems.forEach(showItem);
    return;
  }

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      showItem(entry.target);
      observer.unobserve(entry.target);
    });
  }, {
    threshold: 0.15,
    rootMargin: "0px 0px -24px 0px",
  });

  revealItems.forEach((item) => observer.observe(item));
})();
