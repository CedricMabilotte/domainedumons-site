#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Le recensement associatif de la zone d'une heure, à la source.

Pourquoi ce script existe : la première version comptait les associations dans
l'annuaire des entreprises (SIRENE, activité 94.99Z). C'était faux d'un facteur
quatre. Une association n'a de numéro SIREN que si elle emploie, perçoit des
subventions publiques ou est assujettie à la TVA — environ une sur quatre. Le
registre qui recense les associations, lui, est le RNA. Voir le retex RX-04.

Trois étapes :
  1. extraire du dump Waldec du ministère de l'Intérieur les départements que
     la zone recoupe, par requêtes de plage sur le zip distant : une quinzaine
     de mégaoctets au lieu de quatre cents ;
  2. retenir les associations actives dont l'adresse est dans une commune de la
     zone, et joindre la nomenclature officielle d'objet social de la DILA ;
  3. fusionner les verdicts de lecture (data/lecture-associations.json) et
     écrire les trois jeux publiés.

La lecture elle-même n'est pas dans ce script : chaque objet déclaré du vivier
a été lu un par un contre scripts/GRILLE-ASSOCIATIONS.md. Un mot-clé ne
qualifie pas un intérêt général — c'est précisément l'erreur qu'on corrige.

Usage : python3 scripts/assos.py [--extraire] [--construire]
        --extraire   retélécharge les départements depuis media.interieur.gouv.fr
        --construire recalcule les JSON depuis le cache et les verdicts
        sans option, les deux.
