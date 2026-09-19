/* La carte du réseau, posée sur le socle carto-territoire.
   La liste est déjà dans la page : ce script ne la construit pas, il s'y
   accroche. Si rien ne s'exécute ici, la page reste entière. */
const ICI = [45.351370, 1.932210];
const FAMILLES = ["Terre et alimentation", "Réparer, réemployer",
                  "Habiter ensemble", "Lien social et culture",
                  "Solidarité et droits", "Économie sociale"];
/* Okabe & Ito — palette qualitative sûre pour les daltoniens. Chaque famille
   porte aussi une forme : la couleur seule ne suffit jamais. */
const COULEURS = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9"];
const FORMES = ["rond", "carre", "triangle", "losange", "croix", "pentagone"];

(async () => {
  const lignes = [...document.querySelectorAll("#liste tbody tr")];
  if (!lignes.length) { return; }

  let contours, routes = null;
  try {
    contours = await json("data/zone-communes.geojson");
  } catch (e) {
    document.getElementById("carte").innerHTML =
      "<p class='echec'>Les contours n'ont pas pu être chargés. " +
      "<a href='#annuaire'>La liste des lieux reste disponible ci-dessous.</a></p>";
    return;
  }
  /* Le fond est un supplément : s'il manque, la carte marche quand même. */
  let toponymes = null, eau = null;
  try { routes = await json("data/zone-routes.geojson"); } catch (e) { routes = null; }
  try { toponymes = await json("data/zone-toponymes.geojson"); } catch (e) { toponymes = null; }
  try { eau = await json("data/zone-eau.geojson"); } catch (e) { eau = null; }

  const ctx = Carto.creer({
    zone: "carte", centre: ICI, zoom: 9, zoomMin: 8, zoomMax: 13,
    molette: "cooperative", titreId: "carte-titre", descId: "carte-desc"
  });

  /* L'eau passe sous les routes : c'est à une rivière qu'on se situe en
     rural, mais une rivière ne franchit pas un pont par-dessus la route. */
  if (eau) { Carto.eau(ctx, eau, { depuisZoom: 0 }); }
  /* Les ruisseaux pèsent autant que tout le reste de l'eau et ne servent
     qu'au détail : la page ne va les chercher qu'en arrivant au zoom 12.
     Tant qu'on reste au-dessus, cet octet-là n'est jamais envoyé. */
  Carto.differer(ctx, "data/zone-eau-fine.geojson", 12, function (d) {
    Carto.eau(ctx, d, { depuisZoom: 12 });
  });
  if (routes) { Carto.routes(ctx, routes, { depuisZoom: 0 }); }

  const cc = Carto.contours(ctx, contours, {
    intitule: (p) => p.nom + (p.pop ? " — " + Carto.nf(p.pop) + " hab." : "")
  });
  /* Les noms de communes : Leaflet ne gère aucun évitement de chevauchement,
     donc on les fait apparaître par paliers, les bourgs d'abord. */
  /* Le socle place les noms un par un et saute ceux qui en recouvriraient un
     autre : c'est la seule façon d'en afficher beaucoup sans bouillie, Leaflet
     n'évitant rien de lui-même. Les plus peuplées passent en premier. */
  Carto.etiquettes(ctx, cc, {
    depuisZoom: 10,
    max: 40,
    rang: (p) => p.pop || 0,
    nom: (p) => p.nom,
    intituleSurvol: (p) => p.nom + (p.pop ? " — " + Carto.nf(p.pop) + " hab." : ""),
    surChangement: (n, actif) => {
      const z = document.getElementById("note-etiquettes");
      if (z) {
        z.textContent = actif
          ? n + " noms de communes affichés ici — les plus peuplées d'abord, "
            + "et seulement ceux qui tiennent sans se chevaucher."
          : "Zoomez pour faire apparaître les noms de communes.";
      }
    }
  });

  /* Les noms de villages et de hameaux, par paliers. On écarte ceux que
     l'étiquette de commune porte déjà : sinon le même nom s'écrit deux fois,
     à quelques pixels l'un de l'autre. */
  if (toponymes) {
    const nomsCommunes = new Set(
      (contours.features || []).map((f) => (f.properties || {}).nom).filter(Boolean));
    Carto.toponymes(ctx, toponymes, {
      seuils: [[11, 3], [12, 4], [13, 5]],
      exclure: nomsCommunes,
      max: 55,
      surChangement: (n, total) => {
        const z = document.getElementById("note-toponymes");
        if (z) {
          z.textContent = n
            ? n + " villages et hameaux nommés ici, sur " + Carto.nf(total)
              + " repris — on n'affiche que ceux qui tiennent sans se recouvrir."
            : "Zoomez pour faire apparaître les villages et les hameaux.";
        }
      }
    });
  }

  L.circle(ICI, { radius: 45000, className: "limite", fill: false, weight: 1.4 })
    .addTo(ctx.carte);
  L.circleMarker(ICI, { className: "ici", radius: 6, weight: 0 }).addTo(ctx.carte)
    .bindTooltip("le Mons", { permanent: true, direction: "right", className: "bulle-ici" });

  /* Les données viennent du tableau : une seule source, pas deux. */
  const lieux = lignes.map((l) => ({
    nom: l.dataset.nom,
    commune: l.children[1].textContent,
    distance: l.dataset.km + " km, " + l.dataset.ou,
    fam: (l.dataset.fam || "").split("|").filter(Boolean),
    prim: l.dataset.prim || "",
    site: l.dataset.site || "", decrit: l.dataset.decrit || "",
    heures: l.dataset.heures || "", origine: l.dataset.origine || "",
    lat: +l.dataset.lat, lon: +l.dataset.lon
  }));

  const fiche = Carto.fiche(ctx, "fiche", { intitule: "Fiche du lieu survolé" });

  function html(d) {
    let h = "<h3>" + (d.site
      ? "<a href='" + d.site + "' rel='noopener nofollow'>" + d.nom + "</a>"
      : d.nom) + "</h3>";
    h += "<p>" + d.commune + ", à " + d.distance +
         (d.fam.length ? " · " + d.fam.join(" · ") : "") + "</p>";
    if (d.decrit) { h += "<p>" + d.decrit + "</p>"; }
    h += "<dl>";
    if (d.heures) { h += "<dt>Horaires déclarés</dt><dd>" + d.heures + "</dd>"; }
    if (d.site) {
      h += "<dt>Site</dt><dd><a href='" + d.site + "' rel='noopener nofollow'>" +
           d.site.replace(/^https?:\/\//, "").replace(/\/$/, "") + "</a></dd>";
    }
    h += "</dl>";
    if (d.origine) {
      h += "<p class='carto-fiche-source'><a href='" + d.origine +
           "' rel='noopener nofollow'>Fiche d'origine, avec courriel et " +
           "téléphone</a> — nous ne les republions pas ici.</p>";
    } else {
      h += "<p class='carto-fiche-source'>Aucun lien vers la fiche d'origine " +
           "n'est publié par la source.</p>";
    }
    return h;
  }

  const marques = Carto.symboles(ctx, lieux, {
    categories: FAMILLES, couleurs: COULEURS, formes: FORMES,
    categorie: (d) => d.prim,
    intitule: (d) => d.nom,
    alt: (d) => d.nom + ", " + d.commune + ", à " + d.distance +
                (d.prim ? ", " + d.prim : ""),
    surSurvol: (d) => fiche.montrer(html(d)),
    surClic: (d, i) => { fiche.epingler(html(d), i); ctx.aller([d.lat, d.lon], 11); }
  });

  const sansFamille = lieux.filter((d) => !d.prim).length;
  const entrees = FAMILLES.map((f, i) => ({
      libelle: f, couleur: COULEURS[i], forme: FORMES[i],
      effectif: lieux.filter((d) => d.prim === f).length
    })).filter((e) => e.effectif);
  if (sansFamille) {
    /* Hors catégorie : sa propre forme et un gris hors palette, jamais la
       forme d'une famille — sinon seule la couleur les distinguerait. */
    entrees.push({ libelle: "Aucune famille déclarée", couleur: "#6b665e",
                   forme: "baton", effectif: sansFamille });
  }
  Carto.legende(ctx, "legende", entrees,
    { titre: "Famille principale — couleur et forme" });
  const zn = document.getElementById("note-familles");
  if (zn) {
    zn.textContent = "Un lieu relève souvent de plusieurs familles. Le symbole "
      + "porte la première ; les filtres, eux, tiennent compte de toutes — c'est "
      + "pourquoi les comptes des boutons et ceux de la légende diffèrent.";
  }

  Carto.lier(ctx, marques, lignes, { zoom: 11 });
  lignes.forEach((l, i) => {
    const d = lieux[i];
    l.addEventListener("mouseenter", () => fiche.montrer(html(d)));
    l.addEventListener("focus", () => fiche.montrer(html(d)));
    l.addEventListener("click", (e) => {
      if (e.target.closest("a")) { return; }   /* on suit le lien, on n'épingle pas */
      fiche.epingler(html(d), i);
    });
    l.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.target.closest("a")) { fiche.epingler(html(d), i); }
    });
  });

  /* --- les filtres agissent sur la carte ET sur le tableau --- */
  const zf = document.getElementById("filtres");
  const compte = {};
  lieux.forEach((d) => d.fam.forEach((f) => { compte[f] = (compte[f] || 0) + 1; }));
  zf.innerHTML = FAMILLES.filter((f) => compte[f]).map((f, i) =>
      "<button type='button' data-f=\"" + f + "\" aria-pressed='false'>" + f +
      " <span class='nb'>" + compte[f] + "</span></button>").join("") +
    "<button type='button' data-f='' aria-pressed='true' class='actif'>Tout</button>";

  let actives = new Set();
  function filtrer() {
    let vus = 0;
    lignes.forEach((l, i) => {
      const ok = !actives.size || lieux[i].fam.some((x) => actives.has(x));
      l.hidden = !ok;
      const el = marques[i] && marques[i].getElement();
      if (el) { el.classList.toggle("masque", !ok); }
      if (ok) { vus++; }
    });
    document.getElementById("intro-annuaire").textContent =
      vus + " lieux sur " + lignes.length +
      (actives.size ? " — filtre : " + [...actives].join(", ") : "") +
      ". Survolez une ligne pour lire sa fiche, cliquez pour la fixer.";
    ctx.dire(vus + " lieux affichés sur " + lignes.length + ".");
  }
  zf.addEventListener("click", (e) => {
    const b = e.target.closest("button"); if (!b) { return; }
    const f = b.dataset.f;
    if (!f) { actives.clear(); } else if (actives.has(f)) { actives.delete(f); }
    else { actives.add(f); }
    [...zf.querySelectorAll("button")].forEach((x) => {
      const on = x.dataset.f ? actives.has(x.dataset.f) : !actives.size;
      x.classList.toggle("actif", on);
      x.setAttribute("aria-pressed", on ? "true" : "false");
    });
    filtrer();
  });
})();
