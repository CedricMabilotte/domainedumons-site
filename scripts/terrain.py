#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Le terrain du Domaine du Mons — contraintes réglementaires et physiques.

Construit data/terrain.json : ce qui commande la construction, la plantation
et le forage à cet endroit précis. Sources interrogées :
  - Géorisques (sismicité, radon, retrait-gonflement des argiles, cavités,
    mouvements de terrain, arrêtés de catastrophe naturelle, sites et sols
    pollués, installations classées) ;
  - API Carto / Géoportail de l'urbanisme (document d'urbanisme en vigueur) ;
  - BRGM, géothermie de minime importance (faisabilité des sondes verticales) ;
  - BRGM, Banque du Sous-Sol (forages et puits déclarés autour du point).

Les valeurs du sol viennent du Réseau de Mesures de la Qualité des Sols et
sont figées dans ce fichier : le site RMQS le plus proche est à 5,1 km et son
jeu de données n'est pas interrogeable par point.

Usage : python3 scripts/terrain.py
"""
import json, math, os, sys, urllib.parse, urllib.request
from datetime import date

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SORTIE = os.path.join(RACINE, "data", "terrain.json")
LAT, LON = 45.351433, 1.931875
INSEE = "19287"
UA = {"User-Agent": "domainedumons.actitude.org/1.0"}


def get(url, timeout=60):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return json.load(r)


def km(la, lo):
    return round(6371 * math.acos(min(1, math.sin(math.radians(LAT)) * math.sin(math.radians(la))
                + math.cos(math.radians(LAT)) * math.cos(math.radians(la))
                * math.cos(math.radians(lo - LON)))), 2)


def georisques():
    B = "https://www.georisques.gouv.fr/api/v1/"
    ll = "latlon=%s%%2C%s" % (LON, LAT)
    out = {}
    d = get(B + "zonage_sismique?code_insee=" + INSEE)["data"]
    out["sismicite"] = d[0]["zone_sismicite"] if d else None
    d = get(B + "radon?code_insee=" + INSEE)["data"]
    out["radon"] = d[0]["classe_potentiel"] if d else None
    out["argiles"] = get(B + "rga?" + ll)
    for cle, ep in (("cavites", "cavites"), ("mouvements", "mvt")):
        try:
            out[cle] = get(B + ep + "?" + ll + "&rayon=2000&page_size=20").get("results", 0)
        except Exception:
            out[cle] = None
    try:
        out["risques_gaspar"] = get(B + "gaspar/risques?code_insee=" + INSEE).get("results", 0)
    except Exception:
        out["risques_gaspar"] = None
    cat = get(B + "gaspar/catnat?code_insee=" + INSEE + "&page_size=50").get("data", [])
    vus, arretes = set(), []
    for c in cat:
        cle = (c["date_debut_evt"], c["libelle_risque_jo"])
        if cle in vus:
            continue
        vus.add(cle)
        arretes.append({"debut": c["date_debut_evt"], "fin": c.get("date_fin_evt"),
                        "risque": c["libelle_risque_jo"]})
    arretes.sort(key=lambda a: a["debut"][-4:], reverse=True)
    out["catnat"] = arretes
    # installations classées : on ne garde que les plus proches, sans les inspections
    icpe = []
    for page in (1, 2):
        try:
            d = get(B + "installations_classees?" + ll + "&rayon=6000&page=%d&page_size=20" % page)
        except Exception:
            break
        for i in d.get("data", []):
            if i.get("latitude") is None:
                continue
            icpe.append({"nom": i.get("raisonSociale"), "commune": i.get("commune"),
                         "regime": i.get("regime"), "distance_km": km(i["latitude"], i["longitude"]),
                         "porcs": bool(i.get("porcs")), "bovins": bool(i.get("bovins")),
                         "volailles": bool(i.get("volailles")), "carriere": bool(i.get("carriere")),
                         "seveso": i.get("statutSeveso")})
        if page >= d.get("total_pages", 1):
            break
    icpe.sort(key=lambda i: i["distance_km"])
    out["icpe"] = icpe[:8]
    try:
        s = get(B + "ssp?" + ll + "&rayon=5000")
        cas = s.get("casias", {}).get("data", [])
        out["sites_pollues"] = sorted(
            [{"nom": c.get("nom_etablissement"), "commune": c.get("nom_commune"),
              "statut": c.get("statut"),
              "distance_km": km(c["geom"]["coordinates"][1], c["geom"]["coordinates"][0])}
             for c in cas if c.get("geom")], key=lambda c: c["distance_km"])[:5]
        out["sites_pollues_total"] = s.get("casias", {}).get("results", 0)
    except Exception as e:
        print("  sites pollués : %s" % e, file=sys.stderr)
    return out


def urbanisme():
    try:
        d = get("https://apicarto.ign.fr/api/gpu/municipality?insee=" + INSEE)
        f = d.get("features", [])
        p = f[0]["properties"] if f else {}
        return {"rnu": bool(p.get("is_rnu")), "nom": p.get("name")}
    except Exception as e:
        print("  urbanisme : %s" % e, file=sys.stderr)
        return None


def geothermie():
    """Faisabilité des sondes géothermiques verticales. Ce service ne sert
    que du GML : on lit les balises qui nous intéressent."""
    import re
    u = ("http://mapsref.brgm.fr/wxs/geothermie/gmi_total?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature"
         "&TYPENAMES=ms:GMI_SONDE_200m_WFS&SRSNAME=urn:ogc:def:crs:EPSG::4326"
         "&BBOX=%f,%f,%f,%f,urn:ogc:def:crs:EPSG::4326" % (LAT - 0.0005, LON - 0.0005, LAT + 0.0005, LON + 0.0005))
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60) as r:
            xml = r.read().decode("utf-8", "replace")
        bloc = xml.split("<ms:GMI_SONDE_200m_WFS ")[1] if "<ms:GMI_SONDE_200m_WFS " in xml else ""
        def champ(n):
            m = re.search(r"<ms:%s>([^<]*)</ms:%s>" % (n, n), bloc)
            return m.group(1) if m else None
        exclusions = [c for c in ("evaporite", "cavites_mines", "cavites_autres", "mvt",
                                  "pollution_averee", "artesianisme", "communication_aquifere",
                                  "remontee_nappe") if (champ(c) or "0") != "0"]
        return {"sonde_200m": champ("sonde_value_id_couleur"),
                "carte": champ("type_carte"),
                "profondeur": champ("profondeur"),
                "exclusions": exclusions}
    except Exception as e:
        print("  géothermie : %s" % e, file=sys.stderr)
        return None


def forages():
    u = ("http://geoservices.brgm.fr/geologie?service=WFS&version=2.0.0&request=GetFeature"
         "&typeNames=ms:BSS_EAU_POINT&srsName=EPSG:4326&outputFormat=geojson"
         "&bbox=%f,%f,%f,%f,EPSG:4326" % (LAT - 0.03, LON - 0.03, LAT + 0.03, LON + 0.03))
    try:
        out = []
        for f in get(u).get("features", []):
            c = f["geometry"]["coordinates"]
            la, lo = (c[1], c[0]) if abs(c[0]) < 10 else (c[0], c[1])
            p = f["properties"]
            prof = p.get("prof_invest")
            out.append({"code": p.get("code_bss"), "nature": p.get("nature_pe"),
                        "lieu": (p.get("adresse") or "").title(),
                        "profondeur_m": float(prof) if prof else None,
                        "distance_km": km(la, lo)})
        out.sort(key=lambda o: o["distance_km"])
        return out[:10]
    except Exception as e:
        print("  BSS : %s" % e, file=sys.stderr)
        return None


# Valeurs figées, vérifiées le 14/09/2026 — voir DONNEES-DU-POINT
SOL_RMQS = {
    "site_distance_km": 5.1, "annee": 2006, "horizon": "0-30 cm",
    "texture": "limon argilo-sableux", "argile_g_kg": 263,
    "ph_eau": 4.7, "matiere_organique_g_kg": 165, "cec_cmol_kg": 5.37,
    "aluminium_echangeable_cmol_kg": 4.15, "calcium_cmol_kg": 0.44,
    "magnesium_cmol_kg": 0.32, "potassium_cmol_kg": 0.328,
    "phosphore_assimilable": "sous le seuil de détection",
    "source": "Réseau de Mesures de la Qualité des Sols (RMQS), doi:10.15454/QSXKGA",
}
ZONAGES = {
    "frr": "FRR+", "frr_date": "10/07/2025",
    "pnr": "Parc naturel régional de Millevaches en Limousin",
    "source_frr": "DDT de la Corrèze, couche N_FRR_2025",
}


def main():
    out = {"point": [LAT, LON], "altitude_m": 588, "commune": "Vitrac-sur-Montane",
           "insee": INSEE, "calcule_le": date.today().isoformat()}
    print("Géorisques…")
    out["risques"] = georisques()
    print("urbanisme…")
    out["urbanisme"] = urbanisme()
    print("géothermie…")
    out["geothermie"] = geothermie()
    print("forages et puits…")
    out["forages"] = forages()
    out["sol"] = SOL_RMQS
    out["zonages"] = ZONAGES
    os.makedirs(os.path.dirname(SORTIE), exist_ok=True)
    json.dump(out, open(SORTIE, "w"), ensure_ascii=False, separators=(",", ":"))
    r = out["risques"]
    print("\n  sismicité      %s" % r.get("sismicite"))
    print("  radon          classe %s" % r.get("radon"))
    print("  argiles        %s" % (r.get("argiles") or {}).get("exposition"))
    print("  cavités        %s   mouvements %s" % (r.get("cavites"), r.get("mouvements")))
    print("  arrêtés CatNat %d" % len(r.get("catnat", [])))
    print("  ICPE ≤ 6 km    %d, la plus proche à %s km" % (
        len(r.get("icpe", [])), r["icpe"][0]["distance_km"] if r.get("icpe") else "—"))
    print("  urbanisme      %s" % ("RNU" if (out["urbanisme"] or {}).get("rnu") else "document en vigueur"))
    print("  géothermie     %s" % out.get("geothermie"))
    if out.get("forages"):
        for f in out["forages"][:4]:
            print("  %-5s %s à %.2f km, profondeur %s" % (f["nature"], f["code"], f["distance_km"], f["profondeur_m"]))
    print("\n%s : %d octets" % (SORTIE, len(open(SORTIE).read())))


if __name__ == "__main__":
    main()
