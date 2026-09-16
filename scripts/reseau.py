#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Le réseau autour du Domaine du Mons.

Trois jeux de données, tous publics :

  1. `zone-une-heure.json` — les communes situées à une heure de route, approchées
     par 45 km à vol d'oiseau (source : geo.api.gouv.fr) ;
  2. `reseau-lieux.json`   — les lieux portés par des collectifs déjà référencés
     sur Transiscope, l'agrégateur des cartes d'alternatives ;
  3. `associations.json`   — le décompte des associations de la zone, par commune
     et par thème, à partir de l'annuaire des entreprises et associations.

**Rien de nominatif au-delà de ce qui est déjà publié au Journal officiel** :
nom de l'association, commune, année de création. Ni dirigeants, ni adresses.

Usage : python3 scripts/reseau.py [--zone] [--lieux] [--assos]
        sans option, les trois.
"""
import json, math, os, sys, time, unicodedata, urllib.parse, urllib.request
from datetime import date

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAT, LON = 45.351433, 1.931875
RAYON = 45                      # km à vol d'oiseau ≈ 1 h de route sur ces routes
DEPS = ["19", "23", "87", "15", "63", "24", "46"]
UA = {"User-Agent": "domainedumons.actitude.org/1.0"}


def get(url, essais=3, attente=1.5):
    for i in range(essais):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return json.load(r)
        except Exception as e:
            if i == essais - 1:
                raise
            time.sleep(attente * (i + 1))


def km(la, lo):
    try:
        return 6371 * math.acos(min(1, math.sin(math.radians(LAT)) * math.sin(math.radians(la))
                     + math.cos(math.radians(LAT)) * math.cos(math.radians(la))
                     * math.cos(math.radians(lo - LON))))
    except (TypeError, ValueError):
        return 1e9


def sortie(nom):
    return os.path.join(RACINE, "data", nom)


# ------------------------------------------------------------------ la zone
def zone():
    out = {}
    for d in DEPS:
        c = get("https://geo.api.gouv.fr/departements/%s/communes"
                "?fields=nom,code,population,centre,codeDepartement" % d)
        for x in c:
            ce = x.get("centre")
            if not ce:
                continue
            lo, la = ce["coordinates"]
            dist = km(la, lo)
            if dist <= RAYON:
                out[x["code"]] = {"nom": x["nom"], "dep": x["codeDepartement"],
                                  "pop": x.get("population") or 0,
                                  "lat": round(la, 5), "lon": round(lo, 5), "km": round(dist, 1)}
        print("  %s : %d communes retenues au total" % (d, len(out)))
    res = {"methode": "communes dont le centre est à moins de %d km du chemin du Mons, "
                      "approximation d'une heure de route" % RAYON,
           "source": "geo.api.gouv.fr (découpage administratif, Licence Ouverte 2.0)",
           "rayon_km": RAYON, "communes": out,
           "total": len(out), "population": sum(v["pop"] for v in out.values()),
           "calcule_le": date.today().isoformat()}
    json.dump(res, open(sortie("zone-une-heure.json"), "w"), ensure_ascii=False, separators=(",", ":"))
    print("  %d communes, %d habitants" % (res["total"], res["population"]))
    return res


# ------------------------------------------------------- les lieux collectifs
def lieux():
    u = ("https://transiscope.gogocarto.fr/api/elements.json?bounds=%s" %
         urllib.parse.quote("1.20,44.90,2.70,45.85"))
    d = get(u)
    brut = d.get("data") or d
    out = []
    for e in brut:
        g = e.get("geo") or {}
        la, lo = g.get("latitude"), g.get("longitude")
        if la is None or lo is None:
            continue
        dist = km(float(la), float(lo))
        if dist > RAYON:
            continue
        a = e.get("address") or {}
        fiche = {
            "id": e.get("id"), "nom": (e.get("name") or "").strip(),
            "lat": round(float(la), 5), "lon": round(float(lo), 5),
            "km": round(dist, 1),
            "commune": a.get("addressLocality"), "cp": a.get("postalCode"),
            "source": e.get("sourceKey"),
            "categories": [c for c in (e.get("categories") or [])
                           if c not in ("CC-By-SA", "Alternatives", "Près De Chez Nous")][:6],
            "maj": (e.get("updatedAt") or "")[:10],
        }
        # La fiche de contact, moins le courriel et le téléphone. Ces deux-là
        # sont publics à la source, mais pour un petit collectif le courriel est
        # souvent la boîte personnelle de quelqu'un : la republier sur un
        # nouveau site l'expose aux aspirateurs d'adresses sans rien apporter.
        # Ils restent à un clic, sur la fiche d'origine.
        site = (e.get("website") or e.get("site") or "").strip()
        if site.startswith(("http://", "https://")):
            fiche["site"] = site
        desc = (e.get("abstract") or e.get("description") or "").strip()
        if desc:
            fiche["decrit"] = " ".join(desc.split())[:400]
        # openHours arrive tantôt en chaîne, tantôt en dictionnaire par jour
        oh = e.get("openHours")
        if isinstance(oh, dict):
            JOURS = [("Mo", "lun"), ("Tu", "mar"), ("We", "mer"), ("Th", "jeu"),
                     ("Fr", "ven"), ("Sa", "sam"), ("Su", "dim")]
            bouts = []
            for k, court in JOURS:
                v = oh.get(k)
                if not v:
                    continue
                if isinstance(v, list):
                    v = ", ".join(str(x) for x in v if x)
                v = " ".join(str(v).split())
                if v:
                    bouts.append("%s %s" % (court, v))
            heures = " · ".join(bouts)
        else:
            heures = " ".join(str(oh or "").split())
        if heures:
            fiche["heures"] = heures[:200]
        origine = (e.get("showUrl") or "").strip()
        if origine.startswith(("http://", "https://")):
            fiche["origine"] = origine
        out.append(fiche)
    # Transiscope ne renseigne pas toujours la commune : on prend alors la plus proche
    try:
        z = json.load(open(sortie("zone-une-heure.json")))["communes"]
    except Exception:
        z = {}
    for l in out:
        if not l["commune"] and z:
            proche = min(z.values(), key=lambda c: (c["lat"] - l["lat"]) ** 2 + (c["lon"] - l["lon"]) ** 2)
            l["commune"] = proche["nom"]
            l["commune_deduite"] = True
    out.sort(key=lambda x: x["km"])
    res = {"source": "Transiscope / GoGoCarto, agrégateur des cartes d'alternatives",
           "licence_source": "CC BY-SA",
           "rayon_km": RAYON, "total": len(out), "lieux": out,
           "avertissement": "Reprise brute d'un agrégateur. Aucune fiche n'a été vérifiée sur place, "
                            "et certaines datent de plusieurs années. Chaque lieu peut demander "
                            "correction ou retrait.",
           "calcule_le": date.today().isoformat()}
    json.dump(res, open(sortie("reseau-lieux.json"), "w"), ensure_ascii=False, separators=(",", ":"))
    print("  %d lieux dans %d km" % (len(out), RAYON))
    par_commune = {}
    for l in out:
        par_commune[l["commune"]] = par_commune.get(l["commune"], 0) + 1
    for c, n in sorted(par_commune.items(), key=lambda x: -x[1])[:8]:
        print("    %-28s %d" % (c, n))
    return res


# --------------------------------------------------------- les associations
THEMES = {
    "terre et vivant": ["environnement", "nature", "ecolog", "biodivers", "riviere", "foret",
                        "arbre", "jardin", "permacultur", "paysan", "agricol", "semence",
                        "abeille", "apicol", "apicult", "verger", "sol vivant", "terre"],
    "éducation et culture": ["education", "ecole", "formation", "savoir", "transmission",
                             "biblioth", "mediath", "culturel", "culture", "theatre", "musique",
                             "cinema", "lecture", "patrimoine", "memoire"],
    "solidarité et accueil": ["solidarit", "entraide", "secours", "accueil", "insertion",
                              "epicerie", "alimentaire", "migrant", "handicap", "aidant",
                              "sante", "soin", "social"],
    "habitat et lieux partagés": ["habitat", "tiers-lieu", "tiers lieu", "cooperat", "commun",
                                  "collectif", "hameau", "foyer", "atelier partage", "recyclerie",
                                  "ressourcerie"],
}


def sans_accents(t):
    return "".join(c for c in unicodedata.normalize("NFD", (t or "").lower())
                   if unicodedata.category(c) != "Mn")


def theme_de(nom):
    n = sans_accents(nom)
    trouves = [t for t, mots in THEMES.items() if any(m in n for m in mots)]
    return trouves


def assos(zone_res):
    communes = zone_res["communes"]
    page, total, brut = 1, None, []
    while True:
        u = ("https://recherche-entreprises.api.gouv.fr/near_point?lat=%s&long=%s&radius=%d"
             "&activite_principale=94.99Z&page=%d&per_page=25" % (LAT, LON, RAYON, page))
        d = get(u)
        total = d.get("total_results")
        res = d.get("results") or []
        if not res:
            break
        brut.extend(res)
        if page % 20 == 0:
            print("    page %d / %d" % (page, d.get("total_pages")))
        if page >= d.get("total_pages", 1) or page >= 400:
            break
        page += 1
        time.sleep(0.12)
    print("  %d fiches lues (annoncées : %s)" % (len(brut), total))

    vues, retenues = set(), []
    par_commune, par_theme, par_decennie = {}, {}, {}
    for e in brut:
        siren = e.get("siren")
        if siren in vues:
            continue
        vues.add(siren)
        if e.get("etat_administratif") == "C":
            continue
        # l'établissement retenu est celui qui se trouve dans la zone
        loc = None
        for m in (e.get("matching_etablissements") or []):
            if m.get("etat_administratif") == "F":
                continue
            code = m.get("commune")
            if code in communes:
                loc = m
                break
        if loc is None:
            continue
        code = loc["commune"]
        nom = (e.get("nom_complet") or "").strip()
        annee = (e.get("date_creation") or "")[:4]
        par_commune[code] = par_commune.get(code, 0) + 1
        if annee.isdigit():
            dec = "%s0" % annee[:3]
            par_decennie[dec] = par_decennie.get(dec, 0) + 1
        ths = theme_de(nom)
        for t in ths:
            par_theme[t] = par_theme.get(t, 0) + 1
        if ths:
            retenues.append({"nom": nom, "commune": communes[code]["nom"], "code": code,
                             "annee": annee, "themes": ths,
                             "km": communes[code]["km"]})
    retenues.sort(key=lambda x: (x["km"], x["nom"]))
    res = {
        "source": "annuaire des entreprises et associations (recherche-entreprises.api.gouv.fr), "
                  "activité 94.99Z, données issues du répertoire SIRENE et du Journal officiel",
        "rayon_km": RAYON,
        "total_zone": len(vues and par_commune) and sum(par_commune.values()),
        "par_commune": par_commune, "par_theme": par_theme, "par_decennie": par_decennie,
        "themes": {t: mots[:6] for t, mots in THEMES.items()},
        "retenues": retenues,
        "avertissement": "Le classement par thème repose sur les mots du nom déposé. "
                         "C'est un repérage grossier, pas une qualification d'intérêt général, "
                         "qui ne se décide ni sur un nom ni sur un code d'activité.",
        "donnees_publiees": "nom, commune et année de création — tels qu'ils figurent déjà "
                            "au Journal officiel des associations. Aucune adresse, aucun dirigeant.",
        "calcule_le": date.today().isoformat(),
    }
    json.dump(res, open(sortie("associations.json"), "w"), ensure_ascii=False, separators=(",", ":"))
    print("  %d associations actives localisées dans la zone" % sum(par_commune.values()))
    print("  dont %d dont le nom évoque un objet d'intérêt général :" % len(retenues))
    for t, n in sorted(par_theme.items(), key=lambda x: -x[1]):
        print("    %-30s %d" % (t, n))
    return res


def main():
    args = sys.argv[1:]
    tout = not args
    z = None
    if tout or "--zone" in args:
        print("zone d'une heure…")
        z = zone()
    if z is None:
        z = json.load(open(sortie("zone-une-heure.json")))
    if tout or "--lieux" in args:
        print("lieux collectifs…")
        lieux()
    if tout or "--assos" in args:
        print("associations…")
        assos(z)


if __name__ == "__main__":
    main()
