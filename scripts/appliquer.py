#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pose les quatre pages du réseau depuis les morceaux du dépôt.

Ce fichier a vécu trois jours hors du dépôt, dans ~/ddm-pages. C'est ce qui a
permis à une vieille passe d'écraser data/associations.json le 16 septembre
sans que rien n'en garde trace : le script qui produisait la bonne version et
celui qui l'écrasait n'étaient versionnés ni l'un ni l'autre. Rapatrié le
19/09/2026. Ce qui ne vit pas dans le dépôt se perd à la première reprise.

    python3 scripts/construire.py        ← l'entrée normale
    python3 scripts/appliquer.py         ← cette étape seule

Les morceaux rédigés à la main vivent dans scripts/pages/ ; le corps de la
page de cartographie est engendré par scripts/page-carte.py dans build/.
"""
import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = os.path.join(RACINE, "scripts", "pages")
BUILD = os.path.join(RACINE, "build")

# Le numéro de version des ressources, en un seul endroit. À incrémenter dès
# que style.css, site.js ou tdb.js changent : sinon un visiteur déjà venu garde
# l'ancienne feuille et voit une page à moitié neuve.
VERSION = 28

VERSIONNES = ("style.css", "site.js", "tdb.js",
              "vendor/carto-socle.js", "vendor/carto-socle.css",
              "vendor/leaflet.css", "vendor/leaflet.js")


def lire(nom):
    """Un morceau, pris dans build/ s'il y est engendré, sinon dans pages/."""
    for dossier in (BUILD, PAGES):
        chemin = os.path.join(dossier, nom)
        if os.path.exists(chemin):
            return open(chemin, encoding="utf-8").read()
    raise SystemExit("morceau introuvable : %s (ni dans build/ ni dans scripts/pages/)" % nom)


def page(fichier, titre, description, corps, script, leaflet=False):
    src = open(os.path.join(RACINE, "reseau.html"), encoding="utf-8").read()
    tete = src[:src.index("<main")]
    pied = src[src.index("</main>") + len("</main>"):]
    pied = pied[:pied.index("<script")]
    t = tete
    t = re.sub(r"<title>.*?</title>", "<title>%s — Domaine du Mons</title>" % titre,
               t, count=1, flags=re.S)
    t = re.sub(r'<meta name="description" content=".*?">',
               '<meta name="description" content="%s">' % description, t, count=1, flags=re.S)
    if leaflet:
        t = t.replace('<link rel="stylesheet" href="style.css',
                      '<link rel="stylesheet" href="vendor/leaflet.css?v=%d">\n'
                      '<link rel="stylesheet" href="vendor/carto-socle.css?v=%d">\n'
                      '<link rel="stylesheet" href="style.css' % (VERSION, VERSION), 1)
    t = t.replace(' aria-current="page"', "")
    t = t.replace('<a href="%s">' % fichier, '<a href="%s" aria-current="page">' % fichier, 1)
    html = t + lire(corps) + "\n" + pied
    if leaflet:
        html += ('<script src="vendor/leaflet.js?v=%d"></script>\n'
                 '<script src="vendor/carto-socle.js?v=%d"></script>\n' % (VERSION, VERSION))
    # Une page sans données n'embarque ni tdb.js ni script propre. reseau-fil
    # portait une copie du script du réseau, qui cherchait #condense, #synthese
    # et #horodatage — trois identifiants absents de cette page. Le script
    # levait avant d'avoir rien écrit, et le condensé rédigé à la main ne
    # survivait que par accident.
    if script:
        html += ('<script src="tdb.js?v=%d"></script>\n<script>\n' % VERSION) + lire(script) + '</script>\n'
    html += '<script src="site.js?v=%d"></script>\n</body>\n</html>\n' % VERSION
    chemin = os.path.join(RACINE, fichier)
    open(chemin, "w", encoding="utf-8").write(html)
    print("  écrit : %-26s %7d octets" % (fichier, os.path.getsize(chemin)))


def main():
    page("reseau.html", "Le réseau",
         "Les lieux référencés et les associations d'intérêt général à une heure de "
         "Vitrac-sur-Montane, et une lettre commune à ouvrir.",
         "corps-reseau.html", "js-reseau.js")
    page("reseau-carte.html", "La cartographie des lieux",
         "Carte navigable des lieux référencés à moins de 45 km de Vitrac-sur-Montane, "
         "passés à la grille d'intérêt général. Aucune tuile distante, aucun traceur.",
         "corps-carte.html", "js-carte.js", leaflet=True)
    page("reseau-fil.html", "Le fil commun",
         "Une lettre mensuelle commune aux lieux collectifs de la zone : trois règles, "
         "aucun traceur, et un démarrage à trois participants.",
         "corps-fil.html", None)
    page("reseau-associations.html", "Les associations d'intérêt général",
         "Les associations actives à une heure de Vitrac-sur-Montane, et le tri de celles "
         "dont l'objet déclaré les engage envers des non-membres.",
         "corps-assos.html", "js-assos.js")

    # L'étape « ajouts CSS » est retirée le 19/09/2026. Elle recollait
    # scripts/pages/css-ajouts.css en fin de feuille dès que « .carte-leaflet »
    # n'y figurait plus — c'est-à-dire qu'elle aurait ressuscité, à la première
    # reconstruction, les 55 lignes de l'ancienne carte qu'on vient de retirer.
    # Les règles encore vivantes de ce fichier sont désormais dans style.css.

    # La version de TOUTES les ressources versionnées, sur toutes les pages.
    # La règle précédente en oubliait deux : elle ne couvrait ni leaflet.css
    # ni leaflet.js, et un visiteur gardait l'ancienne bibliothèque.
    motif = re.compile(r"(%s)\?v=\d+" % "|".join(re.escape(r) for r in VERSIONNES))
    sans_version = re.compile(r'((?:src|href)=")(%s)(")'
                              % "|".join(re.escape(r) for r in VERSIONNES))
    n = 0
    for f in sorted(os.listdir(RACINE)):
        if not f.endswith(".html"):
            continue
        p = os.path.join(RACINE, f)
        t = open(p, encoding="utf-8").read()
        t2 = motif.sub(lambda m: "%s?v=%d" % (m.group(1), VERSION), t)
        t2 = sans_version.sub(lambda m: "%s%s?v=%d%s" % (m.group(1), m.group(2), VERSION, m.group(3)), t2)
        if t2 != t:
            open(p, "w", encoding="utf-8").write(t2)
            n += 1
    print("  version des ressources portée à %d sur %d pages" % (VERSION, n))


if __name__ == "__main__":
    sys.exit(main())
