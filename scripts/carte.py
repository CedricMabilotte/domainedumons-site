#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Le fond de carte de la zone d'une heure, en SVG.

Récupère les contours communaux auprès de geo.api.gouv.fr, les simplifie, et
écrit un fond de carte statique dans dessins/zone.svg. Le site n'appelle aucune
tuile distante : la carte est un fichier du dépôt, et les lieux se posent dessus
par-dessus, côté navigateur, avec la même projection.

Usage : python3 scripts/carte.py
"""
import json, math, os, sys, urllib.request

sys.setrecursionlimit(20000)
from datetime import date

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAT, LON = 45.351433, 1.931875
RAYON = 45.0
DEPS = ["19", "23", "87", "15", "46"]
LARGEUR = 900.0
UA = {"User-Agent": "domainedumons.actitude.org/1.0"}
TOL = 0.0045          # tolérance de simplification, en degrés (~350 m)


def projeter(la, lo):
    """Projection locale : équirectangulaire centrée, suffisante sur 90 km."""
    k = math.cos(math.radians(LAT))
    return (lo - LON) * k * 111.32, (LAT - la) * 110.57      # en km, y vers le bas


def simplifier(pts, tol):
    """Douglas-Peucker, sans dépendance."""
    if len(pts) < 3:
        return pts
    dmax, idx = 0.0, 0
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    dx, dy = x2 - x1, y2 - y1
    n = math.hypot(dx, dy) or 1e-9
    for i in range(1, len(pts) - 1):
        x, y = pts[i]
        d = abs(dy * x - dx * y + x2 * y1 - y2 * x1) / n
        if d > dmax:
            dmax, idx = d, i
    if dmax > tol:
        return simplifier(pts[:idx + 1], tol)[:-1] + simplifier(pts[idx:], tol)
    return [pts[0], pts[-1]]


def main():
    zone = json.load(open(os.path.join(RACINE, "data", "zone-une-heure.json")))["communes"]
    formes = []
    for d in DEPS:
        print("  contours du %s…" % d)
        u = "https://geo.api.gouv.fr/departements/%s/communes?fields=nom,code,contour&format=json" % d
        with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=180) as r:
            c = json.load(r)
        for x in c:
            if x["code"] not in zone:
                continue
            g = x.get("contour")
            if not g:
                continue
            # on ne garde que l'enveloppe extérieure de chaque partie
            exts = [g["coordinates"][0]] if g["type"] == "Polygon" else [p[0] for p in g["coordinates"]]
            for a in exts:
                pts = [(float(lo), float(la)) for lo, la in a]
                if len(pts) > 2 and pts[0] == pts[-1]:
                    pts = pts[:-1]
                if len(pts) < 8:
                    continue
                # un anneau fermé rend Douglas-Peucker dégénéré : on le coupe en deux
                m = len(pts) // 2
                s1 = simplifier(pts[:m + 1], TOL)
                s2 = simplifier(pts[m:] + [pts[0]], TOL)
                red = s1[:-1] + s2
                if len(red) > 3:
                    formes.append((x["code"], red))
    print("  %d contours retenus" % len(formes))

    # cadre : le disque de la zone
    demi = RAYON * 1.02
    echelle = LARGEUR / (2 * demi)
    def px(la, lo):
        x, y = projeter(la, lo)
        return (x + demi) * echelle, (y + demi) * echelle
    H = LARGEUR

    chemins = []
    for code, pts in formes:
        d = []
        for i, (lo, la) in enumerate(pts):
            X, Y = px(la, lo)
            d.append("%s%.1f %.1f" % ("M" if i == 0 else "L", X, Y))
        chemins.append('<path class="commune" d="%sZ"/>' % "".join(d))

    cx, cy = px(LAT, LON)
    r = RAYON * echelle
    villes = sorted(zone.values(), key=lambda c: -c["pop"])[:14]
    marques = []
    for v in villes:
        X, Y = px(v["lat"], v["lon"])
        ancre = "end" if X > cx else "start"
        dx = -6 if X > cx else 6
        marques.append('<circle class="ville" cx="%.1f" cy="%.1f" r="2.6"/>'
                       '<text class="nom-ville" x="%.1f" y="%.1f" text-anchor="%s">%s</text>'
                       % (X, Y, X + dx, Y + 3.5, ancre, v["nom"]))

    svg = ('<svg viewBox="0 0 %.0f %.0f" xmlns="http://www.w3.org/2000/svg" class="carte-zone" '
           'role="img" aria-label="Carte des communes situées à une heure de route du Domaine du Mons">\n'
           '  <g class="communes">\n    %s\n  </g>\n'
           '  <circle class="limite" cx="%.1f" cy="%.1f" r="%.1f"/>\n'
           '  <g class="villes">\n    %s\n  </g>\n'
           '  <g class="centre"><circle cx="%.1f" cy="%.1f" r="4.5"/>'
           '<text x="%.1f" y="%.1f">le Mons</text></g>\n'
           '</svg>\n' % (LARGEUR, H, "\n    ".join(chemins), cx, cy, r,
                         "\n    ".join(marques), cx, cy, cx + 9, cy + 4))
    os.makedirs(os.path.join(RACINE, "dessins"), exist_ok=True)
    f = os.path.join(RACINE, "dessins", "zone.svg")
    open(f, "w", encoding="utf-8").write(svg)
    json.dump({"largeur": LARGEUR, "hauteur": H, "centre": [LAT, LON], "rayon_km": RAYON,
               "demi_km": demi, "echelle_px_par_km": echelle,
               "projection": "équirectangulaire locale centrée sur le lieu",
               "calcule_le": date.today().isoformat()},
              open(os.path.join(RACINE, "data", "carte-zone.json"), "w"),
              ensure_ascii=False, separators=(",", ":"))
    print("  %s : %d octets" % (f, os.path.getsize(f)))


if __name__ == "__main__":
    main()
