#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L'eau au Domaine du Mons — série longue et prélèvements.

Construit data/eau.json à partir de trois sources publiques :
  - Hub'Eau hydrométrie « obs_elab » : débits journaliers validés de la Montane
    à Eyrein (station P361401001), depuis le 1er janvier 1957 ;
  - Hub'Eau ONDE : observations d'écoulement (assecs) de la station la plus
    proche, à 6,7 km ;
  - Hub'Eau BNPE : volumes prélevés sur la commune, par ouvrage et par année.

L'API temps réel utilisée par le tableau de bord hebdomadaire ne conserve
qu'un mois ; celle-ci conserve tout. Usage : python3 scripts/eau.py
"""
import json, os, sys, urllib.request, urllib.error
from datetime import date, datetime
import statistics as st

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SORTIE = os.path.join(RACINE, "data", "eau.json")
STATION = "P361401001"
ONDE = "P1320001"
INSEE = "19287"
SEUILS = [50, 20, 10]          # l/s — repères d'étiage
UA = {"User-Agent": "domainedumons.actitude.org/1.0"}


def get(url, essais=3):
    for i in range(essais):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
                return json.load(r)
        except Exception as e:
            if i == essais - 1:
                raise
            print("  nouvel essai (%s)" % e, file=sys.stderr)


def debits():
    """Débits journaliers, paginés par tranches de 15 ans."""
    jours = {}
    for a0 in range(1955, date.today().year + 1, 15):
        a1 = a0 + 14
        u = ("https://hubeau.eaufrance.fr/api/v2/hydrometrie/obs_elab"
             "?code_entite=%s&grandeur_hydro_elab=QmnJ&size=20000"
             "&date_debut_obs_elab=%d-01-01&date_fin_obs_elab=%d-12-31"
             "&fields=date_obs_elab,resultat_obs_elab" % (STATION, a0, a1))
        d = get(u)
        for o in d.get("data", []):
            v = o.get("resultat_obs_elab")
            if v is not None:
                jours[o["date_obs_elab"][:10]] = v
        print("  %d-%d : %d jours" % (a0, a1, len(d.get("data", []))))
    return jours


def annees(jours):
    """Un résumé d'étiage par année civile complète."""
    par_an = {}
    for t, v in jours.items():
        par_an.setdefault(int(t[:4]), []).append((t, v))
    out = {}
    courante = max(par_an)
    for y, s in sorted(par_an.items()):
        if len(s) < 300 and y != courante:
            continue
        s.sort()
        vals = [v for _, v in s]
        # VCN3 et VCN10 : plus faible moyenne sur 3 et 10 jours consécutifs
        def vcn(n):
            if len(vals) < n:
                return None
            c = sum(vals[:n])
            m = c
            for i in range(n, len(vals)):
                c += vals[i] - vals[i - n]
                m = min(m, c)
            return round(m / n, 1)
        mini = min(vals)
        jour_mini = [t for t, v in s if v == mini][0]
        sous = {}
        for seuil in SEUILS:
            js = [t for t, v in s if v < seuil]
            sous[str(seuil)] = {"jours": len(js), "premier": js[0] if js else None}
        out[y] = {
            "n": len(s),
            "complete": len(s) >= 300,
            "module": round(st.mean(vals)),
            "mediane": round(st.median(vals)),
            "min": round(mini, 1),
            "jour_min": jour_mini,
            "vcn3": vcn(3),
            "vcn10": vcn(10),
            "sous_seuil": sous,
        }
    return out


def courbe_annee(jours, y):
    """La courbe de l'année en cours, et les quantiles du même jour sur 1957-2025."""
    ref = {}
    for t, v in jours.items():
        if int(t[:4]) < y:
            ref.setdefault(t[5:], []).append(v)
    serie = []
    for t in sorted(k for k in jours if k.startswith("%d-" % y)):
        md = t[5:]
        r = sorted(ref.get(md, []))
        q = None
        if len(r) >= 20:
            def qt(p):
                i = min(len(r) - 1, max(0, int(round(p * (len(r) - 1)))))
                return round(r[i], 1)
            q = [qt(0.10), qt(0.50), qt(0.90)]
        serie.append([t, round(jours[t], 1)] + ([q] if q else [None]))
    return serie


