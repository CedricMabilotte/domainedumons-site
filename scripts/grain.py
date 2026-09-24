#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Le Grain sur le site : les fiches de contenu/grain/ deviennent des pages.

    python3 scripts/grain.py      écrit build/pages/grain-*.html,
                                  build/pages/ressources.html et build/grain.json

Les fiches sont exportées du corpus (docs du Projet) avec leur en-tête ; la
ligne « source » de chacune dit d'où et quand. Le corpus reste la source : une
fiche se corrige là-bas, puis se réexporte ici.

Ce que la mise en page change, et rien d'autre :
  - les intertitres en « Ce que / Ce qui » du format after-action review sont
    renommés à l'affichage (D-0007 les retire du site) — le texte n'est pas
    touché ;
  - les renvois [[FICHE]] deviennent des liens quand la fiche est publiée, et
    restent du texte sinon ;
  - la passe typographique du site (scripts/typographie.py) est appliquée.

Trois fiches du corpus ne sont pas publiées (RETENUES ci-dessous) : deux
portent sur le montage juridique, et une recommandation juridique ne passe du
corpus au site qu'après avis professionnel (RX-01) ; la troisième décrit une
chaîne d'outils qui n'est pas encore distribuée.

Aucune dépendance : un convertisseur Markdown minimal suffit au format des
fiches, et il est éprouvé par --test.
"""
import html, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import typographie  # noqa: E402

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(RACINE, "contenu", "grain")
SORTIE = os.path.join(RACINE, "build", "pages")

RETENUES = {
    "RX-01": "porte sur le choix de l'instrument juridique, qui attend l'avis du notaire",
    "RE-01": "porte sur le choix de l'instrument juridique, qui attend l'avis du notaire",
    "RE-02": "décrit une chaîne d'outils qui n'est pas encore distribuée publiquement",
}

INTERTITRES = {
    "Ce qui devait arriver": "L'attendu",
    "Ce qui s'est passé": "Le déroulé",
    "Ce qu'on en apprend": "Les leçons",
    "Ce qu'on change": "Les changements",
    "Ce qui se transporte": "Un motif, huit contrôles",
    "Ce qui rend les corrections cumulatives": "Rendre les corrections cumulatives",
    "Quatre règles d'écriture qui découlent de tout cela": "Quatre règles d'écriture",
}

# Date de mise en ligne par défaut : celle de la première publication du Grain.
# Une fiche publiée plus tard le déclare dans son en-tête (« publié: AAAA-MM-JJ »).
PUBLICATION = "2026-09-24"

FAMILLES = {
    "digest": ("digest", "Le digest"),
    "retex": ("retex", "Retours d'expérience"),
    "pattern": ("patterns", "Patterns"),
    "gabarit": ("gabarits", "Gabarits"),
    "recette": ("recettes", "Recettes"),
}


# --------------------------------------------------------------- Markdown

def en_ligne(t, liens):
    """Le balisage à l'intérieur d'un paragraphe."""
    t = html.escape(t, quote=False)
    codes = []

    def garder(m):
        codes.append(m.group(1))
        return "\x00%d\x00" % (len(codes) - 1)
    t = re.sub(r"`([^`]+)`", garder, t)
    t = re.sub(r"\[\[([^\]]+)\]\]", lambda m: liens(m.group(1)), t)
    t = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
               lambda m: '<a href="%s">%s</a>' % (m.group(2).replace("&amp;", "&").replace("&", "&amp;"), m.group(1)), t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", t)

    def rendre(m):
        c = codes[int(m.group(1))]
        cible = {"tdb-eau": "tdb-eau.html"}.get(c)
        return '<a href="%s"><code>%s</code></a>' % (cible, c) if cible else "<code>%s</code>" % c
    return re.sub(r"\x00(\d+)\x00", rendre, t)


def markdown(md, liens=lambda x: x):
    lignes = md.split("\n")
    out, i = [], 0

    def para(bloc):
        return "<p>%s</p>" % en_ligne(" ".join(l.strip() for l in bloc), liens)
    while i < len(lignes):
        l = lignes[i]
        if not l.strip():
            i += 1
            continue
        if l.startswith("```"):
            j = i + 1
            while j < len(lignes) and not lignes[j].startswith("```"):
                j += 1
            out.append('<pre class="gabarit-texte">%s</pre>' % html.escape("\n".join(lignes[i + 1:j])))
            i = j + 1
            continue
        m = re.match(r"(#{1,4})\s+(.*)", l)
        if m:
            n = len(m.group(1))
            out.append("<h%d>%s</h%d>" % (n, en_ligne(m.group(2), liens), n))
            i += 1
            continue
        if re.match(r"^-{3,}\s*$", l):
            out.append("<hr>")
            i += 1
            continue
        if l.startswith(">"):
            bloc = []
            while i < len(lignes) and lignes[i].startswith(">"):
                bloc.append(lignes[i][1:].strip())
                i += 1
            out.append("<blockquote>%s</blockquote>" % para(bloc))
            continue
        if l.startswith("|"):
            bloc = []
            while i < len(lignes) and lignes[i].startswith("|"):
                bloc.append([c.strip() for c in lignes[i].strip().strip("|").split("|")])
                i += 1
            tete, corps = bloc[0], [r for r in bloc[2:]]
            th = "".join("<th scope=\"col\">%s</th>" % en_ligne(c, liens) for c in tete)
            trs = []
            for r in corps:
                cells = []
                for k, c in enumerate(r):
                    if k == 0:
                        cells.append('<th scope="row">%s</th>' % en_ligne(c, liens))
                    else:
                        cells.append("<td>%s</td>" % en_ligne(c, liens))
                trs.append("<tr>%s</tr>" % "".join(cells))
            out.append('<div class="defilant"><table class="donnees"><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>'
                       % (th, "".join(trs)))
            continue
        if re.match(r"^(\s*[-*]|\s*\d+\.)\s+", l):
            ordonnee = bool(re.match(r"^\s*\d+\.", l))
            items = []
            while i < len(lignes) and re.match(r"^(\s*[-*]|\s*\d+\.)\s+", lignes[i]):
                items.append(re.sub(r"^(\s*[-*]|\s*\d+\.)\s+", "", lignes[i]))
                i += 1
            balise = "ol" if ordonnee else "ul"
            out.append("<%s>%s</%s>" % (balise, "".join("<li>%s</li>" % en_ligne(x, liens) for x in items), balise))
            continue
        bloc = []
        while i < len(lignes) and lignes[i].strip() and not re.match(r"^(#|>|\||```|-{3,}\s*$|\s*[-*]\s|\s*\d+\.\s)", lignes[i]):
            bloc.append(lignes[i])
            i += 1
        if bloc:
            out.append(para(bloc))
        else:
            i += 1
    return "\n".join(out)


def entete(md):
    m = re.match(r"---\n(.*?)\n---\n", md, re.S)
    meta = {}
    if m:
        for l in m.group(1).split("\n"):
            if ":" in l:
                k, v = l.split(":", 1)
                meta[k.strip()] = v.strip()
        md = md[m.end():]
    return meta, md


# --------------------------------------------------------------- les fiches

def typo(t):
    """La passe typographique du site, sans sa liste de quantités en lettres.

    Cette liste a été écrite pour les pages du site : « soixante-dix ans » y
    désigne les 69 étés de la série, et la règle le remplace par « 69 ans ».
    Appliquée à RX-03, elle changeait « une série de soixante-dix ans » en
    « 69 ans » — faux dans ce contexte. Le Grain garde ses quantités telles
    que le corpus les écrit ; seules les insécables sont posées.
    """
    out = []
    for bout, protege in typographie.morceaux(t):
        if protege:
            out.append(bout)
        else:
            masque, entites = typographie.masquer(bout)
            out.append(typographie.demasquer(typographie.unites(typographie.ponctuation(masque)), entites))
    # un titre anglais cité ne prend pas l'espace française avant le deux-points
    return re.sub(r"(Resources)&nbsp;:", r"\1:", "".join(out))


def slug_de(nom):
    return "grain-" + nom.lower()


def charger():
    fiches = []
    for f in sorted(os.listdir(SOURCE)):
        if not f.endswith(".md"):
            continue
        md = open(os.path.join(SOURCE, f), encoding="utf-8").read()
        meta, corps = entete(md)
        nom = f[:-3]
        code = meta.get("code", nom[:5])
        if code in RETENUES:
            raise SystemExit("%s est déclarée retenue et ne doit pas être dans contenu/grain/" % code)
        h1 = re.search(r"^#\s+(.*)$", corps, re.M).group(1)
        titre = re.sub(r"^[A-Z]{2}-\d{2}\s+—\s+", "", h1)
        titre = meta.get("titre_site", titre)
        chapeau = re.search(r"^\*(?!\*)(.+?)(?<!\*)\*\s*$", corps, re.M)
        if not chapeau:
            # un pattern n'a pas de chapeau : sa solution en tient lieu
            chapeau = re.search(r"^## Solution\s+\*\*(.+?)\*\*\s*$", corps, re.M)
        fiches.append(dict(nom=nom, code=code, titre=titre, meta=meta, corps=corps,
                           page=slug_de(nom if code != "DG" else "digest") + ".html",
                           resume=chapeau.group(1) if chapeau else "",
                           type=meta.get("type", "retex")))
    return fiches


def rendre(f, publiees):
    def liens(cible):
        code = cible[:5]
        if code in publiees:
            return '<a href="%s">%s</a>' % (publiees[code]["page"], code)
        return "<span class=\"renvoi-absent\" title=\"fiche non publiée\">%s</span>" % (
            code if re.match(r"[A-Z]{2}-\d{2}", code) else cible)
    corps = re.sub(r"^#\s+.*$", "", f["corps"], count=1, flags=re.M)
    corps = re.sub(r"^\*(?!\*)(.+?)(?<!\*)\*\s*$", "", corps, count=1, flags=re.M)
    corps = re.sub(r"^\s*---\s*$", "", corps, count=1, flags=re.M)
    for a, b in INTERTITRES.items():
        corps = re.sub(r"^(#{2,3})\s+%s\s*$" % re.escape(a), r"\1 " + b, corps, flags=re.M)
    h = markdown(corps, liens)
    # Les listes numérotées en gras (« **1. …** ») du format retex deviennent
    # des points repérables : la mise en page les numérote en marge.
    h = re.sub(r"<p><strong>(\d+)\. (.+?)</strong>", r'<p class="point" data-n="\1"><strong>\2</strong>', h)
    # « Contre-indications » et « Vérification » prennent leur encadré.
    h = re.sub(r"<h2>(Contre-indications|Vérification|Portée)</h2>", lambda m: '<h2 class="h-%s">%s</h2>'
               % (m.group(1).lower().replace("é", "e").replace("-", ""), m.group(1)), h)
    return h


def cartouche(f):
    m = f["meta"]
    fam = FAMILLES.get(f["type"], ("retex", f["type"]))[1]
    lignes = [("Famille", fam), ("Généricité", m.get("généricité", "—"))]
    if m.get("confiance"):
        lignes.append(("Confiance", m["confiance"]))
    lignes.append(("Statut", m.get("statut", "EXPLORÉ — production du corpus, non validée par une décision")))
    lignes.append(("Écrit le", date_fr(m.get("date", ""))))
    lignes.append(("Licence", m.get("licence", "CC BY-SA 4.0")))
    dl = "\n".join("  <div><dt>%s</dt><dd>%s</dd></div>" % (a, html.escape(b)) for a, b in lignes)
    return '<dl class="cartouche">\n%s\n</dl>' % dl


def date_fr(iso):
    if not re.match(r"\d{4}-\d{2}-\d{2}", iso):
        return iso
    y, mo, d = iso.split("-")
    mois = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
            "septembre", "octobre", "novembre", "décembre"][int(mo) - 1]
    return "%d%s %s %s" % (int(d), "er" if d == "01" else "", mois, y)


def emporter(f):
    pdf = "editions/pdf/%s.pdf" % f["page"][:-5]
    return """<div class="a-emporter">
  <p class="a-emporter-titre">À emporter</p>
  <ul>
    <li><a href="editions/{p}.html">Version paginée A5</a>{pdf}</li>
    <li><a href="contenu/grain/{n}.md">Source Markdown</a></li>
    <li><a href="relayer.html#x-{s}">Extraits à relayer</a></li>
  </ul>
  <p class="citer">Citer&nbsp;: Collectif du Domaine du Mons, «&nbsp;{t}&nbsp;», fiche {c}, {d}. {lic}.</p>
