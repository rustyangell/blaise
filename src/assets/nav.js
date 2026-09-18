// Only one nav dropdown open at a time; clicking elsewhere or pressing Escape closes them.
(function () {
  var menus = document.querySelectorAll(".nav-dropdown");
  function closeAll(except) {
    menus.forEach(function (m) { if (m !== except) m.removeAttribute("open"); });
  }
  menus.forEach(function (m) {
    m.addEventListener("toggle", function () { if (m.open) closeAll(m); });
  });
  document.addEventListener("click", function (e) {
    if (!e.target.closest(".nav-dropdown")) closeAll(null);
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") closeAll(null);
  });
})();
