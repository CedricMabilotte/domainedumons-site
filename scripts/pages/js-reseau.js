(async () => {
  // Écrire dans un élément qui n'existe pas fait tomber tout ce qui suit.
  // C'est ainsi que le condensé, les tuiles et l'horodatage de cette page
  // sont restés muets trois jours quand une seule clé manquait.
  const poser = (id, html) => { const e = document.getElementById(id); if (e) e.innerHTML = html; };
  const texte = (id, t) => { const e = document.getElementById(id); if (e) e.textContent = t; };
  let L2, C, A;
  try {
    [L2, C, A] = await Promise.all([json("data/reseau-lieux.json"), json("data/zone-une-heure.json"),
                                    json("data/associations.json")]);
  } catch (e) { echec("condense", "Données du réseau indisponibles."); echec("synthese", ""); return; }
  const communes = new Set(L2.lieux.map((l) => l.commune)).size;
  poser("condense", "<ul>" +
    "<li><strong>" + nf0(L2.total) + " fiches</strong> d'annuaire dans l'heure, sur " + communes + " communes — au plus " + nf0(L2.lieux.filter((l) => !l.doublon_de).length) + " lieux distincts.</li>" +
    "<li><strong>" + nf0(A.actives) + " associations actives</strong> domiciliées dans la zone, dont <strong>" +
      nf0(A.verdicts.retenu) + "</strong> retenues après lecture de leur objet déclaré.</li>" +
    "<li>La zone couvre " + nf0(C.total) + " communes et " + nf0(C.population) + " habitants, à 45 km à la ronde.</li>" +
    "<li>Le fil commun reste à ouvrir&nbsp;: il démarrera à trois lieux participants.</li>" +
    "</ul>");
  poser("synthese",
    tuile("Lieux référencés", nf0(L2.total), "", "sur " + communes + " communes · aucun vérifié sur place") +
    tuile("Associations actives", nf0(A.actives), "", "une pour " + nf0(A.population_zone / A.actives) + " habitants") +
    tuile("Retenues après lecture", nf0(A.verdicts.retenu), "", nf0(A.lues) + " objets déclarés lus un par un") +
    tuile("Le fil commun", "0", "envoi", "il démarre à trois lieux participants"));
  texte("horodatage",
    "Relevé le " + new Date(L2.calcule_le).toLocaleDateString("fr-FR", { dateStyle: "long" }) +
    " · Transiscope, Répertoire national des associations, geo.api.gouv.fr · Licence Ouverte 2.0.");
})();
