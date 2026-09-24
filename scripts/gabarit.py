#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Habille les fragments de contenu/pages/ et build/pages/ en pages complètes.

    python3 scripts/gabarit.py        ← appelé par scripts/construire.py

Une page du site est un fragment : un en-tête JSON, le corps, et ses scripts.
Ce fichier leur ajoute tout ce qui se répète — la tête, les métadonnées de
partage, le bandeau, le fil d'Ariane, le sommaire, le bloc « Relayer », le
pied — et engendre à côté ce qui se déduit des pages : le flux Atom, le plan
du site, la page 404, les extraits à partager, les éditions paginées et la
planche de visuels.

Avant le 24/09/2026, dix-neuf pages portaient chacune leur copie du bandeau.
Le contenu ne dit rien de sa mise en page : il déclare un gabarit, et c'est
la feuille de style qui décide.

Les gabarits
    accueil    la page d'entrée : un portail en mosaïque
    recit      texte long : sommaire à gauche, notes en marge à droite
    planche    tableau de bord : titres de section en rail, contenu large
    registre   tableaux et listes longues : pleine largeur
    portail    une page qui mène à d'autres : cartes en mosaïque
    fiche      une fiche du Grain : cartouche, sommaire, à emporter

Directives reconnues dans un fragment
    <!--#inclure chemin-->           insère un fichier du dépôt tel quel
    <!--#script chemin-->            insère un script du dépôt dans <script>
    <!--#module nom-->               insère contenu/modules/nom.html
    <!--#sans-js data/a.json …-->    le bloc « Sans JavaScript », daté depuis
                                     les fichiers eux-mêmes
"""
import datetime, html, json, os, re, sys
from html.parser import HTMLParser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import partage  # noqa: E402  les extraits à relayer, calculés sur data/

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENU = os.path.join(RACINE, "contenu")
BUILD = os.path.join(RACINE, "build")
SITE = "https://domainedumons.actitude.org/"
NOM = "Domaine du Mons"

# Le numéro de version des ressources, en un seul endroit. À incrémenter dès
# que style.css, site.js, tdb.js ou partage.js changent : sinon un visiteur
# déjà venu garde l'ancienne feuille et voit une page à moitié neuve.
VERSION = 29
VERSIONNES = ("style.css", "site.js", "tdb.js", "partage.js", "edition.css",
              "visuels.css", "vendor/carto-socle.js", "vendor/carto-socle.css",
              "vendor/leaflet.css", "vendor/leaflet.js",
              "vendor/paged.polyfill.min.js")

# Fichiers relevés chaque matin par .github/workflows/releve-quotidien.yml :
# leur date de calcul change tous les jours sans que la page soit refaite, on
# ne l'écrit donc pas en dur — c'est ce qui laissait sept pages afficher des
# dates périmées le 24/09.
QUOTIDIENS = {"data/annee.json", "data/humidite-sol.json", "data/humidite-sol.csv",
              "data/releve-quotidien.csv", "data/secheresse-historique.json"}

# ------------------------------------------------------------------ la carte
# (fichier, libellé) ; une chaîne seule est un intertitre de groupe.
NAV = [
    ("projet", "Le projet", "index.html", [
        ("index.html", "Le lieu"),
        ("liberer-la-terre.html", "Libérer la terre"),
        ("marcher-libre.html", "Marcher libre"),
    ]),
    ("ressources", "Ressources", "ressources.html", [
        "Le Grain",
        ("ressources.html#retex", "Retours d'expérience"),
        ("ressources.html#patterns", "Patterns"),
        ("ressources.html#gabarits", "Gabarits"),
        "À emporter",
        ("editions.html", "Éditions à imprimer"),
        ("relayer.html", "Relayer, partager"),
    ]),
    ("tdb", "Tableaux de bord", "tableaux-de-bord.html", [
        "La semaine",
        ("tdb-eau-meteo.html", "Le jour et la semaine"),
        ("tdb-annee.html", "L'année"),
        "La longue durée",
        ("tdb-climat.html", "Le climat, 1950-2025"),
        ("tdb-eau.html", "L'eau depuis 1957"),
        ("tdb-saisons.html", "Chauffage, verger, fenaison"),
        "Le lieu",
        ("tdb-terrain.html", "Le terrain, le gel, l'eau"),
        ("tdb-construire.html", "Construire ici"),
        "Le collectif",
        ("tdb-registre.html", "Registre d'intérêt général"),
        ("rapport-2025.html", "Rapport annuel 2025"),
    ]),
    ("reseau", "Le réseau", "reseau.html", [
        ("reseau-carte.html", "La cartographie des lieux"),
        ("reseau-fil.html", "Le fil commun"),
        ("reseau-associations.html", "Les associations d'intérêt général"),
    ]),
    ("contact", "Nous joindre", "nous-joindre.html", []),
]

GABARITS = {
    "index.html": "accueil",
    "liberer-la-terre.html": "recit", "marcher-libre.html": "recit",
    "nous-joindre.html": "recit", "reseau-fil.html": "recit",
    "mentions.html": "recit",
    "tableaux-de-bord.html": "portail", "reseau.html": "portail",
    "ressources.html": "portail", "editions.html": "portail",
    "relayer.html": "registre",
    "reseau-associations.html": "registre", "reseau-carte.html": "registre",
    "rapport-2025.html": "registre",
}


def gabarit_de(page, meta):
    if meta.get("gabarit"):
        return meta["gabarit"]
    if page in GABARITS:
        return GABARITS[page]
    if page.startswith("tdb-"):
        return "planche"
    if page.startswith("grain-"):
        return "fiche"
    return "recit"


def rubrique_de(page):
    for cle, _, tete, entrees in NAV:
        if page == tete:
            return cle
        for e in entrees:
            if isinstance(e, tuple) and e[0].split("#")[0] == page:
                return cle
    if page.startswith("grain-"):
        return "ressources"
    return None


# ------------------------------------------------------------- les fragments

def lire_fragment(chemin):
    t = open(chemin, encoding="utf-8").read()
    m = re.match(r"<!--meta\s*(\{.*?\})\s*-->\s*", t, re.S)
    if not m:
        raise SystemExit("fragment sans en-tête : %s" % chemin)
    meta = json.loads(m.group(1))
    reste = t[m.end():]
    corps, _, scripts = reste.partition("<!--scripts-->")
    return meta, corps, scripts


def date_de(fichier):
    """La date de calcul d'un fichier de données, lue dans le fichier."""
    chemin = os.path.join(RACINE, fichier)
    if fichier in QUOTIDIENS:
        return "mis à jour chaque matin"
    if fichier.endswith(".json"):
        try:
            d = json.load(open(chemin, encoding="utf-8"))
        except Exception:
            return None
        if isinstance(d, dict):
            for k in ("calcule_le", "mis_a_jour", "date_carte", "date_donnees"):
                if isinstance(d.get(k), str):
                    return "relevé du " + d[k]
    return None


