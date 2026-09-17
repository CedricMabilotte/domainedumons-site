#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Le fond de carte, sans aucune tuile : routes, eau, toponymes.

Les DONNÉES d'OpenStreetMap sont libres ; ses SERVEURS DE TUILES sont une
infrastructure tierce comme une autre. Changer de fournisseur de tuiles ne
change donc rien à ce qui part du navigateur du visiteur, seulement le
destinataire. La seule façon de ne rien envoyer est que le fond vienne de notre
propre domaine — c'est ce que fait ce script : mêmes données, reprises au
moment de la publication, servies par le dépôt.

Ce qu'on n'aura pas : le bâti, les noms de rue, le relief.

LICENCE — ODbL. Chaque couche reste dans SON PROPRE FICHIER et n'est superposée
qu'au rendu. Attribution « © les contributeurs OpenStreetMap » obligatoire.

    python3 scripts/fond-local.py toponymes|eau|routes-fines
"""
import json, math, os, sys, time, urllib.parse, urllib.request

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OVERPASS = "https://overpass-api.de/api/interpreter"
UA = "carto-territoire/0.4 (extraction au build, usage unique)"
ICI, RAYON, ZOOM_MAX = (45.35137, 1.93221), 45.0, 13

RANGS_LIEU = {"city": 1, "town": 2, "village": 3, "hamlet": 4,
              "isolated_dwelling": 5, "locality": 5, "farm": 5}


def bbox():
    dlat = RAYON / 111.12
    dlon = RAYON / (111.32 * math.cos(math.radians(ICI[0])))
    return (ICI[0] - dlat, ICI[1] - dlon, ICI[0] + dlat, ICI[1] + dlon)


def appel(req, essais=3):
    for e in range(essais):
        try:
            r = urllib.request.Request(
                OVERPASS, data=urllib.parse.urlencode({"data": req}).encode(),
                headers={"User-Agent": UA})
            with urllib.request.urlopen(r, timeout=240) as rep:
                return json.loads(rep.read().decode("utf-8"))
        except Exception as ex:
            if e == essais - 1:
                raise
            print("      (reprise : %s)" % str(ex)[:60])
            time.sleep(8 * (e + 1))


def cases(n):
    s, o, nn, e = bbox()
    dlat, dlon = (nn - s) / n, (e - o) / n
    return [(s + i * dlat, o + j * dlon, s + (i + 1) * dlat, o + (j + 1) * dlon)
            for i in range(n) for j in range(n)]


def collecter(gabarit, n, pause=2.0):
    """Une requête sur toute l'emprise fait couper la connexion : les instances
    rendent quelques mégaoctets puis lâchent. On découpe, et on marque une
    pause — c'est une ressource communautaire, pas un service."""
    vus, out = set(), []
    liste = cases(n)
    for i, c in enumerate(liste, 1):
        rep = appel(gabarit % c)
        neufs = 0
        for el in rep.get("elements", []):
            k = (el.get("type"), el.get("id"))
            if k in vus:
                continue
            vus.add(k); out.append(el); neufs += 1
        print("    case %d/%d : %d objets (%d nouveaux)"
              % (i, len(liste), len(rep.get("elements", [])), neufs))
        time.sleep(pause)
    return out


def km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (ICI[0], ICI[1], a, b))
    h = (math.sin((la2 - la1) / 2) ** 2
         + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2)
    return 2 * 6371.0088 * math.asin(math.sqrt(h))


def aire(a, b, c):
    return abs((b[0]-a[0])*(c[1]-a[1])-(c[0]-a[0])*(b[1]-a[1])) / 2.0


def simplifier(pts, tol, mini=2):
    if len(pts) <= mini:
        return list(pts)
    seuil, p = tol * tol, list(pts)
    while len(p) > mini:
        ai = [(aire(p[i-1], p[i], p[i+1]), i) for i in range(1, len(p)-1)]
        if not ai:
            break
        m, i = min(ai)
        if m > seuil:
            break
        del p[i]
    return p


def tolerance():
    return (40075016.686 * math.cos(math.radians(ICI[0]))
            / (2 ** (ZOOM_MAX + 8))) * 0.5 / 111120.0