def onde():
    u = ("https://hubeau.eaufrance.fr/api/v1/ecoulement/observations?code_station=%s"
         "&size=500&fields=date_observation,libelle_ecoulement,code_campagne" % ONDE)
    d = get(u)
    obs = [{"date": o["date_observation"][:10], "etat": o.get("libelle_ecoulement")}
           for o in d.get("data", []) if o.get("date_observation")]
    obs.sort(key=lambda o: o["date"])
    par_an = {}
    for o in obs:
        a = par_an.setdefault(o["date"][:4], {"observations": 0, "assecs": 0, "faibles": 0})
        a["observations"] += 1
        e = (o["etat"] or "").lower()
        if "assec" in e:
            a["assecs"] += 1
        elif "faible" in e or "non visible" in e:
            a["faibles"] += 1
    return {"station": ONDE, "distance_km": 6.7,
            "libelle": "ruisseau de l'étang de Bourre à Champagnac-la-Noaille",
            "observations": obs, "par_annee": par_an}


def prelevements():
    u = ("https://hubeau.eaufrance.fr/api/v1/prelevements/chroniques?code_commune_insee=%s"
         "&size=500&fields=annee,volume,nom_ouvrage,libelle_usage,code_ouvrage" % INSEE)
    d = get(u)
    par_an, ouvrages = {}, {}
    for o in d.get("data", []):
        v, a = o.get("volume"), str(o.get("annee"))
        if v is None:
            continue
        par_an[a] = round(par_an.get(a, 0) + v)
        nom = (o.get("nom_ouvrage") or "").strip()
        ouvrages.setdefault(nom, {})[a] = round(v)
    dernier = max(par_an) if par_an else None
    classement = sorted(((n, v.get(dernier, 0)) for n, v in ouvrages.items()),
                        key=lambda x: -x[1])
    return {"par_annee": par_an, "derniere_annee": dernier,
            "ouvrages": [{"nom": n, "volume": v} for n, v in classement if v],
            "usages": sorted({(o.get("libelle_usage") or "") for o in d.get("data", [])})}


def main():
    print("débits journaliers…")
    j = debits()
    print("  %d jours, de %s à %s" % (len(j), min(j), max(j)))
    courant = max(int(t[:4]) for t in j)
    an = annees(j)
    vals = list(j.values())

    # classement des étiages : le rang de chaque année sur le VCN10
    cl = sorted(((y, a["vcn10"]) for y, a in an.items()
                 if a["vcn10"] is not None and (a["complete"] or y == courant)),
                key=lambda x: x[1])
    rangs = {str(y): i + 1 for i, (y, _) in enumerate(cl)}

    out = {
        "station": {"code": STATION, "nom": "La Montane à Eyrein [Pont du Geai]",
                    "distance_km": 1.2, "bassin_versant_km2": 43},
        "periode": [min(j)[:4], max(j)[:4]],
        "jours": len(j),
        "module_l_s": round(st.mean(vals)),
        "seuils": SEUILS,
        "annees": {str(y): a for y, a in an.items()},
        "rang_etiage": rangs,
        "annee_courante": courant,
        "courbe": courbe_annee(j, courant),
        "calcule_le": date.today().isoformat(),
    }
    print("ONDE…")
    try:
        out["onde"] = onde()
    except Exception as e:
        print("  indisponible : %s" % e, file=sys.stderr)
    print("prélèvements…")
    try:
        out["prelevements"] = prelevements()
    except Exception as e:
        print("  indisponible : %s" % e, file=sys.stderr)

    os.makedirs(os.path.dirname(SORTIE), exist_ok=True)
    json.dump(out, open(SORTIE, "w"), ensure_ascii=False, separators=(",", ":"))
    print("\n%s : %d octets" % (SORTIE, len(open(SORTIE).read())))
    pires = sorted(an.items(), key=lambda x: x[1]["vcn10"] if x[1]["vcn10"] is not None else 1e9)[:8]
    print("\nLes huit étiages les plus sévères (VCN10, l/s) :")
    for y, a in pires:
        print("  %d : VCN10 %6.1f   mini %6.1f le %s   %d jours sous 20 l/s"
              % (y, a["vcn10"], a["min"], a["jour_min"], a["sous_seuil"]["20"]["jours"]))


if __name__ == "__main__":
    main()