def bloc_sans_js(fichiers, planche):
    lignes = []
    for f in fichiers:
        if not os.path.exists(os.path.join(RACINE, f)):
            raise SystemExit("sans-js : %s absent du dépôt" % f)
        d = date_de(f)
        lignes.append('    <li><a href="%s">%s</a>%s</li>' % (f, f, " — " + d if d else ""))
    fin = ("Publiées en Licence Ouverte 2.0. Les sources et la méthode sont décrites plus bas, "
           "dans du texte qui ne dépend d'aucun script." if planche else
           "Publiées en Licence Ouverte 2.0.")
    return ('<noscript>\n  <div class="note">\n  <span class="etiquette">Sans JavaScript</span>\n'
            '  <p>Les chiffres de cette page sont calculés dans votre navigateur à partir de '
            'fichiers ouverts. Sans JavaScript ils ne s\'affichent pas, mais <strong>les données '
            'restent lisibles et téléchargeables</strong>&nbsp;:</p>\n  <ul>\n%s\n  </ul>\n'
            '  <p>%s</p>\n  </div>\n</noscript>' % ("\n".join(lignes), fin))


def directives(t, planche=False):
    def inclure(m):
        return open(os.path.join(RACINE, m.group(1)), encoding="utf-8").read()

    def script(m):
        return "<script>\n" + open(os.path.join(RACINE, m.group(1)), encoding="utf-8").read() + "</script>"

    def module(m):
        return open(os.path.join(CONTENU, "modules", m.group(1) + ".html"), encoding="utf-8").read().strip()

    t = re.sub(r"<!--#inclure (\S+)-->", inclure, t)
    t = re.sub(r"<!--#script (\S+)-->", script, t)
    t = re.sub(r"<!--#module (\S+)-->", module, t)
    t = re.sub(r"<!--#sans-js ([^>]+?)-->", lambda m: bloc_sans_js(m.group(1).split(), planche), t)
    t = re.sub(r"<!--#nouvelles (\d+)-->", lambda m: bloc_nouvelles(int(m.group(1))), t)
    return t


