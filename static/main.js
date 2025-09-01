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
document.querySelectorAll('.meal').forEach(mealDiv => {
  const switchButton = mealDiv.querySelector('.switch-recipe');
  const recipes = mealDiv.querySelectorAll('.recipe');
  const dots = mealDiv.querySelectorAll('.dot');
  
  const switchContent = (index) => {
    recipes.forEach(r => r.classList.remove("active"));
    recipes.forEach(r => r.classList.add("hidden"));
    dots.forEach(d => d.classList.remove("active"));

    recipes[index].classList.remove("hidden");
    recipes[index].classList.add("active");
    dots[index].classList.add("active");

    const activeRecipeId = recipes[index].dataset.receptId;
    const input = document.getElementById("snidane_recept_id");
    if (input) {
      input.value = activeRecipeId;
    };
  };

  switchButton.addEventListener('click', () => {
    const currentIndex = Array.from(recipes).findIndex(r => r.classList.contains("active"));
    const newIndex = (currentIndex + 1) % recipes.length;
    switchContent(newIndex)
  });
  dots.forEach((dot,index) => {
    dot.addEventListener("click",() => {
      switchContent(index);
    });
  });
});
