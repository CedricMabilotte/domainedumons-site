#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contrôles d'avant-publication. Trois défauts se sont répétés, on les teste.

    python3 scripts/verifier.py

1. Identifiants dupliqués. Un <h2 id="x"> au-dessus d'un <div id="x"> fait que
   getElementById renvoie le titre, et le contenu s'injecte dans le titre.
   Quatre occurrences en deux jours, sur quatre pages différentes.
2. Fichiers de données appelés mais absents du dépôt.
3. Ressources sans numéro de version : un visiteur déjà venu garde l'ancienne.
4. Étiquettes de croquis qui sortent du cadre. Les tailles sont en unités de
   viewBox : grossir le texte pour le rendre lisible au téléphone pousse les
   étiquettes hors du dessin, et cela ne se voit sur aucune page tant qu'on
   ne mesure pas. Ajouté le 19/09/2026 avec le passage de 13,5 à 17 px.
5. Clés appelées par une page mais absentes du JSON qu'elle charge. Ajouté le
   19/09/2026 : data/associations.json était resté en version 1 pendant trois
   jours, sans la clé « verdicts ». Les pages « Le réseau », « Les associations »
   et « Le fil commun » plantaient sur d.verdicts.retenu et restaient bloquées
   sur « … ». Rien ne le signalait : ni erreur de publication, ni page blanche.
   Un contrôle qui ne tourne pas ne protège de rien.
"""
import collections, glob, json, os, re, sys
RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Tailles de .texte-croquis, en unités de viewBox. À tenir en phase avec
# style.css : si l'une des deux bouge seule, ce contrôle ne mesure plus rien.
TAILLES_CROQUIS = {"": 17.0, "fort": 22.0, "petit": 15.0, "sur": 15.0}
# Georgia, avance moyenne ~0,50 em en bas de casse. Estimation volontairement
# généreuse : mieux vaut une alerte de trop qu'une étiquette coupée en ligne.
AVANCE = 0.50


def croquis_qui_debordent(nom, t):
    fautes = []
    for vbs, corps in re.findall(r'<svg[^>]*viewBox="([^"]+)"[^>]*>(.*?)</svg>', t, re.S):
        if "texte-croquis" not in corps:
            continue
        try:
            x0, _, largeur, _ = [float(v) for v in vbs.split()]
        except ValueError:
            continue
        for m in re.finditer(r"<text([^>]*)>(.*?)</text>", corps, re.S):
            attrs, txt = m.group(1), re.sub(r"<[^>]+>", "", m.group(2))
            px = re.search(r'x="([-\d.]+)"', attrs)
            if not px:
                continue
            cls = re.search(r'class="([^"]*)"', attrs)
            taille = TAILLES_CROQUIS[""]
            if cls:
                for c in ("fort", "petit", "sur"):
                    if c in cls.group(1).split():
                        taille = TAILLES_CROQUIS[c]
                        break
            anc = re.search(r'text-anchor="(\w+)"', attrs)
            anc = anc.group(1) if anc else "start"
            w = len(txt) * taille * AVANCE
            x = float(px.group(1))
            gauche = x - w / 2 if anc == "middle" else (x - w if anc == "end" else x)
            if gauche < x0 - 1 or gauche + w > x0 + largeur + 1:
                fautes.append("%s : l'étiquette « %s » sort du cadre du croquis "
                              "(%.0f à %.0f, cadre %.0f à %.0f)"
                              % (nom, txt[:32], gauche, gauche + w, x0, x0 + largeur))
    return sorted(set(fautes))


def aplatir(o, prefixe=""):
    """Toutes les clés d'un JSON, en notation pointée."""
    cles = set()
    if isinstance(o, dict):
        for k, v in o.items():
            cles.add(prefixe + k)
            cles |= aplatir(v, prefixe + k + ".")
    elif isinstance(o, list) and o:
        cles |= aplatir(o[0], prefixe)
    return cles


IGNORE = {"length", "map", "filter", "slice", "sort", "join", "forEach", "reverse",
          "find", "findIndex", "some", "every", "reduce", "push", "concat", "indexOf",
          "includes", "split", "replace", "trim", "toLowerCase", "toUpperCase",
          "toFixed", "toLocaleDateString", "getTime", "keys", "values", "entries"}


def sources(t):
    """Les variables affectées depuis un fichier de données, et leur fichier.
    Deux écritures, et il faut les deux — la seconde est celle des trois pages
    restées cassées trois jours en septembre 2026.
        const X = await json("data/y.json")
        [A, B] = await Promise.all([json("data/a.json"), json("data/b.json")])
    """
    paires = re.findall(r'(?:const|let|var)?\s*([A-Za-z_$][\w$]*)\s*=\s*await\s+json\("(data/[^"]+)"\)', t)
    for noms, corps in re.findall(r'\[([^\]]+)\]\s*=\s*await\s+Promise\.all\(\s*\[(.*?)\]\s*\)', t, re.S):
        v = [x.strip() for x in noms.split(",") if x.strip()]
        f = re.findall(r'json\("(data/[^"]+)"\)', corps)
        if len(v) == len(f):
            paires += list(zip(v, f))
    return paires


