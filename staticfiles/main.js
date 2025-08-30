// Přepínání tabů
const tabBtns = document.querySelectorAll(".tab-btn");
const contents = document.querySelectorAll(".tab-content");

tabBtns.forEach(btn => {
  btn.addEventListener("click", () => {
    tabBtns.forEach(b => b.classList.remove("active"));
    btn.classList.add("active");

    contents.forEach(c => c.classList.remove("active"));
    document.getElementById(btn.dataset.target).classList.add("active");
  });
});

// Přepínání receptů pomocí tlačítka a teček
document.querySelectorAll(".meal").forEach(meal => {
  const textEl = meal.querySelector(".recipe-text");
  const dots = meal.querySelectorAll(".dot");
  const alt = meal.dataset.alt;
  const original = textEl.textContent.trim();

  function showVariant(isAlt) {
    textEl.textContent = isAlt ? alt : original;
    dots[0].classList.toggle("active", !isAlt);
    dots[1].classList.toggle("active", isAlt);
  }

  meal.querySelector(".switch-recipe").addEventListener("click", () => {
    const isAlt = textEl.textContent.trim() === original;
    showVariant(isAlt);
  });

  dots[0].addEventListener("click", () => showVariant(false));
  dots[1].addEventListener("click", () => showVariant(true));
});
