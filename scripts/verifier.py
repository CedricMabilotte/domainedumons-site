#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contrôles d'avant-publication. Trois défauts se sont répétés, on les teste.

    python3 scripts/verifier.py

1. Identifiants dupliqués. Un <h2 id="x"> au-dessus d'un <div id="x"> fait que
   getElementById renvoie le titre, et le contenu s'injecte dans le titre.
   Quatre occurrences en deux jours, sur quatre pages différentes.
2. Fichiers de données appelés mais absents du dépôt.
3. Ressources sans numéro de version : un visiteur déjà venu garde l'ancienne.
"""
import collections, glob, os, re, sys
RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
    if fautes:
        print("\n".join("  ✗ " + x for x in fautes))
        sys.exit(1)
    print("  ✓ identifiants, versions et fichiers appelés : rien à signaler")
main()
