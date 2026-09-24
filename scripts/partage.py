#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Les extraits à relayer : un contenu, plusieurs canaux.

    python3 scripts/partage.py         écrit partage/extraits.json et le
                                       fragment build/pages/relayer.html

Un extrait est une unité de sens autonome, prise dans une page du site :
un chiffre, une phrase, une liste, un dessin, une fiche. Il est écrit une
fois, ici, et composé ensuite pour chaque canal selon ses contraintes —
Mastodon (500 signes), Telegram (1 024 en légende d'image), Instagram
(2 200, pas de lien cliquable), Facebook, Substack (texte riche).

Deux règles tiennent ce fichier honnête :

1. Les chiffres ne sont jamais recopiés à la main. Ils sont lus dans data/
   au moment de la construction. Un extrait qui affirmerait une tendance que
   le fichier ne porte plus arrête la construction (H7 : ce qui est publié
   correspond à ce que le corpus établit).
2. Le texte d'un extrait reprend celui de la page. Il ne dit rien que la
   page ne dise pas, et il renvoie toujours vers elle.

Aucun appel à un service tiers : les liens de partage sont des liens
ordinaires, suivis seulement si le visiteur clique.
"""
import html, json, os, re, sys
from urllib.parse import quote

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://domainedumons.actitude.org/"
MOINS = "−"
NBSP = " "


def lire(f):
    return json.load(open(os.path.join(RACINE, f), encoding="utf-8"))


def nf(x, d=1, signe=False):
    s = ("%+.*f" if signe else "%.*f") % (d, x)
    s = s.replace("-", MOINS).replace(".", ",")
    return s


def milliers(n):
    return "{:,}".format(n).replace(",", " ")


class Incoherence(Exception):
    pass


def exiger(cond, message):
    if not cond:
        raise Incoherence(message)


# ------------------------------------------------------------ les extraits

def extraits_calcules():
    c = lire("data/climat.json")["tendances"]
    a = lire("data/analyses.json")
    h = lire("data/humidite-sol.json")
    s = lire("data/associations.json")
    exiger(not c["pluie"]["significative"] and c["jp"]["significative"],
           "climat.json : l'extrait « jours de pluie » suppose un cumul sans tendance et des jours "
           "de pluie en baisse significative — ce n'est plus le cas, le texte est à revoir")
    ta = a["tendances"]
    rg = a["risque_gel"]
    exiger(ta["floraison"]["significative"], "analyses.json : la floraison n'avance plus significativement")
    exiger(not ta["gel_floraison"]["significative"],
           "analyses.json : la gelée sur fleur est devenue significative, le texte dit le contraire")
    rang = h["rang_ete"]
    an = str(h["annee_courante"])
    exiger(an in rang, "humidite-sol.json : l'année courante n'est pas classée")
    r_sol = rang[an]
    n_etes = len(rang)
    v = s["verdicts"]

    ext = []
    ext.append(dict(
        id="jours-de-pluie", page="tdb-climat.html", forme="chiffre",
        titre="Moins de jours de pluie, un cumul sans tendance",
        chiffre=nf(c["jp"]["pente_par_decennie"], 1, True), unite="jour de pluie par décennie",
        texte=("Au Domaine du Mons, de 1950 à 2025, le cumul annuel de pluie n'a pas de tendance "
               "détectable. Le nombre de jours de pluie recule de %s par décennie."
               % nf(abs(c["jp"]["pente_par_decennie"]), 1)),
        source="Réanalyse Open-Meteo au point du lieu, 1950-2025 ; test de Mann-Kendall et pente de Sen",
        mots=["Corrèze", "climat", "DonnéesOuvertes"], formats=["carre", "portrait", "story"]))
    ext.append(dict(
        id="gel-et-chaleur", page="tdb-climat.html", forme="chiffre",
        titre="Température, gel et chaleur depuis 1950",
        chiffre=nf(c["gel"]["pente_par_decennie"], 1, True), unite="jours de gel par décennie",
        texte=("Au point du lieu depuis 1950 : %s °C par décennie en moyenne annuelle, %s jours de "
               "gel par décennie, %s jour à 30 °C ou plus par décennie."
               % (nf(c["tmoy"]["pente_par_decennie"], 2, True), nf(c["gel"]["pente_par_decennie"], 1, True),
                  nf(c["chaud"]["pente_par_decennie"], 1, True))),
        source="Réanalyse Open-Meteo au point du lieu, 1950-2025 ; test de Mann-Kendall et pente de Sen",
        mots=["Corrèze", "climat"], formats=["carre", "portrait"]))
    ext.append(dict(
        id="gel-sur-fleur", page="tdb-saisons.html", forme="chiffre",
        titre="La floraison avance, les gelées de printemps restent",
        chiffre="%d %% → %d %%" % (rg["1961-1990"]["part_gelee_en_floraison"],
                                                     rg["1996-2025"]["part_gelee_en_floraison"]),
        unite="des années avec une gelée sur fleur ouverte",
        texte=("La floraison des fruitiers avance de %s jours par décennie depuis 1950 au Domaine du "
               "Mons. Les années avec une gelée sur fleur ouverte passent de %d %% (1961-1990) à %d %% "
               "(1996-2025) ; l'écart reste sous le seuil de significativité habituel (p = %s)."
               % (nf(abs(ta["floraison"]["pente_par_decennie"]), 1),
                  rg["1961-1990"]["part_gelee_en_floraison"], rg["1996-2025"]["part_gelee_en_floraison"],
                  nf(ta["gel_floraison"]["p"], 3))),
        source="Réanalyse Open-Meteo 1950-2025 ; floraison à 150 °C·j base 5 depuis le 1er février",
        mots=["verger", "climat", "Corrèze"], formats=["carre", "portrait", "story"]))
    ext.append(dict(
        id="sol-ete", page="tdb-eau.html", forme="chiffre",
        titre="Le sol, cet été",
        chiffre="%d%s" % (r_sol, "er" if r_sol == 1 else "e"),
        unite="été le plus sec pour le sol, sur %d depuis 1958" % n_etes,
        texte=("Au relevé du %s, l'été %s se classe %s pour l'humidité du sol sur les %d étés "
               "calculés depuis 1958 dans la maille qui contient le lieu."
               % (date_fr(h["actuel"]["date"]), an,
                  "au premier rang des plus secs" if r_sol == 1 else "au %de rang des plus secs" % r_sol,
                  n_etes)),
        source="Météo-France, réanalyse SIM2, maille de 8 km ; humidité ramenée à la réserve utile",
        mots=["sécheresse", "eau", "Corrèze"], formats=["carre", "portrait", "story"], date=h["actuel"]["date"]))
    ext.append(dict(
        id="associations", page="reseau-associations.html", forme="chiffre",
        titre="Les associations à une heure de route",
        chiffre=milliers(s["actives"]), unite="associations actives dans %d communes" % s["communes_zone"],
        texte=("À moins d'une heure du lieu, le Répertoire national des associations compte %s "
               "associations actives, au sens de celles qui n'ont pas déclaré leur dissolution. "
               "Nous avons lu %s objets déclarés contre une grille écrite d'avance : %s engagent "
               "l'association envers des non-membres, %s laissent un doute, publié lui aussi."
               % (milliers(s["actives"]), milliers(s["lues"]), milliers(v["retenu"]), milliers(v["douteux"]))),
        source="Répertoire national des associations, ministère de l'Intérieur, dump du 1er septembre 2026",
        mots=["associations", "Corrèze", "InteretGeneral"], formats=["carre", "portrait", "story"]))
    return ext


EXTRAITS_ECRITS = [
    dict(id="faisceau", page="liberer-la-terre.html", forme="croquis", croquis="dessins/montage.svg",
         titre="Libérer la terre",
         citation="La propriété est un faisceau de droits, qui peuvent être répartis entre plusieurs titulaires.",
         texte=("Au Domaine du Mons, la nue-propriété du foncier va à un fonds de dotation dont les "
                "statuts doivent rendre la vente impossible ; l'usage va à une association d'intérêt "
                "général autogérée par ses membres. Le montage est en cours de constitution."),
         mots=["communs", "foncier", "Corrèze"], formats=["carre", "portrait"]),
    dict(id="verrou", page="liberer-la-terre.html", forme="citation",
         titre="Le fonds de dotation",
         citation=("Le verrou doit tenir dans les statuts eux-mêmes. Une clause qui dépendrait de la "
                   "volonté des dirigeants futurs ne protégerait rien."),
         texte=("Les fondateurs se font confiance, leurs successeurs ne se connaissent pas. C'est "
                "pourquoi l'interdiction de vendre doit être écrite dans les statuts du fonds, et non "
                "laissée à ceux qui le dirigeront dans trente ans."),
         mots=["communs", "foncier"], formats=["carre", "portrait"]),
    dict(id="droits-acquis", page="marcher-libre.html", forme="liste",
         titre="Ce qui reste acquis en toute circonstance",
         liste=["le droit de partir", "le droit de dire non",
                "le droit d'être informé avant qu'une décision soit prise",
                "le droit de demander qu'une règle soit réexaminée"],
         texte=("Ce qui reste acquis en toute circonstance : le droit de partir, le droit de dire non, "
                "le droit d'être informé avant qu'une décision soit prise, et le droit de demander "
                "qu'une règle soit réexaminée."),
         mots=["autogestion", "communs"], formats=["carre", "portrait", "story"]),
    dict(id="trois-cercles", page="marcher-libre.html", forme="croquis", croquis="dessins/cercles.svg",
         titre="Le périmètre du commun",
         citation="Mettre en commun la terre et le travail ne veut pas dire tout mettre en commun.",
         texte=("Une chambre qui ferme, un revenu qui n'appartient qu'à soi, des amitiés en dehors, "
                "du temps sans personne. Et vers l'extérieur, un lieu qui accueille : sans quoi il "
                "devient un entre-soi."),
         mots=["autogestion", "communs"], formats=["carre", "portrait"]),
    dict(id="decider", page="marcher-libre.html", forme="tableau",
         titre="Décider sans chef",
         lignes=[("Ce qui n'engage que soi", "la personne, qui informe si ça touche les autres"),
                 ("Le courant d'un domaine confié", "celui ou celle qui le porte, par mandat écrit"),
                 ("Ce qui engage le collectif", "tout le monde : proposition écrite, objections, décision consignée"),
                 ("Ce qui engage l'avenir du lieu", "tout le monde, plus la structure porteuse, avec un délai long")],
         texte=("Écrire qui décide de quoi, et à quel niveau d'engagement : tout ne se décide pas de la "
                "même façon. Une décision se consigne avec son motif et sa date de réexamen."),
         mots=["autogestion", "gouvernance"], formats=["portrait"]),
    dict(id="fil-commun", page="reseau-fil.html", forme="appel",
         titre="Le fil commun",
         citation="Une lettre mensuelle que chaque lieu écrit dans ses mots, envoyée à date fixe.",
         texte=("Un chantier ouvert, un coup de main cherché, un surplus, une assemblée ouverte, un "
                "départ : chaque lieu de la zone produit des nouvelles qui se perdent. Le fil commun "
                "démarrera quand trois lieux auront dit qu'ils y participeraient. Aucun traceur, "
                "aucune plateforme, désinscription en un mot."),
         appel="Pour en être : contact@actitude.org",
         mots=["Corrèze", "collectifs", "entraide"], formats=["carre", "portrait", "story"]),
]

SERIES = [
    dict(id="liberer-planches", page="liberer-la-terre.html", titre="Libérer la terre, en cinq planches",
         mots=["communs", "foncier", "Corrèze"],
         texte=("Le montage du Domaine du Mons en cinq planches : le faisceau de droits, le fonds de "
                "dotation, l'association, et ce qui reste à trancher."),
         planches=[
             dict(forme="couverture", titre="Libérer la terre",
                  citation="Sortir une terre du marché, durablement, sans sortir du droit."),
             dict(forme="croquis", croquis="dessins/montage.svg", titre="Le titre d'un côté, l'usage de l'autre",
                  citation="La propriété est un faisceau de droits, qui peuvent être répartis entre plusieurs titulaires."),
             dict(forme="citation", titre="Le fonds de dotation",
                  citation=("Il détient la nue-propriété du foncier, et ses statuts ont une fonction : rendre "
                            "la vente impossible, y compris à ceux qui le dirigeront dans 30 ans.")),
             dict(forme="citation", titre="L'association",
                  citation=("Une association loi 1901, d'intérêt général, autogérée par ses membres, reçoit "
                            "l'usage du lieu. Ce qui se fait ici doit profiter au-delà de ceux qui y habitent.")),
             dict(forme="liste", titre="Où nous en sommes",
                  liste=["à l'étude — l'instrument de mise à disposition",
                         "à l'étude — la garantie de l'intérêt général",
                         "à l'étude — le statut des personnes qui vivent ici",
                         "en cours — la constitution des structures"]),
         ]),
]


def extraits_grain():
    chemin = os.path.join(RACINE, "build", "grain.json")
    if not os.path.exists(chemin):
        return []
    out = []
    for f in json.load(open(chemin, encoding="utf-8")):
        out.append(dict(id=f["slug"], page=f["page"], forme="fiche", code=f["code"],
                        titre=f["titre"], niveau=f["genericite"], famille=f["famille"],
                        texte=f["resume"], citation=f.get("maxime") or "",
                        mots=["communs", "RetourDExpérience"] if f["famille"] == "retex" else ["communs"],
                        formats=["carre", "portrait"]))
    return out


def date_fr(iso):
    y, m, d = iso.split("-")
    mois = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
            "septembre", "octobre", "novembre", "décembre"][int(m) - 1]
    return "%d%s %s %s" % (int(d), "er" if d == "01" else "", mois, y)


_CACHE = {}


def tous():
    if "x" not in _CACHE:
        _CACHE["x"] = extraits_calcules() + EXTRAITS_ECRITS + extraits_grain()
    return _CACHE["x"]


def extraits_de(page):
    return [x for x in tous() if x["page"] == page] + [s for s in SERIES if s["page"] == page]


# ------------------------------------------------------------ composition

def url_de(x):
    return SITE + x["page"] + ("#" + x["ancre"] if x.get("ancre") else "")


def tags(x, n=4):
    return " ".join("#" + m for m in x.get("mots", [])[:n])


def corps_de(x):
    """La phrase-titre, puis le texte : ce que tous les canaux partagent."""
    tete = x.get("citation") or ""
    if x.get("chiffre"):
        tete = "%s %s." % (x["chiffre"], x["unite"])
    return (tete + "\n\n" if tete else "") + x["texte"]


def composer(x):
    u = url_de(x)
    corps = corps_de(x)
    src = ("Source : %s." % x["source"]) if x.get("source") else ""
    code = (x["code"] + " — ") if x.get("code") else ""
    c = {}
    c["mastodon"] = "\n\n".join(p for p in [code + x["titre"], corps, u, tags(x)] if p)
    c["telegram"] = "\n\n".join(p for p in ["**%s%s**" % (code, x["titre"]), corps, src, u] if p)
    c["instagram"] = "\n\n".join(p for p in [code + x["titre"], corps, src,
                                              "Page complète : " + u.replace("https://", ""),
                                              tags(x, 6)] if p)
    c["facebook"] = "\n\n".join(p for p in [code + x["titre"], corps, u] if p)
    paras = "".join("<p>%s</p>" % html.escape(p) for p in corps.split("\n\n"))
    c["substack"] = ("<h3>%s%s</h3>%s<p>%s<a href=\"%s\">Lire sur le site du Domaine du Mons</a></p>"
                     % (html.escape(code), html.escape(x["titre"]), paras,
                        ("<em>%s</em> " % html.escape(src)) if src else "", u))
    return c


LIMITES = {"mastodon": 500, "telegram": 1024, "instagram": 2200, "facebook": 5000}


def longueur_mastodon(t):
    # Mastodon compte toute adresse pour 23 signes.
    return len(re.sub(r"https?://\S+", "x" * 23, t))


def controler(x, c):
    fautes = []
    for canal, lim in LIMITES.items():
        n = longueur_mastodon(c[canal]) if canal == "mastodon" else len(c[canal])
        if n > lim:
            fautes.append("extrait « %s » : %d signes pour %s (limite %d)" % (x["id"], n, canal, lim))
    if len(x.get("mots", [])) > 30:
        fautes.append("extrait « %s » : plus de 30 mots-dièse" % x["id"])
    return fautes


# ------------------------------------------------- la page « Relayer »

CANAUX = [("mastodon", "Mastodon et le fédivers"), ("telegram", "Telegram"),
          ("instagram", "Instagram"), ("facebook", "Facebook"), ("substack", "Substack")]


def fiche_extrait(x, n_id):
    c = composer(x)
    u = url_de(x)
    visuels = []
    for f in x.get("formats", []):
        visuels.append('<a href="visuels/%s/%s.png">%s</a>' % (f, x["id"], FORMATS[f][0]))
    vignette = ('<img src="visuels/carre/%s.png" alt="" width="160" height="160" loading="lazy">'
                % x["id"]) if "carre" in x.get("formats", []) else ""
    blocs = []
    for canal, libelle in CANAUX:
        val = c[canal]
        n = longueur_mastodon(val) if canal == "mastodon" else len(val)
        lim = LIMITES.get(canal)
        compte = " · %d / %d signes" % (n, lim) if lim else ""
        action = ""
        if canal == "telegram":
            action = ('<a class="bouton" href="https://t.me/share/url?url=%s&amp;text=%s" rel="noopener">Ouvrir dans Telegram</a>'
                      % (quote(u, safe=""), quote(val.replace("**", ""), safe="")))
        elif canal == "facebook":
            action = ('<a class="bouton" href="https://www.facebook.com/sharer/sharer.php?u=%s" rel="noopener">Ouvrir Facebook</a>'
                      % quote(u, safe=""))
        elif canal == "mastodon":
            action = '<button type="button" class="bouton" data-mastodon>Publier sur mon instance…</button>'
        texte = html.escape(val)
        riche = ' data-riche="%s"' % html.escape(val) if canal == "substack" else ""
        blocs.append("""      <details class="canal canal-{c}">
        <summary>{l}<span class="compte">{k}</span></summary>
        <textarea readonly rows="7" id="t-{i}-{c}" aria-label="Texte pour {l}">{t}</textarea>
        <p class="actions"><button type="button" class="bouton" data-copier="t-{i}-{c}"{r}>Copier</button> {a}</p>
      </details>""".format(c=canal, l=libelle, k=compte, i=n_id, t=texte, a=action, r=riche))
    code = ('<span class="code">%s</span> ' % x["code"]) if x.get("code") else ""
    return """  <article class="extrait" id="x-{id}">
    <div class="extrait-vignette">{v}</div>
    <div class="extrait-corps">
      <h3>{code}{t}</h3>
      <p class="extrait-texte">{txt}</p>
      <p class="extrait-meta"><a href="{p}">La page</a> · Visuels : {vis}</p>
{blocs}
    </div>
  </article>
""".format(id=x["id"], v=vignette, code=code, t=html.escape(x["titre"]), txt=html.escape(corps_de(x)).replace("\n\n", "<br>"),
           p=x["page"] + ("#" + x["ancre"] if x.get("ancre") else ""), vis=", ".join(visuels) or "—",
           blocs="\n".join(blocs))


FORMATS = {
    "carre": ("carré 1080", 1080, 1080),
    "portrait": ("portrait 1080 × 1350", 1080, 1350),
    "story": ("story 1080 × 1920", 1080, 1920),
    "og": ("vignette de lien 1200 × 630", 1200, 630),
}


def page_relayer(titres):
    """Le fragment de relayer.html, groupé par page d'origine."""
    par_page = {}
    for x in tous():
        par_page.setdefault(x["page"], []).append(x)
    corps = ["""<h1>Relayer</h1>
<p class="chapeau">Des extraits du site prêts à publier, un visuel pour chacun, et le texte déjà mis au format de chaque réseau.</p>
<p>Chaque extrait reprend une page du site et y renvoie. Les chiffres sont recalculés à chaque construction du site depuis les fichiers de données publiés&nbsp;: ils ne peuvent pas diverger de la page. Textes sous CC&nbsp;BY-SA&nbsp;4.0, données sous Licence Ouverte&nbsp;2.0&nbsp;: reprenez-les, en citant le Domaine du Mons.</p>
<div class="note" id="mastodon">
<span class="etiquette">Mode d'emploi</span>
<p><strong>Mastodon et le fédivers</strong>&nbsp;: le bouton demande le nom de votre instance, puis ouvre sa page de publication avec le texte prérempli. Rien n'est retenu. <strong>Telegram et Facebook</strong>&nbsp;: liens de partage ordinaires. <strong>Instagram</strong> n'accepte pas de publication depuis une page web&nbsp;: téléchargez le visuel, collez la légende. <strong>Substack</strong>&nbsp;: «&nbsp;Copier&nbsp;» place le texte mis en forme dans le presse-papiers, à coller dans l'éditeur.</p>
<p>Les visuels sont composés avec Paged.js, une page par format&nbsp;: <a href="visuels/planche.html">la planche complète</a>.</p>
</div>
"""]
    n = 0
    fautes = []
    groupes = {}
    for page in sorted(par_page, key=lambda p: ORDRE.index(p) if p in ORDRE else 99):
        cle = "grain" if page.startswith("grain-") else page[:-5]
        groupes.setdefault(cle, (titres.get(page, page) if cle != "grain" else "Le Grain", []))[1].extend(par_page[page])
    for cle, (titre, xs) in groupes.items():
        corps.append('<h2 id="%s">%s</h2>' % (cle, html.escape(titre, quote=False)))
        for x in xs:
            n += 1
            corps.append(fiche_extrait(x, n))
            fautes += controler(x, composer(x))
    for s in SERIES:
        corps.append(serie_bloc(s))
    meta = {"titre": "Relayer", "description": "Des extraits du site du Domaine du Mons prêts à publier sur Mastodon, Telegram, Instagram, Facebook et Substack, avec leurs visuels."}
    frag = "<!--meta\n%s\n-->\n%s" % (json.dumps(meta, ensure_ascii=False, indent=1), "\n".join(corps))
    return frag, fautes


def serie_bloc(s):
    vign = "".join('<a href="visuels/serie/%s-%d.png"><img src="visuels/serie/%s-%d.png" alt="Planche %d : %s" width="120" height="150" loading="lazy"></a>'
                   % (s["id"], i + 1, s["id"], i + 1, i + 1, html.escape(p["titre"])) for i, p in enumerate(s["planches"]))
    leg = s["texte"] + "\n\n" + "Page complète : " + (SITE + s["page"]).replace("https://", "") + "\n\n" + tags(s, 6)
    return """<h2 id="series">Séries pour carrousel</h2>
  <article class="extrait extrait-serie" id="x-{id}">
    <div class="extrait-corps">
      <h3>{t}</h3>
      <p class="serie">{v}</p>
      <details class="canal canal-instagram" open>
        <summary>Légende Instagram et Facebook</summary>
        <textarea readonly rows="6" id="t-{id}">{leg}</textarea>
        <p class="actions"><button type="button" class="bouton" data-copier="t-{id}">Copier</button></p>
      </details>
    </div>
  </article>
""".format(id=s["id"], t=html.escape(s["titre"]), v=vign, leg=html.escape(leg))


ORDRE = ["index.html", "liberer-la-terre.html", "marcher-libre.html", "tdb-climat.html",
         "tdb-saisons.html", "tdb-eau.html", "reseau-associations.html", "reseau-fil.html"]


def main():
    titres = {}
    for d in ("contenu/pages", "build/pages"):
        p = os.path.join(RACINE, d)
        if os.path.isdir(p):
            for f in os.listdir(p):
                if f.endswith(".html"):
                    t = open(os.path.join(p, f), encoding="utf-8").read()
                    m = re.search(r'"titre":\s*"([^"]+)"', t)
                    if m:
                        titres[f] = m.group(1)
    try:
        frag, fautes = page_relayer(titres)
    except Incoherence as ex:
        print("  ✗ %s" % ex)
        return 1
    if fautes:
        print("\n".join("  ✗ " + f for f in fautes))
        return 1
    os.makedirs(os.path.join(RACINE, "build", "pages"), exist_ok=True)
    open(os.path.join(RACINE, "build", "pages", "relayer.html"), "w", encoding="utf-8").write(frag)
    os.makedirs(os.path.join(RACINE, "partage"), exist_ok=True)
    sortie = []
    for x in tous():
        sortie.append(dict(x, url=url_de(x), textes=composer(x)))
    json.dump({"licence": "textes CC BY-SA 4.0, chiffres Licence Ouverte 2.0",
               "explication": "Extraits du site prêts à relayer, un texte par canal. Recalculé à chaque construction.",
               "extraits": sortie, "series": SERIES},
              open(os.path.join(RACINE, "partage", "extraits.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("  %d extraits, %d série(s), textes contrôlés pour cinq canaux" % (len(tous()), len(SERIES)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