NOUVELLES = []


def bloc_nouvelles(n):
    li = []
    groupes = []
    for d, page, titre, texte in NOUVELLES:
        if page.startswith("grain-") and groupes and groupes[-1][1] == "grain" and groupes[-1][0] == d:
            groupes[-1][2] += 1
            continue
        if page.startswith("grain-"):
            groupes.append([d, "grain", 1, page, titre, texte])
        else:
            groupes.append([d, "page", 1, page, titre, texte])
    for d, sorte, nb, page, titre, texte in groupes[:n]:
        if sorte == "grain" and nb > 1:
            page, titre, texte = "ressources.html", "Ressources", "%d fiches du Grain mises en ligne." % nb
        court = texte if len(texte) < 180 else texte[:texte.rfind(" ", 0, 170)] + "…"
        court = re.sub(r"^\d{1,2}(?:er)? \w+ \d{4}\s*—\s*", "", court)
        li.append('  <li><time datetime="%s">%s</time> <a href="%s">%s</a><span>%s</span></li>'
                  % (d.isoformat(), date_courte(d), page, e(titre), e(court)))
    return '<ol class="nouvelles">\n%s\n</ol>' % "\n".join(li)


def date_courte(d):
    mois = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]
    return "%d %s" % (d.day, mois[d.month - 1])


# ------------------------------------------------ sections et sommaire

VIDES = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
         "source", "track", "wbr", "path", "circle", "rect", "line", "polyline",
         "polygon", "ellipse", "use", "stop"}


class Niveaux(HTMLParser):
    """Repère les <h2> de premier niveau : ceux qui ouvrent une section."""

    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.pile = 0
        self.h2 = []

    def handle_starttag(self, tag, attrs):
        if tag == "h2" and self.pile == 0:
            self.h2.append(self.getpos())
        if tag not in VIDES:
            self.pile += 1

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        if tag not in VIDES:
            self.pile = max(0, self.pile - 1)


def decoupe(corps):
    """Coupe le corps avant chaque <h2> de premier niveau."""
    p = Niveaux()
    p.feed(corps)
    lignes = corps.split("\n")
    debuts = [0]
    acc = 0
    offs = []
    for l in lignes:
        offs.append(acc)
        acc += len(l) + 1
    for ligne, col in p.h2:
        debuts.append(offs[ligne - 1] + col)
    debuts.append(len(corps))
    return [corps[a:b] for a, b in zip(debuts, debuts[1:])]


def ancre(texte, pris):
    base = re.sub(r"<[^>]+>|&[a-z]+;", " ", texte).lower()
    for a, b in (("àâä", "a"), ("éèêë", "e"), ("îï", "i"), ("ôö", "o"), ("ùûü", "u"), ("ç", "c"), ("œ", "oe")):
        for c in a:
            base = base.replace(c, b)
    base = re.sub(r"[^a-z0-9]+", "-", base).strip("-")[:40] or "section"
    a, n = base, 2
    while a in pris:
        a, n = "%s-%d" % (base, n), n + 1
    pris.add(a)
    return a


def sectionner(corps):
    """Enveloppe chaque h2 et sa suite dans une <section>, et rend le sommaire."""
    pris = set(re.findall(r'\sid="([^"]+)"', corps))
    morceaux = decoupe(corps)
    tete, suite = morceaux[0], morceaux[1:]
    sommaire, sortie = [], []
    for m in suite:
        h = re.match(r"\s*<h2([^>]*)>(.*?)</h2>", m, re.S)
        if not h:
            sortie.append(m)
            continue
        attrs, titre = h.group(1), h.group(2)
        i = re.search(r'id="([^"]+)"', attrs)
        if i:
            ident = i.group(1)
        else:
            ident = ancre(titre, pris)
            m = m.replace("<h2%s>" % attrs, '<h2 id="%s"%s>' % (ident, attrs), 1)
        court = html.unescape(re.sub(r"<[^>]+>", "", titre)).strip()
        sommaire.append((ident, court))
        if court.lower().startswith(("journal des versions", "méthode")):
            cls = "sec sec-annexe"
        else:
            cls = "sec"
        sortie.append('<section class="%s" aria-labelledby="%s">\n%s\n</section>\n'
                      % (cls, ident, m.strip()))
    return tete, "".join(sortie), sommaire


# ------------------------------------------------------------------- l'habit