</div>""".format(p=f["page"][:-5], n=f["nom"], s=f["page"][:-5], t=html.escape(f["titre"]),
                 c=f["code"], d=date_fr(f["meta"].get("date", "")),
                 lic=html.escape(f["meta"].get("licence", "CC BY-SA 4.0")),
                 pdf=(' · <a href="%s">PDF</a>' % pdf) if os.path.exists(os.path.join(RACINE, pdf)) else "")


def fragment(f, publiees):
    fam = FAMILLES.get(f["type"], ("retex", ""))
    meta = {"titre": "%s — %s" % (f["code"], f["titre"]) if f["code"] != "DG" else f["titre"],
            "description": f["resume"] or f["titre"],
            "date": f["meta"].get("date"), "publie": f["meta"].get("publié", PUBLICATION),
            "famille_ancre": list(fam), "rail": emporter(f)}
    code = '<span class="code">%s</span> ' % f["code"] if f["code"] != "DG" else ""
    corps = """<h1>{code}{t}</h1>
<p class="chapeau">{r}</p>
{cart}
{h}
""".format(code=code, t=html.escape(f["titre"]), r=en_ligne(f["resume"], lambda x: x),
           cart=cartouche(f), h=rendre(f, publiees))
    corps = typo(corps)
    return "<!--meta\n%s\n-->\n%s" % (json.dumps(meta, ensure_ascii=False, indent=1), corps)


# ------------------------------------------------------------- l'index

def ressources(fiches):
    par = {}
    for f in fiches:
        par.setdefault(f["type"], []).append(f)
    digest = par.get("digest", [None])[0]
    blocs = ["""<h1>Ressources</h1>