def ecrire(fc, nom, note):
    fc["attribution"] = "© les contributeurs OpenStreetMap"
    fc["licence"] = "ODbL"
    fc["extrait_le"] = time.strftime("%Y-%m-%d")
    fc["note"] = note
    c = os.path.join(RACINE, "data", nom)
    json.dump(fc, open(c, "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    import subprocess
    gz = subprocess.run(["bash", "-c", "gzip -c %s | wc -c" % c],
                        capture_output=True, text=True).stdout.strip()
    print("  data/%s : %d octets bruts, %s compressés, %d objets"
          % (nom, os.path.getsize(c), gz, len(fc["features"])))


# --------------------------------------------------------------- toponymes
def toponymes():
    gab = ('[out:json][timeout:180];(node["place"~"^(%s)$"]["name"]'
           "(%%f,%%f,%%f,%%f););out body;" % "|".join(RANGS_LIEU))
    pts = []
    for el in collecter(gab, 2):
        t = el.get("tags") or {}
        if not t.get("name") or el.get("lat") is None:
            continue
        if km(el["lat"], el["lon"]) > RAYON + 1.5:
            continue
        pop = t.get("population")
        try:
            pop = int(str(pop).replace(" ", "")) if pop else None
        except ValueError:
            pop = None
        pts.append({"type": "Feature",
                    "properties": {"nom": t["name"], "genre": t.get("place"),
                                   "rang": RANGS_LIEU.get(t.get("place"), 5),
                                   "pop": pop},
                    "geometry": {"type": "Point",
                                 "coordinates": [round(el["lon"], 5),
                                                 round(el["lat"], 5)]}})
    pts.sort(key=lambda f: (f["properties"]["rang"], -(f["properties"]["pop"] or 0)))
    par = {}
    for f in pts:
        g = f["properties"]["genre"]; par[g] = par.get(g, 0) + 1
    print("  par genre :", par)
    ecrire({"type": "FeatureCollection", "features": pts}, "zone-toponymes.geojson",
           "Villes, bourgs, villages et hameaux. Affichés par paliers de zoom : "
           "Leaflet n'écarte pas les étiquettes, il les empile.")


# --------------------------------------------------------------------- eau
def eau():
    gab = ('[out:json][timeout:180];('
           'way["natural"="water"](%(s)f,%(o)f,%(n)f,%(e)f);'
           'way["waterway"~"^(river|canal)$"](%(s)f,%(o)f,%(n)f,%(e)f););'
           "out geom;")
    vus, traits = set(), []
    liste = cases(4)
    for i, c in enumerate(liste, 1):
        rep = appel(gab % {"s": c[0], "o": c[1], "n": c[2], "e": c[3]})
        neufs = 0
        for el in rep.get("elements", []):
            k = (el.get("type"), el.get("id"))
            if k in vus:
                continue
            vus.add(k)
            geo = el.get("geometry")
            if not geo or len(geo) < 2:
                continue
            t = el.get("tags") or {}
            co = [[p["lon"], p["lat"]] for p in geo]
            if not any(km(y, x) <= RAYON + 1.5 for x, y in co):
                continue
            plan = t.get("natural") == "water" and co[0] == co[-1]
            traits.append({"type": "Feature",
                           "properties": {"genre": "plan" if plan else "cours"},
                           "geometry": ({"type": "Polygon", "coordinates": [co]}
                                        if plan else
                                        {"type": "LineString", "coordinates": co})})
            neufs += 1
        print("    case %d/%d : %d objets (%d nouveaux)"
              % (i, len(liste), len(rep.get("elements", [])), neufs))
        time.sleep(2.0)
    tol, n0, n1 = tolerance(), 0, 0
    for f in traits:
        g = f["geometry"]
        if g["type"] == "LineString":
            n0 += len(g["coordinates"])
            s = simplifier(g["coordinates"], tol)
            g["coordinates"] = [[round(x, 4), round(y, 4)] for x, y in s]; n1 += len(s)
        else:
            a = g["coordinates"][0]; n0 += len(a)
            s = simplifier(a, tol, 4)
            if s[0] != s[-1]:
                s.append(s[0])
            g["coordinates"] = [[[round(x, 4), round(y, 4)] for x, y in s]]; n1 += len(s)
    print("  sommets : %d → %d" % (n0, n1))
    ecrire({"type": "FeatureCollection", "features": traits}, "zone-eau.geojson",
           "Plans d'eau et cours d'eau. Seules les géométries portées par des "
           "chemins sont reprises : les grandes retenues décrites comme "
           "relations multipolygones sont absentes.")


if __name__ == "__main__":
    quoi = sys.argv[1] if len(sys.argv) > 1 else "toponymes"
    print("emprise : %.3f,%.3f → %.3f,%.3f" % bbox())
    {"toponymes": toponymes, "eau": eau}[quoi]()
