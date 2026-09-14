#!/usr/bin/env python3
"""Relevé quotidien — Domaine du Mons.

Interroge les sources publiques ouvertes et ajoute une ligne à data/releve-quotidien.csv.
Idempotent : une seule ligne par date. Ne casse jamais le dépôt si une source est muette —
les colonnes manquantes restent vides.

Sources : Open-Meteo (météo), Hub'Eau (débit de la Montane), VigiEau (sécheresse).
"""
import csv, json, os, sys, urllib.request, urllib.error
from datetime import date, timedelta
from statistics import mean

LAT, LON = 45.351433, 1.931875   # chemin du Mons, 588 m
STATION = "P361401001"
CSV = os.path.join(os.path.dirname(__file__), "..", "data", "releve-quotidien.csv")
COLS = ["date", "t_min_c", "t_max_c", "t_moy_c", "pluie_mm", "etp_mm",
        "rafale_max_kmh", "debit_montane_l_s", "secheresse_niveau", "secheresse_zone"]


def get(url, timeout=45):
    req = urllib.request.Request(url, headers={"User-Agent": "domainedumons.actitude.org/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def meteo(jour):
    j = jour.isoformat()
    u = (f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}"
         f"&timezone=Europe%2FParis&past_days=7&forecast_days=1"
         "&daily=temperature_2m_max,temperature_2m_min,temperature_2m_mean,"
         "precipitation_sum,et0_fao_evapotranspiration,wind_gusts_10m_max")
    d = get(u)["daily"]
    if j not in d["time"]:
        return {}
    i = d["time"].index(j)
    return {
        "t_min_c": d["temperature_2m_min"][i],
        "t_max_c": d["temperature_2m_max"][i],
        "t_moy_c": d["temperature_2m_mean"][i],
        "pluie_mm": d["precipitation_sum"][i],
        "etp_mm": d["et0_fao_evapotranspiration"][i],
        "rafale_max_kmh": d["wind_gusts_10m_max"][i],
    }


def debit(jour):
    u = (f"https://hubeau.eaufrance.fr/api/v2/hydrometrie/observations_tr?code_entite={STATION}"
         f"&grandeur_hydro=Q&date_debut_obs={jour}T00:00:00&date_fin_obs={jour}T23:59:59"
         "&size=2000&sort=desc")
    vals = [o["resultat_obs"] for o in get(u).get("data", []) if o.get("resultat_obs") is not None]
    return {"debit_montane_l_s": round(mean(vals), 1)} if vals else {}


def secheresse():
    rang = {"vigilance": 1, "alerte": 2, "alerte_renforcee": 3, "crise": 4}
    z = get(f"https://api.vigieau.beta.gouv.fr/api/zones?lon={LON}&lat={LAT}&profil=particulier")
    if not isinstance(z, list) or not z:
        return {"secheresse_niveau": "aucune", "secheresse_zone": ""}
    pire = max(z, key=lambda x: rang.get(x.get("niveauGravite"), 0))
    return {"secheresse_niveau": pire.get("niveauGravite", ""), "secheresse_zone": pire.get("nom", "")}


def main():
    jour = date.today() - timedelta(days=1)
    ligne = {"date": jour.isoformat()}
    for nom, f in (("météo", lambda: meteo(jour)), ("débit", lambda: debit(jour)), ("sécheresse", secheresse)):
        try:
            ligne.update(f())
        except Exception as e:                      # une source muette ne casse rien
            print(f"  {nom} : indisponible ({e})", file=sys.stderr)

    os.makedirs(os.path.dirname(CSV), exist_ok=True)
    lignes, vues = [], set()
    if os.path.exists(CSV):
        with open(CSV, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if r["date"] not in vues:
                    vues.add(r["date"]); lignes.append(r)
    lignes = [r for r in lignes if r["date"] != ligne["date"]]
    lignes.append({c: ligne.get(c, "") for c in COLS})
    lignes.sort(key=lambda r: r["date"])

    with open(CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows(lignes)
    print(f"relevé du {ligne['date']} : {len(lignes)} lignes au total")


if __name__ == "__main__":
    main()
