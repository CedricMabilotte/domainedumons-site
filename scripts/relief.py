#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Le relief fin du Domaine du Mons — air froid, écoulements, exposition.

À partir du modèle numérique de terrain LiDAR HD de l'IGN (50 cm, vol du
24 août 2022, rééchantillonné ici à 2 m) et du modèle de hauteur de
végétation, calcule ce qu'aucune donnée publique ne dit à cette échelle :

  - les cuvettes et les couloirs où l'air froid s'accumule la nuit ;
  - l'indice d'humidité topographique, qui situe sources et zones humides ;
  - la pente, l'exposition et la position topographique du lieu ;
  - les haies et lisières qui font barrage à l'écoulement de l'air froid.

Produit dessins/relief-airfroid.png, dessins/relief-eau.png et
data/relief.json. Calcul ponctuel : le relief ne change pas.

Usage : python3 scripts/relief.py [taille_m] [resolution_m]
"""
import heapq, json, math, os, sys, urllib.request
from datetime import date
import numpy as np
import tifffile
from scipy import ndimage

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.expanduser("~/ddm-relief")
LAT, LON = 45.351433, 1.931875
X0, Y0 = 616363.0, 6473015.0          # Lambert 93 du chemin du Mons
TAILLE = int(sys.argv[1]) if len(sys.argv) > 1 else 2400      # côté de la fenêtre, en mètres
RES = float(sys.argv[2]) if len(sys.argv) > 2 else 2.0        # mètres par pixel
N = int(TAILLE / RES)
WMS = ("https://data.geopf.fr/wms-r?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&LAYERS=%s"
       "&FORMAT=image/geotiff&CRS=EPSG:2154&STYLES=&BBOX=%d,%d,%d,%d&WIDTH=%d&HEIGHT=%d")
COUCHES = {
    "mnt": "IGNF_LIDAR-HD_MNT_ELEVATION.ELEVATIONGRIDCOVERAGE.LAMB93",
    "mnh": "IGNF_LIDAR-HD_MNH_ELEVATION.ELEVATIONGRIDCOVERAGE.LAMB93",
}


def dalle(nom):
    """Télécharge une couche, ou reprend celle du cache."""
    os.makedirs(CACHE, exist_ok=True)
    f = os.path.join(CACHE, "%s_%d_%g.tif" % (nom, TAILLE, RES))
    if not os.path.exists(f):
        h = TAILLE // 2
        u = WMS % (COUCHES[nom], X0 - h, Y0 - h, X0 + h, Y0 + h, N, N)
        print("  téléchargement %s (%d×%d)…" % (nom, N, N))
        with urllib.request.urlopen(urllib.request.Request(
                u, headers={"User-Agent": "domainedumons.actitude.org/1.0"}), timeout=300) as r:
            open(f, "wb").write(r.read())
    a = tifffile.imread(f).astype(np.float64)
    a[a < -1000] = np.nan
    return a


def moyenne_fenetre(a, rayon_px):
    """Moyenne sur une fenêtre carrée, par image intégrale."""
    r = int(rayon_px)
    p = np.pad(a, r + 1, mode="edge")
    s = p.cumsum(0).cumsum(1)
    s = np.pad(s, ((1, 0), (1, 0)))
    n = a.shape[0]
    k = 2 * r + 1
    tot = (s[k:k + n, k:k + n] - s[0:n, k:k + n] - s[k:k + n, 0:n] + s[0:n, 0:n])
    return tot / (k * k)


def remplir(z, eps=1e-3):
    """Remplissage des cuvettes par inondation prioritaire AVEC INCRÉMENT
    (Barnes 2014). Renvoie la surface remplie ; la différence avec l'original
    donne la profondeur de chaque cuvette.
    L'incrément n'est pas un raffinement. Sans lui, le remplissage crée des
    surfaces parfaitement planes, une surface plane n'a pas de direction
    d'écoulement, et toute l'aire amont qui aurait dû transiter s'arrête au
    bord de la cuvette — sans que rien ne le signale. Corrigé le 19/09/2026 :
    au chemin du Mons, l'indice d'humidité passait de 9,57 à 7,11 sans cet
    incrément, soit une sous-estimation muette d'un facteur dix sur l'aire."""
    n, m = z.shape
    rempli = np.full((n, m), np.inf)
    ferme = np.zeros((n, m), dtype=bool)
    tas = []
    for i in range(n):
        for j in (0, m - 1):
            heapq.heappush(tas, (z[i, j], i, j)); rempli[i, j] = z[i, j]; ferme[i, j] = True
    for j in range(m):
        for i in (0, n - 1):
            if not ferme[i, j]:
                heapq.heappush(tas, (z[i, j], i, j)); rempli[i, j] = z[i, j]; ferme[i, j] = True
    while tas:
        v, i, j = heapq.heappop(tas)
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            a, b = i + di, j + dj
            if 0 <= a < n and 0 <= b < m and not ferme[a, b]:
                ferme[a, b] = True
                rempli[a, b] = max(z[a, b], v + eps)
                heapq.heappush(tas, (rempli[a, b], a, b))
    return rempli


def accumulation(z, res, p=1.1):
    """Accumulation de flux multidirectionnelle (Freeman 1991) sur une surface
    sans cuvette. D8 est inadapté sous 2° de pente : la discrétisation de la
    direction d'écoulement en huit valeurs produit, sur un plateau, des
    filaments parallèles artificiels. Ici la pente médiane est de 4° et plus
    de 60 % de la surface est sous 5° : l'écoulement multidirectionnel est une
    nécessité, pas un raffinement. Corrigé le 19/09/2026."""
    n, m = z.shape
    zf = z.ravel()
    ordre = np.argsort(zf)[::-1]
    acc = np.ones(n * m)
    vois = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))
    for k in ordre:
        k = int(k)
        i, j = divmod(k, m)
        zk = zf[k]
        pentes, cibles = [], []
        for di, dj in vois:
            a, b = i + di, j + dj
            if 0 <= a < n and 0 <= b < m:
                d = (zk - z[a, b]) / (res * math.hypot(di, dj))
                if d > 0:
                    pentes.append(d ** p)
                    cibles.append(a * m + b)
        if cibles:
            somme = sum(pentes)
            v = acc[k]
            for w, cible in zip(pentes, cibles):
                acc[cible] += v * w / somme
    return acc.reshape(n, m)
def ombrage(z, res, azimut=315, hauteur=40):
    gy, gx = np.gradient(z, res)
    pente = np.arctan(np.hypot(gx, gy))
    expo = np.arctan2(-gx, gy)
    az, al = math.radians(360 - azimut + 90), math.radians(hauteur)
    v = (math.sin(al) * np.cos(pente) + math.cos(al) * np.sin(pente) * np.cos(az - expo))
    return np.clip(v, 0, 1)


def png(chemin, rgb, cote=860):
    """Image indexée : un rendu de relief tient en quelques dizaines de kilo-octets."""
    from PIL import Image
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    im = Image.fromarray(rgb.astype(np.uint8), "RGB")
    if im.width > cote:
        im = im.resize((cote, cote), Image.LANCZOS)
    im.convert("P", palette=Image.ADAPTIVE, colors=48, dither=Image.NONE).save(chemin, optimize=True)


def melange(base, couleur, masque, force):
    """Pose une couleur sur le fond, là où le masque est vrai."""
    out = base.copy()
    for c in range(3):
        out[:, :, c] = np.where(masque, base[:, :, c] * (1 - force) + couleur[c] * force, base[:, :, c])
    return out


def croix(rgb, i, j, couleur=(217, 77, 8), taille=16):
    """Une croix cerclée de blanc, lisible sur n'importe quel fond."""
    n = rgb.shape[0]
    for d in range(-taille, taille + 1):
        for e in (-3, -2, 2, 3):
            for a, b in ((i + e, j + d), (i + d, j + e)):
                if 0 <= a < n and 0 <= b < n:
                    rgb[a, b] = (255, 255, 255)
    for d in range(-taille, taille + 1):
        for e in (-1, 0, 1):
            for a, b in ((i + e, j + d), (i + d, j + e)):
                if 0 <= a < n and 0 <= b < n:
                    rgb[a, b] = couleur
    return rgb


