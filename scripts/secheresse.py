#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archive des restrictions sécheresse — Domaine du Mons.

Agrège la colonne `secheresse_niveau` du relevé quotidien en une série
consultable : nombre de jours passés à chaque niveau par année, dates de
bascule, épisodes, niveau courant et son ancienneté.

Cette série n'existe nulle part ailleurs : VigiEau publie l'état du jour et
ne conserve pas d'historique ouvert à cette maille. Chaque journée non
relevée est définitivement perdue, d'où le relevé quotidien automatique.

Usage : python3 scripts/secheresse.py
"""
import csv, json, os
from datetime import date, datetime, timedelta

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(RACINE, "data", "releve-quotidien.csv")
SORTIE = os.path.join(RACINE, "data", "secheresse-historique.json")

NIVEAUX = ["aucune", "vigilance", "alerte", "alerte_renforcee", "crise"]
RANG = {n: i for i, n in enumerate(NIVEAUX)}

def main():
    if not os.path.exists(CSV):
        raise SystemExit("relevé quotidien absent : " + CSV)
    lignes = []
    with open(CSV, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            niveau = (r.get("secheresse_niveau") or "").strip()
            if niveau:
                lignes.append((r["date"], niveau, (r.get("secheresse_zone") or "").strip()))
    lignes.sort()
    if not lignes:
        sortie = {"jours_releves": 0, "note": "aucun relevé de niveau à ce jour"}
        json.dump(sortie, open(SORTIE, "w"), ensure_ascii=False, separators=(",", ":"))
        print("aucun relevé de niveau")
        return

    par_annee, bascules, episodes = {}, [], []
    precedent = None
    debut_episode = None
    for d, niveau, zone in lignes:
        an = d[:4]
        a = par_annee.setdefault(an, {n: 0 for n in NIVEAUX})
        a[niveau] = a.get(niveau, 0) + 1
        if niveau != precedent:
            bascules.append({"date": d, "de": precedent, "vers": niveau, "zone": zone})
            if precedent is not None and debut_episode is not None:
                episodes.append({"niveau": precedent, "debut": debut_episode["date"],
                                 "fin": (datetime.fromisoformat(d) - timedelta(days=1)).date().isoformat()})
            debut_episode = {"date": d, "niveau": niveau}
            precedent = niveau
    dernier = lignes[-1]
    jours_courant = (datetime.fromisoformat(dernier[0]).date()
                     - datetime.fromisoformat(debut_episode["date"]).date()).days + 1

    # une année n'est comparable que si elle est complète ; on le dit plutôt
    # que de laisser croire à un total annuel
    for an, a in par_annee.items():
        a["jours_releves"] = sum(a[n] for n in NIVEAUX)
        a["jours_restreints"] = sum(a[n] for n in NIVEAUX if RANG[n] >= RANG["alerte"])
        a["complete"] = a["jours_releves"] >= (366 if int(an) % 4 == 0 else 365)

    sortie = {
        "source": "VigiEau (api.vigieau.beta.gouv.fr), relevé quotidien automatique",
        "zone": dernier[2],
        "niveaux": NIVEAUX,
        "debut": lignes[0][0],
        "fin": dernier[0],
        "jours_releves": len(lignes),
        "par_annee": par_annee,
        "bascules": bascules,
        "episodes_clos": episodes,
        "actuel": {"niveau": dernier[1], "depuis": debut_episode["date"],
                   "jours": jours_courant, "zone": dernier[2]},
        "calcule_le": date.today().isoformat(),
    }
    json.dump(sortie, open(SORTIE, "w"), ensure_ascii=False, separators=(",", ":"))
    print("archive sécheresse : %d jours relevés, du %s au %s, niveau actuel %s depuis %d jour(s)"
          % (len(lignes), lignes[0][0], dernier[0], dernier[1], jours_courant))

if __name__ == "__main__":
    main()