<p class="chapeau">Le Grain&nbsp;: ce qui, du travail fait ici, peut servir ailleurs. Des fiches à reprendre telles quelles, avec leurs coûts réels et leurs contre-indications.</p>
<p>Chaque fiche porte son niveau de généricité et son statut. Toutes celles qui sont publiées sont <strong>génériques</strong>&nbsp;: rien n'y dépend du Domaine du Mons. Elles sont sous licence CC&nbsp;BY-SA&nbsp;4.0, disponibles en page web, en version paginée à imprimer et en Markdown.</p>
"""]
    if digest:
        blocs.append("""<div class="vedette">
  <p class="vedette-sur">Pour commencer</p>
  <h2 id="digest"><a href="{p}">{t}</a></h2>
  <p>{r}</p>
  <p>Six enquêtes, six erreurs d'une seule forme&nbsp;: un résultat propre, plausible, et faux. Les huit contrôles qui les attrapent, et trois outils prêts à l'emploi.</p>
  <p><a href="{p}">Lire le digest</a> · <a href="editions/{s}.html">version paginée</a></p>
</div>""".format(p=digest["page"], t=html.escape(digest["titre"]), r=html.escape(digest["resume"]), s=digest["page"][:-5]))
    for typ in ("retex", "pattern", "gabarit"):
        if typ not in par:
            continue
        ancre, libelle = FAMILLES[typ]
        intro = {
            "retex": "Une erreur réelle, comment elle s'est vue, et ce qui a changé depuis. Format after-action review.",
            "pattern": "Un problème récurrent, les forces en tension, une solution observée ailleurs, ses coûts et ses contre-indications.",
            "gabarit": "Un tableau vide, à copier tel quel, avec le mode d'emploi.",
        }[typ]
        cartes = []
        for f in par[typ]:
            cartes.append("""  <li>
    <p class="carte-code">{c} · {g}</p>
    <h3><a href="{p}">{t}</a></h3>
    <p>{r}</p>
    <p class="source">{d} · <a href="editions/{s}.html">à imprimer</a></p>
  </li>""".format(c=f["code"], g=f["meta"].get("généricité", ""), p=f["page"], t=html.escape(f["titre"]),
                  r=html.escape(f["resume"]), d=date_fr(f["meta"].get("date", "")), s=f["page"][:-5]))
        blocs.append('<h2 id="%s">%s</h2>\n<p>%s</p>\n<ul class="cartes">\n%s\n</ul>'
                     % (ancre, libelle, intro, "\n".join(cartes)))
    blocs.append("""<h2 id="non-publiees">Pas encore publiées</h2>
