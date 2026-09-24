#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reconstruit le site depuis le dépôt, et refuse de finir si un contrôle échoue.
    python3 scripts/construire.py
Six étapes, dans cet ordre :
  1. scripts/page-carte.py   engendre build/corps-carte.html depuis data/
  2. scripts/grain.py        les fiches du Grain et la page des ressources
  3. scripts/partage.py      les extraits à relayer, chiffres relus dans data/
  4. scripts/editions.py     les éditions paginées et les planches de visuels
  5. scripts/gabarit.py      habille tous les fragments, flux Atom, plan du site
  6. scripts/verifier.py     contrôle identifiants, versions, fichiers, clés,
                             liens internes, métadonnées de partage
L'étape 6 n'est pas facultative. Un contrôle qui ne tourne pas ne protège de
rien : data/associations.json est resté trois jours en version 1, sans la clé
« verdicts », et trois pages sont restées bloquées sur « … » sans qu'aucune
publication n'échoue.

Ce qui ne se fait pas ici, parce que ça demande un navigateur ou le réseau :
  - python3 scripts/editions.py --rendre   PDF des éditions et PNG des visuels
    (Chromium + playwright) — à relancer quand un texte publié change ;
  - python3 scripts/relief.py              demande les dalles LiDAR, une minute.

Les pages de la racine sont toutes engendrées depuis le 24/09/2026 : on les
modifie dans contenu/pages/, jamais à la racine.
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
    os.makedirs(os.path.join(RACINE, "build", "pages"), exist_ok=True)
    etape("1. la page de cartographie", "scripts/page-carte.py",
          os.path.join(RACINE, "build"))
    etape("2. le Grain", "scripts/grain.py")
    etape("3. les extraits à relayer", "scripts/partage.py")
    etape("4. les éditions paginées et les visuels", "scripts/editions.py")
    etape("5. les pages", "scripts/gabarit.py")
    etape("6. les contrôles d'avant-publication", "scripts/verifier.py")
    print("\n  ✓ site reconstruit et contrôlé.")


if __name__ == "__main__":
    main()