def e(s):
    """Échappe pour le texte et les attributs entre guillemets doubles.
    L'apostrophe reste une apostrophe : &#x27; dans un titre est illisible
    dans le code source et ne protège rien entre guillemets doubles."""
    return html.escape(s, quote=False).replace('"', "&quot;")


def texte_seul(s):
    s = re.sub(r"<[^>]+>", "", s)
    return html.unescape(s).strip()


def tete(page, meta, gabarit):
    titre = meta["titre"]
    t_complet = NOM + " — collectif expérimental" if page == "index.html" else "%s — %s" % (titre, NOM)
    desc = meta["description"]
    url = SITE + ("" if page == "index.html" else page)
    image = SITE + "visuels/og/%s.png" % page[:-5]
    liens = ""
    if meta.get("leaflet"):
        liens += ('<link rel="stylesheet" href="vendor/leaflet.css">\n'
                  '<link rel="stylesheet" href="vendor/carto-socle.css">\n')
    return """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{t}</title>
<meta name="description" content="{d}">
<link rel="canonical" href="{u}">
<meta property="og:type" content="{ogt}">
<meta property="og:site_name" content="Domaine du Mons">
<meta property="og:locale" content="fr_FR">
<meta property="og:title" content="{ti}">
<meta property="og:description" content="{d}">
<meta property="og:url" content="{u}">
<meta property="og:image" content="{img}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{alt}">
<meta name="twitter:card" content="summary_large_image">
<link rel="alternate" type="application/atom+xml" title="Domaine du Mons — nouvelles" href="flux.xml">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
{liens}<link rel="stylesheet" href="style.css">
</head>
<body data-gabarit="{g}">
<a class="evitement" href="#contenu">Aller au contenu</a>
""".format(t=e(t_complet), d=e(desc), u=e(url), ti=e(titre), img=e(image),
           alt=e("%s — %s" % (titre, NOM)), g=gabarit, liens=liens,
           ogt="article" if page.startswith("grain-") else "website")


def navigation(page):
    rub = rubrique_de(page)
    items = []
    for cle, libelle, cible, entrees in NAV:
        courant = ' aria-current="page"' if page == cible else ""
        marque = ' class="rubrique-courante"' if rub == cle else ""
        if not entrees:
            items.append('        <li%s><a href="%s"%s>%s</a></li>' % (marque, cible, courant, libelle))
            continue
        sous = []
        for x in entrees:
            if isinstance(x, str):
                sous.append('            <li class="groupe">%s</li>' % x)
            else:
                c = ' aria-current="page"' if x[0] == page else ""
                sous.append('            <li><a href="%s"%s>%s</a></li>' % (x[0], c, x[1]))
        if cible not in [x[0] for x in entrees if isinstance(x, tuple)]:
            sous.append("            <li><hr></li>")
            sous.append('            <li><a href="%s"%s>Vue d\'ensemble</a></li>' % (cible, courant))
        items.append("""        <li%s>
          <span class="menu-deroulant"><a href="%s"%s>%s</a><button type="button" class="chevron" aria-expanded="false" aria-controls="m-%s" aria-label="Ouvrir le menu %s">⌄</button></span>
          <ul class="sous-menu" id="m-%s" hidden>
%s
          </ul>
        </li>""" % (marque, cible, courant if page == cible else "", libelle, cle,
                    "« %s »" % libelle, cle, "\n".join(sous)))
    return """<div class="bandeau">
  <div class="bandeau-contenu">
    <p class="titre"><a href="index.html">Domaine du Mons</a></p>
    <p class="sous-titre">Vitrac-sur-Montane, Corrèze</p>
    <nav aria-label="Navigation principale">
      <ul>
%s
      </ul>
    </nav>
  </div>
</div>
""" % "\n".join(items)


def ariane(page, meta):
    if page == "index.html":
        return ""
    rub = rubrique_de(page)
    pas = ['<a href="index.html">Accueil</a>']
    for cle, libelle, cible, _ in NAV:
        if cle == rub and cible != page and cle != "projet":
            pas.append('<a href="%s">%s</a>' % (cible, libelle))
    if page.startswith("grain-"):
        pas.append('<a href="ressources.html#%s">%s</a>' % tuple(meta.get("famille_ancre", ("retex", "Retours d'expérience"))))
    pas.append('<span aria-current="page">%s</span>' % e(meta["titre"]))
    return '<nav class="ariane" aria-label="Fil d\'Ariane"><ol>%s</ol></nav>\n' % "".join(
        "<li>%s</li>" % p for p in pas)


