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
import hashlib, heapq, io, json, math, os, sys, time, urllib.parse, urllib.request

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


CACHE = os.path.expanduser("~/ddm-tmp/overpass")

def appel(req, essais=5):
    """Une requete rendue est gardee sur disque. Un reseau qui lache ou une
    instance qui rend 504 ne fait alors perdre que la case en cours : la
    relance repart de la, pas du debut. Le cache est hors du depot."""
    os.makedirs(CACHE, exist_ok=True)
    cle = os.path.join(CACHE, hashlib.sha1(req.encode("utf-8")).hexdigest() + ".json")
    if os.path.exists(cle) and os.path.getsize(cle) > 2:
        with io.open(cle, encoding="utf-8") as fh:
            return json.load(fh)
    for e in range(essais):
        try:
            r = urllib.request.Request(
                OVERPASS, data=urllib.parse.urlencode({"data": req}).encode(),
                headers={"User-Agent": UA})
            with urllib.request.urlopen(r, timeout=180) as rep:
                d = json.loads(rep.read().decode("utf-8"))
            with io.open(cle, "w", encoding="utf-8") as fh:
                json.dump(d, fh)
            return d
        except Exception as ex:
            if e == essais - 1:
                raise
            # 504 veut dire que l'instance est chargee : attendre franchement,
            # sans quoi on ne fait qu'ajouter a sa charge.
            attente = 15 * (2 ** e)
            print("      (reprise dans %d s : %s)" % (attente, str(ex)[:70]))
            time.sleep(attente)


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
    """Visvalingam par tas. Une entree perimee est recalculee et repoussee,
    jamais jetee : la jeter laisse derriere des sommets que l'algorithme croit
    deja traites, et la simplification ne retire presque rien. La version
    naive, elle, est en O(n2) et ne rend pas la main sur une riviere de
    quatre mille sommets."""
    n = len(pts)
    if n <= mini:
        return [list(p) for p in pts]
    p = [list(x) for x in pts]
    prec = list(range(-1, n - 1))
    suiv = list(range(1, n + 1)); suiv[-1] = -1
    vivant = [True] * n
    tas = []
    for i in range(1, n - 1):
        heapq.heappush(tas, (aire(p[i-1], p[i], p[i+1]), i))
    restants, seuil = n, tol * tol
    while tas and restants > mini:
        a, i = heapq.heappop(tas)
        if not vivant[i] or prec[i] < 0 or suiv[i] < 0:
            continue
        courante = aire(p[prec[i]], p[i], p[suiv[i]])
        if courante > a + 1e-18:
            heapq.heappush(tas, (courante, i))
            continue
        if courante > seuil:
            break
        vivant[i] = False; restants -= 1
        g, d = prec[i], suiv[i]
        suiv[g] = d; prec[d] = g
        for k in (g, d):
            if 0 < k < n - 1 and vivant[k] and prec[k] >= 0 and suiv[k] >= 0:
                heapq.heappush(tas, (aire(p[prec[k]], p[k], p[suiv[k]]), k))
    return [p[i] for i in range(n) if vivant[i]]


def tolerance(pixels=0.5):
    """Le deplacement admis, exprime en pixels au zoom maximal. 0,5 px pour la
    donnee : on ne deforme pas ce qu'on mesure. 1 px pour un fond : il recule,
    et le sommet economise est un octet de moins a telecharger sur une liaison
    qui, en rural, n'est pas toujours la."""
    return (40075016.686 * math.cos(math.radians(ICI[0]))
            / (2 ** (ZOOM_MAX + 8))) * pixels / 111120.0


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
def longueur_m(co):
    t = 0.0
    for k in range(len(co) - 1):
        x1, y1 = co[k]; x2, y2 = co[k + 1]
        t += math.hypot((x2 - x1) * 111320 * math.cos(math.radians(ICI[0])),
                        (y2 - y1) * 111120)
    return t


def aire_m2(co):
    t = 0.0
    for k in range(len(co) - 1):
        x1, y1 = co[k]; x2, y2 = co[k + 1]
        t += x1 * y2 - x2 * y1
    return abs(t) / 2 * 111120 * 111320 * math.cos(math.radians(ICI[0]))


