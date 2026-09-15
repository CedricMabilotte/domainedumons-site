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

  var survol = matchMedia("(hover:hover)").matches;

  document.querySelectorAll("nav [aria-controls]").forEach(function (b) {
    var menu = document.getElementById(b.getAttribute("aria-controls"));
    if (!menu) return;
    var bloc = b.closest("li");
    var minuterie = null;

    function ouvrir(o) {
      b.setAttribute("aria-expanded", o ? "true" : "false");
      menu.hidden = !o;
    }
    function fermerPlusTard() {
      clearTimeout(minuterie);
      /* on laisse un délai : traverser le vide entre le titre et le menu
         ne doit pas le refermer */
      minuterie = setTimeout(function () { ouvrir(false); }, 400);
    }
    function annuler() { clearTimeout(minuterie); }

    b.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();
      annuler();
      ouvrir(b.getAttribute("aria-expanded") !== "true");
    });

    if (survol && bloc) {
      bloc.addEventListener("mouseenter", function () { annuler(); ouvrir(true); });
      bloc.addEventListener("mouseleave", fermerPlusTard);
      menu.addEventListener("mouseenter", annuler);
      menu.addEventListener("mouseleave", fermerPlusTard);
    }
    if (bloc) {
      bloc.addEventListener("focusin", function () { annuler(); ouvrir(true); });
      bloc.addEventListener("focusout", function () {
        setTimeout(function () {
          if (bloc && !bloc.contains(document.activeElement)) ouvrir(false);
        }, 0);
      });
    }
    addEventListener("keydown", function (e) {
      if (e.key === "Escape" && !menu.hidden) { ouvrir(false); b.focus(); }
    });
    addEventListener("click", function (e) {
      if (bloc && !bloc.contains(e.target)) { annuler(); ouvrir(false); }
    });
  });
})();
