#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Migration du 24/09/2026 : des pages complètes vers des fragments.

A servi une fois. Gardé dans le dépôt parce que ce qui ne vit pas dans le
dépôt se perd, et qu'il documente comment les pages ont été découpées.

Jusqu'au 24/09, chaque page portait sa copie du bandeau, de la navigation et
du pied : dix-neuf copies, dont quinze écrites à la main. Changer une entrée
de menu voulait dire éditer dix-neuf fichiers, et trois d'entre elles avaient
déjà divergé. Depuis, une page est un fragment dans contenu/pages/, et
scripts/gabarit.py l'habille.

    python3 scripts/migrer.py      écrit contenu/pages/*.html depuis *.html

Ce que la migration retire du corps, parce que le gabarit le produit :
  - le lien « ← Tableaux de bord » (remplacé par le fil d'Ariane) ;
  - le bloc <noscript> « Sans JavaScript », dont les dates de relevé étaient
    écrites à la main et fausses sur sept pages le 24/09 : il devient la
    directive <!--#sans-js data/x.json …--> et se date depuis les fichiers.
"""
import json, os, re, sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SORTIE = os.path.join(RACINE, "contenu", "pages")
PAGES_RESEAU = {
    # page : (corps, script) — ces quatre pages étaient posées par appliquer.py
    "reseau.html": ("scripts/pages/corps-reseau.html", "scripts/pages/js-reseau.js"),
    "reseau-carte.html": ("build/corps-carte.html", "scripts/pages/js-carte.js"),
    "reseau-fil.html": ("scripts/pages/corps-fil.html", None),
    "reseau-associations.html": ("scripts/pages/corps-assos.html", "scripts/pages/js-assos.js"),
}


def sans_js(corps):
    """Remplace le <noscript> par une directive qui se date seule."""
    def rempl(m):
        fichiers = re.findall(r'href="(data/[^"]+)"', m.group(0))
        return "<!--#sans-js %s-->" % " ".join(fichiers) if fichiers else m.group(0)
    return re.sub(r"<noscript>.*?</noscript>", rempl, corps, count=1, flags=re.S)


def main():
    os.makedirs(SORTIE, exist_ok=True)
    for f in sorted(os.listdir(RACINE)):
        if not f.endswith(".html") or f.startswith(("404", "grain-")):
            continue
        t = open(os.path.join(RACINE, f), encoding="utf-8").read()
        if "<main" not in t:
            continue
        titre = re.search(r"<title>(.*?)</title>", t, re.S).group(1)
        titre = re.sub(r"\s*—\s*Domaine du Mons.*$", "", titre).strip()
        if f == "index.html":
            titre = "Le lieu"
        desc = re.search(r'<meta name="description" content="(.*?)">', t, re.S).group(1)
        classe = re.search(r"<main([^>]*)>", t).group(1)
        classe = re.search(r'class="([^"]*)"', classe)
        meta = {"titre": titre, "description": desc}
        if classe:
            meta["classe"] = classe.group(1)
        if f in PAGES_RESEAU:
            corps_src, js = PAGES_RESEAU[f]
            if corps_src.startswith("build/"):
                corps = "<!--#inclure %s-->" % corps_src
            else:
                corps = open(os.path.join(RACINE, corps_src), encoding="utf-8").read()
            scripts = ""
            if js:
                scripts = '<script src="tdb.js"></script>\n<!--#script %s-->\n' % js
            if f == "reseau-carte.html":
                meta["leaflet"] = True
        else:
            corps = t[t.index(">", t.index("<main")) + 1:t.index("</main>")]
            fin = t[t.index("</footer>") + len("</footer>"):]
            fin = re.sub(r'<script src="site\.js[^"]*"></script>', "", fin)
            fin = fin.replace("</body>", "").replace("</html>", "")
            scripts = re.sub(r'(src="(?:tdb|site)\.js)\?v=\d+', r"\1", fin).strip() + "\n"
        corps = re.sub(r'\s*<p class="retour">.*?</p>\s*', "\n", corps, count=1, flags=re.S)
        corps = sans_js(corps).strip() + "\n"
        entete = "<!--meta\n%s\n-->\n" % json.dumps(meta, ensure_ascii=False, indent=1)
        sortie = entete + corps + ("<!--scripts-->\n" + scripts if scripts.strip() else "")
        open(os.path.join(SORTIE, f), "w", encoding="utf-8").write(sortie)
        print("  %-26s %6d octets" % (f, len(sortie.encode())))


if __name__ == "__main__":
    sys.exit(main())
