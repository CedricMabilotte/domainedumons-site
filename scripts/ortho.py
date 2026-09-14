#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Le même carré de terrain, à deux époques.

Récupère la photographie aérienne ancienne et l'orthophotographie actuelle
sur la même emprise, autour du chemin du Mons, et les enregistre en deux
images comparables. Le vol ancien disponible ici date du 30 juillet 1959.

Usage : python3 scripts/ortho.py [taille_m]
"""
import json, os, sys, urllib.request
from datetime import date
from PIL import Image
import io

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
X0, Y0 = 616363.0, 6473015.0
TAILLE = int(sys.argv[1]) if len(sys.argv) > 1 else 900
PX = 900
COUCHES = [
    ("1959", "ORTHOIMAGERY.ORTHOPHOTOS.1950-1965", "Vol du 30 juillet 1959"),
    ("1972", "ORTHOIMAGERY.ORTHOPHOTOS.1965-1980", "Vol de 1972"),
    ("auj", "ORTHOIMAGERY.ORTHOPHOTOS", "Orthophotographie actuelle"),
]
WMS = ("https://data.geopf.fr/wms-r?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&LAYERS=%s"
       "&FORMAT=image/png&CRS=EPSG:2154&STYLES=&BBOX=%d,%d,%d,%d&WIDTH=%d&HEIGHT=%d")


def main():
    h = TAILLE // 2
    os.makedirs(os.path.join(RACINE, "dessins"), exist_ok=True)
    meta = {"emprise_m": TAILLE, "centre_l93": [X0, Y0], "calcule_le": date.today().isoformat(),
            "source": "Géoplateforme IGN, photographies aériennes", "vues": []}
    for cle, couche, libelle in COUCHES:
        u = WMS % (couche, X0 - h, Y0 - h, X0 + h, Y0 + h, PX, PX)
        print("  %s…" % libelle)
        with urllib.request.urlopen(urllib.request.Request(
                u, headers={"User-Agent": "domainedumons.actitude.org/1.0"}), timeout=180) as r:
            brut = r.read()
        im = Image.open(io.BytesIO(brut)).convert("RGB")
        ext = im.convert("L").getextrema()
        if ext[0] == ext[1]:
            print("    aucune couverture ici, image ignorée")
            continue
        f = os.path.join(RACINE, "dessins", "ortho-%s.jpg" % cle)
        im.save(f, "JPEG", quality=72, optimize=True, progressive=True)
        meta["vues"].append({"cle": cle, "libelle": libelle,
                             "fichier": "dessins/ortho-%s.jpg" % cle,
                             "poids_ko": round(os.path.getsize(f) / 1024)})
        print("    %s, %d Ko" % (f, os.path.getsize(f) / 1024))
    json.dump(meta, open(os.path.join(RACINE, "data", "ortho.json"), "w"),
              ensure_ascii=False, separators=(",", ":"))


if __name__ == "__main__":
    main()
