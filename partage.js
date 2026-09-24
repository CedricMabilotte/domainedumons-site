/* Relayer, copier, et le sommaire qui suit la lecture. Rien d'autre.
   Aucun appel réseau : les liens de partage ne partent que si l'on clique,
   et le nom d'instance Mastodon n'est ni envoyé ni conservé. */
(function () {
  "use strict";

  /* --------------------------------------------------------- copier */
  function copier(bouton) {
    var cible = document.getElementById(bouton.getAttribute("data-copier"));
    if (!cible) return;
    var texte = cible.value !== undefined ? cible.value : cible.textContent;
    var riche = bouton.getAttribute("data-riche");
    var fait = function () {
      var avant = bouton.textContent;
      bouton.textContent = "Copié";
      bouton.setAttribute("data-fait", "");
      setTimeout(function () { bouton.textContent = avant; bouton.removeAttribute("data-fait"); }, 1800);
    };
    var repli = function () { cible.select && cible.select(); try { document.execCommand("copy"); fait(); } catch (e) {} };
    if (riche && window.ClipboardItem && navigator.clipboard && navigator.clipboard.write) {
      var item = new ClipboardItem({
        "text/html": new Blob([riche], { type: "text/html" }),
        "text/plain": new Blob([cible.value], { type: "text/plain" })
      });
      navigator.clipboard.write([item]).then(fait, repli);
    } else if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(texte).then(fait, repli);
    } else {
      repli();
    }
  }
  document.addEventListener("click", function (e) {
    var b = e.target.closest("[data-copier]");
    if (b) { e.preventDefault(); copier(b); }
  });

  /* ------------------------------------------------------ Mastodon */
  function formulaire(apres, texte) {
    var existant = apres.parentNode.querySelector(".mastodon-form");
    if (existant) { existant.querySelector("input").focus(); return; }
    var f = document.createElement("form");
    f.className = "mastodon-form";
    f.innerHTML = '<label>Votre instance <input type="text" inputmode="url" autocomplete="off" ' +
      'spellcheck="false" placeholder="mastodon.social" required></label>' +
      '<button type="submit" class="bouton">Ouvrir</button>';
    f.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var hote = f.querySelector("input").value.trim()
        .replace(/^https?:\/\//, "").replace(/\/.*$/, "").replace(/^@?[^@]*@/, "");
      if (!/^[a-z0-9.-]+\.[a-z]{2,}$/i.test(hote)) { f.querySelector("input").setCustomValidity("Un nom d'instance, par exemple mastodon.social"); f.reportValidity(); return; }
      window.open("https://" + hote + "/share?text=" + encodeURIComponent(texte), "_blank", "noopener");
    });
    f.querySelector("input").addEventListener("input", function () { this.setCustomValidity(""); });
    apres.parentNode.insertBefore(f, apres.nextSibling);
    f.querySelector("input").focus();
  }
  document.querySelectorAll(".relais-mastodon").forEach(function (a) {
    var bloc = a.closest(".relayer");
    var texte = bloc.getAttribute("data-titre") + "\n\n" + bloc.getAttribute("data-url");
    a.addEventListener("click", function (e) {
      e.preventDefault();
      formulaire(a.closest(".relais"), texte);
    });
  });
  document.querySelectorAll("[data-mastodon]").forEach(function (b) {
    b.addEventListener("click", function () {
      var zone = b.closest("details").querySelector("textarea");
      formulaire(b.closest(".actions"), zone.value);
    });
  });

  /* -------------------------------------- partage natif du téléphone */
  if (navigator.share) {
    document.querySelectorAll(".relayer").forEach(function (bloc) {
      var li = document.createElement("li");
      var b = document.createElement("button");
      b.type = "button";
      b.textContent = "Partager…";
      b.addEventListener("click", function () {
        navigator.share({ title: bloc.getAttribute("data-titre"), url: bloc.getAttribute("data-url") }).catch(function () {});
      });
      li.appendChild(b);
      bloc.querySelector(".relais").insertBefore(li, bloc.querySelector(".relais").firstChild);
    });
  }

  /* ------------------------------ le sommaire suit la section lue */
  var liens = document.querySelectorAll(".sommaire a[href^='#']");
  if (liens.length && "IntersectionObserver" in window) {
    var parId = {};
    liens.forEach(function (a) { parId[a.getAttribute("href").slice(1)] = a; });
    var obs = new IntersectionObserver(function (entrees) {
      entrees.forEach(function (en) {
        if (!en.isIntersecting) return;
        var a = parId[en.target.getAttribute("aria-labelledby")];
        if (!a) return;
        liens.forEach(function (x) { x.removeAttribute("aria-current"); });
        a.setAttribute("aria-current", "true");
      });
    }, { rootMargin: "-20% 0px -70% 0px" });
    document.querySelectorAll("section.sec[aria-labelledby]").forEach(function (s) { obs.observe(s); });
  }
})();
