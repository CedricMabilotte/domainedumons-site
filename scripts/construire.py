#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reconstruit le site depuis le dépôt, et refuse de finir si un contrôle échoue.

    python3 scripts/construire.py

Trois étapes, dans cet ordre :
  1. scripts/page-carte.py   engendre build/corps-carte.html depuis data/
  2. scripts/appliquer.py    pose les quatre pages du réseau et les versions
  3. scripts/verifier.py     contrôle identifiants, versions, fichiers et clés

L'étape 3 n'est pas facultative. Un contrôle qui ne tourne pas ne protège de
rien : data/associations.json est resté trois jours en version 1, sans la clé
« verdicts », et trois pages sont restées bloquées sur « … » sans qu'aucune
publication n'échoue.

Le relief ne se recalcule pas ici : scripts/relief.py demande les dalles LiDAR
et met une minute. Il se lance à la main quand la méthode change.
"""
import os
import subprocess
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def etape(titre, *commande):
    print("\n\033[1m%s\033[0m" % titre)
    r = subprocess.run([sys.executable] + list(commande), cwd=RACINE)
    if r.returncode != 0:
        print("\n  ✗ échec de l'étape « %s » — rien n'est publié." % titre)
        sys.exit(r.returncode)


def main():
    os.makedirs(os.path.join(RACINE, "build"), exist_ok=True)
    etape("1. la page de cartographie", "scripts/page-carte.py",
          os.path.join(RACINE, "build"))
    etape("2. les pages du réseau", "scripts/appliquer.py")
    etape("3. les contrôles d'avant-publication", "scripts/verifier.py")
    print("\n  ✓ site reconstruit et contrôlé.")


if __name__ == "__main__":
    main()