def bloc_sommaire(sommaire):
    if len(sommaire) < 3:
        return ""
    li = "\n".join('    <li><a href="#%s">%s</a></li>' % (i, e(t)) for i, t in sommaire)
    return ('<nav class="sommaire" aria-labelledby="sommaire-t">\n  <p class="sommaire-titre" id="sommaire-t">Sur cette page</p>\n'
            '  <ol>\n%s\n  </ol>\n</nav>\n' % li)


def bloc_relayer(page, meta):
    """Des liens simples : aucune requête vers ces services tant qu'on ne clique pas."""
    from urllib.parse import quote
    url = SITE + ("" if page == "index.html" else page)
    titre = meta["titre"] + " — " + NOM
    u, t = quote(url, safe=""), quote(titre, safe="")
    extraits = partage.extraits_de(page)
    lien_extraits = ('<li><a href="relayer.html#x-%s">%d extrait%s prêt%s à publier</a></li>'
                     % (extraits[0]["id"], len(extraits), "s" if len(extraits) > 1 else "",
                        "s" if len(extraits) > 1 else "")) if extraits else ""
    return """<aside class="relayer" aria-labelledby="relayer-t" data-url="{url}" data-titre="{ti}">
  <h2 id="relayer-t">Relayer cette page</h2>
  <ul class="relais">
    <li><a href="https://t.me/share/url?url={u}&amp;text={t}" rel="noopener">Telegram</a></li>
    <li><a href="relayer.html#mastodon" class="relais-mastodon">Mastodon</a></li>
    <li><a href="https://www.facebook.com/sharer/sharer.php?u={u}" rel="noopener">Facebook</a></li>
    <li><a href="mailto:?subject={t}&amp;body={u}">Courriel</a></li>
    <li><a href="visuels/og/{slug}.png">Visuel</a></li>
    {extraits}
  </ul>
  <p class="relais-note">Des liens ordinaires&nbsp;: ces services ne reçoivent rien tant que vous ne cliquez pas.</p>
</aside>
""".format(url=e(url), ti=e(titre), u=u, t=t, slug=page[:-5], extraits=lien_extraits)


def pied():
    return """<footer>
  <div>
    <p>Collectif du Domaine du Mons — Vitrac-sur-Montane (19). <a href="mailto:contact@actitude.org">contact@actitude.org</a></p>
    <ul>
      <li><a href="index.html">Le lieu</a></li>
      <li><a href="liberer-la-terre.html">Libérer la terre</a></li>
      <li><a href="marcher-libre.html">Marcher libre</a></li>
      <li><a href="ressources.html">Ressources</a></li>
      <li><a href="tableaux-de-bord.html">Tableaux de bord</a></li>
      <li><a href="reseau.html">Le réseau</a></li>
      <li><a href="nous-joindre.html">Nous joindre</a></li>
    </ul>
    <ul class="pied-second">
      <li><a href="editions.html">Éditions à imprimer</a></li>
      <li><a href="relayer.html">Relayer</a></li>
      <li><a href="flux.xml">Flux des nouvelles</a></li>
      <li><a href="mentions.html">Mentions et licences</a></li>
    </ul>
  </div>
</footer>
"""


def versionner(t, prefixe=""):
    motif = re.compile(r'((?:src|href)=")(%s)(?:\?v=\d+)?(")' % "|".join(re.escape(prefixe + r) for r in VERSIONNES))
    return motif.sub(lambda m: "%s%s?v=%d%s" % (m.group(1), m.group(2), VERSION, m.group(3)), t)


def assembler(page, meta, corps, scripts):
    gab = gabarit_de(page, meta)
    corps = directives(corps, planche=(gab == "planche"))
    entete, sections, sommaire = sectionner(corps)
    classe = ' class="%s"' % meta["classe"] if meta.get("classe") else ""
    rail = bloc_sommaire(sommaire) if gab in ("recit", "planche", "registre", "fiche") else ""
    rail += meta.get("rail", "")
    if rail:
        rail = '<div class="rail">\n%s</div>\n' % rail
    html_page = (tete(page, meta, gab) + navigation(page)
                 + '\n<main id="contenu"%s>\n' % classe
                 + ariane(page, meta)
                 + '<header class="tete-page">\n%s\n</header>\n' % entete.strip()
                 + rail
                 + '<div class="corps-page">\n%s</div>\n' % sections
                 + bloc_relayer(page, meta)
                 + "</main>\n\n" + pied() + "\n")
    if meta.get("leaflet"):
        html_page += '<script src="vendor/leaflet.js"></script>\n<script src="vendor/carto-socle.js"></script>\n'
    html_page += directives(scripts).strip() + "\n" if scripts.strip() else ""
    html_page += '<script src="site.js"></script>\n<script src="partage.js"></script>\n</body>\n</html>\n'
    return versionner(html_page)