#: Un plan d'eau plus petit que cela fait moins de cinq pixels au zoom
#: maximal : ce n'est plus un repere, c'est une poussiere bleue.
PLAN_MIN_HA = 0.45
#: Un ruisseau plus court que cela fait moins de quarante pixels : il ne dit
#: pas ou l'on est.
RUISSEAU_MIN_M = 500.0


def eau():
    """Deux fichiers, pas un.

    Les rivieres, les canaux et les plans d'eau tiennent en 220 Ko compresses
    et servent des le premier zoom : c'est a une riviere qu'on se situe en
    rural, avant toute limite administrative.

    Les ruisseaux pesent autant a eux seuls, et ne servent qu'au zoom de
    detail. Les mettre dans le meme fichier ferait payer a chaque visiteur,
    des l'ouverture, une couche que la plupart ne verront jamais. Ils vont
    donc dans un fichier a part, que la page ne va chercher qu'en arrivant au
    zoom ou ils s'affichent.

    Limite assumee : seules les geometries portees par des chemins sont
    reprises. Les grandes retenues decrites comme relations multipolygones
    sont absentes.
    """
    gab = ('[out:json][timeout:120];('
           'way["natural"="water"](%(s)f,%(o)f,%(n)f,%(e)f);'
           'way["waterway"~"^(river|stream|canal)$"](%(s)f,%(o)f,%(n)f,%(e)f););'
           "out geom;")
    vus, bruts = set(), []
    liste = cases(6)
    for i, c in enumerate(liste, 1):
        rep = appel(gab % {"s": c[0], "o": c[1], "n": c[2], "e": c[3]})
        neufs = 0
        for el in rep.get("elements", []):
            k = (el.get("type"), el.get("id"))
            if k in vus:
                continue
            vus.add(k); bruts.append(el); neufs += 1
        print("    case %d/%d : %d objets (%d nouveaux)"
              % (i, len(liste), len(rep.get("elements", [])), neufs))
        time.sleep(2.0)

    # Un fond recule : 1 px de deplacement admis, contre 0,5 px pour la donnee.
    tol = tolerance(1.0)
    large, fine = [], []
    n0 = n1 = 0
    for el in bruts:
        t = el.get("tags") or {}
        geo = el.get("geometry")
        if not geo or len(geo) < 2:
            continue
        co = [[p["lon"], p["lat"]] for p in geo]
        if not any(km(y, x) <= RAYON + 1.5 for x, y in co):
            continue
        n0 += len(co)
        plan = t.get("natural") == "water" and co[0] == co[-1]
        if plan:
            if aire_m2(co) < PLAN_MIN_HA * 10000:
                continue
            sp = simplifier(co, tol, 4)
            if sp[0] != sp[-1]:
                sp.append(sp[0])
            n1 += len(sp)
            large.append({"type": "Feature", "properties": {"genre": "plan"},
                          "geometry": {"type": "Polygon", "coordinates":
                                       [[[round(x, 4), round(y, 4)] for x, y in sp]]}})
            continue
        w = t.get("waterway")
        if w not in ("river", "canal", "stream"):
            continue
        if w == "stream" and longueur_m(co) < RUISSEAU_MIN_M:
            continue
        sp = simplifier(co, tol)
        n1 += len(sp)
        f = {"type": "Feature", "properties": {"genre": "cours"},
             "geometry": {"type": "LineString",
                          "coordinates": [[round(x, 4), round(y, 4)] for x, y in sp]}}
        (fine if w == "stream" else large).append(f)

    print("  sommets : %d -> %d" % (n0, n1))
    ecrire({"type": "FeatureCollection", "features": large}, "zone-eau.geojson",
           "Rivieres, canaux et plans d'eau d'au moins %g ha. Seules les "
           "geometries portees par des chemins sont reprises : les grandes "
           "retenues decrites comme relations multipolygones sont absentes."
           % PLAN_MIN_HA)
    ecrire({"type": "FeatureCollection", "features": fine}, "zone-eau-fine.geojson",
           "Ruisseaux d'au moins %d m. Fichier separe, que la page ne va "
           "chercher qu'au zoom ou ils s'affichent : il pese autant que tout "
           "le reste de l'eau et ne sert qu'au detail."
           % int(RUISSEAU_MIN_M))


if __name__ == "__main__":
    quoi = sys.argv[1] if len(sys.argv) > 1 else "toponymes"
    print("emprise : %.3f,%.3f → %.3f,%.3f" % bbox())
    {"toponymes": toponymes, "eau": eau}[quoi]()