def cles_manquantes(nom, t):
    """Vérifie que chaque clé lue par la page existe dans le fichier publié.
    C'est le contrôle qui manquait : data/associations.json est resté en
    version 1 du 16 au 19 septembre 2026, sans la clé « verdicts ». Trois pages
    plantaient sur d.verdicts.retenu et restaient bloquées sur « … ». Ni erreur
    de publication, ni page blanche : rien ne le signalait.

    Deux règles pour ne pas accuser à tort, réglées sur les pages réelles :
    une variable liée à plusieurs fichiers est contrôlée contre leur union ;
    une variable qui sert aussi de paramètre, de destructuration ou de seconde
    déclaration n'est plus la donnée et n'est pas contrôlée du tout."""
    fautes = []
    # une variable peut être liée à plusieurs fichiers dans la même page
    par_var = {}
    for var, fichier in sources(t):
        par_var.setdefault(var, set()).add(fichier)
    for var, fichiers in par_var.items():
        dispo = set()
        for fichier in fichiers:
            chemin = os.path.join(RACINE, fichier)
            if not os.path.exists(chemin):
                dispo = None
                break
            try:
                dispo |= aplatir(json.load(open(chemin, encoding="utf-8")))
            except Exception as e:
                fautes.append("%s : %s illisible (%s)" % (nom, fichier, e))
                dispo = None
                break
        if dispo is None:          # illisible ou absent : déjà signalé plus haut
            continue                # un fichier vide, lui, donne un ensemble
                                    # vide et doit être signalé, pas sauté
        ou = " ou ".join(sorted(fichiers))
        racines = {var: ""}
        for a, b in re.findall(r'(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*'
                               + re.escape(var) + r'\.([A-Za-z_$][\w$]*)\b', t):
            racines[a] = b + "."
        for v, prefixe in racines.items():
            if ombre(v, t):
                continue
            for suite in re.findall(r'(?<![\w$.])' + re.escape(v)
                                    + r'\.([A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)?)\b', t):
                if suite.split(".")[-1] in IGNORE:
                    continue
                cle = prefixe + suite
                if cle in dispo:
                    continue
                # a.b.c absent mais a.b présent : c est une clé de contenu libre
                if "." in cle and cle.rsplit(".", 1)[0] in dispo:
                    continue
                fautes.append("%s : %s.%s appelé, absent de %s" % (nom, v, suite, ou))
    return sorted(set(fautes))


def ombre(v, t):
    """La variable sert-elle ailleurs de paramètre ou de seconde déclaration ?
    Alors ce n'est plus la donnée, et la contrôler produirait une fausse alerte
    — c'est ce qui est arrivé à la première version de ce contrôle."""
    motifs = [
        r'\(\s*' + re.escape(v) + r'\s*[,)]',          # (v) => … / (v, i) => …
        r',\s*' + re.escape(v) + r'\s*[,)]',            # (a, v) => …
        r'(?<![\w$])' + re.escape(v) + r'\s*=>',        # v => …
        r'\[\s*[\w$]*\s*,\s*' + re.escape(v) + r'\s*\]',   # [k, v] de Object.entries
        r'\bfor\s*\(\s*(?:const|let|var)\s+' + re.escape(v) + r'\b',
    ]
    declarations = len(re.findall(r'(?:const|let|var)\s+' + re.escape(v) + r'\b', t))
    return declarations > 1 or any(re.search(m, t) for m in motifs)


def main():
    fautes = []
    for f in sorted(glob.glob(os.path.join(RACINE, "*.html"))):
        nom = os.path.basename(f)
        t = open(f, encoding="utf-8").read()
        ids = re.findall(r'\sid="([^"]+)"', t)
        for i, n in collections.Counter(ids).items():
            if n > 1:
                fautes.append("%s : identifiant « %s » présent %d fois" % (nom, i, n))
        for r in re.findall(r'(?:src|href)="((?:style\.css|site\.js|tdb\.js)[^"]*)"', t):
            if "?v=" not in r:
                fautes.append("%s : %s sans numéro de version" % (nom, r))
        for d in set(re.findall(r'"(data/[a-z0-9\-\.]+|dessins/[a-z0-9\-\.]+)"', t)):
            if not os.path.exists(os.path.join(RACINE, d)):
                fautes.append("%s : %s appelé mais absent du dépôt" % (nom, d))
        fautes += cles_manquantes(nom, t)
        fautes += croquis_qui_debordent(nom, t)
    if fautes:
        print("\n".join("  ✗ " + x for x in fautes))
        sys.exit(1)
    print("  ✓ identifiants, versions, fichiers, clés et croquis : rien à signaler")
main()
