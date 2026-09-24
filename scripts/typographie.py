#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Passe typographique française sur les pages écrites à la main.

    python3 scripts/typographie.py            contrôle et n'écrit rien
    python3 scripts/typographie.py --poser    applique
    python3 scripts/typographie.py --test     s'éprouve sur des cas connus

Trois règles, et rien d'autre :

  1. Espace insécable devant « ; : ? ! » et à l'intérieur des guillemets
     français. C'est la règle de l'Imprimerie nationale, et sans elle un point
     d'interrogation se retrouve seul en début de ligne au téléphone.
  2. Espace insécable entre un nombre et son unité, et devant le signe %.
     « 45 km » coupé en fin de ligne se lit « 45 » puis « km ».
  3. Les quantités écrites en toutes lettres passent en chiffres. Une page qui
     écrit « 6,7 km » puis « quatorze kilomètres » dans la même phrase donne
     l'impression d'un texte rédigé plutôt que relevé.

Ce qu'elle ne touche pas : le contenu des balises <script>, <style> et <svg>,
les attributs, et les fichiers engendrés (reseau-carte.html et les pages du
réseau, qui se refont depuis scripts/pages/). La prose qui vit dans des
chaînes JavaScript est signalée mais pas modifiée : la corriger à l'aveugle
casserait une échappement un jour ou l'autre.

La passe est idempotente : la relancer ne change rien. C'est éprouvé par
--test, parce qu'une passe typographique non idempotente empile les insécables
à chaque exécution sans que personne ne le voie.
"""
import glob
import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NBSP = "&nbsp;"

# Les pages engendrées se refont depuis scripts/pages/ : les corriger ici
# serait perdu à la première reconstruction.
ENGENDREES = {"reseau.html", "reseau-carte.html", "reseau-fil.html",
              "reseau-associations.html"}

UNITES = (r"km/h|kWh/kWc|kWc|kWh|m³|m²|km²|ha|km|cm|mm|m|°C|°|%|€|"
          r"habitants|habitant|jours|jour|mois|ans|an|heures|heure|minutes|minute|"
          r"litres|litre|l/s|g/kg|cmol/kg|DJU|°Cj|°C·j")

# Les quantités en toutes lettres relevées sur le site, avec leur unité.
# Liste fermée et explicite : un remplacement automatique de tous les nombres
# écrits en lettres abîmerait « les Trois Glorieuses » ou « un lieu ».
CHIFFRES = [
    (r"\bquatre-vingts centimètres\b", "0,80&nbsp;m"),
    (r"\bcinquante centimètres\b", "50&nbsp;cm"),
    (r"\bquarante-huit heures\b", "48&nbsp;heures"),
    (r"\bQuarante-huit heures\b", "48&nbsp;heures"),
    (r"\bsoixante-dix étés\b", "69 étés"),
    (r"\bsoixante-dix ans\b", "69&nbsp;ans"),
    (r"\bSoixante-dix ans\b", "69&nbsp;ans"),
    (r"\bquatorze kilomètres\b", "14&nbsp;km"),
    (r"\bquatorze ans\b", "14&nbsp;ans"),
    (r"\bQuatorze ans\b", "14&nbsp;ans"),
    (r"\bquatre cents mètres\b", "400&nbsp;m"),
    (r"\bhuit cents mètres\b", "800&nbsp;m"),
    (r"\bcinq kilomètres\b", "5&nbsp;km"),
    (r"\bneuf kilomètres\b", "9&nbsp;km"),
    (r"\bsix kilomètres\b", "6&nbsp;km"),
    (r"\bcent mètres\b", "100&nbsp;m"),
    (r"\bquinze mètres\b", "15&nbsp;m"),
    (r"\bdeux mètres\b", "2&nbsp;m"),
    (r"\btrois mètres\b", "3&nbsp;m"),
    (r"\bdix mètres\b", "10&nbsp;m"),
    (r"\bsix centimètres\b", "6&nbsp;cm"),
    (r"\bdix jours\b", "10&nbsp;jours"),
    (r"\bvingt jours\b", "20&nbsp;jours"),
    (r"\btrente à soixante jours\b", "30 à 60&nbsp;jours"),
    (r"\btrente années\b", "30&nbsp;années"),
    (r"\bquinze ans\b", "15&nbsp;ans"),
    (r"\bune trentaine d'euros\b", "environ 30&nbsp;€"),
    (r"\bune vingtaine d'euros\b", "environ 20&nbsp;€"),
    (r"\btrente euros\b", "30&nbsp;€"),
    (r"\bun kilomètre deux cents\b", "1,2&nbsp;km"),
]


def morceaux(t):
    """Découpe en (texte, protégé). Le protégé n'est jamais touché : balises,
    attributs, scripts, styles et tracés SVG."""
    hors = re.compile(r"(<script\b.*?</script>|<style\b.*?</style>|<svg\b.*?</svg>|<[^>]+>)",
                      re.S | re.I)
    pos, out = 0, []
    for m in hors.finditer(t):
        if m.start() > pos:
            out.append((t[pos:m.start()], False))
        out.append((m.group(0), True))
        pos = m.end()
    if pos < len(t):
        out.append((t[pos:], False))
    return out


SENTINELLE = "\x00"


def masquer(s):
    """Met les entités HTML à l'abri. Sans cela, le « ; » qui ferme &nbsp;
    est lu comme une ponctuation et reçoit son propre insécable : la passe
    empile alors une entité de plus à chaque exécution, sans que personne ne
    le voie. C'est le défaut trouvé par --test à la première écriture."""
    trouvees = []

    def prendre(m):
        trouvees.append(m.group(0))
        return SENTINELLE + str(len(trouvees) - 1) + SENTINELLE

    return re.sub(r"&[a-zA-Z][a-zA-Z0-9]*;|&#\d+;", prendre, s), trouvees


