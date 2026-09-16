#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Le fond routier de la zone, sans aucune tuile.

Une carte routière suppose d'habitude un fournisseur de tuiles, donc l'adresse
de chaque visiteur et la suite de ce qu'il regarde envoyées à un tiers. On prend
l'autre chemin : extraire les axes structurants au moment de la publication, les
alléger, et les servir depuis le dépôt comme les contours.

Ce qu'on perd, et qui doit être écrit sur la carte : les petites routes, les
noms de rue, le bâti.

LICENCE — les données viennent d'OpenStreetMap, sous ODbL. Elles restent dans
LEUR PROPRE FICHIER et ne sont superposées qu'au rendu. Fusionnées avec les
nôtres dans une même table, elles en feraient une base dérivée et toute la
table basculerait sous ODbL.

Dérivé de carto-territoire (carto/routes.py).
    python3 scripts/fond-routier.py
"""
import json, math, os, sys, time, urllib.parse, urllib.request

sys.path.insert(0, "/home/ced/ddm-carto")
from carto import routes  # noqa: E402

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICI = (45.35137, 1.93221)
RAYON = 45.0
ZOOM_MAX = 12          # la carte est bornée à 12 : inutile d'aller plus fin


def bbox(centre, rayon_km):
    dlat = rayon_km / 111.12
    dlon = rayon_km / (111.32 * math.cos(math.radians(centre[0])))
    return (centre[0] - dlat, centre[1] - dlon,
            centre[0] + dlat, centre[1] + dlon)


def metres_par_pixel(zoom, lat):
    return 40075016.686 * math.cos(math.radians(lat)) / (2 ** (zoom + 8))


def simplifier(pts, tol, mini=2):
    """Visvalingam. Les routes n'ont pas de topologie partagée à préserver :
    chaque trait se simplifie seul, sans risque de fente entre voisins."""
    if len(pts) <= mini:
        return list(pts)
    aire = lambda a, b, c: abs((b[0]-a[0])*(c[1]-a[1])-(c[0]-a[0])*(b[1]-a[1]))/2.0
    seuil = tol * tol
    p = list(pts)
    while len(p) > mini:
        ai = [(aire(p[i-1], p[i], p[i+1]), i) for i in range(1, len(p)-1)]
        if not ai:
            break
        m, i = min(ai)
        if m > seuil:
            break
        del p[i]
    return p


def main():
    b = bbox(ICI, RAYON)
    print("emprise : %.3f,%.3f → %.3f,%.3f" % b)
    print("interrogation d'Overpass, par morceaux…")
    # Une seule requête sur toute l'emprise fait couper la connexion : les
    # instances sont bénévoles et coupent au-delà de quelques mégaoctets. On
    # découpe donc, et on marque une pause entre deux appels — c'est une
    # ressource communautaire, pas un service.
    t0 = time.time()
    elements, vus = [], set()
    N = 3
    dlat = (b[2] - b[0]) / N
    dlon = (b[3] - b[1]) / N
    for i in range(N):
        for j in range(N):
            case = (b[0] + i*dlat, b[1] + j*dlon,
                    b[0] + (i+1)*dlat, b[1] + (j+1)*dlon)
            r = routes.extraire(case, jusqua="departementale")
            neufs = 0
            for el in r.get("elements", []):
                if el.get("id") in vus:
                    continue          # un chemin à cheval sort dans deux cases
                vus.add(el.get("id")); elements.append(el); neufs += 1
            print("    case %d/%d : %d chemins (%d nouveaux)"
                  % (i*N + j + 1, N*N, len(r.get("elements", [])), neufs))
            time.sleep(2)
    rep = {"elements": elements}
    print("  %d chemins uniques en %ds" % (len(elements), time.time()-t0))

    fc = routes.en_geojson(rep)
    avant = sum(len(f["geometry"]["coordinates"]) for f in fc["features"])
    fc = routes.fusionner(fc)
    print("  %d tronçons recollés en %d traits" % (len(rep.get("elements", [])),
                                                   len(fc["features"])))

    tol = metres_par_pixel(ZOOM_MAX, ICI[0]) * 0.5 / 111120.0
    dec = 4
    apres = 0
    for f in fc["features"]:
        s = simplifier(f["geometry"]["coordinates"], tol)
        f["geometry"]["coordinates"] = [[round(x, dec), round(y, dec)] for x, y in s]
        apres += len(s)
    print("  sommets : %d → %d (%d %% retirés)" % (avant, apres, 100 - 100*apres//max(1, avant)))

    par_rang = {}
    for f in fc["features"]:
        r = f["properties"]["rang"]
        par_rang[r] = par_rang.get(r, 0) + 1
    fc["attribution"] = "© les contributeurs OpenStreetMap"
    fc["licence"] = "ODbL"
    fc["note"] = ("Axes structurants — autoroutes, nationales, départementales. "
                  "Ni petites routes, ni noms de rue, ni bâti : c'est le prix "
                  "d'un fond servi par le dépôt plutôt que par un fournisseur "
                  "de tuiles. Simplifié pour un affichage jusqu'au zoom %d."
                  % ZOOM_MAX)
    fc["extrait_le"] = time.strftime("%Y-%m-%d")
    fc["par_rang"] = par_rang

    chemin = os.path.join(RACINE, "data/zone-routes.geojson")
    json.dump(fc, open(chemin, "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    print("  data/zone-routes.geojson :", os.path.getsize(chemin), "octets")
    print("  par rang :", par_rang)


if __name__ == "__main__":
    main()