def main():
    print("relief : fenêtre de %d m à %g m par pixel (%d×%d)" % (TAILLE, RES, N, N))
    z = dalle("mnt")
    mnh = dalle("mnh")
    z = np.where(np.isnan(z), np.nanmedian(z), z)
    c = N // 2

    gy, gx = np.gradient(z, RES)
    pente_deg = np.degrees(np.arctan(np.hypot(gx, gy)))
    expo_deg = (np.degrees(np.arctan2(-gx, gy)) + 360) % 360
    # à 2 m, la pente d'un replat n'est que du bruit : l'exposition qui compte
    # se lit sur une surface lissée à 200 m
    zl = moyenne_fenetre(z, 200 / RES)
    gyl, gxl = np.gradient(zl, RES)
    pente_large = np.degrees(np.arctan(np.hypot(gxl, gyl)))
    expo_large = (np.degrees(np.arctan2(-gxl, gyl)) + 360) % 360

    print("  position topographique…")
    tpi_p = z - moyenne_fenetre(z, 100 / RES)     # 100 m — la forme du replat
    tpi_g = z - moyenne_fenetre(z, 400 / RES)     # 400 m — la position dans le versant

    print("  remplissage des cuvettes…")
    rempli = remplir(z)
    creux = rempli - z                            # profondeur de cuvette, en mètres

    print("  accumulation de flux…")
    acc = accumulation(rempli, RES)
    aire = acc * RES * RES
    twi = np.log(aire / np.maximum(np.tan(np.radians(np.maximum(pente_deg, 0.2))), 1e-3))

    # --- l'air froid, en grandeurs séparées ---------------------------------
    # Aucune donnée thermique n'existe sur cette emprise. Un indice agrégé y
    # aurait la forme d'une mesure sans en être une : on n'en construit pas.
    # Trois grandeurs, chacune dans son unité, et le critère de poche est
    # celui de l'analyse LiDAR du 17/09/2026 — position topographique sous
    # −3 m à 400 m, pente sous 2°, micro-cuvette de plus de 0,30 m.
    bas = tpi_g < -1.0                                  # bas dans le versant
    plat_bas = (tpi_g < -3.0) & (pente_deg < 2.0)       # bas ET plat
    poche = plat_bas & (creux > 0.30)                   # bas, plat, et en creux
    # Les cuvettes brutes surestiment de deux ordres de grandeur : le modèle
    # de terrain restitue les remblais de route et de voie ferrée mais pas les
    # ouvrages qui les traversent, et chaque busage devient un barrage fictif.
    # On ne garde que les objets compacts et de taille plausible (RX-06).
    etiq, n_obj = ndimage.label(creux > 0.30)
    surfaces = ndimage.sum(np.ones_like(etiq), etiq, range(1, n_obj + 1)) * RES * RES
    # périmètre par comptage de bord, en une passe
    bord = np.zeros(etiq.shape, dtype=bool)
    for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        bord |= (etiq != np.roll(etiq, (di, dj), (0, 1)))
    bord &= etiq > 0
    perim = ndimage.sum(bord, etiq, range(1, n_obj + 1)) * RES
    with np.errstate(divide="ignore", invalid="ignore"):
        compacite = np.where(perim > 0, 4 * math.pi * surfaces / perim ** 2, 0)
    garde = (compacite >= 0.25) & (surfaces <= 10000)   # compact, et sous l'hectare
    avere = np.zeros(etiq.shape, dtype=bool)
    if n_obj:
        table = np.concatenate([[False], garde])
        avere = table[etiq]
    classes = np.zeros(z.shape, dtype=int)
    classes[bas] = 1
    classes[plat_bas] = 2
    classes[poche] = 3
    print("  rendu…")
    om = ombrage(z, RES)
    om = np.round(om * 10) / 10          # aplati le dégradé : une image indexée reste légère
    base = np.stack([247 - (1 - om) * 120, 244 - (1 - om) * 125, 236 - (1 - om) * 130], axis=-1)
    carte = base.copy()
    carte = melange(carte, (150, 180, 205), classes == 1, 0.28)   # bas dans le versant
    carte = melange(carte, (95, 145, 190), classes == 2, 0.44)    # bas et plat
    carte = melange(carte, (40, 95, 160), classes == 3, 0.62)     # bas, plat, en creux
    # les boisements et haies, qui font barrage
    ligneux = np.where(np.isnan(mnh), 0, mnh) > 3
    carte = melange(carte, (74, 96, 58), ligneux, 0.34)
    carte = croix(carte, c, c)
    png(os.path.join(RACINE, "dessins", "relief-airfroid.png"), carte)

    eau = base.copy()
    eau = melange(eau, (120, 165, 195), twi > 7.5, 0.30)
    eau = melange(eau, (55, 115, 165), twi > 9.0, 0.50)
    eau = melange(eau, (25, 70, 125), twi > 10.5, 0.70)
    eau = croix(eau, c, c)
    png(os.path.join(RACINE, "dessins", "relief-eau.png"), eau)

    # --- chiffres -----------------------------------------------------------
    def part(m):
        return round(100 * float(np.mean(m)), 1)
    out = {
        "source": "MNT et MNH LiDAR HD de l'IGN, vol du 24 août 2022, rééchantillonnés à %g m" % RES,
        "fenetre_m": TAILLE, "resolution_m": RES,
        "point": {"altitude_m": round(float(z[c, c]), 1),
                  "pente_deg": round(float(pente_deg[c, c]), 2),
                  "exposition_deg": round(float(expo_deg[c, c])),
                  "pente_large_deg": round(float(pente_large[c, c]), 2),
                  "exposition_large_deg": round(float(expo_large[c, c])),
                  "tpi_100m": round(float(tpi_p[c, c]), 2),
                  "tpi_400m": round(float(tpi_g[c, c]), 2),
                  "twi": round(float(twi[c, c]), 2),
                  "aire_amont_m2": round(float(aire[c, c])),
                  "en_poche_froide": bool(poche[c, c])},
        "fenetre": {
            "altitude_min": round(float(z.min()), 1), "altitude_max": round(float(z.max()), 1),
            "part_plus_bas_que_le_point": part(z < z[c, c]),
            "part_bas_dans_le_versant": part(bas),
            "part_bas_et_plat": part(plat_bas),
            "part_poche_froide": part(poche),
            "part_creux_brut": part(creux > 0.30),
            "part_creux_avere": part(avere),
            "part_ligneux_3m": part(ligneux),
            "part_ligneux_10m": part(np.where(np.isnan(mnh), 0, mnh) > 10),
            "hauteur_vegetation_max_m": round(float(np.nanpercentile(mnh[~np.isnan(mnh)], 99.9)), 1),
            "hauteur_vegetation_extreme_m": round(float(np.nanmax(mnh)), 1),
            "creux_max_m": round(float(creux.max()), 2),
            "creux_avere_max_m": round(float(creux[avere].max()) if avere.any() else 0.0, 2),
            "part_twi_humide": part(twi > 9.0),
        },
        "calcule_le": date.today().isoformat(),
    }
    # l'exposition du versant : un plan ajusté sur 500 m, plutôt qu'un gradient
    # de deux pixels sur un replat où il ne mesure que du bruit
    rv = int(500 / RES)
    sl = slice(max(0, c - rv), min(N, c + rv))
    sub = z[sl, sl]
    jj, ii = np.meshgrid(np.arange(sub.shape[1]) * RES, np.arange(sub.shape[0]) * RES)
    A = np.stack([ii.ravel(), jj.ravel(), np.ones(sub.size)], axis=1)
    coef, *_ = np.linalg.lstsq(A, sub.ravel(), rcond=None)
    dzdy, dzdx = coef[0], coef[1]
    out["point"]["pente_versant_deg"] = round(float(np.degrees(np.arctan(math.hypot(dzdx, dzdy)))), 2)
    out["point"]["exposition_versant_deg"] = round(float((math.degrees(math.atan2(-dzdx, dzdy)) + 360) % 360))

    # l'écart d'altitude entre le point et le fond le plus proche, dans 400 m
    r = int(400 / RES)
    fen = z[max(0, c - r):c + r, max(0, c - r):c + r]
    out["fenetre"]["denivele_sous_le_point_400m"] = round(float(z[c, c] - fen.min()), 1)

    # La poche d'air froid la plus proche, au critère de l'analyse du
    # 17/09/2026 : position topographique sous −3 m à 400 m, pente sous 2°,
    # micro-cuvette de plus de 0,30 m. L'ancien critère passait par l'indice
    # composite et désignait un point à 114 m au nord-ouest — à l'opposé.
    yy, xx = np.nonzero(poche)
    if len(yy):
        dd = np.hypot(yy - c, xx - c) * RES
        k = int(np.argmin(dd))
        out["poche_proche"] = {
            "distance_m": round(float(dd[k])),
            "denivele_m": round(float(z[c, c] - z[yy[k], xx[k]]), 1),
            "direction_deg": round(float((math.degrees(math.atan2(xx[k] - c, c - yy[k])) + 360) % 360)),
            "critere": "position topographique < −3 m à 400 m, pente < 2°, cuvette > 0,30 m",
        }
        sp = poche[max(0, c - r):c + r, max(0, c - r):c + r]
        out["fenetre"]["part_poche_froide_400m"] = round(100 * float(np.mean(sp)), 1)
    json.dump(out, open(os.path.join(RACINE, "data", "relief.json"), "w"),
              ensure_ascii=False, separators=(",", ":"))
    print("\n  altitude %.1f m, pente %.2f°, exposition %d°" % (
        out["point"]["altitude_m"], out["point"]["pente_deg"], out["point"]["exposition_deg"]))
    print("  position : %+.2f m sur 100 m, %+.2f m sur 400 m" % (
        out["point"]["tpi_100m"], out["point"]["tpi_400m"]))
    print("  le point est-il en poche d'air froid : %s" % ("oui" if out["point"]["en_poche_froide"] else "non"))
    print("  aire amont au point : %d m² · indice d'humidité %.2f"
          % (out["point"]["aire_amont_m2"], out["point"]["twi"]))
    f = out["fenetre"]
    print("  air froid : %.1f %% faible, %.1f %% marqué, %.1f %% fort" % (
        f["part_bas_dans_le_versant"], f["part_bas_et_plat"], f["part_poche_froide"]))
    print("  ligneux > 3 m : %.1f %%, > 10 m : %.1f %%, max %.1f m" % (
        f["part_ligneux_3m"], f["part_ligneux_10m"], f["hauteur_vegetation_max_m"]))
    print("  terrain plus bas que le point : %.1f %%" % f["part_plus_bas_que_le_point"])
    print("  dénivelé sous le point dans 400 m : %.1f m" % f["denivele_sous_le_point_400m"])
    if out.get("poche_proche"):
        pp = out["poche_proche"]
        print("  poche d'air froid la plus proche : %d m, %.1f m plus bas, azimut %d°" % (
            pp["distance_m"], pp["denivele_m"], pp["direction_deg"]))


if __name__ == "__main__":
    main()