def demasquer(s, trouvees):
    return re.sub(SENTINELLE + r"(\d+)" + SENTINELLE,
                  lambda m: trouvees[int(m.group(1))], s)


def ponctuation(s):
    # devant ; : ? ! — le caractère d'avant doit être du texte, jamais une
    # entité masquée ni une espace déjà posée
    s = re.sub(r"(?<=[\w»)\]%\.\u00e0-\u00ff])[ \u00a0]?(?=[;:?!](?:\s|$|<))", NBSP, s)
    # guillemets français, sauf si l'insécable est déjà là
    s = re.sub(r"«[ \u00a0]?(?=[^\s" + SENTINELLE + r"])", "«" + NBSP, s)
    s = re.sub(r"(?<=[^\s" + SENTINELLE + r"])[ \u00a0]?»", NBSP + "»", s)
    return s


def unites(s):
    """Nombre et unité ne se séparent pas en fin de ligne."""
    s = re.sub(r"(\d(?:[ \u00a0]\d{3})*(?:,\d+)?)[ ](?=(?:%s)\b)" % UNITES,
               lambda m: m.group(1) + NBSP, s)
    s = re.sub(r"(\d(?:[ \u00a0]\d{3})*(?:,\d+)?)[ ](?=%)", lambda m: m.group(1) + NBSP, s)
    return s


def lettres(s):
    """Les quantités en toutes lettres passent en chiffres."""
    for motif, remplacement in CHIFFRES:
        s = re.sub(motif, remplacement, s)
    return s


def passe(t):
    """La passe complète, sur les seuls morceaux de texte."""
    out = []
    for bout, protege in morceaux(t):
        if protege:
            out.append(bout)
        else:
            # lettres() d'abord, et le masquage ensuite : elle pose
            # elle-même des &nbsp; qui doivent être protégés comme les autres
            masque, entites = masquer(lettres(bout))
            masque = unites(ponctuation(masque))
            out.append(demasquer(masque, entites))
    return "".join(out)


