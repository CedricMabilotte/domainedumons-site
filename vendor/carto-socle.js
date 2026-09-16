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


  /* ------------------------------------------------ étiquettes de communes */
  /* Leaflet ne gère AUCUN évitement de chevauchement : il empile des blocs
     positionnés. Poser 284 noms d'un coup donne une bouillie. On n'en affiche
     donc qu'à partir d'un zoom, et seulement au-dessus d'un rang — les bourgs
     d'abord. C'est une limite de la bibliothèque, pas un choix esthétique. */
  function etiquettes(ctx, couche, opts) {
    opts = opts || {};
    var depuis = opts.depuisZoom || 11;
    var rang = opts.rang || function (p) { return p.pop || 0; };
    var nom = opts.nom || function (p) { return p.nom; };
    var seuils = opts.seuils || [[11, 1500], [12, 600], [13, 0]];
    var posees = [];

    couche.eachLayer(function (l) {
      var p = l.feature && l.feature.properties;
      if (!p || !nom(p)) { return; }
      posees.push({ couche: l, rang: rang(p), nom: nom(p), visible: false });
    });

    function seuilPour(z) {
      for (var i = 0; i < seuils.length; i++) {
        if (z <= seuils[i][0]) { return seuils[i][1]; }
      }
      return 0;
    }

    function revoir() {
      var z = ctx.carte.getZoom();
      var actif = z >= depuis;
      var s = seuilPour(z);
      var n = 0;
      posees.forEach(function (e) {
        var veut = actif && e.rang >= s;
        if (veut === e.visible) { if (veut) { n++; } return; }
        e.visible = veut;
        if (veut) {
          e.couche.bindTooltip(e.nom, {
            permanent: true, direction: "center", className: "carto-etiquette",
            interactive: false
          }).openTooltip();
          n++;
        } else {
          e.couche.unbindTooltip();
          if (opts.intituleSurvol) {
            e.couche.bindTooltip(opts.intituleSurvol(e.couche.feature.properties),
                                 { sticky: true, className: "carto-bulle" });
          }
        }
      });
      if (opts.surChangement) { opts.surChangement(n, actif); }
    }
    ctx.carte.on("zoomend", revoir);
    revoir();
    return { revoir: revoir, compte: function () { return posees.length; } };
  }

  /* ------------------------------------------------------- fond de routes */
  /* Un fond routier sans tuile : les axes structurants en géométries servies
     par le dépôt. On y perd les petites routes et les noms de rue ; on y gagne
     de ne rien envoyer à personne. */
  var ROUTES = {
    autoroute:    { poids: 3.0, classe: "carto-route-a" },
    nationale:    { poids: 2.2, classe: "carto-route-n" },
    departementale: { poids: 1.3, classe: "carto-route-d" },
    autre:        { poids: 0.8, classe: "carto-route-x" }
  };
  function routes(ctx, geojson, opts) {
    opts = opts || {};
    var depuis = opts.depuisZoom || 0;
    var couche = L.geoJSON(geojson, {
      style: function (f) {
        var r = ROUTES[(f.properties || {}).rang] || ROUTES.autre;
        return { className: r.classe, weight: r.poids, fill: false,
                 interactive: false };
      }
    });
    if (opts.sousLesPoints !== false && ctx.carte.getPane("carto-fond") === undefined) {
      ctx.carte.createPane("carto-fond");
      ctx.carte.getPane("carto-fond").style.zIndex = 390;
    }
    couche.options.pane = "carto-fond";
    function revoir() {
      var z = ctx.carte.getZoom();
      if (z >= depuis && !ctx.carte.hasLayer(couche)) { couche.addTo(ctx.carte); }
      else if (z < depuis && ctx.carte.hasLayer(couche)) { ctx.carte.removeLayer(couche); }
    }
    ctx.carte.on("zoomend", revoir);
    revoir();
    return couche;
  }

  /* --------------------------------------- symboles : couleur ET forme */
  /* La couleur seule ne suffit jamais — environ 8 % des hommes ont une
     déficience de la vision des couleurs, et une carte photocopiée en noir et
     blanc est un usage réel. Chaque catégorie porte donc une teinte ET une
     forme, et son nom figure dans l'intitulé accessible. */
  var FORMES = {
    rond:      'M0,-7a7,7 0 1,0 0.1,0z',
    carre:     'M-6,-6h12v12h-12z',
    triangle:  'M0,-7.5L7,6H-7z',
    losange:   'M0,-8L8,0L0,8L-8,0z',
    croix:     'M-2.3,-7h4.6v4.7h4.7v4.6h-4.7v4.7h-4.6v-4.7h-4.7v-4.6h4.7z',
    pentagone: 'M0,-7.5L7.1,-2.3L4.4,6H-4.4L-7.1,-2.3z',
    baton:     'M-1.8,-7.5h3.6v15h-3.6z'
  };
  var ORDRE_FORMES = ["rond", "carre", "triangle", "losange", "croix",
                      "pentagone", "baton"];

  function symboles(ctx, liste, opts) {
    opts = opts || {};
    var cats = opts.categories || [];
    var couleurs = opts.couleurs || [];
    var formes = opts.formes ||
      cats.map(function (_, i) { return ORDRE_FORMES[i % ORDRE_FORMES.length]; });
    var cle = opts.categorie || function (d) { return d.cat; };
    var marques = [];
    var trop = liste.length > (opts.maxClavier || 20);

    liste.forEach(function (d, i) {
      var k = cle(d);
      var j = cats.indexOf(k);
      var couleur = j >= 0 ? couleurs[j] : (opts.couleurDefaut || "#6b665e");
      var forme = FORMES[j >= 0 ? formes[j] : "rond"] || FORMES.rond;
      var svg = '<svg viewBox="-10 -10 20 20" width="17" height="17" '
              + 'aria-hidden="true" focusable="false">'
              + '<path d="' + forme + '" fill="' + couleur + '" '
              + 'stroke="#ffffff" stroke-width="1.6"/></svg>';
      var icone = L.divIcon({
        html: '<button type="button" class="carto-symbole" tabindex="'
              + (trop ? "-1" : "0") + '">' + svg + '</button>',
        className: "carto-symbole-hote", iconSize: [17, 17],
        iconAnchor: [8.5, 8.5]
      });
      var m = L.marker([d.lat, d.lon], {
        icon: icone,
        keyboard: false,
        alt: opts.alt ? opts.alt(d) : (d.nom || "")
      }).addTo(ctx.carte);
      var b = m.getElement() && m.getElement().querySelector("button");
      if (b) {
        b.setAttribute("aria-label", opts.alt ? opts.alt(d) : (d.nom || ""));
        var montrer = function () { if (opts.surSurvol) { opts.surSurvol(d, i); } };
        b.addEventListener("mouseenter", montrer);
        b.addEventListener("focus", montrer);
        b.addEventListener("click", function (e) {
          e.preventDefault();
          if (opts.surClic) { opts.surClic(d, i); }
        });
      }
      m.bindTooltip(opts.intitule ? opts.intitule(d) : (d.nom || ""),
                    { direction: "top", className: "carto-bulle" });
      marques.push(m);
    });
    if (trop) {
      ctx.dire(liste.length + " lieux sur la carte. Utilisez la liste sous la "
             + "carte pour les parcourir un par un.");
    }
    return marques;
  }

  /* --------------------------------------------------- panneau de fiche */
  /* Demandé comme « info-bulle au survol ». Une bulle qui suit le curseur
     échoue sur trois points : elle disparaît dès qu'on veut la lire, elle
     masque la carte, et elle n'existe pas au doigt ni au clavier. Un panneau
     posé dans le flux règle les trois : il se remplit au survol, au focus et
     au clic, il reste, Échap le vide, et il ne recouvre rien. */
  function fiche(ctx, cible, opts) {
    opts = opts || {};
    var zone = typeof cible === "string" ? document.getElementById(cible) : cible;
    if (!zone) { return { montrer: function () {}, vider: function () {} }; }
    zone.setAttribute("role", "region");
    zone.setAttribute("aria-live", "polite");
    if (opts.intitule) { zone.setAttribute("aria-label", opts.intitule); }
    var vide = opts.vide || "<p class='carto-fiche-vide'>Survolez un point, ou "
             + "choisissez une ligne dans la liste, pour lire sa fiche.</p>";
    zone.innerHTML = vide;
    var epingle = null;

    function montrer(html, force) {
      if (epingle !== null && !force) { return; }
      zone.innerHTML = html;
    }
    function vider() { epingle = null; zone.innerHTML = vide; }
    function epingler(html, id) { epingle = id; zone.innerHTML = html; }

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") { vider(); }
    });
    return { montrer: montrer, vider: vider, epingler: epingler,
             zone: zone, estEpingle: function () { return epingle !== null; } };
  }

  /* ------------------------------------------------------------ légende */
  function legende(ctx, cible, entrees, opts) {
    opts = opts || {};
    var zone = typeof cible === "string" ? document.getElementById(cible) : cible;
    if (!zone) { return; }
    var html = "<ul>";
    entrees.forEach(function (e, i) {
      var forme = FORMES[e.forme || ORDRE_FORMES[i % ORDRE_FORMES.length]] || FORMES.rond;
      html += "<li><span class='carto-pastille-svg' aria-hidden='true'>"
            + '<svg viewBox="-10 -10 20 20" width="15" height="15">'
            + '<path d="' + forme + '" fill="' + e.couleur + '" '
            + 'stroke="#ffffff" stroke-width="1.6"/></svg></span>'
            + "<span>" + e.libelle
            + (e.effectif != null ? " <span class='nb'>" + e.effectif + "</span>" : "")
            + "</span></li>";
    });
    html += "</ul>";
    zone.innerHTML = (opts.titre ? "<p class='carto-legende-titre'>" + opts.titre
                                 + "</p>" : "") + html;
    zone.classList.add("carto-legende");
  }

  global.Carto = {
    creer: creer, contours: contours, points: points, lier: lier,
    etiquettes: etiquettes, routes: routes, symboles: symboles,
    fiche: fiche, legende: legende,
    FORMES: FORMES, ORDRE_FORMES: ORDRE_FORMES,
    nf: nf, sobre: sobre
  };
})(window);
