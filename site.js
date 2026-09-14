/* Bandeau rétractable et menu déroulant. Rien d'autre. */
(function () {
  var bandeau = document.querySelector(".bandeau");
  if (bandeau) {
    var dernier = window.scrollY, seuil = 90;
    addEventListener("scroll", function () {
      var y = window.scrollY;
      if (Math.abs(y - dernier) < 6) return;
      bandeau.classList.toggle("replie", y > dernier && y > seuil);
      dernier = y;
    }, { passive: true });
  }

  document.querySelectorAll("nav button[aria-controls]").forEach(function (b) {
    var menu = document.getElementById(b.getAttribute("aria-controls"));
    if (!menu) return;
    function ouvrir(o) { b.setAttribute("aria-expanded", o); menu.hidden = !o; }
    b.addEventListener("click", function (e) {
      e.stopPropagation();
      ouvrir(b.getAttribute("aria-expanded") !== "true");
    });
    b.parentNode.addEventListener("mouseenter", function () { if (matchMedia("(hover:hover)").matches) ouvrir(true); });
    b.parentNode.addEventListener("mouseleave", function () { if (matchMedia("(hover:hover)").matches) ouvrir(false); });
    addEventListener("keydown", function (e) { if (e.key === "Escape") { ouvrir(false); b.focus(); } });
    addEventListener("click", function (e) { if (!b.parentNode.contains(e.target)) ouvrir(false); });
  });
})();