def prose_dans_les_scripts(nom, t):
    """Signale, sans y toucher, les quantités en lettres restées dans du JS."""
    trouves = []
    for bloc in re.findall(r"<script\b.*?</script>", t, re.S | re.I):
        for motif, _ in CHIFFRES:
            for m in re.finditer(motif, bloc):
                trouves.append("%s : « %s » dans un script, à reprendre à la main"
                               % (nom, m.group(0)))
    return sorted(set(trouves))


def test():
    cas = [
        ("<p>Il y a 45 km et 12 %.</p>",
         "<p>Il y a 45&nbsp;km et 12&nbsp;%.</p>"),
        ("<p>Trois choses : la première ; la deuxième ?</p>",
         "<p>Trois choses&nbsp;: la première&nbsp;; la deuxième&nbsp;?</p>"),
        ("<p>Il dit « bonjour » ici.</p>",
         "<p>Il dit «&nbsp;bonjour&nbsp;» ici.</p>"),
        ("<p>dans un rayon de quatorze kilomètres</p>",
         "<p>dans un rayon de 14&nbsp;km</p>"),
        # ce qui ne doit surtout pas bouger
        ('<path d="M300.9 321.2C299.4 324.2"/>', '<path d="M300.9 321.2C299.4 324.2"/>'),
        ('<a href="x.html?a=1">45 km</a>', '<a href="x.html?a=1">45&nbsp;km</a>'),
        ('<script>var a = "45 km";</script>', '<script>var a = "45 km";</script>'),
        ("<p>déjà 45&nbsp;km et 12&nbsp;%.</p>", "<p>déjà 45&nbsp;km et 12&nbsp;%.</p>"),
        # une quantité convertie, suivie d'une ponctuation : la passe ne doit
        # pas insérer d'insécable dans l'entité qu'elle vient de poser
        ("<p>un rayon de quatorze kilomètres : voilà</p>",
         "<p>un rayon de 14&nbsp;km&nbsp;: voilà</p>"),
        ("<p>3 000 habitants et 1 234,5 m</p>", "<p>3 000&nbsp;habitants et 1 234,5&nbsp;m</p>"),
    ]
    fautes = 0
    for avant, attendu in cas:
        obtenu = passe(avant)
        if obtenu != attendu:
            fautes += 1
            print("  ✗ %r\n      attendu %r\n      obtenu  %r" % (avant, attendu, obtenu))
        # idempotence : la seconde passe ne change rien
        if passe(obtenu) != obtenu:
            fautes += 1
            print("  ✗ NON IDEMPOTENT sur %r → %r" % (obtenu, passe(obtenu)))
    if fautes:
        print("\n  %d cas en échec." % fautes)
        return 1
    print("  ✓ %d cas, idempotence comprise." % len(cas))
    return 0


def main():
    if "--test" in sys.argv:
        return test()
    poser = "--poser" in sys.argv
    # Depuis le 24/09/2026, les pages de la racine sont toutes engendrées par
    # scripts/gabarit.py : la passe porte sur les sources, dans contenu/.
    fichiers = sorted(glob.glob(os.path.join(RACINE, "contenu", "pages", "*.html")))
    fichiers += sorted(glob.glob(os.path.join(RACINE, "contenu", "modules", "*.html")))
    changes, signale = 0, []
    for f in fichiers:
        nom = os.path.relpath(f, RACINE)
        t = open(f, encoding="utf-8").read()
        t2 = passe(t)
        signale += prose_dans_les_scripts(nom, t2)
        if t2 != t:
            changes += 1
            n = sum(1 for a, b in zip(t.split(), t2.split()) if a != b)
            print("  %-34s %d mot(s) touché(s)" % (nom, n))
            if poser:
                open(f, "w", encoding="utf-8").write(t2)
    print("\n  %d fichier(s) %s" % (changes, "corrigé(s)" if poser else "à corriger"))
    if signale:
        print("\n  À reprendre à la main — la prose dans les scripts n'est pas touchée :")
        for s in signale:
            print("    ·", s)
    if not poser and changes:
        print("\n  Relancer avec --poser pour appliquer.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