# --------------------------------------------------------------- les pages

def fragments():
    """Tous les fragments : écrits à la main, puis engendrés (build/pages)."""
    vus = {}
    for dossier in (os.path.join(CONTENU, "pages"), os.path.join(BUILD, "pages")):
        if not os.path.isdir(dossier):
            continue
        for f in sorted(os.listdir(dossier)):
            if f.endswith(".html"):
                vus[f] = os.path.join(dossier, f)
    return vus


def main():
    pages = fragments()
    tous = [(p, lire_fragment(c)[0]) for p, c in pages.items()]
    NOUVELLES[:] = nouvelles(tous)
    faites = []
    for page, chemin in pages.items():
        meta, corps, scripts = lire_fragment(chemin)
        sortie = assembler(page, meta, corps, scripts)
        open(os.path.join(RACINE, page), "w", encoding="utf-8").write(sortie)
        faites.append((page, meta))
        print("  écrit : %-34s %7d octets  [%s]" % (page, len(sortie.encode()), gabarit_de(page, meta)))
    flux(faites)
    plan(faites)
    print("  flux.xml, sitemap.xml : %d pages" % len(faites))


# ------------------------------------------------------ flux et plan du site

def nouvelles(faites):
    """Les entrées datées : journaux des versions des pages, dates des fiches."""
    items = []
    for page, meta in faites:
        chemin = fragments()[page]
        t = directives(open(chemin, encoding="utf-8").read())
        j = re.search(r"Journal des versions</h2>(.*?)(?:</section>|<h2|$)", t, re.S)
        if j:
            for li in re.findall(r"<li>(.*?)</li>", j.group(1), re.S):
                d = re.match(r"\s*(?:<[^>]+>)*\s*(\d{1,2})(?:er)?\s+(\w+)\s+(\d{4})", texte_seul(li))
                if d:
                    try:
                        date = datetime.date(int(d.group(3)), MOIS[d.group(2).lower()], int(d.group(1)))
                    except (KeyError, ValueError):
                        continue
                    items.append((date, page, meta["titre"], texte_seul(li)))
        if meta.get("publie"):
            y, m, dd = [int(x) for x in meta["publie"].split("-")]
            items.append((datetime.date(y, m, dd), page, meta["titre"],
                          "Fiche du Grain mise en ligne. " + meta["description"]))
    items.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return items


MOIS = {"janvier": 1, "février": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6, "juillet": 7,
        "août": 8, "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12}


def flux(faites):
    items = nouvelles(faites)[:40]
    maj = items[0][0].isoformat() if items else datetime.date.today().isoformat()
    entrees = []
    for i, (d, page, titre, texte) in enumerate(items):
        entrees.append("""  <entry>
    <title>{t}</title>
    <link href="{u}"/>
    <id>{u}#{d}-{i}</id>
    <updated>{d}T12:00:00Z</updated>
    <summary>{s}</summary>
  </entry>""".format(t=e(titre), u=e(SITE + page), d=d.isoformat(), i=i, s=e(texte)))
    xml = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="fr">
  <title>Domaine du Mons — nouvelles</title>
  <subtitle>Les pages et les fiches du site, à chaque version datée.</subtitle>
  <link href="{s}flux.xml" rel="self"/>
  <link href="{s}"/>
  <id>{s}</id>
  <updated>{m}T12:00:00Z</updated>
  <author><name>Collectif du Domaine du Mons</name><email>contact@actitude.org</email></author>
{e}
</feed>
""".format(s=SITE, m=maj, e="\n".join(entrees))
    open(os.path.join(RACINE, "flux.xml"), "w", encoding="utf-8").write(xml)


def plan(faites):
    urls = "\n".join("  <url><loc>%s</loc></url>" % e(SITE + ("" if p == "index.html" else p))
                     for p, _ in sorted(faites) if p != "404.html")
    open(os.path.join(RACINE, "sitemap.xml"), "w", encoding="utf-8").write(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n%s\n</urlset>\n' % urls)


if __name__ == "__main__":
    sys.exit(main())
