const hamburger = document.getElementById("hamburger");
const sidebar = document.getElementById("sidebar");
const closeBtn = document.getElementById("closeBtn");

hamburger.addEventListener("click", () => {
  sidebar.classList.add("active");
});

closeBtn.addEventListener("click", () => {
  sidebar.classList.remove("active");
});

// ✅ Plus menu toggle
const plusBtn = document.getElementById("plusBtn");
const plusMenu = document.getElementById("plusMenu");

plusBtn.addEventListener("click", () => {
  plusMenu.style.display = plusMenu.style.display === "flex" ? "none" : "flex";
});

// Kliknutí mimo menu ho zavře
document.addEventListener("click", (e) => {
  if (!plusBtn.contains(e.target) && !plusMenu.contains(e.target)) {
    plusMenu.style.display = "none";
  }
});
document.addEventListener("DOMContentLoaded", () => {
  const messageBox = document.getElementById("messages");
  if (messageBox) {
    messageBox.scrollTop = messageBox.scrollHeight;
  }
});