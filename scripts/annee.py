#!/usr/bin/env python3
"""Analyses de l'année en cours et de l'année glissante — Domaine du Mons.

Produit data/annee.json : cumuls à date, position dans la distribution
1991-2020 au même jour de l'année, bilan des douze derniers mois, et la
courbe quotidienne de cumul de pluie pour comparaison à la bande normale.

S'appuie sur data/climat-reference.json, calculé une fois sur 1950-2025.
"""
import json, os, sys, urllib.request, datetime
from statistics import mean

LAT, LON = 45.351433, 1.931875
ICI = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(ICI, "..", "data", "climat-reference.json")
OUT = os.path.join(ICI, "..", "data", "annee.json")
VARS = "temperature_2m_min,temperature_2m_max,temperature_2m_mean,precipitation_sum,et0_fao_evapotranspiration"


def get(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": "domainedumons.actitude.org/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def fusion(d, src):
    j = src.get("daily", {})
    for i, t in enumerate(j.get("time", [])):
        v = (j["temperature_2m_min"][i], j["temperature_2m_max"][i], j["temperature_2m_mean"][i],
             j["precipitation_sum"][i], j["et0_fao_evapotranspiration"][i])
        if v[2] is not None:
            d[t] = v


def doy(t):
    y, m, jr = int(t[:4]), int(t[5:7]), int(t[8:10])
    if m == 2 and jr == 29:
        return None
    n = datetime.date(y, m, jr).timetuple().tm_yday
    bis = y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)
    return n - 1 if bis and n > 59 else n


def position(val, q):
    """Où se situe val dans les quantiles [q10,q25,q50,q75,q90] de 1991-2020."""
    if val < q[0]: return "sous le dixième le plus bas"
    if val < q[1]: return "dans le quart le plus bas"
    if val < q[3]: return "dans la moitié centrale"
    if val < q[4]: return "dans le quart le plus haut"
    return "au-dessus du dixième le plus haut"


def main():
    hier = datetime.date.today() - datetime.timedelta(days=1)
    debut = (hier - datetime.timedelta(days=400)).isoformat()
    j = {}
    try:
        fusion(j, get(f"https://archive-api.open-meteo.com/v1/archive?latitude={LAT}&longitude={LON}"
                      f"&start_date={debut}&end_date={hier}&daily={VARS}&timezone=Europe%2FParis"))
    except Exception as e:
        print(f"  archive indisponible ({e})", file=sys.stderr)
    try:   # les tout derniers jours, que l'archive n'a pas encore
        fusion(j, get(f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}"
                      f"&past_days=92&forecast_days=1&daily={VARS}&timezone=Europe%2FParis"))
    except Exception as e:
        print(f"  prévision indisponible ({e})", file=sys.stderr)
    if not j:
        print("aucune donnée : fichier inchangé", file=sys.stderr)
        return 1

    ref = json.load(open(REF, encoding="utf-8"))
    dates = sorted(t for t in j if t <= hier.isoformat())
    an = hier.year
    ts = [t for t in dates if t.startswith(str(an))]
    if not ts:
        print("année en cours vide", file=sys.stderr); return 1
    dernier = ts[-1]; k = doy(dernier) or 365

    # --- cumuls à date ---
    cp = ct = cd = 0.0; n = 0; courbe = []
    gel = chaud = st0 = 0
    for t in ts:
        tmin, tmax, tmoy, p, et0 = j[t]
        cp += p or 0; ct += tmoy; n += 1
        if 4 <= int(t[5:7]) <= 9 and et0 is not None: cd += et0 - (p or 0)
        if tmin is not None and tmin < 0: gel += 1
        if tmax is not None and tmax >= 30: chaud += 1
        if t >= f"{an}-02-01": st0 += max(0, tmoy)
        d0 = doy(t)
        if d0: courbe.append([d0, round(cp, 1)])
    ytd = {"pluie": round(cp), "tmoy": round(ct / n, 2), "deficit": round(cd),
           "gel": gel, "chaud30": chaud, "sommeT": round(st0), "jours": n}

    # --- position dans la distribution de référence ---
    pos = {}
    for cle in ("pluie", "tmoy", "defic"):
        q = ref["doy"].get(cle, {}).get(str(k))
        if q:
            val = ytd["deficit"] if cle == "defic" else ytd[cle]
            pos[cle] = {"quantiles": q, "valeur": val, "position": position(val, q),
                        "ecart_mediane": round(val - q[2], 1)}

    # --- année glissante (365 derniers jours) ---
    fen = dates[-365:]
    gl = {"pluie": round(sum(j[t][3] or 0 for t in fen)),
          "tmoy": round(mean(j[t][2] for t in fen), 2),
          "debut": fen[0], "fin": fen[-1], "jours": len(fen)}
    for cle in ("pluie", "tmoy"):
        q = ref.get("glissant", {}).get(cle)
        if q: gl[cle + "_position"] = position(gl[cle], q); gl[cle + "_quantiles"] = q

    # --- mensuel ---
    mois = {}
    for m in range(1, 13):
        mt = [t for t in ts if int(t[5:7]) == m]
        if mt:
            mois[str(m)] = {"pluie": round(sum(j[t][3] or 0 for t in mt)),
                            "tmoy": round(mean(j[t][2] for t in mt), 1), "jours": len(mt)}

    out = {"annee": an, "arrete_au": dernier, "jour_de_lannee": k,
           "calcule_le": datetime.date.today().isoformat(),
           "point": [LAT, LON], "normale": "1991-2020",
           "a_date": ytd, "position": pos, "glissant": gl, "mois": mois,
           "courbe_pluie": courbe,
           "bande_pluie": {d: q for d, q in ref["doy"].get("pluie", {}).items() if int(d) <= k}}
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"annee.json : {an} arrêtée au {dernier} — {ytd['pluie']} mm, {ytd['tmoy']} °C, "
          f"{ytd['chaud30']} jours ≥ 30 °C")
    return 0


if __name__ == "__main__":
    sys.exit(main())
