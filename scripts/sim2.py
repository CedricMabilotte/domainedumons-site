#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L'humidité des sols au Domaine du Mons, depuis 1958.

Météo-France publie SIM2, une réanalyse qui fait tourner un modèle de sol sur
une grille de 8 km depuis 1958. La maille qui contient le chemin du Mons est
LAMBX 5720 / LAMBY 20410, centre à 4,2 km du lieu. On en tire deux choses que
ni la pluie ni le bilan P − ETP ne donnent :

  - le SWI, l'humidité du sol ramenée à sa réserve utile ;
  - le SSWI, ce même indice ramené à la normale du jour, qui dit si le sol est
    sec *pour la saison*.

Deux usages :
    python3 scripts/sim2.py --reprendre ~/ddm-sim2/cellule.csv
        reprend l'extraction longue et écrit data/humidite-sol.csv
    python3 scripts/sim2.py
        complète avec le fichier des soixante derniers jours et recalcule
        data/humidite-sol.json — c'est ce que fait le travail quotidien
"""
import csv, gzip, io, json, os, sys, urllib.request
from datetime import date, datetime
import statistics as st

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(RACINE, "data", "humidite-sol.csv")
JSON = os.path.join(RACINE, "data", "humidite-sol.json")
LAMBX, LAMBY = "5720", "20410"
LATEST = "https://meteofrance.s3.sbg.io.cloud.ovh.net/data/REF_CC/SIM/QUOT_SIM2_latest.csv.gz"
COLS = ["date", "pluie_mm", "etp_mm", "t_c", "swi", "sswi_10j", "drainage_mm", "ruissellement_mm"]
REF = (1958, 2020)           # période de référence des quantiles


def lire_csv():
    if not os.path.exists(CSV):
        return {}
    with open(CSV, newline="", encoding="utf-8") as f:
        return {r["date"]: r for r in csv.DictReader(f)}


def ecrire_csv(lignes):
    with open(CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for d in sorted(lignes):
            w.writerow(lignes[d])


def convertir(ligne, entetes):
    """Une ligne brute SIM2 vers nos colonnes."""
    v = dict(zip(entetes, ligne))
    if v.get("LAMBX") != LAMBX or v.get("LAMBY") != LAMBY:
        return None
    d = v["DATE"]
    iso = "%s-%s-%s" % (d[0:4], d[4:6], d[6:8])
    def nb(c):
        x = v.get(c, "")
        try:
            return round(float(x), 3)
        except (TypeError, ValueError):
            return ""
    return {"date": iso, "pluie_mm": nb("PRELIQ"), "etp_mm": nb("ETP"), "t_c": nb("T"),
            "swi": nb("SWI"), "sswi_10j": nb("SSWI_10J"),
            "drainage_mm": nb("DRAINC"), "ruissellement_mm": nb("RUNC")}


def reprendre(chemin):
    lignes = lire_csv()
    n = 0
    with open(chemin, newline="", encoding="utf-8") as f:
        entetes = None
        for brut in csv.reader(f, delimiter=";"):
            if not brut:
                continue
            if brut[0] == "LAMBX":
                entetes = brut
                continue
            if entetes is None:
                continue
            r = convertir(brut, entetes)
            if r:
                lignes[r["date"]] = r
                n += 1
    ecrire_csv(lignes)
    print("  %d lignes reprises, %d jours au total" % (n, len(lignes)))
    return lignes


def completer():
    """Les soixante derniers jours, depuis le fichier courant de Météo-France."""
    lignes = lire_csv()
    print("  téléchargement du fichier courant…")
    with urllib.request.urlopen(urllib.request.Request(
            LATEST, headers={"User-Agent": "domainedumons.actitude.org/1.0"}), timeout=300) as r:
        brut = gzip.decompress(r.read()).decode("utf-8", "replace")
    entetes, n = None, 0
    for ligne in csv.reader(io.StringIO(brut), delimiter=";"):
        if not ligne:
            continue
        if ligne[0] == "LAMBX":
            entetes = ligne
            continue
        v = convertir(ligne, entetes) if entetes else None
        if v and v["date"] not in lignes:
            lignes[v["date"]] = v
            n += 1
    ecrire_csv(lignes)
    print("  %d jours ajoutés, %d au total" % (n, len(lignes)))
    return lignes


def quantiles(vals, ps):
    v = sorted(vals)
    return [round(v[min(len(v) - 1, max(0, int(round(p * (len(v) - 1))))) ], 3) for p in ps]


def calculer(lignes):
    jours = sorted(lignes)
    if not jours:
        raise SystemExit("aucune donnée")
    courante = int(jours[-1][:4])

    # --- quantiles climatologiques du SWI, par jour de l'année
    par_md = {}
    for d in jours:
        y = int(d[:4])
        if not (REF[0] <= y <= REF[1]):
            continue
        s = lignes[d]["swi"]
        if s not in ("", None):
            par_md.setdefault(d[5:], []).append(float(s))
    bande = {md: quantiles(v, [0.1, 0.5, 0.9]) for md, v in par_md.items() if len(v) >= 20}

    # --- la courbe de l'année en cours
    courbe = []
    for d in jours:
        if int(d[:4]) != courante:
            continue
        s = lignes[d]["swi"]
        if s in ("", None):
            continue
        q = bande.get(d[5:])
        courbe.append([d, round(float(s), 3)] + ([q] if q else [None]))

    # --- par année : sécheresse du sol, en jours
    annees = {}
    for d in jours:
        y = str(int(d[:4]))
        ss = lignes[d]["sswi_10j"]
        sw = lignes[d]["swi"]
        a = annees.setdefault(y, {"jours": 0, "sous_1": 0, "sous_1_5": 0, "sous_2": 0,
                                  "swi_ete": [], "serie_max": 0, "_serie": 0})
        a["jours"] += 1
        if ss not in ("", None):
            x = float(ss)
            if x < -1:
                a["sous_1"] += 1
            if x < -1.5:
                a["sous_1_5"] += 1
                a["_serie"] += 1
                a["serie_max"] = max(a["serie_max"], a["_serie"])
            else:
                a["_serie"] = 0
            if x < -2:
                a["sous_2"] += 1
        if sw not in ("", None) and 6 <= int(d[5:7]) <= 8:
            a["swi_ete"].append(float(sw))
    for y, a in annees.items():
        a.pop("_serie", None)
        a["swi_ete"] = round(st.mean(a["swi_ete"]), 3) if a["swi_ete"] else None
        a["complete"] = a["jours"] >= 360

    # --- classement des étés par humidité de sol
    cl = sorted(((y, a["swi_ete"]) for y, a in annees.items()
                 if a["swi_ete"] is not None and (a["complete"] or int(y) == courante)),
                key=lambda x: x[1])
    rang_ete = {y: i + 1 for i, (y, _) in enumerate(cl)}

    # --- les épisodes : au moins vingt jours consécutifs sous -1,5
    episodes, debut, fond = [], None, 0
    for d in jours:
        ss = lignes[d]["sswi_10j"]
        sec = ss not in ("", None) and float(ss) < -1.5
        if sec:
            if debut is None:
                debut, fond = d, float(ss)
            fond = min(fond, float(ss))
        elif debut is not None:
            n = (datetime.fromisoformat(d) - datetime.fromisoformat(debut)).days
            if n >= 20:
                episodes.append({"debut": debut, "fin": d, "jours": n, "fond": round(fond, 2)})
            debut = None
    if debut is not None:
        n = (datetime.fromisoformat(jours[-1]) - datetime.fromisoformat(debut)).days + 1
        if n >= 20:
            episodes.append({"debut": debut, "fin": jours[-1], "jours": n, "fond": round(fond, 2),
                             "en_cours": True})

    dernier = lignes[jours[-1]]
    out = {
        "source": "Météo-France, réanalyse SIM2 (SAFRAN-ISBA), maille de 8 km",
        "maille": [LAMBX, LAMBY], "distance_centre_km": 4.2,
        "periode": [jours[0][:4], jours[-1][:4]], "jours": len(jours),
        "reference": list(REF),
        "annee_courante": courante,
        "actuel": {"date": jours[-1],
                   "swi": None if dernier["swi"] == "" else float(dernier["swi"]),
                   "sswi": None if dernier["sswi_10j"] == "" else float(dernier["sswi_10j"])},
        "courbe": courbe,
        "annees": annees,
        "rang_ete": rang_ete,
        "episodes": sorted(episodes, key=lambda e: -e["jours"])[:25],
        "calcule_le": date.today().isoformat(),
    }
    json.dump(out, open(JSON, "w"), ensure_ascii=False, separators=(",", ":"))
    print("\n  %d jours, de %s à %s" % (len(jours), jours[0], jours[-1]))
    print("  SWI au %s : %s   SSWI : %s" % (jours[-1], out["actuel"]["swi"], out["actuel"]["sswi"]))
    print("  été %d : SWI moyen %s, rang %s sur %d" % (
        courante, annees[str(courante)]["swi_ete"], rang_ete.get(str(courante)), len(rang_ete)))
    print("\n  Les cinq étés les plus secs (SWI moyen de juin à août) :")
    for y, v in cl[:5]:
        print("    %s : %.3f   %d jours sous −1,5 de SSWI" % (y, v, annees[y]["sous_1_5"]))
    print("\n  Les cinq plus longs épisodes sous −1,5 :")
    for e in out["episodes"][:5]:
        print("    %s → %s, %d jours, fond %.2f" % (e["debut"], e["fin"], e["jours"], e["fond"]))
    print("\n  %s : %d octets" % (JSON, len(open(JSON).read())))


def main():
    if "--reprendre" in sys.argv:
        i = sys.argv.index("--reprendre")
        chemin = sys.argv[i + 1] if len(sys.argv) > i + 1 else os.path.expanduser("~/ddm-sim2/cellule.csv")
        lignes = reprendre(chemin)
    else:
        lignes = completer()
    calculer(lignes)


if __name__ == "__main__":
    main()