"""
import csv, io, json, os, struct, subprocess, sys, urllib.request, zlib
from datetime import date

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(RACINE, ".cache-rna")
MILLESIME = "20260901"
ZIP = "https://media.interieur.gouv.fr/rna/rna_waldec_%s.zip" % MILLESIME
NOMEN = ("https://journal-officiel-datadila.opendatasoft.com/api/explore/v2.1"
         "/catalog/datasets/joafe_domaine_activite/exports/json")
DEPS = ["19", "23", "87", "15", "63", "24", "46"]
UA = {"User-Agent": "domainedumons.actitude.org/1.0"}

# Les familles de la nomenclature officielle susceptibles de porter un fait
# d'intérêt général. Elles ne suffisent pas à retenir — elles délimitent le
# vivier à lire. Les autres familles y entrent par le repérage de mots.
CHAUDES = {"003000", "005000", "009000", "010000", "015000", "016000", "017000",
           "018000", "019000", "020000", "021000", "022000", "024000", "030000",
           "032000", "036000"}


def plage(url, a, b):
    return subprocess.run(["curl", "-sS", "--retry", "8", "--retry-all-errors",
                           "-r", "%d-%d" % (a, b), url], capture_output=True).stdout


def extraire():
    """Ne tire du zip distant que les membres voulus, par requêtes de plage.

    Le zip national fait 408 Mo pour 1,46 Go décompressés. On lit le catalogue
    central en fin de fichier, on y trouve l'offset de chaque membre, et on ne
    récupère que les sept qui nous concernent.
    """
    os.makedirs(CACHE, exist_ok=True)
    tete = subprocess.run(["curl", "-sSI", url_final(ZIP)], capture_output=True, text=True).stdout
    total = int([l for l in tete.lower().splitlines() if l.startswith("content-length:")][-1].split()[1])
    queue = plage(ZIP, max(0, total - 500000), total - 1)
    i = queue.rfind(b"PK\x05\x06")
    taille_cat, debut_cat = struct.unpack("<II", queue[i + 12:i + 20])
    cat = plage(ZIP, debut_cat, debut_cat + taille_cat - 1)
    p, membres = 0, []
    while p + 46 <= len(cat) and cat[p:p + 4] == b"PK\x01\x02":
        comp, decomp = struct.unpack("<II", cat[p + 20:p + 28])
        n, m, k = struct.unpack("<HHH", cat[p + 28:p + 34])
        offset = struct.unpack("<I", cat[p + 42:p + 46])[0]
        membres.append((cat[p + 46:p + 46 + n].decode("utf8", "replace"), offset, comp))
        p += 46 + n + m + k
    for d in DEPS:
        cible = "dpt_%s.csv" % d
        for nom, offset, comp in membres:
            if not nom.endswith(cible):
                continue
            dest = os.path.join(CACHE, os.path.basename(nom))
            if os.path.exists(dest):
                print("  %s : déjà en cache" % d)
                break
            en_tete = plage(ZIP, offset, offset + 29)
            n2, m2 = struct.unpack("<HH", en_tete[26:30])
            brut = plage(ZIP, offset + 30 + n2 + m2, offset + 30 + n2 + m2 + comp - 1)
            open(dest, "wb").write(zlib.decompressobj(-15).decompress(brut))
            print("  %s : %.1f Mo" % (d, os.path.getsize(dest) / 1e6))
            break
    n = os.path.join(CACHE, "nomenclature.json")
    if not os.path.exists(n):
        subprocess.run(["curl", "-sS", "--retry", "5", "--retry-all-errors", "-o", n, NOMEN])
        print("  nomenclature : %d codes" % len(json.load(open(n))))


def url_final(u):
    return u


def construire():
    zone = json.load(open(os.path.join(RACINE, "data", "zone-une-heure.json")))
    communes = zone["communes"]
    nomen = {x["id_domaine_6car"]: x["domaine_libelle"]
             for x in json.load(open(os.path.join(CACHE, "nomenclature.json")))}
    lecture = json.load(open(os.path.join(RACINE, "data", "lecture-associations.json")))["lecture"]

    actives, hors, dissoutes = [], 0, 0
    for f in sorted(os.listdir(CACHE)):
        if not f.endswith(".csv"):
            continue
        with open(os.path.join(CACHE, f), encoding="utf-8-sig", newline="") as fh:
            for r in csv.DictReader(fh, delimiter=";"):
                if r["adrs_codeinsee"] not in communes:
                    hors += 1
                    continue
                if r["position"] != "A":
                    dissoutes += 1
                    continue
                actives.append(r)
    print("  %d associations actives dans la zone (%d hors zone, %d dissoutes)"
          % (len(actives), hors, dissoutes))

    def fam(r):
        return r["objet_social1"][:3] + "000"

    par_commune, par_famille, par_decennie = {}, {}, {}
    for r in actives:
        c = r["adrs_codeinsee"]
        par_commune[c] = par_commune.get(c, 0) + 1
        par_famille[fam(r)] = par_famille.get(fam(r), 0) + 1
        a = r["date_creat"][:4]
        if a.isdigit() and a != "0001":
            d = a[:3] + "0"
            par_decennie[d] = par_decennie.get(d, 0) + 1

    retenues, douteuses, ecartees = [], [], 0
    par_fait, lues = {}, 0
    for r in sorted(actives, key=lambda x: (communes[x["adrs_codeinsee"]]["km"], x["titre"])):
        v = lecture.get(r["id"])
        if not v:
            continue
        lues += 1
        e = {"rna": r["id"], "nom": r["titre"],
             "commune": communes[r["adrs_codeinsee"]]["nom"], "code": r["adrs_codeinsee"],
             "km": communes[r["adrs_codeinsee"]]["km"],
             "annee": r["date_creat"][:4] if r["date_creat"][:4].isdigit() else "",
             "famille": nomen.get(fam(r), "")}
        if r.get("siteweb", "").strip():
            e["site"] = r["siteweb"].strip()
        if v["v"] == "retenu":
            e["faits"] = v.get("f") or []
            e["lecture"] = v.get("n", "")
            for x in e["faits"]:
                par_fait[x] = par_fait.get(x, 0) + 1
            retenues.append(e)
        elif v["v"] == "douteux":
            douteuses.append(e)
        else:
            ecartees += 1

    commun = {
        "source": "Répertoire national des associations (RNA), dump Waldec du 1er septembre 2026, "
                  "ministère de l'Intérieur — associations dont le siège déclaré est dans une commune "
                  "de la zone et dont la position est « active »",
        "nomenclature": "familles officielles d'objet social du Journal officiel des associations (DILA)",
        "rayon_km": zone["rayon_km"], "communes_zone": zone["total"],
        "population_zone": zone["population"],
        "calcule_le": date.today().isoformat(),
    }
    res = dict(commun)
    res.update({
        "actives": len(actives), "lues": lues,
        "par_commune": par_commune, "par_famille": par_famille,
        "par_decennie": dict(sorted(par_decennie.items())),
        "familles": {c: nomen.get(c, c) for c in par_famille},
        "verdicts": {"retenu": len(retenues), "douteux": len(douteuses), "hors": ecartees},
        "par_fait": par_fait, "retenues": retenues,
        "methode": "Chaque objet déclaré du vivier a été lu et classé un par un contre une grille "
                   "écrite d'avance (scripts/GRILLE-ASSOCIATIONS.md). Le vivier réunit les familles "
                   "officielles susceptibles de porter un fait d'intérêt général, plus les "
                   "associations des autres familles dont l'objet en portait plusieurs.",
        "avertissement": "La grille lit une déclaration, pas une pratique. Une association peut "
                         "déclarer un objet généreux et ne plus rien faire depuis quinze ans ; une "
                         "autre peut rendre un service réel sous un objet sec. Aucune n'a été "
                         "vérifiée sur place. « Active » veut dire ici : qui n'a pas déclaré sa "
                         "dissolution.",
        "donnees_publiees": "nom, numéro RNA, commune, année de création, famille déclarée — tous "
                            "publiés au Journal officiel des associations. Aucune adresse, aucun "
                            "dirigeant, aucun contact.",
    })
    ecrire("associations.json", res)
    d2 = dict(commun)
    d2.update({
        "explication": "Associations dont l'objet déclaré laisse un doute réel : un fait apparaît "
                       "mais le bénéficiaire reste le cercle, ou l'objet est trop vague pour "
                       "trancher. Elles sont publiées parce qu'un doute affiché vaut mieux qu'un "
                       "tri silencieux.",
        "total": len(douteuses), "douteuses": douteuses,
    })
    ecrire("associations-douteuses.json", d2)
    print("  retenues %d · douteuses %d · écartées %d" % (len(retenues), len(douteuses), ecartees))
    print("  faits :", ", ".join("%s %d" % (k, v) for k, v in sorted(par_fait.items(), key=lambda x: -x[1])))


def ecrire(nom, obj):
    f = os.path.join(RACINE, "data", nom)
    json.dump(obj, open(f, "w"), ensure_ascii=False, separators=(",", ":"))
    print("  %s : %d octets" % (nom, os.path.getsize(f)))


def main():
    tout = len(sys.argv) == 1
    if tout or "--extraire" in sys.argv:
        extraire()
    if tout or "--construire" in sys.argv:
        construire()


main()
