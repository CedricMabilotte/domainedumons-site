#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Les éditions paginées et les visuels, composés avec Paged.js.

    python3 scripts/editions.py            écrit editions/*.html, visuels/planche.html
                                           et le fragment build/pages/editions.html
                                           (appelé par construire.py : aucun réseau,
                                           aucune dépendance)
    python3 scripts/editions.py --rendre   imprime les éditions en PDF
                                           (editions/pdf/) et découpe la planche
                                           en PNG (visuels/<format>/) — demande
                                           Chromium et le module playwright

Paged.js tourne dans le navigateur : les pages editions/*.html se lisent déjà
paginées à l'écran, et « Imprimer » en fait un PDF. --rendre ne fait que le
même geste sans intervention, pour que les PDF et les images publiés soient
ceux que le dépôt décrit.

Les contenus viennent des fragments du site — rien n'est réécrit pour
l'impression. Ce qui change avec le support :
  - les adresses des liens externes descendent en note de bas de page ;
  - les encadrés « Contre-indications » et « Vérification » gardent leur bloc ;
  - les éléments qui n'ont de sens qu'à l'écran (portes, nouvelles, scripts,
    blocs « Sans JavaScript ») sont retirés.
"""
import html, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gabarit as G  # noqa: E402
import partage as P  # noqa: E402

RACINE = G.RACINE
ED = os.path.join(RACINE, "editions")
VIS = os.path.join(RACINE, "visuels")
DATE = "septembre 2026"


def fragment(page):
    chemin = G.fragments()[page]
    meta, corps, _ = G.lire_fragment(chemin)
    corps = G.directives(corps)
    return meta, corps


def pour_papier(corps):
    """Ce qui ne s'imprime pas sort ; les liens externes passent en note."""
    corps = re.sub(r"<noscript>.*?</noscript>", "", corps, flags=re.S)
    corps = re.sub(r'<ul class="portes">.*?</ul>', "", corps, flags=re.S)
    corps = re.sub(r'<ol class="nouvelles">.*?</ol>', "", corps, flags=re.S)
    corps = re.sub(r"<script\b.*?</script>", "", corps, flags=re.S)
    corps = re.sub(r'<p class="horodatage"[^>]*></p>', "", corps)

    def lien(m):
        url, texte = m.group(1), m.group(2)
        if re.sub(r"<[^>]+>", "", texte).strip() in (url, url.replace("https://", "")):
            return texte
        return '%s<span class="note-lien">%s</span>' % (texte, html.escape(html.unescape(url)).replace("/", "/​"))
    corps = re.sub(r'<a href="(https?://[^"]+)"[^>]*>(.*?)</a>', lien, corps, flags=re.S)
    # liens internes : le papier ne mène nulle part, on garde le texte
    corps = re.sub(r'<a href="(?!#)[^"]*"[^>]*>(.*?)</a>', r"\1", corps, flags=re.S)
    return corps


def blocs_fiche(corps):
    """Contre-indications et Vérification : un bloc qu'on ne coupe pas."""
    for classe, bloc in (("h-contreindications", "bloc-contre"), ("h-verification", "bloc-verif")):
        corps = re.sub(r'(<h2 class="%s">.*?)(?=<h2|\Z)' % classe,
                       lambda m: '<div class="%s">%s</div>' % (bloc, m.group(1)), corps, flags=re.S)
    return corps


FORMATS_PAGE = {
    "a5": "",
    "a4": "@page { size: A4; margin: 20mm 20mm 22mm 22mm; } @page :left { margin: 20mm 22mm 22mm 20mm; }",
    "paysage": ("@page { size: A4 landscape; margin: 12mm 14mm 14mm; "
                "@top-right { content: 'Le faisceau de droits — gabarit GA-01'; } "
                "@bottom-right { content: 'domainedumons.actitude.org · CC BY-SA 4.0'; } } "
                "@page :left { margin: 12mm 14mm 14mm; @top-left { content: none; } "
                "@bottom-left { content: counter(page); } @bottom-right { content: 'domainedumons.actitude.org · CC BY-SA 4.0'; } }"),
}


def page_html(titre, corps, classe="a5", apres_js=""):
    return """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{t} — édition paginée — Domaine du Mons</title>
<meta name="robots" content="noindex">
<link rel="stylesheet" href="../edition.css">
{style}<script>
window.PagedConfig = {{
  auto: true,
  after: function () {{
    var b = document.createElement("div");
    b.className = "barre-edition";
    b.innerHTML = '<a href="../editions.html">← Éditions</a> <span>{te}</span> ' +
      '<button type="button" onclick="window.print()">Imprimer ou enregistrer en PDF</button>';
    document.body.appendChild(b);
    document.body.setAttribute("data-pret", String(document.querySelectorAll(".pagedjs_page").length));
  }}
}};
</script>
<script src="../vendor/paged.polyfill.min.js"></script>
</head>
<body class="{c}">
{corps}
</body>
</html>
""".format(t=G.e(titre), te=G.e(titre).replace("'", "\\'"), c=classe, corps=corps,
           style=("<style>%s</style>\n" % FORMATS_PAGE[classe]) if FORMATS_PAGE.get(classe) else "")


def couverture(sur, titre, chapeau, croquis=None, lignes=()):
    svg = ""
    if croquis:
        svg = open(os.path.join(RACINE, croquis), encoding="utf-8").read()
    pied = "".join("<p>%s</p>" % l for l in lignes)
    return """<section class="couverture">
  <p class="sur-titre">{s}</p>
  <h1>{t}</h1>
  <p class="chapeau">{c}</p>
  {svg}
  <div class="pied"><p><strong>Domaine du Mons</strong> — collectif expérimental, Vitrac-sur-Montane (Corrèze)</p>{p}<p>domainedumons.actitude.org</p></div>
</section>""".format(s=sur, t=titre, c=chapeau, svg=svg, p=pied)


def verso(texte):
    return '<section class="verso">%s</section>' % texte


# --------------------------------------------------------------- éditions

def fiche_chapitre(page):
    meta, corps = fragment(page)
    corps = pour_papier(corps)
    corps = blocs_fiche(corps)
    m = re.match(r"\s*<h1>(?:<span class=\"code\">(.*?)</span>\s*)?(.*?)</h1>", corps, re.S)
    code, titre = (m.group(1) or ""), m.group(2)
    reste = corps[m.end():]
    ident = page[:-5]
    return ident, code, titre, """<article class="chapitre" id="{i}">
<h1>{cd}<span class="titre-courant">{t}</span></h1>
{r}
<p class="colophon">Collectif du Domaine du Mons — {cc}{t2}. Fiche du Grain, CC BY-SA 4.0. Version en ligne&nbsp;: domainedumons.actitude.org/{p}</p>
</article>""".format(i=ident, cd=('<span class="code-fiche">%s</span>' % code) if code else "",
                     t=titre, r=reste, cc=(code + ", ") if code else "", t2=re.sub(r"<[^>]+>", "", titre), p=page)


def editions_grain():
    grain = json.load(open(os.path.join(RACINE, "build", "grain.json"), encoding="utf-8"))
    faites = []
    chapitres = []
    for f in grain:
        ident, code, titre, chap = fiche_chapitre(f["page"])
        chapitres.append((f, ident, code, titre, chap))
        corps = chap.replace('class="chapitre"', 'class="chapitre seul"')
        ecrire(ident, page_html(re.sub(r"<[^>]+>", "", titre), corps))
        faites.append(dict(slug=ident, titre=("%s — %s" % (code, re.sub(r"<[^>]+>", "", titre))) if code else re.sub(r"<[^>]+>", "", titre),
                           format="A5", genre="fiche", desc=f["resume"]))
    # le cahier : toutes les fiches, avec couverture et sommaire
    som = []
    fam_prec = None
    libelles = {"digest": "Pour commencer", "retex": "Retours d'expérience", "patterns": "Patterns", "gabarits": "Gabarits"}
    for f, ident, code, titre, _ in chapitres:
        if f["famille"] != fam_prec:
            som.append('<li class="famille">%s</li>' % libelles.get(f["famille"], f["famille"]))
            fam_prec = f["famille"]
        som.append('<li><span class="code">%s</span><a href="#%s">%s</a></li>' % (code, ident, re.sub(r"<[^>]+>", "", titre)))
    ordre = {"digest": 0, "retex": 1, "patterns": 2, "gabarits": 3}
    chapitres.sort(key=lambda c: (ordre.get(c[0]["famille"], 9), c[2]))
    som = []
    fam_prec = None
    for f, ident, code, titre, _ in chapitres:
        if f["famille"] != fam_prec:
            som.append('<li class="famille">%s</li>' % libelles.get(f["famille"], f["famille"]))
            fam_prec = f["famille"]
        som.append('<li><span class="code">%s</span><a href="#%s">%s</a></li>' % (code, ident, re.sub(r"<[^>]+>", "", titre)))
    corps = (couverture("Le Grain — cahier", "Ce qui se transporte",
                        "Retours d'expérience, patterns et gabarits génériques, écrits pour être repris tels quels par d'autres collectifs.",
                        "dessins/boucle.svg", ("%d fiches · %s · CC BY-SA 4.0" % (len(chapitres), DATE),))
             + verso("<p>Ce cahier rassemble les fiches publiées du Grain du Domaine du Mons. Chacune existe aussi en ligne, "
                     "en version A5 séparée et en Markdown. Textes sous licence CC BY-SA 4.0 : copiez, adaptez, republiez, "
                     "en citant la source et sous la même licence.</p><p>Composé avec Paged.js. Aucune fiche n'est un avis "
                     "juridique ; celles qui touchent au droit disent leurs sources et leurs limites.</p>")
             + '<nav class="sommaire-edition"><h2>Sommaire</h2><ol>%s</ol></nav>' % "".join(som)
             + "".join(c[4] for c in chapitres))
    ecrire("cahier-grain", page_html("Le Grain, cahier complet", corps))
    faites.insert(0, dict(slug="cahier-grain", titre="Le Grain, cahier complet", format="A5",
                          genre="cahier", desc="Toutes les fiches publiées, avec couverture et sommaire paginé."))
    return faites


def edition_projet():
    parties = []
    for page, courant in (("index.html", "Le lieu"), ("liberer-la-terre.html", "Libérer la terre"),
                          ("marcher-libre.html", "Marcher libre")):
        meta, corps = fragment(page)
        corps = pour_papier(corps)
        corps = re.sub(r"<h1>(.*?)</h1>", r'<h1><span class="titre-courant">\1</span></h1>', corps, count=1)
        parties.append('<article class="chapitre" id="%s">%s</article>' % (page[:-5], corps))
    som = "".join('<li><a href="#%s">%s</a></li>' % (i, t) for i, t in
                  (("index", "Le lieu"), ("liberer-la-terre", "Libérer la terre"), ("marcher-libre", "Marcher libre")))
    corps = (couverture("Le projet", "Sortir une terre du marché",
                        "Le lieu, le montage juridique, et la manière de vivre ensemble. Ce qui est acté, ce qui ne l'est pas.",
                        "dessins/coupe.svg", ("Livret A5 · %s" % DATE,))
             + verso("<p>Ce livret reprend trois pages du site, telles qu'elles sont en ligne à la date d'édition. Le montage "
                     "juridique est en cours de constitution : les statuts et les actes seront publiés dès qu'ils seront "
                     "signés. Version à jour : domainedumons.actitude.org.</p>")
             + '<nav class="sommaire-edition"><h2>Sommaire</h2><ol>%s</ol></nav>' % som
             + "".join(parties))
    ecrire("le-projet", page_html("Le projet — livret", corps))
    return dict(slug="le-projet", titre="Le projet — livret", format="A5", genre="livret",
                desc="Le lieu, Libérer la terre et Marcher libre, en un livret à imprimer et plier.")


def edition_rapport():
    meta, corps = fragment("rapport-2025.html")
    corps = pour_papier(corps)
    corps = re.sub(r"<h1>(.*?)</h1>", r'<h1><span class="titre-courant">\1</span></h1>', corps, count=1)
    corps = '<article class="chapitre flux-a4">%s</article>' % corps
    ecrire("rapport-2025", page_html("Rapport annuel 2025", corps, "a4"))
    return dict(slug="rapport-2025", titre="Rapport annuel 2025", format="A4", genre="rapport",
                desc="Le bilan climatique 2025 au point du lieu, figé au 31 décembre.")


def edition_faisceau():
    ressources = [
        ("Le foncier et le bâti", ""), ("L'eau", ""), ("Le bois, les haies, le couvert", ""),
        ("Les récoltes, les semences, les animaux", ""), ("Les outils et le matériel", "apporté · acquis · donné"),
        ("Les savoirs, les fiches", ""), ("Le nom, l'image, le domaine", ""), ("Les données", ""),
        ("Le travail", "qui décide de ce qui doit être fait, et que c'est fait"), ("…………………………", ""),
    ]
    droits = [("Accès", "qui peut venir sans demander ?"), ("Prélèvement", "qui peut emporter quelque chose ?"),
              ("Gestion", "qui décide de ce qu'on fait du lieu ?"), ("Exclusion", "qui décide qui entre ?"),
              ("Aliénation", "qui peut faire sortir la ressource ?")]
    feuilles = []
    for nom, precision in ressources:
        lignes = "".join('<tr><th>%s<small>%s</small></th><td></td><td></td><td></td><td></td><td></td><td></td></tr>' % d for d in droits)
        feuilles.append("""<section class="feuille">
<h2>Ressource&nbsp;: {n}</h2>
<p class="consigne">{p}Une colonne par ayant droit. Un statut par cellule, jamais une case vide&nbsp;: «&nbsp;on n'y a pas pensé&nbsp;» est une réponse. La colonne «&nbsp;Par quel acte&nbsp;?&nbsp;» fait le travail&nbsp;: un droit sans instrument est une intention.</p>
<table>
<colgroup><col class="col-droit"><col><col><col><col><col class="col-statut"><col class="col-acte"></colgroup>
<thead><tr><th>Droit</th><th>…………</th><th>…………</th><th>…………</th><th>…………</th><th>Statut</th><th>Par quel acte&nbsp;?</th></tr></thead>
<tbody>{l}</tbody>
</table>
<p class="legende-statuts">ACTÉ (acte signé, décision datée) · PROPOSÉ (soumis, en attente) · EXPLORÉ (piste) · NON TRANCHÉ (identifié, pas instruit) · NON POSÉ (personne n'y a encore pensé). Avant de remplir&nbsp;: qui exerce ce droit aujourd'hui, en fait&nbsp;? que se passe-t-il quand cette personne part&nbsp;? qui peut retirer ce droit, et comment&nbsp;?</p>
</section>""".format(n=nom, p=("<em>%s.</em> " % precision) if precision else "", l=lignes))
    corps = '<div class="flux-paysage">%s</div>' % "".join(feuilles)
    ecrire("faisceau-feuilles", page_html("Le faisceau de droits — feuilles à remplir", corps, "paysage"))
    return dict(slug="faisceau-feuilles", titre="Le faisceau de droits — feuilles à remplir", format="A4 paysage",
                genre="feuille", desc="Le gabarit GA-01 en dix feuilles vierges, une par ressource, à remplir en réunion.")


def ecrire(slug, texte):
    os.makedirs(ED, exist_ok=True)
    texte = G.versionner(texte, "../")
    open(os.path.join(ED, slug + ".html"), "w", encoding="utf-8").write(texte)


# --------------------------------------------------------------- la page

def page_editions(liste):
    items = []
    for x in liste:
        pdf = "editions/pdf/%s.pdf" % x["slug"]
        a_pdf = os.path.exists(os.path.join(RACINE, pdf))
        apercu = "visuels/editions/%s.png" % x["slug"]
        img = ('<img src="%s" alt="" loading="lazy">' % apercu) if os.path.exists(os.path.join(RACINE, apercu)) else ""
        cls = "a4" if x["format"] == "A4" else ("paysage" if "paysage" in x["format"] else "")
        items.append("""  <li>
    <a class="apercu {c}" href="editions/{s}.html" aria-hidden="true" tabindex="-1">{img}</a>
    <div>
      <h3><a href="editions/{s}.html">{t}</a></h3>
      <p>{d}</p>
      <p>{f} · <a href="editions/{s}.html">lire paginé</a>{pdf}</p>
    </div>
  </li>""".format(c=cls, s=x["slug"], img=img, t=G.e(x["titre"]), d=G.e(x["desc"]), f=x["format"],
                  pdf=(' · <a href="%s">PDF</a>' % pdf) if a_pdf else ""))
    corps = """<h1>Éditions à imprimer</h1>
<p class="chapeau">Les pages du site et les fiches du Grain, mises en page pour le papier&nbsp;: A5 pour les fiches et le livret, A4 pour le rapport, A4 paysage pour les feuilles à remplir.</p>
<p>Chaque édition se lit déjà paginée dans le navigateur, avec ses folios, ses titres courants et ses notes de bas de page. La commande «&nbsp;Imprimer&nbsp;» en fait un PDF. La mise en page est faite par <a href="https://pagedjs.org">Paged.js</a>, servi par le site lui-même.</p>
<div class="note">
<span class="etiquette">Pour une réunion ou un stand</span>
<p>Le livret se plie en cahier si l'imprimante sait faire le recto-verso en «&nbsp;brochure&nbsp;». Les feuilles du faisceau de droits sont faites pour être remplies à la main, une ressource par feuille.</p>
</div>
<h2 id="grain">Le Grain</h2>
<ul class="editions">
{g}
</ul>
<h2 id="projet">Le projet et le territoire</h2>
<ul class="editions">
{p}
</ul>
""".format(g="\n".join(i for x, i in zip(liste, items) if x["genre"] in ("fiche", "cahier")),
           p="\n".join(i for x, i in zip(liste, items) if x["genre"] not in ("fiche", "cahier")))
    meta = {"titre": "Éditions à imprimer", "description": "Les pages du site et les fiches du Grain du Domaine du Mons en éditions paginées A5 et A4, composées avec Paged.js."}
    os.makedirs(os.path.join(RACINE, "build", "pages"), exist_ok=True)
    open(os.path.join(RACINE, "build", "pages", "editions.html"), "w", encoding="utf-8").write(
        "<!--meta\n%s\n-->\n%s" % (json.dumps(meta, ensure_ascii=False, indent=1), corps))
    json.dump(liste, open(os.path.join(RACINE, "build", "editions.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


# --------------------------------------------------------------- visuels

TETE = '<div class="v-tete"><strong>Domaine du Mons</strong><span>{r}</span></div>'


def pied(x, source=True):
    src = ('<span class="v-source">Source : %s</span>' % G.e(x["source"])) if source and x.get("source") else "<span></span>"
    url = "domainedumons.actitude.org/" + x["page"].replace("index.html", "")
    return '<div class="v-pied">%s<span class="url">%s</span></div>' % (src, G.e(url))


def svg_de(chemin):
    return open(os.path.join(RACINE, chemin), encoding="utf-8").read()


RUBRIQUES = {"tdb": "Tableaux de bord", "reseau": "Le réseau", "ressources": "Le Grain", "projet": "Le projet"}


def visuel(x, fmt):
    forme = x["forme"]
    r = RUBRIQUES.get(G.rubrique_de(x["page"]) or "", "Vitrac-sur-Montane")
    cls = "v v-%s v-f-%s" % (fmt, forme)
    if forme == "appel":
        cls += " v-appel"
    if forme == "fiche":
        cls += " v-fiche"
    corps = TETE.format(r=r)
    if forme == "chiffre":
        long_ = " v-chiffre-long" if len(x["chiffre"]) > 6 else ""
        corps += ('<p class="v-chiffre%s">%s</p><p class="v-unite">%s</p><p class="v-texte">%s</p>'
                  % (long_, G.e(x["chiffre"]), G.e(x["unite"]), G.e(x["texte"])))
    elif forme == "citation":
        corps += '<p class="v-titre">%s</p><p class="v-citation">%s</p>' % (G.e(x["titre"]), G.e(x["citation"]))
        if fmt != "carre" and x.get("texte"):
            corps += '<p class="v-texte">%s</p>' % G.e(x["texte"])
    elif forme == "croquis":
        corps += '<div class="v-croquis">%s</div><p class="v-citation">%s</p>' % (svg_de(x["croquis"]), G.e(x["citation"]))
    elif forme == "liste":
        corps += '<p class="v-titre">%s</p><ul class="v-liste">%s</ul>' % (
            G.e(x["titre"]), "".join("<li>%s</li>" % G.e(l) for l in x["liste"]))
    elif forme == "tableau":
        corps += '<p class="v-titre">%s</p><table class="v-tableau">%s</table>' % (
            G.e(x["titre"]), "".join("<tr><th>%s</th><td>%s</td></tr>" % (G.e(a), G.e(b)) for a, b in x["lignes"]))
    elif forme == "appel":
        corps += '<p class="v-titre">%s</p><p class="v-citation">%s</p>' % (G.e(x["titre"]), G.e(x["citation"]))
        if fmt != "carre" and x.get("texte"):
            corps += '<p class="v-texte">%s</p>' % G.e(x["texte"])
        corps += '<p class="v-action">%s</p>' % G.e(x["appel"])
    elif forme == "fiche":
        corps += ('<p class="v-code">%s</p><p class="v-famille">%s · %s</p><p class="v-titre">%s</p>'
                  % (G.e(x["code"] if x["code"] != "DG" else "Le Grain"), {"retex": "Retour d'expérience", "patterns": "Pattern", "gabarits": "Gabarit", "digest": "Digest"}.get(x["famille"], ""),
                     G.e(x["niveau"]), G.e(x["titre"])))
        if fmt != "carre" and x.get("texte"):
            corps += '<p class="v-texte">%s</p>' % G.e(x["texte"])
    corps += pied(x, source=(forme == "chiffre"))
    return '<section class="%s" data-visuel="%s/%s">%s</section>' % (cls, fmt, x["id"], corps)


def visuel_serie(s):
    out = []
    n = len(s["planches"])
    for i, p in enumerate(s["planches"]):
        x = dict(p, page=s["page"], id="%s-%d" % (s["id"], i + 1))
        num = '<span class="v-numero">%d / %d</span>' % (i + 1, n)
        if p["forme"] == "couverture":
            corps = ('%s<p class="v-titre">%s</p><p class="v-texte">%s</p><p class="v-texte" style="margin-top:48px;color:#5b5749">%s</p>'
                     % (num, G.e(p["titre"]), G.e(p["citation"]), "Glisser pour lire →"))
            corps += pied(x, False)
            out.append('<section class="v v-serie v-couverture" data-visuel="serie/%s">%s</section>' % (x["id"], corps))
            continue
        html_v = visuel(x, "serie").replace('data-visuel="serie/%s">' % x["id"], 'data-visuel="serie/%s">%s' % (x["id"], num), 1)
        out.append(html_v)
    return out


def og_de(page, meta):
    rub = RUBRIQUES.get(G.rubrique_de(page) or "", "")
    titre = meta["titre"]
    desc = meta["description"]
    if len(desc) > 190:
        desc = desc[:desc.rfind(" ", 0, 185)] + "…"
    x = dict(page=page)
    corps = TETE.format(r=rub or "Vitrac-sur-Montane, Corrèze")
    corps += '<p class="v-titre">%s</p><p class="v-texte">%s</p>' % (G.e(titre), G.e(desc))
    corps += pied(x, False)
    return '<section class="v v-og" data-visuel="og/%s">%s</section>' % (page[:-5], corps)


TAILLES = {"carre": (1080, 1080), "portrait": (1080, 1350), "story": (1080, 1920),
           "og": (1200, 630), "serie": (1080, 1350)}


def planche():
    par = {f: [] for f in TAILLES}
    for x in P.tous():
        for fmt in x.get("formats", []):
            par[fmt].append(visuel(x, fmt))
    for s in P.SERIES:
        par["serie"] += visuel_serie(s)
    for page, chemin in sorted(G.fragments().items()):
        meta, _, _ = G.lire_fragment(chemin)
        par["og"].append(og_de(page, meta))
    os.makedirs(VIS, exist_ok=True)
    for fmt, secs in par.items():
        l, h = TAILLES[fmt]
        texte = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>Visuels {f} — Domaine du Mons</title>
<meta name="robots" content="noindex">
<link rel="stylesheet" href="../visuels.css">
<style>@page {{ size: {l}px {h}px; margin: 0; }}</style>
<script>window.PagedConfig = {{ auto: true, after: function () {{
  document.body.setAttribute("data-pret", String(document.querySelectorAll(".pagedjs_page").length)); }} }};</script>
<script src="../vendor/paged.polyfill.min.js"></script>
</head>
<body>
{s}
</body>
</html>
""".format(f=fmt, l=l, h=h, s="\n".join(secs))
        open(os.path.join(VIS, fmt + ".html"), "w", encoding="utf-8").write(G.versionner(texte, "../"))
    liens = "".join('<li><a href="%s.html">%s</a> — %d visuels, %d × %d</li>' % (f, f, len(par[f]), *TAILLES[f]) for f in TAILLES)
    open(os.path.join(VIS, "planche.html"), "w", encoding="utf-8").write(
        '<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8"><title>Planches de visuels — Domaine du Mons</title>'
        '<meta name="robots" content="noindex"><link rel="stylesheet" href="../style.css?v=%d"></head><body><main>'
        '<h1>Planches de visuels</h1><p>Une planche par format, composée avec Paged.js&nbsp;; chaque page est un visuel. '
        'Les images découpées sont dans les dossiers du même nom. Retour à <a href="../relayer.html">Relayer</a>.</p>'
        '<ul>%s</ul></main></body></html>\n' % (G.VERSION, liens))
    return sum(len(v) for v in par.values())


# --------------------------------------------------------------- rendu

def rendre(port=8766):
    """Imprime les éditions et découpe la planche. Demande playwright."""
    import threading, http.server, functools, socketserver
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  ✗ le module playwright manque : pip install playwright (Chromium requis)")
        return 1
    class Muet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    gestion = functools.partial(Muet, directory=RACINE)
    socketserver.TCPServer.allow_reuse_address = True
    srv = socketserver.TCPServer(("127.0.0.1", port), gestion)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = "http://127.0.0.1:%d/" % port
    liste = json.load(open(os.path.join(RACINE, "build", "editions.json"), encoding="utf-8"))
    os.makedirs(os.path.join(ED, "pdf"), exist_ok=True)
    os.makedirs(os.path.join(VIS, "editions"), exist_ok=True)
    with sync_playwright() as p:
        nav = p.chromium.launch()
        pg = nav.new_page(viewport={"width": 1200, "height": 900})
        for x in liste:
            pg.goto(base + "editions/%s.html" % x["slug"])
            pg.wait_for_selector("body[data-pret]", timeout=120000)
            n = pg.get_attribute("body", "data-pret")
            pg.pdf(path=os.path.join(ED, "pdf", x["slug"] + ".pdf"), prefer_css_page_size=True, print_background=True)
            pg.locator(".pagedjs_page").first.screenshot(path=os.path.join(VIS, "editions", x["slug"] + ".png"), scale="css")
            print("  %-44s %3s pages  %7d octets" % (x["slug"] + ".pdf", n, os.path.getsize(os.path.join(ED, "pdf", x["slug"] + ".pdf"))))
        nb = 0
        for fmt, (l, h) in TAILLES.items():
            pg.goto(base + "visuels/%s.html" % fmt)
            pg.wait_for_selector("body[data-pret]", timeout=180000)
            pg.add_style_tag(content=".pagedjs_pages{zoom:1 !important}")
            pages = pg.locator(".pagedjs_page")
            for i in range(pages.count()):
                el = pages.nth(i)
                cle = el.locator("[data-visuel]").first.get_attribute("data-visuel")
                f, ident = cle.split("/")
                os.makedirs(os.path.join(VIS, f), exist_ok=True)
                el.screenshot(path=os.path.join(VIS, f, ident + ".png"), scale="css")
                nb += 1
            pg.pdf(path=os.path.join(VIS, fmt + ".pdf"), prefer_css_page_size=True, print_background=True)
        print("  %d visuels découpés, une planche PDF par format" % nb)
        nav.close()
    srv.shutdown()
    return 0


def main():
    if "--rendre" in sys.argv:
        return rendre()
    liste = editions_grain()
    liste.append(edition_projet())
    liste.append(edition_rapport())
    liste.append(edition_faisceau())
    page_editions(liste)
    n = planche()
    print("  %d éditions paginées, planche de %d visuels" % (len(liste), n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
