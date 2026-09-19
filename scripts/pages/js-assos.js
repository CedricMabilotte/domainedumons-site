const FAITS = {
  ouverture:   ["Ouvrir un lieu ou une ressource", "accueillir, héberger, prêter des outils, mettre une ressource à disposition de non-membres"],
  transmission:["Transmettre un savoir", "former, sensibiliser, accompagner des personnes extérieures à l'association"],
  commun:      ["Entretenir un commun", "prendre soin d'un bien qui n'est à personne : rivière, forêt, chemins, semences, petit patrimoine"],
  solidarite:  ["Porter une solidarité", "aider des personnes en difficulté qui ne sont pas les membres"],
  territoire:  ["Faire vivre le territoire autrement", "circuits courts, réemploi, énergie citoyenne, habitat partagé, installation agricole"]
};
(async () => {
  let d, dt;
  try {
    [d, dt] = await Promise.all([json("data/associations.json"),
                                 json("data/associations-douteuses.json").catch(() => null)]);
  } catch (e) {
    ["condense", "synthese", "liste"].forEach((i) => echec(i, "Recensement associatif indisponible."));
    return;
  }
  const parHab = d.population_zone / d.actives;
  document.getElementById("condense").innerHTML = "<ul>" +
    "<li><strong>" + nf0(d.actives) + " associations actives</strong> sont domiciliées dans la zone — une pour " +
      nf0(parHab) + " habitants.</li>" +
    "<li><strong>" + nf0(d.lues) + " objets déclarés</strong> ont été lus un par un contre une grille écrite d'avance.</li>" +
    "<li><strong>" + nf0(d.verdicts.retenu) + " retenues</strong>, " + nf0(d.verdicts.douteux) +
      " laissées en doute, " + nf0(d.verdicts.hors) + " écartées.</li>" +
    "<li>Le critère est <strong>ce que l'association dit faire pour des non-membres</strong>, jamais son statut ni son nom.</li>" +
    "</ul>";
  const avant1990 = Object.entries(d.par_decennie).filter(([k]) => +k < 1990)
                          .reduce((a, [, v]) => a + v, 0);
  document.getElementById("synthese").innerHTML =
    tuile("Associations actives", nf0(d.actives), "", "domiciliées dans une des " + nf0(d.communes_zone) + " communes de la zone") +
    tuile("Une pour", nf0(parHab), "hab.", "sur " + nf0(d.population_zone) + " habitants") +
    tuile("Déclarées avant 1990", nf0(avant1990), "", Math.round(100 * avant1990 / d.actives) + " % du total — le tissu est ancien") +
    tuile("Retenues après lecture", nf0(d.verdicts.retenu), "", "sur " + nf0(d.lues) + " objets lus, soit " +
          Math.round(100 * d.verdicts.retenu / d.lues) + " %");
  document.getElementById("lecture-total").innerHTML =
    "<p>Ce total est <strong>plus de quatre fois</strong> celui que nous publiions la veille. La première version comptait les associations " +
    "de l'annuaire des entreprises, qui ne voit que celles qui ont un numéro SIREN — c'est-à-dire celles qui emploient, " +
    "perçoivent des subventions publiques ou sont assujetties à la TVA. <strong>Environ une association sur quatre.</strong> " +
    "Les autres, la grande majorité, n'existent que dans le répertoire du ministère de l'Intérieur.</p>" +
    "<p>Une association pour " + nf0(parHab) + " habitants, c'est un chiffre à lire avec précaution&nbsp;: " +
    "« active » veut dire ici <em>qui n'a pas déclaré sa dissolution</em>, ce qui n'est pas la même chose que vivante. " +
    "Il n'empêche&nbsp;: <strong>la densité associative n'est pas une hypothèse ici, c'est un fait mesuré</strong>, et l'idée " +
    "d'un territoire vide où tout serait à construire ne tient pas.</p>";
  document.getElementById("faits").innerHTML = Object.entries(FAITS).map(([k, v]) =>
    tuile(v[0], nf0(d.par_fait[k] || 0), "", v[1])).join("");
  const fam = Object.entries(d.par_famille).sort((a, b) => b[1] - a[1]).slice(0, 14);
  document.getElementById("familles").innerHTML =
    "<table class='donnees'><thead><tr><th>Famille déclarée</th><th>Associations</th><th>Part</th></tr></thead><tbody>" +
    fam.map((x) => "<tr><td>" + (d.familles[x[0]] || x[0]) + "</td><td>" + nf0(x[1]) + "</td><td>" +
      nf(100 * x[1] / d.actives, 1) + " %</td></tr>").join("") + "</tbody></table>";
  const actives = new Set();
  const zf = document.getElementById("filtres-faits");
  zf.innerHTML = Object.entries(FAITS).map(([k, v]) =>
    "<button type='button' aria-pressed='false' data-f='" + k + "'>" + v[0] +
    " <span class='nb'>" + nf0(d.par_fait[k] || 0) + "</span></button>").join("") +
    "<button type='button' data-f='' aria-pressed='true'>Tout</button>";
  zf.addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (!b) return;
    const f = b.dataset.f;
    if (!f) actives.clear();
    else if (actives.has(f)) actives.delete(f); else actives.add(f);
    zf.querySelectorAll("button").forEach((x) => x.setAttribute("aria-pressed",
      x.dataset.f ? String(actives.has(x.dataset.f)) : String(actives.size === 0)));
    rendre();
  });
  /* La liste complète ferait quatre-vingts mètres de page : on la sert par
     tranches, avec une recherche par nom ou par commune. */
  const PAS = 60;
  let montre = PAS, cherche = "";
  const sa = (t) => (t || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
  const zr = document.getElementById("recherche");
  zr.innerHTML = "<label for='q'>Chercher un nom ou une commune</label>" +
    "<input type='search' id='q' autocomplete='off' placeholder='ressourcerie, Tulle, jardin…'>";
  zr.querySelector("input").addEventListener("input", (e) => {
    cherche = sa(e.target.value); montre = PAS; rendre();
  });
  function filtrees() {
    return d.retenues.filter((a) =>
      (!actives.size || a.faits.some((f) => actives.has(f))) &&
      (!cherche || sa(a.nom).includes(cherche) || sa(a.commune).includes(cherche) ||
       sa(a.lecture).includes(cherche)));
  }
  function rendre() {
    const vus = filtrees();
    document.getElementById("intro-retenues").innerHTML =
      "<strong>" + nf0(vus.length) + " associations</strong>, de la plus proche à la plus éloignée" +
      (actives.size ? " — filtre : " + [...actives].map((k) => FAITS[k][0].toLowerCase()).join(", ") : "") +
      (cherche ? " — recherche en cours" : "") +
      ". Chacune porte ce qu'elle déclare faire.";
    const tranche = vus.slice(0, montre);
    document.getElementById("liste").innerHTML = tranche.map((a) =>
      "<p><span class='lieu-nom'>" + a.nom + "</span> <span class='lieu-detail'>" +
      a.commune + " · " + nf(a.km, 1) + " km" + (a.annee ? " · " + a.annee : "") + "</span>" +
      "<br><span class='lecture'>" + a.lecture + "</span></p>").join("") ||
      "<p class='nb'>Aucune association ne correspond.</p>";
    const reste = vus.length - tranche.length;
    document.getElementById("suite").innerHTML = reste > 0
      ? "<button type='button' class='suite'>Voir " + nf0(Math.min(PAS, reste)) +
        " associations de plus <span class='nb'>" + nf0(reste) + " restantes</span></button>"
      : (vus.length > PAS ? "<p class='nb'>Fin de la liste — " + nf0(vus.length) + " associations affichées.</p>" : "");
  }
  document.getElementById("suite").addEventListener("click", (e) => {
    if (e.target.closest("button")) { montre += PAS; rendre(); }
  });
  rendre();
  if (dt) {
    document.getElementById("intro-douteuses").innerHTML =
      "<strong>" + nf0(dt.total) + " associations</strong> pour lesquelles la lecture de l'objet n'a pas suffi à trancher.";
    /* Repliées par défaut : on ne les construit qu'à l'ouverture, sinon on paie
       neuf cents nœuds pour un bloc que personne n'a demandé. */
    const det = document.getElementById("pli-douteuses");
    det.addEventListener("toggle", function poser() {
      if (!det.open) return;
      det.removeEventListener("toggle", poser);
      document.getElementById("liste-douteuses").innerHTML = dt.douteuses.map((a) =>
        "<p><span class='lieu-nom'>" + a.nom + "</span> <span class='lieu-detail'>" +
        a.commune + " · " + nf(a.km, 1) + " km" + (a.famille ? " · " + a.famille : "") + "</span></p>").join("");
    });
  }
  document.getElementById("horodatage").textContent =
    "Recensement du " + new Date(d.calcule_le).toLocaleDateString("fr-FR", { dateStyle: "long" }) +
    " · Répertoire national des associations (millésime du 1er septembre 2026) et nomenclature DILA · Licence Ouverte 2.0.";
})();
