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
    /* Sur TACTILE seulement : un doigt fait défiler la page, deux doigts
       manipulent la carte. À la souris, le glisser doit rester actif — le
       désactiver partout rend la carte immobile, et c'est un piège dans lequel
       on tombe une fois. */
    var tactile = global.matchMedia &&
      global.matchMedia("(pointer: coarse)").matches;
    if (tactile && carte.dragging) {
      zone.addEventListener("touchstart", function (e) {
        if (e.touches.length > 1) { carte.dragging.enable(); }
        else { carte.dragging.disable(); }
      }, { passive: true });
      carte.dragging.disable();
    }
  }

  /* ---------------------------------------------------------- l'état d'URL */
  function urlEtat(carte) {
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
    ecrire();
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

    /* L'état d'URL est lu AVANT de construire la carte. Le poser après, par
       setView, laissait la carte se créer au zoom par défaut puis sauter :
       tout ce qui dépend du zoom à l'initialisation (les étiquettes, par
       exemple) voyait alors la mauvaise valeur. */
    var centre = opts.centre, zoom = opts.zoom;
    if (opts.urlEtat !== false && opts.urlEtat !== "ecrire" && global.location.hash) {
      var h = global.location.hash.match(/^#(\d+)\/(-?[\d.]+)\/(-?[\d.]+)/);
      if (h) { zoom = +h[1]; centre = [+h[2], +h[3]]; }
    }

    var carte = L.map(zone, {
      center: centre, zoom: zoom,
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

    if (opts.urlEtat !== false) { urlEtat(carte); }

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


  /* ----------------------------------------- placement sans chevauchement */
  /* Leaflet ne gère AUCUN évitement : il empile des blocs positionnés. Des
     paliers par rang ne suffisent pas — il y a trois mille hameaux dans un
     carré de quatre-vingt-dix kilomètres, et au zoom où ils deviennent
     pertinents ils s'écrasent tous les uns sur les autres.

     La parade est le placement glouton : on trie par importance, on pose, et
     on saute tout ce qui recouvrirait un nom déjà posé. C'est ce que font les
     vrais moteurs de rendu ; ça tient en trente lignes et ça change tout.

     On ne considère que ce qui est dans la vue : au zoom de détail, c'est une
     fraction du jeu, et le coût s'effondre. */
  function placer(ctx, candidats, opts) {
    opts = opts || {};
    var carte = ctx.carte;
    var bornes = carte.getBounds().pad(opts.marge == null ? 0.08 : opts.marge);
    var max = opts.max || 70;
    var parCar = opts.largeurCaractere || 5.6;
    var hauteur = opts.hauteur || 15;
    var ecart = opts.ecart || 3;

    var vus = [];
    for (var i = 0; i < candidats.length; i++) {
      var c = candidats[i];
      if (c.rangMax != null && c.rang > c.rangMax) { continue; }
      if (!bornes.contains(c.latlng)) { continue; }
      vus.push(c);
    }
    vus.sort(function (a, b) {
      return (a.rang - b.rang) || ((b.poids || 0) - (a.poids || 0));
    });

    var pris = [], retenus = [];
    for (var j = 0; j < vus.length && retenus.length < max; j++) {
      var d = vus[j];
      var p = carte.latLngToContainerPoint(d.latlng);
      var l = d.texte.length * parCar + 8;
      var r = [p.x - l / 2 - ecart, p.y - hauteur / 2 - ecart,
               p.x + l / 2 + ecart, p.y + hauteur / 2 + ecart];
      var libre = true;
      for (var k = 0; k < pris.length; k++) {
        var q = pris[k];
        if (r[0] < q[2] && r[2] > q[0] && r[1] < q[3] && r[3] > q[1]) {
          libre = false; break;
        }
      }
      if (!libre) { continue; }
      pris.push(r);
      retenus.push(d);
    }
    return retenus;
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
    var candidats = [];

    couche.eachLayer(function (l) {
      var p = l.feature && l.feature.properties;
      if (!p || !nom(p)) { return; }
      var centre;
      try { centre = l.getBounds().getCenter(); } catch (e) { return; }
      candidats.push({ latlng: centre, texte: nom(p), couche: l,
                       /* le rang est inversé : plus la commune est peuplée,
                          plus elle passe tôt */
                       rang: -(rang(p) || 0), poids: rang(p) || 0,
                       posee: false });
    });

    function revoir() {
      var actif = ctx.carte.getZoom() >= depuis;
      var retenus = actif ? placer(ctx, candidats, {
        max: opts.max || 45, hauteur: 15, largeurCaractere: 5.8
      }) : [];
      var garde = new Set(retenus);
      var n = 0;
      candidats.forEach(function (e) {
        var veut = garde.has(e);
        if (veut) { n++; }
        if (veut === e.posee) { return; }
        e.posee = veut;
        if (veut) {
          e.couche.bindTooltip(e.texte, {
            permanent: true, direction: "center", className: "carto-etiquette",
            interactive: false
          }).openTooltip();
        } else {
          e.couche.unbindTooltip();
          if (opts.intituleSurvol) {
            e.couche.bindTooltip(
              opts.intituleSurvol(e.couche.feature.properties),
              { sticky: true, className: "carto-bulle" });
          }
        }
      });
      if (opts.surChangement) { opts.surChangement(n, actif); }
    }
    ctx.carte.on("zoomend moveend", revoir);
    ctx.carte.whenReady(revoir);
    revoir();
    return { revoir: revoir, compte: function () { return candidats.length; } };
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
    /* Borne haute : quand des tuiles prennent le relais, ces routes-ci doivent
       DISPARAÎTRE. Sans ça on dessine deux fois le même réseau, celui du dépôt
       par-dessus celui du fond, avec des tracés qui ne coïncident pas tout à
       fait — c'est illisible et ça se voit. */
    var jusqua = opts.jusquaZoom == null ? 99 : opts.jusquaZoom;
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
      var veut = z >= depuis && z <= jusqua;
      if (veut && !ctx.carte.hasLayer(couche)) { couche.addTo(ctx.carte); }
      else if (!veut && ctx.carte.hasLayer(couche)) { ctx.carte.removeLayer(couche); }
    }
    ctx.carte.on("zoomend", revoir);
    revoir();
    return couche;
  }

  /* ------------------------------------------------------------- l'eau */
  /* Sur un territoire rural, on se repère à une rivière et à un étang bien
     avant de se repérer à une limite administrative. L'eau passe donc sous
     tout le reste, dans un bleu sourd : c'est un repère, pas une donnée. */
  function eau(ctx, geojson, opts) {
    opts = opts || {};
    pane(ctx);
    var couche = L.geoJSON(geojson, {
      pane: "carto-fond",
      style: function (f) {
        var plan = (f.properties || {}).genre === "plan";
        return plan
          ? { className: "carto-eau-plan", weight: 0.6, fill: true,
              fillOpacity: 1, interactive: false }
          : { className: "carto-eau-cours", weight: 1.1, fill: false,
              interactive: false };
      }
    });
    return borner(ctx, couche, opts);
  }

  /* ------------------------------------------------------- les toponymes */
  /* Villages et hameaux, par paliers de zoom. Même raison que pour les
     communes : Leaflet empile les étiquettes sans les écarter, donc sans
     hiérarchie tout se chevauche. Le rang vient de la source — ville, bourg,
     village, hameau — et on en montre de plus en plus en descendant. */
  function toponymes(ctx, geojson, opts) {
    opts = opts || {};
    var seuils = opts.seuils || [[11, 2], [12, 3], [13, 4], [14, 5]];
    var exclure = opts.exclure || null;   /* noms déjà portés par les communes */
    var candidats = [];

    (geojson.features || []).forEach(function (f) {
      var p = f.properties || {};
      if (!p.nom) { return; }
      if (exclure && exclure.has(p.nom)) { return; }
      var c = f.geometry.coordinates;
      candidats.push({ latlng: L.latLng(c[1], c[0]), texte: p.nom,
                       rang: p.rang || 5, poids: p.pop || 0,
                       genre: p.genre || "lieu", marque: null });
    });

    function rangMax(z) {
      for (var i = 0; i < seuils.length; i++) {
        if (z <= seuils[i][0]) { return seuils[i][1]; }
      }
      return 9;
    }
    function revoir() {
      var z = ctx.carte.getZoom();
      var max = z < seuils[0][0] ? 0 : rangMax(z);
      candidats.forEach(function (e) { e.rangMax = max; });
      var retenus = max ? placer(ctx, candidats, {
        max: opts.max || 60, hauteur: 13, largeurCaractere: 5.2
      }) : [];
      var garde = new Set(retenus);
      candidats.forEach(function (e) {
        if (garde.has(e)) {
          if (!e.marque) {
            e.marque = L.marker(e.latlng, {
              icon: L.divIcon({
                className: "carto-toponyme-hote",
                html: '<span class="carto-toponyme carto-toponyme-' + e.genre
                      + '">' + e.texte + "</span>",
                iconSize: null }),
              interactive: false, keyboard: false });
          }
          if (!ctx.carte.hasLayer(e.marque)) { e.marque.addTo(ctx.carte); }
        } else if (e.marque && ctx.carte.hasLayer(e.marque)) {
          ctx.carte.removeLayer(e.marque);
        }
      });
      if (opts.surChangement) { opts.surChangement(retenus.length, candidats.length); }
    }
    ctx.carte.on("zoomend moveend", revoir);
    ctx.carte.whenReady(revoir);
    revoir();
    return { revoir: revoir, total: candidats.length };
  }

  /* --------------------------------------------------------- outils communs */
  function pane(ctx) {
    if (ctx.carte.getPane("carto-fond") === undefined) {
      ctx.carte.createPane("carto-fond");
      ctx.carte.getPane("carto-fond").style.zIndex = 390;
    }
  }
  function borner(ctx, couche, opts) {
    var depuis = opts.depuisZoom || 0;
    var jusqua = opts.jusquaZoom == null ? 99 : opts.jusquaZoom;
    function revoir() {
      var z = ctx.carte.getZoom();
      var veut = z >= depuis && z <= jusqua;
      if (veut && !ctx.carte.hasLayer(couche)) { couche.addTo(ctx.carte); }
      else if (!veut && ctx.carte.hasLayer(couche)) { ctx.carte.removeLayer(couche); }
    }
    ctx.carte.on("zoomend", revoir);
    ctx.carte.whenReady(revoir);
    revoir();
    return couche;
  }

  /* ------------------------------------------- tuiles, à partir d'un zoom */
  /* Des tuiles, c'est une requête par carreau vers un tiers : il reçoit
     l'adresse du visiteur ET la suite des carreaux demandés, donc son parcours
     de regard. On ne les allume donc qu'à partir d'un zoom, et JAMAIS sur la
     vue d'ensemble : tant que personne n'a zoomé, rien ne sort.

     Trois obligations qui vont avec, et que cette fonction rend difficiles à
     oublier : l'attribution doit être visible sur la carte, la page doit dire
     ce qui se déclenche et à partir de quand, et la politique de sécurité de
     contenu doit lister l'hôte — sinon la carte reste grise sans explication. */
  function tuiles(ctx, opts) {
    opts = opts || {};
    if (!opts.url) { throw new Error("tuiles() : url manquante."); }
    if (!opts.attribution) {
      throw new Error("tuiles() : attribution obligatoire. Un fond servi par "
                    + "un tiers se cite, visiblement, sur la carte.");
    }
    var depuis = opts.depuisZoom == null ? 12 : opts.depuisZoom;
    var couche = L.tileLayer(opts.url, {
      minZoom: depuis,
      maxZoom: opts.maxZoom || 19,
      /* Pas de crossOrigin : il n'apporte rien ici et fait échouer le
         chargement chez tout fournisseur qui n'envoie pas d'en-tête CORS. */
      /* Le pane des tuiles est sous les surcouches : les contours, les routes
         et les points restent lisibles par-dessus. */
      className: "carto-tuiles"
    });
    var bandeau = null;
    if (opts.dansLaCarte !== false) {
      bandeau = document.createElement("p");
      bandeau.className = "carto-attribution";
      bandeau.hidden = true;
      bandeau.innerHTML = opts.attribution;
      ctx.zone.appendChild(bandeau);
    }
    var allume = false;
    function revoir() {
      var veut = ctx.carte.getZoom() >= depuis;
      if (veut === allume) { return; }
      allume = veut;
      if (veut) { couche.addTo(ctx.carte); }
      else { ctx.carte.removeLayer(couche); }
      if (bandeau) { bandeau.hidden = !veut; }
      if (opts.surBascule) { opts.surBascule(veut); }
      ctx.dire(veut
        ? "Fond de carte détaillé affiché. Il est servi par " +
          (opts.fournisseur || "un tiers") + ", qui reçoit votre adresse."
        : "Fond de carte détaillé retiré. Plus aucune requête ne sort.");
    }
    ctx.carte.on("zoomend", revoir);
    ctx.carte.whenReady(revoir);
    revoir();
    return { couche: couche, revoir: revoir, depuisZoom: depuis,
             estAllume: function () { return allume; } };
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
      /* Sans catégorie : une forme À PART. Réutiliser celle de la première
         catégorie ferait deux symboles que seule la couleur distingue — c'est
         exactement ce que le double codage doit empêcher. */
      var forme = FORMES[j >= 0 ? formes[j] : (opts.formeDefaut || "baton")]
                  || FORMES.baton;
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
    etiquettes: etiquettes, routes: routes, tuiles: tuiles,
    eau: eau, toponymes: toponymes, symboles: symboles,
    fiche: fiche, legende: legende,
    FORMES: FORMES, ORDRE_FORMES: ORDRE_FORMES,
    nf: nf, sobre: sobre
  };
})(window);