<p>Trois fiches du corpus attendent. Deux portent sur le choix de l'instrument juridique&nbsp;: une recommandation juridique ne passe du corpus au site qu'après avis professionnel, et le rendez-vous avec le notaire n'a pas eu lieu. La troisième décrit une chaîne d'outils de diagnostic territorial qui n'est pas encore distribuée publiquement.</p>
<h2 id="reprendre">Reprendre une fiche</h2>
<p>Copiez, adaptez, republiez, en citant la source et sous la même licence. Si une fiche vous a servi, <a href="nous-joindre.html">dites-le-nous</a>&nbsp;: c'est la seule mesure qui nous intéresse, et nous la notons dans le registre d'intérêt général.</p>""")
    meta = {"titre": "Ressources", "description": "Le Grain du Domaine du Mons : retours d'expérience, patterns et gabarits génériques, sous licence libre, à reprendre tels quels par d'autres collectifs."}
    return "<!--meta\n%s\n-->\n%s\n" % (json.dumps(meta, ensure_ascii=False, indent=1),
                                       typo("\n".join(blocs)))


def test():
    cas = [
        ("**a** et *b*", "<p><strong>a</strong> et <em>b</em></p>"),
        ("1 952 sur 8 340", "<p>1 952 sur 8 340</p>"),
        ("[x](https://a.b/c?d=1&e=2)", '<p><a href="https://a.b/c?d=1&amp;e=2">x</a></p>'),
        ("`SWI` et `tdb-eau`", '<p><code>SWI</code> et <a href="tdb-eau.html"><code>tdb-eau</code></a></p>'),
        ("- un\n- deux", "<ul><li>un</li><li>deux</li></ul>"),
        ("| a | b |\n|---|---|\n| c | d |", '<div class="defilant"><table class="donnees"><thead><tr><th scope="col">a</th><th scope="col">b</th></tr></thead><tbody><tr><th scope="row">c</th><td>d</td></tr></tbody></table></div>'),
        ("des 1ᵉʳ *états* 3 × 4", "<p>des 1ᵉʳ <em>états</em> 3 × 4</p>"),
    ]
    ko = 0
    for md, attendu in cas:
        r = markdown(md)
        if r != attendu:
            ko += 1
            print("  ✗ %r\n     donne   %r\n     attendu %r" % (md, r, attendu))
    print("  %s markdown : %d cas, %d échec(s)" % ("✓" if not ko else "✗", len(cas), ko))
    return 1 if ko else 0


def main():
    if "--test" in sys.argv:
        return test()
    os.makedirs(SORTIE, exist_ok=True)
    fiches = charger()
    publiees = {f["code"]: f for f in fiches}
    for f in fiches:
        open(os.path.join(SORTIE, f["page"]), "w", encoding="utf-8").write(fragment(f, publiees))
    open(os.path.join(SORTIE, "ressources.html"), "w", encoding="utf-8").write(ressources(fiches))
    json.dump([dict(slug=f["page"][:-5], page=f["page"], code=f["code"], titre=f["titre"],
                    resume=f["resume"], genericite=f["meta"].get("généricité", ""),
                    famille=FAMILLES.get(f["type"], ("retex",))[0], date=f["meta"].get("date"),
                    nom=f["nom"])
               for f in fiches],
              open(os.path.join(RACINE, "build", "grain.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("  %d fiches du Grain, index des ressources" % len(fiches))
    return 0


if __name__ == "__main__":
    sys.exit(main())
