#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Analyses longue duree derivees de la reanalyse servie par Open-Meteo.
L'API d'archive combine par defaut ERA5-Land (9 km) et ERA5 (25 km) selon la
variable : on n'interroge aucun modele nomme, et on ne doit donc pas en
annoncer un. Corrige le 19/09/2026 — « ERA5 » etait ecrit a cote d'une maille
de 9 km, qui est celle d'ERA5-Land.

Produit data/analyses.json : trois series annuelles 1950-2025 que le tableau
de bord climat n'exposait pas encore.

  1. degres-jours unifies de chauffage, base 18 C, par saison de chauffe
  2. gel apres debourrement : date de debourrement (somme de temperatures
     base 5 depuis le 1er fevrier, seuil 250 Cj) et gelees posterieures
  3. fenetres de fenaison : suites de jours secs consecutifs, mai a juillet

Les donnees brutes sont lues dans un repertoire de cache contenant les
reponses de l'API decoupees par tranches de 5 ans (p_AAAA.json). Usage :

    python3 scripts/analyses.py [repertoire_de_cache] [fichier_sortie]
"""
import json, glob, math, os, sys, datetime
import statistics as st
from collections import Counter

CACHE = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/ddm-tmp")
SORTIE = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "analyses.json")

# --- lecture ---------------------------------------------------------------
jours = {}
for f in sorted(glob.glob(os.path.join(CACHE, "p_*.json"))):
    d = json.load(open(f))["daily"]
    for i, t in enumerate(d["time"]):
        jours[t] = (d["temperature_2m_min"][i], d["temperature_2m_max"][i],
                    d["temperature_2m_mean"][i], d["precipitation_sum"][i],
                    d["et0_fao_evapotranspiration"][i])
if not jours:
    sys.exit("aucune donnee dans " + CACHE)
dates = sorted(jours)
print("jours lus : %d, de %s a %s" % (len(jours), dates[0], dates[-1]))

par_an = {}
for t in dates:
    par_an.setdefault(int(t[:4]), []).append(t)
annees_completes = sorted(y for y, v in par_an.items() if len(v) >= 360)
Y0, Y1 = annees_completes[0], annees_completes[-1]

# --- 1. degres-jours de chauffage ------------------------------------------
# Convention : saison de chauffe du 1er juillet au 30 juin, nommee par son
# annee de fin. DJU = somme des (18 - temperature moyenne du jour) positifs.
BASE = 18.0
dju = {}
for t in dates:
    tmoy = jours[t][2]
    if tmoy is None:
        continue
    y, m = int(t[:4]), int(t[5:7])
    saison = y + 1 if m >= 7 else y
    d = dju.setdefault(saison, {"somme": 0.0, "n": 0, "jours_chauffes": 0})
    d["n"] += 1
    if tmoy < BASE:
        d["somme"] += BASE - tmoy
        d["jours_chauffes"] += 1
s_dju = [[y, round(v["somme"])] for y, v in sorted(dju.items())
         if v["n"] >= 360 and Y0 < y <= Y1]
s_jours_chauffes = [[y, v["jours_chauffes"]] for y, v in sorted(dju.items())
                    if v["n"] >= 360 and Y0 < y <= Y1]

# --- 2. gel apres debourrement ---------------------------------------------
# Deux stades, approches par le cumul des (temperature moyenne - 5 C) positifs
# depuis le 1er fevrier. Seuils cales pour que la mediane des dates tombe sur
# le debourrement (80 Cj, mediane 4 avril) et sur la floraison (150 Cj,
# mediane 24 avril) d'un pommier a cette altitude.
#   - apres le debourrement, une gelee a 0 C abime les jeunes pousses,
#     une gelee a -2 C les detruit ;
#   - apres l'ouverture des fleurs, -1 C suffit a supprimer la recolte.
# Fenetre d'observation : du stade jusqu'au 31 mai.
S_DEB, S_FLO = 80.0, 150.0

def stade(y, seuil):
    cumul = 0.0
    for t in par_an[y]:
        m = int(t[5:7])
        if m < 2:
            continue
        if m > 6:
            return None
        tmoy = jours[t][2]
        if tmoy is not None and tmoy > 5:
            cumul += tmoy - 5
        if cumul >= seuil:
            return t
    return None

s_debourrement, s_floraison = [], []
s_gelees_apres, s_gel_destructeur, s_gel_floraison, s_tmin_apres = [], [], [], []
detail_gel = {}
for y in annees_completes:
    d_deb, d_flo = stade(y, S_DEB), stade(y, S_FLO)
    if d_deb is None:
        continue
    fin_fenetre = "%d-05-31" % y
    doy = lambda t: datetime.date(y, int(t[5:7]), int(t[8:10])).timetuple().tm_yday
    n_gel = n_dest = n_flo = 0
    tmin_min = None
    for t in par_an[y]:
        if t <= d_deb or t > fin_fenetre:
            continue
        tmin = jours[t][0]
        if tmin is None:
            continue
        if tmin_min is None or tmin < tmin_min:
            tmin_min = tmin
        if tmin <= 0:
            n_gel += 1
        if tmin <= -2:
            n_dest += 1
        if d_flo and t > d_flo and tmin <= -1:
            n_flo += 1
    s_debourrement.append([y, doy(d_deb)])
    if d_flo:
        s_floraison.append([y, doy(d_flo)])
    s_gelees_apres.append([y, n_gel])
    s_gel_destructeur.append([y, n_dest])
    s_gel_floraison.append([y, n_flo])
    if tmin_min is not None:
        s_tmin_apres.append([y, round(tmin_min, 1)])
    detail_gel[y] = {"debourrement": d_deb, "floraison": d_flo, "gelees": n_gel,
                     "destructrices": n_dest, "gelees_floraison": n_flo,
                     "tmin": None if tmin_min is None else round(tmin_min, 1)}

# --- 3. fenetres de fenaison ------------------------------------------------
# Jour sec : moins de 1 mm de pluie. Une fenetre est une suite maximale d'au
# moins 3 jours secs entre le 1er mai et le 31 juillet. On compte aussi les
# fenetres larges (5 jours et plus) et, pour les fenetres de 3 jours et plus,
# le cumul d'evapotranspiration, qui mesure le pouvoir sechant.
s_fenetres, s_fenetres_larges, s_jours_secs, s_plus_longue = [], [], [], []
detail_fen = {}
for y in annees_completes:
    serie_jours = [t for t in par_an[y] if 5 <= int(t[5:7]) <= 7]
    if len(serie_jours) < 88:
        continue
    suites, courant, et0_courant = [], 0, 0.0
    for t in serie_jours:
        p, et0 = jours[t][3], jours[t][4]
        if p is not None and p < 1:
            courant += 1
            et0_courant += et0 or 0
        else:
            if courant:
                suites.append((courant, et0_courant))
            courant, et0_courant = 0, 0.0
    if courant:
        suites.append((courant, et0_courant))
    f3 = [s for s in suites if s[0] >= 3]
    f5 = [s for s in suites if s[0] >= 5]
    s_fenetres.append([y, len(f3)])
    s_fenetres_larges.append([y, len(f5)])
    s_jours_secs.append([y, sum(s[0] for s in suites if s[0] >= 3)])
    s_plus_longue.append([y, max([s[0] for s in suites], default=0)])
    detail_fen[y] = {"fenetres": len(f3), "larges": len(f5),
                     "plus_longue": max([s[0] for s in suites], default=0),
                     "et0_moyen": round(st.mean([s[1] for s in f3]), 1) if f3 else None}

# --- tendances -------------------------------------------------------------
def mk(vals):
    n = len(vals)
    if n < 15:
        return None
    S = sum(1 if vals[j] > vals[i] else -1 if vals[j] < vals[i] else 0
            for i in range(n - 1) for j in range(i + 1, n))
    ties = Counter(vals)
    tsum = sum(t * (t - 1) * (2 * t + 5) for t in ties.values() if t > 1)
    var = (n * (n - 1) * (2 * n + 5) - tsum) / 18.0
    if var <= 0:
        return None
    Z = (S - 1) / math.sqrt(var) if S > 0 else ((S + 1) / math.sqrt(var) if S < 0 else 0.0)
    p = 2 * (1 - 0.5 * (1 + math.erf(abs(Z) / math.sqrt(2))))
    return S, Z, p

def sen(xs, ys):
    pentes = sorted((ys[j] - ys[i]) / (xs[j] - xs[i])
                    for i in range(len(xs) - 1) for j in range(i + 1, len(xs)) if xs[j] != xs[i])
    if not pentes:
        return None
    n, N = len(xs), len(pentes)
    C = 1.96 * math.sqrt(n * (n - 1) * (2 * n + 5) / 18.0)
    lo = max(0, int(round((N - C) / 2)) - 1)
    hi = min(N - 1, int(round((N + C) / 2)))
    return st.median(pentes), pentes[lo], pentes[hi]

series = {
    "dju": s_dju, "jours_chauffes": s_jours_chauffes,
    "debourrement": s_debourrement, "floraison": s_floraison,
    "gelees_apres": s_gelees_apres, "gel_destructeur": s_gel_destructeur,
    "gel_floraison": s_gel_floraison, "tmin_apres": s_tmin_apres,
    "fenetres": s_fenetres, "fenetres_larges": s_fenetres_larges,
    "jours_secs_utiles": s_jours_secs, "plus_longue_suite": s_plus_longue,
}
tendances, normales = {}, {}
for k, s in series.items():
    xs = [a for a, _ in s]
    ys = [v for _, v in s]
    r, sl = mk(ys), sen(xs, ys)
    if r and sl:
        _, _, p = r
        pente, lo, hi = sl
        tendances[k] = {"pente_par_decennie": round(pente * 10, 3),
                        "ic95": [round(lo * 10, 3), round(hi * 10, 3)],
                        "p": round(p, 5),
                        "significative": bool(p < 0.05 and not (lo <= 0 <= hi)),
                        "y0": round(st.median(ys[:10]), 2),
                        "y1": round(st.median(ys[-10:]), 2)}
    n = [v for a, v in s if 1991 <= a <= 2020]
    if n:
        normales[k] = round(st.mean(n), 2)

# part des annees a risque de gel apres debourrement, par tranche de 30 ans
def part_risque(a, b):
    v = [g for y, g in s_gelees_apres if a <= y <= b]
    d = [g for y, g in s_gel_destructeur if a <= y <= b]
    f = [g for y, g in s_gel_floraison if a <= y <= b]
    if not v:
        return None
    return {"annees": len(v),
            "part_avec_gelee": round(100 * sum(1 for x in v if x > 0) / len(v)),
            "part_avec_gelee_destructrice": round(100 * sum(1 for x in d if x > 0) / len(d)),
            "part_gelee_en_floraison": round(100 * sum(1 for x in f if x > 0) / len(f)),
            "gelees_moyennes": round(st.mean(v), 2)}

out = {
    "lieu": "Vitrac-sur-Montane (19287), chemin du Mons",
    "source": "Open-Meteo archive — ERA5-Land (9 km) et ERA5 (25 km) combines par defaut",
    "periode": [Y0, Y1],
    "calcule_le": datetime.date.today().isoformat(),
    "methode": {
        "dju": "somme des (18 C - temperature moyenne du jour) positifs, saison du 1er juillet au 30 juin, nommee par son annee de fin",
        "debourrement": "premier jour ou le cumul des (temperature moyenne - 5 C) positifs depuis le 1er fevrier atteint 80 Cj ; floraison au seuil 150 Cj",
        "gelees_apres": "jours a temperature minimale <= 0 C entre le debourrement et le 31 mai ; destructrice a <= -2 C ; gelee en floraison a <= -1 C apres le stade floraison",
        "fenetres": "suites d'au moins 3 jours consecutifs a moins de 1 mm de pluie, du 1er mai au 31 juillet",
    },
    "series": series,
    "tendances": tendances,
    "normale_1991_2020": normales,
    "risque_gel": {"1951-1980": part_risque(1951, 1980),
                   "1961-1990": part_risque(1961, 1990),
                   "1996-2025": part_risque(1996, 2025)},
    "detail_gel": detail_gel,
    "detail_fenaison": detail_fen,
}
os.makedirs(os.path.dirname(SORTIE), exist_ok=True)
json.dump(out, open(SORTIE, "w"), ensure_ascii=False, separators=(",", ":"))

lib = {"dju": "DJU chauffage base 18", "jours_chauffes": "Jours a chauffer",
       "debourrement": "Debourrement (jour de l'annee)", "floraison": "Floraison (jour de l'annee)",
       "gelees_apres": "Gelees apres debourrement",
       "gel_destructeur": "Gelees <= -2 C apres deb.", "gel_floraison": "Gelees <= -1 C en floraison",
       "tmin_apres": "Tmin apres debourrement",
       "fenetres": "Fenetres de fenaison (3 j+)", "fenetres_larges": "Fenetres larges (5 j+)",
       "jours_secs_utiles": "Jours secs en fenetre", "plus_longue_suite": "Plus longue suite seche"}
print("\n=== TENDANCES par decennie (IC 95 %) ===")
for k, t in tendances.items():
    print("  %-32s %+8.2f  IC[%+.2f;%+.2f]  p=%.4f  %s  | %s -> %s" % (
        lib[k], t["pente_par_decennie"], t["ic95"][0], t["ic95"][1], t["p"],
        "SIGNIFICATIVE" if t["significative"] else "non detectable", t["y0"], t["y1"]))
print("\n=== NORMALES 1991-2020 ===")
for k, v in normales.items():
    print("  %-32s %s" % (lib[k], v))
print("\n=== RISQUE DE GEL APRES DEBOURREMENT ===")
for per, v in out["risque_gel"].items():
    if v:
        print("  %s : %d %% des annees avec une gelee apres debourrement, %d %% avec une gelee <= -2 C, %d %% avec une gelee en floraison, %.2f gelees en moyenne"
              % (per, v["part_avec_gelee"], v["part_avec_gelee_destructrice"],
                 v["part_gelee_en_floraison"], v["gelees_moyennes"]))
print("\n%s : %d octets" % (SORTIE, len(open(SORTIE).read())))
