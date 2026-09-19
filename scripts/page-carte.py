#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Engendre le corps de la page de cartographie.

Principe repris du plugin carto-territoire : la LISTE est la source de vérité,
la carte est une vue posée dessus. Le tableau est donc écrit ici, au moment de
la publication, et figure dans le HTML même si le navigateur n'exécute aucun
script. C'est ce qui rend la page utilisable sans souris, sans écran, sans
JavaScript et sur une connexion faible — et c'est aussi la condition à laquelle
l'exemption cartographique du référentiel d'accessibilité s'applique.

    python3 scripts/page-carte.py [dossier-des-morceaux]
"""
import html
import json
import os
import sys
from datetime import date

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SORTIE = sys.argv[1] if len(sys.argv) > 1 else "/home/ced/ddm-pages"

FAMILLES = [
    ("Terre et alimentation", ["agricult", "aliment", "producteur", "foret nourric", "amap", "ecologie"]),
    ("Réparer, réemployer", ["repar", "zero dechet", "objets", "recycler", "ressourcer"]),
    ("Habiter ensemble", ["habitat", "urbanisme", "oasis"]),
    ("Lien social et culture", ["rencontre", "lien social", "culture", "media"]),
    ("Solidarité et droits", ["solidarit", "citoyennete", "droits"]),
    ("Économie sociale", ["economie sociale", "magasin", "commerce"]),
]

# Okabe & Ito : la palette qualitative de référence en accessibilité. Chaque
# famille porte AUSSI une forme — la couleur seule ne suffit jamais, et une
# carte photocopiée en noir et blanc est un usage réel en milieu rural.
COULEURS = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9"]
FORMES = ["rond", "carre", "triangle", "losange", "croix", "pentagone"]


def sans_acc(t):
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", t or "")
                   if unicodedata.category(c) != "Mn").lower()

def familles(cats):
    c = " | ".join(sans_acc(x) for x in (cats or []))
    return [n for n, mots in FAMILLES if any(m in c for m in mots)]

def e(t):
    return html.escape(str(t if t is not None else ""), quote=True)

def cardinal(lat, lon, ici=(45.35137, 1.93221)):
    """« à 12 km au nord-est » se lit ; « 45.41, 2.05 » ne se lit pas."""
    import math
    dy, dx = lat - ici[0], (lon - ici[1]) * math.cos(math.radians(ici[0]))
    if abs(dy) < 1e-6 and abs(dx) < 1e-6:
        return "sur place"
    a = (math.degrees(math.atan2(dx, dy)) + 360) % 360
    pts = ["au nord", "au nord-est", "à l'est", "au sud-est", "au sud",
           "au sud-ouest", "à l'ouest", "au nord-ouest"]
    return pts[int((a + 22.5) % 360 // 45)]

def main():
    d = json.load(open(os.path.join(RACINE, "data/reseau-lieux.json"), encoding="utf-8"))
    z = json.load(open(os.path.join(RACINE, "data/zone-une-heure.json"), encoding="utf-8"))
    lieux = sorted(d["lieux"], key=lambda l: l["km"])
    for l in lieux:
        l["fam"] = familles(l.get("categories"))
    communes = len({l["commune"] for l in lieux})
    # Les 191 fiches ne sont pas 191 lieux, et tous ne sont pas des collectifs.
    # La grille d'intérêt général leur a été appliquée le 17/09/2026 ; les
    # comptes sont recalculés ici plutôt qu'écrits à la main, pour qu'une
    # reprise des données ne laisse pas une phrase fausse derrière elle.
    distincts = [l for l in lieux if not l.get("doublon_de")]
    verd = {}
    nat = {}
    for l in distincts:
        verd[l.get("verdict")] = verd.get(l.get("verdict"), 0) + 1
        nat[l.get("nature")] = nat.get(l.get("nature"), 0) + 1
    retenus = [l for l in distincts if l.get("verdict") == "retenu"]
    sur_reseau = sum(1 for l in retenus if l.get("base") == "reseau")
    loin = [l for l in lieux if l["km"] > 0.4]
    nf = lambda n: format(int(n), ",d").replace(",", " ")

    o = []
    a = o.append
    a('<main>')
    a('<p class="retour"><a href="reseau.html">← Le réseau</a></p>')
    a('<h1>La cartographie des lieux</h1>')

    # --- le condensé, écrit ici et non par le script : il doit être lisible
    #     même si rien ne s'exécute
    a('<div class="condense"><ul>')
    a('<li><strong>%d fiches</strong> d\'annuaire, soit <strong>au plus %d lieux '
      'distincts</strong> dans l\'heure, sur %d communes.</li>'
      % (len(lieux), len(distincts), communes))
    a('<li>Passés à la grille d\'intérêt général&nbsp;: <strong>%d retenus</strong>, '
      '%d laissés en doute, %d écartés. <strong>%d sont des acteurs marchands</strong> '
      'et non des collectifs.</li>'
      % (verd.get("retenu", 0), verd.get("douteux", 0), verd.get("hors", 0),
         nat.get("commerce", 0)))
    a('<li>Le plus proche est à %s km, le plus lointain à %s km.</li>'
      % (("%.1f" % loin[0]["km"]).replace(".", ","),
         ("%.1f" % lieux[-1]["km"]).replace(".", ",")))
    a('<li>La zone couvre %s communes et %s habitants, à %d km à la ronde.</li>'
      % (nf(z["total"]), nf(z["population"]), z["rayon_km"]))
    a('<li><strong>Aucune fiche n\'a été vérifiée sur place</strong> — la nôtre '
      'non plus, et elle date de 2019.</li>')
    a('</ul></div>')

    a('<p>Les communes dont le centre est à moins de %d&nbsp;km d\'ici, ce qui '
      'correspond à peu près à une heure de route sur ces routes-là. Chaque '
      'point est une fiche reprise d\'un annuaire public. <strong>Tous ne sont pas '
      'des collectifs</strong>&nbsp;: %d des %d lieux distincts sont des acteurs '
      'marchands — fermes en vente directe, épiceries, une enseigne nationale.</p>'
      % (z["rayon_km"], nat.get("commerce", 0), len(distincts)))

    # --- lien d'évitement : au clavier, on ne traverse pas 191 points
    a('<p><a href="#annuaire" class="carto-evitement">Passer la carte, aller à '
      'la liste des lieux</a></p>')

    a('<h2 id="carte-titre">La carte</h2>')
    a('<p id="carte-desc">%d points sur %d communes de Corrèze et des '
      'départements voisins. La molette fait défiler la page&nbsp;; '
      '<kbd>Ctrl</kbd> + molette zoome, ou deux doigts sur écran tactile. '
      'Échap rend la main. Chaque famille porte une couleur <em>et</em> une '
      'forme. <strong>La même information figure dans le tableau sous la '
      'carte</strong>, qui se filtre en même temps qu\'elle.</p>'
      % (len(lieux), communes))

    a('<div class="filtres" id="filtres"></div>')
    a('<div class="carto">')
    a('<div class="carto-zone" id="carte">'
      '<p class="chargement">La carte se charge. Le tableau ci-dessous donne '
      'la même information.</p></div>')
    a('<p class="nb" id="note-etiquettes">Zoomez pour faire apparaître les '
      'noms de communes.</p>')
    a('<div id="legende"></div>')
    a('<p class="nb" id="note-familles"></p>')
    a('<p class="nb" id="note-toponymes">Zoomez pour faire apparaître les '
      'villages et les hameaux.</p>')
    a('<div class="carto-fiche" id="fiche" role="region" '
      'aria-label="Fiche du lieu survolé"><p class="carto-fiche-vide">'
      'Survolez un point, ou choisissez une ligne dans la liste, pour lire sa '
      'fiche.</p></div>')
    a('</div>')

    # --- le bloc de métadonnées : non supprimable
    a('<dl class="carto-meta">')
    for terme, valeur in [
        ("Contours", "Admin Express (IGN), via geo.api.gouv.fr — Licence Ouverte 2.0"),
        ("Lieux", "Transiscope, agrégation d'une vingtaine de cartes — CC BY-SA"),
        ("Fond de carte", "Routes structurantes et noms de lieux repris "
                          "d'OpenStreetMap — ODbL — © les contributeurs "
                          "OpenStreetMap. Extraits à la publication et servis "
                          "par ce dépôt, dans leurs propres fichiers, "
                          "superposés au rendu seulement."),
        ("Données arrêtées au", "15 septembre 2026"),
        ("Carte produite le", date.today().strftime("%d/%m/%Y")),
        ("Maillage", "communes, code officiel géographique 2026"),
        ("Projection", "Web Mercator (EPSG:3857) — aucune surface n'est comparée ici"),
        ("Non représenté", "les lieux sans coordonnées publiées ; les fiches non "
                           "vérifiées sur place, soit la totalité ; les petites "
                           "routes, les noms de rue et le bâti ; les courriels "
                           "et téléphones, qui restent sur la fiche d'origine ; "
                           "les contours sont généralisés à environ 130 m, donc "
                           "indicatifs au-delà du zoom 10"),
        ("Requêtes sortantes", "aucune — bibliothèque et contours servis par ce dépôt"),
    ]:
        a('<dt>%s</dt><dd>%s</dd>' % (e(terme), valeur))
    a('</dl>')

    # --- l'annuaire, en dur
    a('<h2 id="annuaire">L\'annuaire</h2>')
    a('<div class="note">')
    a('<span class="etiquette">Ce que vaut cette liste, et ce qu\'elle ne vaut pas</span>')
    a('<p>Elle est reprise telle quelle d\'un agrégateur de cartes '
      'd\'alternatives. <strong>Aucune fiche n\'a été vérifiée sur place</strong>, '
      'certaines datent de plusieurs années, et un lieu peut avoir fermé, changé '
      'd\'objet ou ne plus vouloir y figurer.</p>')
    a('<p>Notre propre fiche en est l\'exemple&nbsp;: elle date du 3 janvier 2019 '
      'et décrit encore le lieu comme un élevage en vente directe. Nous la '
      'corrigeons — et c\'est exactement ce que nous proposons à chacun de faire '
      'pour la sienne.</p>')
    a('<p>Cette carte montre <strong>le milieu</strong>, pas le noyau d\'intérêt '
      'général. Les fiches ont été passées à la grille appliquée aux associations '
      'le 17 septembre 2026&nbsp;: <strong>%d lieux distincts sur %d sont retenus</strong>, '
      '%d restent douteux et sont publiés comme tels. Et <strong>%d des %d retenus '
      'le sont sur l\'attestation d\'un réseau tiers</strong>, pas sur ce qu\'ils '
      'déclarent eux-mêmes. La grille lit une déclaration d\'annuaire, souvent '
      'vieille de plusieurs années&nbsp;: elle repère, elle ne constate pas.</p>'
      % (verd.get("retenu", 0), len(distincts), verd.get("douteux", 0),
         sur_reseau, len(retenus)))
    a('<p><strong>Droit de réponse.</strong> Toute personne concernée par une '
      'fiche peut demander sa correction ou son retrait à '
      '<a href="mailto:contact@actitude.org">contact@actitude.org</a>. Le retrait '
      'est fait sans discussion et sans délai&nbsp;; la correction est datée dans '
      'le journal des versions, en bas de page.</p>')
    a('</div>')

    a('<p id="intro-annuaire">%d fiches, du plus proche au plus éloigné. '
      'Un même lieu peut y figurer plusieurs fois, sous des graphies '
      'différentes. Cliquer une ligne la montre sur la carte.</p>' % len(lieux))
    a('<div class="carto-liste" id="liste-bloc">')
    a('<table id="liste">')
    a('<caption class="sr-only">Fiches de lieux référencés à moins de %d km '
      'de Vitrac-sur-Montane</caption>' % z["rayon_km"])
    a('<thead><tr><th scope="col">Lieu</th><th scope="col">Commune</th>'
      '<th scope="col">Distance</th><th scope="col">Familles</th>'
      '<th scope="col">Ce qu\'il dit faire</th>'
      '<th scope="col">Fiche mise à jour</th></tr></thead><tbody>')
    for i, l in enumerate(lieux):
        km = ("%.1f" % l["km"]).replace(".", ",")
        ou = cardinal(l["lat"], l["lon"])
        prim = l["fam"][0] if l["fam"] else ""
        nom = e(l["nom"])
        if l.get("site"):
            nom = '<a href="%s" rel="noopener nofollow">%s</a>' % (e(l["site"]), nom)
        dit = e(l.get("decrit") or "")
        if l.get("heures"):
            dit += ('<br><span class="nb">Horaires déclarés : %s</span>'
                    % e(l["heures"]))
        if l.get("origine"):
            dit += ('<br><a class="nb" href="%s" rel="noopener nofollow">'
                    'Fiche d\'origine, avec les contacts</a>' % e(l["origine"]))
        a('<tr tabindex="0" data-i="%d" data-nom="%s" data-fam="%s" '
          'data-prim="%s" data-lat="%.5f" data-lon="%.5f" data-km="%s" '
          'data-ou="%s"%s%s%s%s>'
          '<td>%s</td><td>%s</td><td>%s km, %s</td><td>%s</td>'
          '<td class="carto-dit">%s</td><td>%s</td></tr>'
          % (i, e(l["nom"]), e("|".join(l["fam"])), e(prim), l["lat"], l["lon"],
             km, e(ou),
             (' data-site="%s"' % e(l["site"])) if l.get("site") else "",
             (' data-decrit="%s"' % e(l["decrit"])) if l.get("decrit") else "",
             (' data-heures="%s"' % e(l["heures"])) if l.get("heures") else "",
             (' data-origine="%s"' % e(l["origine"])) if l.get("origine") else "",
             nom, e(l["commune"]), km, e(ou),
             e(", ".join(l["fam"]) or "—"), dit or "—", e(l.get("maj") or "—")))
    a('</tbody></table></div>')
    a('<p class="nb"><a href="data/reseau-lieux.json">Télécharger les lieux '
      '(JSON)</a> · <a href="data/zone-communes.geojson">les contours '
      '(GeoJSON)</a> · <a href="data/carte.json">la fiche de la carte</a></p>')

    # --- méthode et versions
    a('<h2 id="la-methode">Méthode</h2>')
    a('<p><strong>La zone.</strong> Une heure de route est approchée par '
      '%d&nbsp;km à vol d\'oiseau. C\'est une simplification&nbsp;: sur ces '
      'routes de moyenne montagne, une heure porte plus loin vers Tulle que vers '
      'le plateau, et aucune approximation simple ne corrige cela. La liste des '
      'communes vient du découpage administratif officiel.</p>' % z["rayon_km"])
    a('<p><strong>Les lieux.</strong> Repris de <a href="https://transiscope.org/">'
      'Transiscope</a>, qui agrège une vingtaine de cartes — Près de chez nous, '
      'Colibris, Alternatiba, le réseau des ressourceries, Longue vie aux objets. '
      'Les catégories affichées sont celles des cartes d\'origine, pas les '
      'nôtres.</p>')
    a('<p><strong>La carte.</strong> Elle est dessinée par '
      '<a href="https://leafletjs.com/">Leaflet</a>, dont une copie est déposée '
      'dans le dépôt du site. Il n\'y a ni fond photographique ni tuiles&nbsp;: '
      'seulement les contours des %s communes de la zone, servis eux aussi par le '
      'dépôt. <strong>Rien ne part vers un tiers quand vous ouvrez cette '
      'page.</strong> Le prix est assumé&nbsp;: pas de routes, pas de relief, pas '
      'de noms de hameaux.</p>' % nf(z["total"]))
    a('<p><strong>Ce que la carte ne sait pas.</strong> Les contours publics sont '
      'généralisés&nbsp;: environ 130 mètres entre deux sommets. Ils sont donc '
      'fidèles jusqu\'au zoom 10 et seulement indicatifs au-delà. Le zoom est '
      'borné à 12 pour cette raison — les points, eux, restent à leur coordonnée '
      'exacte quel que soit le zoom. Nous avons mesuré ce que coûterait un tracé '
      'plus fin&nbsp;: trois fois le poids du fichier pour un gain invisible aux '
      'échelles réellement consultées.</p>')
    a('<p><strong>Accessibilité.</strong> Le tableau ci-dessus contient la même '
      'information que la carte et se filtre avec elle. Il est écrit dans la page '
      'et ne dépend d\'aucun script&nbsp;: sans JavaScript, la liste reste '
      'entière. Les points sont atteignables au clavier, la molette ne confisque '
      'pas le défilement, et les animations sont supprimées si le système le '
      'demande.</p>')
    a('<h2 id="les-versions">Journal des versions</h2>')
    a('<ul>')
    a('<li><strong>15 septembre 2026</strong> — première version. Reprise de %d '
      'fiches depuis Transiscope, carte statique de la zone. Aucune fiche vérifiée '
      'sur place.</li>' % len(lieux))
    a('<li><strong>16 septembre 2026</strong> — la carte devient navigable&nbsp;: '
      'zoom, déplacement, fiche au clic, contours communaux au trait fin. '
      'Toujours sans aucune tuile distante.</li>')
    a('<li><strong>%s</strong> — l\'annuaire est écrit dans la page et non plus '
      'par un script&nbsp;: il reste lisible sans JavaScript, au clavier et au '
      'lecteur d\'écran. La molette rend le défilement à la page. Le zoom est '
      'ramené à 12, la fidélité réelle des contours étant plus grossière que ce '
      'que le zoom 14 laissait croire.</li>' % "17 septembre 2026")
    a('<li><strong>19 septembre 2026</strong> — correction. La page annonçait '
      '«&nbsp;191 lieux portés par des collectifs&nbsp;». Il y a 191 fiches, au plus '
      '%d lieux distincts, et %d d\'entre eux sont des acteurs marchands. Les '
      'verdicts de la grille du 17 septembre sont désormais affichés.</li>'
      % (len(distincts), nat.get("commerce", 0)))
    a('</ul>')
    a('<p class="horodatage" id="horodatage"></p>')
    a('</main>')

    chemin = os.path.join(SORTIE, "corps-carte.html")
    open(chemin, "w", encoding="utf-8").write("\n".join(o) + "\n")
    print("  écrit :", chemin, os.path.getsize(chemin), "octets")
    print("  %d lieux dans le tableau, %d communes" % (len(lieux), communes))

if __name__ == "__main__":
    main()
