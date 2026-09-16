/* carto-territoire — socle de rendu, mode local (Leaflet, aucune tuile).
 *
 * Principe de construction : la LISTE est la source de vérité, la carte est
 * une vue posée dessus. Dans cet ordre, l'accessibilité, l'absence de
 * JavaScript, le lecteur d'écran et le réseau faible se règlent d'eux-mêmes —
 * et l'exemption cartographique du référentiel est satisfaite, puisqu'elle est
 * conditionnée à la présence de l'information essentielle sous une forme
 * numérique accessible.
 *
 * Aucune requête sortante : Leaflet est en copie locale, les géométries sont
 * servies par le dépôt, il n'y a pas de tuile.
 */
(function (global) {
  "use strict";

  var sobre = global.matchMedia &&
    global.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function nf(x, d) {
    return new Intl.NumberFormat("fr-FR", {
      minimumFractionDigits: d || 0, maximumFractionDigits: d || 0
    }).format(x);
  }

  /* ------------------------------------------------ région d'état parlée */
  function Etat(zone) {
    var p = document.createElement("p");
    p.id = (zone.id || "carte") + "-etat";
    p.className = "sr-only";
    p.setAttribute("role", "status");
    p.setAttribute("aria-live", "polite");   /* jamais assertive : la carte bouge */
    zone.parentNode.insertBefore(p, zone.nextSibling);
    var minuteur = null;
    return function (texte) {
      clearTimeout(minuteur);
      minuteur = setTimeout(function () { p.textContent = texte; }, 500);
    };
  }

  /* ----------------------------------------- molette : gestion coopérative */
  function molette(carte, zone, mode) {
    if (mode === "libre") { return; }
    carte.scrollWheelZoom.disable();
    if (mode === "desactivee") { return; }
    if (mode === "apres-clic") {
      carte.once("click", function () { carte.scrollWheelZoom.enable(); });
      return;
    }
    /* coopérative : la page défile, Ctrl+molette zoome, deux doigts zooment */
    var voile = document.createElement("div");
    voile.className = "carto-voile";
    voile.setAttribute("aria-hidden", "true");
    voile.textContent = "Utilisez Ctrl + molette pour zoomer";
    zone.appendChild(voile);
    var cache = null;
    zone.addEventListener("wheel", function (e) {
      if (e.ctrlKey || e.metaKey) {
        e.preventDefault();
        carte.setZoom(carte.getZoom() - Math.sign(e.deltaY));
        return;
      }
      voile.classList.add("visible");
      clearTimeout(cache);
      cache = setTimeout(function () { voile.classList.remove("visible"); }, 1200);
    }, { passive: false });
    /* sur tactile : un doigt fait défiler la page, deux doigts manipulent */
    if (carte.dragging) {
      zone.addEventListener("touchstart", function (e) {
        if (e.touches.length > 1) { carte.dragging.enable(); }
        else { carte.dragging.disable(); }
      }, { passive: true });
      carte.dragging.disable();
    }
  }

  /* ---------------------------------------------------------- l'état d'URL */
  function urlEtat(carte, lire) {
    var report = null;
    function ecrire() {
      clearTimeout(report);
      report = setTimeout(function () {
        var c = carte.getCenter();
        var h = "#" + carte.getZoom() + "/" + c.lat.toFixed(4) + "/" + c.lng.toFixed(4);
        /* replaceState pour les mouvements continus : sinon chaque pixel de
           déplacement crée une entrée et le bouton Retour devient inutilisable */
        history.replaceState(null, "", h);
      }, 400);
    }
    carte.on("moveend zoomend", ecrire);
    if (lire && location.hash) {
      var m = location.hash.match(/^#(\d+)\/(-?[\d.]+)\/(-?[\d.]+)/);
      if (m) { carte.setView([+m[2], +m[3]], +m[1]); }
    }
  }

  /* ------------------------------------------------------------- la carte */
  function creer(opts) {
    var zone = typeof opts.zone === "string"
      ? document.getElementById(opts.zone) : opts.zone;
    if (!zone) { throw new Error("Conteneur de carte introuvable."); }

    zone.innerHTML = "";
    zone.setAttribute("role", "region");
    zone.setAttribute("tabindex", "0");
    if (opts.titreId) { zone.setAttribute("aria-labelledby", opts.titreId); }
    if (opts.descId) { zone.setAttribute("aria-describedby", opts.descId); }

    var carte = L.map(zone, {
      center: opts.centre, zoom: opts.zoom,
      minZoom: opts.zoomMin, maxZoom: opts.zoomMax,
      scrollWheelZoom: false,
      attributionControl: false,
      zoomControl: opts.zoomControl !== false
    });
    if (opts.bornes) { carte.setMaxBounds(opts.bornes); }
    L.control.scale({ imperial: false, maxWidth: 140 }).addTo(carte);

    molette(carte, zone, opts.molette || "cooperative");
    var dire = Etat(zone);

    /* Échap rend toujours la main : pas de piège au clavier */
    zone.addEventListener("keydown", function (e) {
      if (e.key === "Escape") { zone.blur(); }
    });

    if (opts.urlEtat !== false) { urlEtat(carte, opts.urlEtat !== "ecrire"); }

    return {
      carte: carte, zone: zone, dire: dire,
      aller: function (latlon, z) {
        /* une carte qui vole donne la nausée : on saute quand la préférence
           de mouvement réduit est posée */
        if (sobre) { carte.setView(latlon, z || carte.getZoom()); }
        else { carte.flyTo(latlon, z || carte.getZoom(), { duration: 0.8 }); }
      }
    };
  }

  /* ------------------------------------------- contours, points, liaisons */
  function contours(ctx, geojson, opts) {
    opts = opts || {};
    return L.geoJSON(geojson, {
      style: opts.style || { className: "carto-maille", fill: true,
                             fillOpacity: 0, weight: 1 },
      onEachFeature: function (f, couche) {
        var t = opts.intitule ? opts.intitule(f.properties) : null;
        if (t) { couche.bindTooltip(t, { sticky: true, className: "carto-bulle" }); }
      }
    }).addTo(ctx.carte);
  }

  /* Chaque point est un tracé SVG : on peut donc lui donner un intitulé et le
     rendre atteignable au clavier — ce qu'un rendu par le processeur
     graphique ne permet pas, puisqu'il n'y a aucun nœud derrière l'image. */
  function points(ctx, liste, opts) {
    opts = opts || {};
    var marques = [];
    liste.forEach(function (d, i) {
      var m = L.circleMarker([d.lat, d.lon], {
        className: opts.classe || "carto-point",
        radius: opts.rayon ? opts.rayon(d) : 5, weight: 1
      });
      m.bindTooltip(opts.intitule ? opts.intitule(d) : (d.nom || ""),
                    { direction: "top" });
      m.on("click", function () { if (opts.surClic) { opts.surClic(d, i); } });
      m.addTo(ctx.carte);
      var el = m.getElement();
      if (el) {
        el.setAttribute("tabindex", "0");
        el.setAttribute("role", "button");
        el.setAttribute("aria-label", opts.alt ? opts.alt(d) : (d.nom || ""));
        el.addEventListener("keydown", function (e) {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            if (opts.surClic) { opts.surClic(d, i); }
          }
        });
        el.addEventListener("focus", function () {
          if (opts.surSurvol) { opts.surSurvol(d, i, true); }
        });
      }
      marques.push(m);
    });
    /* Au-delà d'une vingtaine d'arrêts de tabulation, la carte devient un
       labyrinthe : on retire les points du parcours clavier et on renvoie vers
       la liste, qui est de toute façon la source de vérité. */
    if (marques.length > 20) {
      marques.forEach(function (m) {
        var el = m.getElement();
        if (el) { el.setAttribute("tabindex", "-1"); }
      });
      ctx.dire(marques.length + " lieux sur la carte. Utilisez la liste sous " +
               "la carte pour les parcourir un par un.");
    }
    return marques;
  }

  /* Le survol d'une ligne éclaire son point, le clic recentre. C'est
     l'équivalent clavier du clic sur la carte, et c'est ce qui rend la carte
     pilotable sans souris. */
  function lier(ctx, marques, lignes, opts) {
    opts = opts || {};
    lignes.forEach(function (ligne, i) {
      var m = marques[i];
      if (!m) { return; }
      function allumer(on) {
        var el = m.getElement();
        if (el) { el.classList.toggle("en-avant", on); }
        ligne.classList.toggle("en-avant", on);
      }
      ligne.addEventListener("mouseenter", function () { allumer(true); });
      ligne.addEventListener("mouseleave", function () { allumer(false); });
      ligne.addEventListener("focus", function () { allumer(true); }, true);
      ligne.addEventListener("blur", function () { allumer(false); }, true);
      ligne.addEventListener("click", function () {
        ctx.aller(m.getLatLng(), opts.zoom);
        ctx.dire((ligne.dataset.nom || "Lieu") + " sélectionné sur la carte.");
      });
    });
  }

  global.Carto = {
    creer: creer, contours: contours, points: points, lier: lier,
    nf: nf, sobre: sobre
  };
})(window);
