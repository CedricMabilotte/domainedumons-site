# Données ouvertes — Domaine du Mons

Publiées sous **Licence Ouverte 2.0** (Etalab). Réutilisation libre, y compris commerciale,
avec mention de la source : « Collectif expérimental du Domaine du Mons ».

## `climat-annuel.csv` et `climat.json`

Indicateurs climatiques annuels au point 45,351433 N / 1,931875 E (Domaine du Mons, chemin du Mons, Vitrac-sur-Montane, Corrèze — 588 m),
de 1950 à 2025.

| Colonne | Définition |
|---|---|
| `annee` | Année civile |
| `temperature_moyenne_c` | Moyenne annuelle des températures moyennes quotidiennes |
| `jours_de_gel` | Nombre de jours dont la température minimale est inférieure à 0 °C |
| `jours_tmax_sup_30c` | Nombre de jours dont la température maximale atteint ou dépasse 30 °C |
| `cumul_pluie_mm` | Cumul annuel des précipitations |
| `jours_pluie_sup_1mm` | Nombre de jours dont le cumul atteint ou dépasse 1 mm |
| `deficit_estival_avr_sep_mm` | Somme d'avril à septembre de (ET0 FAO − précipitations). Positif = déficit |
| `derniere_gelee_printemps_jour_annee` | Quantième du dernier jour à minimale ≤ 0 °C avant le 1er juillet |
| `premiere_gelee_automne_jour_annee` | Quantième du premier jour à minimale ≤ 0 °C après le 1er juillet |

**Source primaire** : réanalyse [Open-Meteo](https://open-meteo.com/) (ERA5), maille d'environ
9 km, point de grille à 589 m. Les tendances du fichier JSON sont calculées par test de
Mann-Kendall et pente de Sen, avec intervalle de confiance à 95 %.

**Représentativité.** Le lieu est à 587,5 m sur un replat exposé au sud (pente ~1°), et non en
fond de vallée : dans un rayon de 800 m, 89 % du terrain est plus bas. L'écart entre l'altitude
réelle et celle du point de modèle est inférieur à 2 m, ce qui rend la réanalyse inhabituellement
représentative pour ce site.

**Limites subsistantes.** La maille lisse les extrêmes et représente mal les orages convectifs
d'été. Les parcelles situées en contrebas reçoivent l'air froid drainé des hauteurs et gèlent
plus sévèrement que ne l'indiquent ces séries.

## `releve-quotidien.csv`

Relevé quotidien constitué automatiquement chaque matin, à partir du même point et de la
même station. Une ligne par jour, ajoutée la veille pour le jour écoulé.

| Colonne | Définition | Source |
|---|---|---|
| `date` | Jour du relevé | — |
| `t_min_c`, `t_max_c`, `t_moy_c` | Températures minimale, maximale, moyenne | Open-Meteo |
| `pluie_mm` | Cumul de précipitations | Open-Meteo |
| `etp_mm` | Évapotranspiration de référence (ET0 FAO-56) | Open-Meteo |
| `rafale_max_kmh` | Rafale maximale | Open-Meteo |
| `debit_montane_l_s` | Débit moyen du jour de la Montane, station d'Eyrein (P361401001) | Hub'Eau |
| `secheresse_niveau` | Niveau de restriction le plus élevé applicable | VigiEau |
| `secheresse_zone` | Zone d'alerte concernée | VigiEau |

Une cellule vide signifie que la source était muette ce jour-là. Le relevé n'est jamais
interrompu par l'indisponibilité d'une source.

## `eau.json`

Série longue de l'eau, produite par `scripts/eau.py` à partir de trois API Hub'Eau.

| Clé | Contenu |
|---|---|
| `annees` | Pour chaque année : nombre de jours mesurés, module, médiane, débit minimal et sa date, `vcn3` et `vcn10` (plus faible moyenne sur 3 et 10 jours consécutifs), et pour chaque seuil (50, 20, 10 l/s) le nombre de jours passés en dessous et la date du premier |
| `rang_etiage` | Rang de chaque année sur le VCN10, 1 étant l'étiage le plus sévère |
| `courbe` | Débit journalier de l'année en cours, avec les quantiles 10 / 50 / 90 % du même jour calculés sur toutes les années antérieures |
| `onde` | Observations d'écoulement de la station ONDE la plus proche (6,7 km), et leur résumé annuel |
| `prelevements` | Volumes prélevés sur la commune par année et par ouvrage (BNPE), et les usages déclarés |

**Station** : `P361401001`, la Montane à Eyrein (pont du Geai), 1,2 km, bassin versant 43 km², en service depuis le 1er janvier 1957. Ce sont les données *élaborées* (validées, expertisées), et non le flux temps réel, qui ne conserve qu'un mois.

**Limite** : la station draine 43 km². Elle ne dit rien du chevelu de tête de bassin, qui s'arrête bien avant et repart bien après. Les observations ONDE en donnent une approximation ; seule une mesure locale la remplacerait.

## `analyses.json`

Trois familles d'indicateurs dérivés de la même réanalyse, 1950-2025, calculées par
`scripts/analyses.py`. Chaque série est un tableau `[année, valeur]` ; `tendances` porte la
pente de Sen par décennie, son intervalle de confiance à 95 %, la p-value de Mann-Kendall et
le verdict de significativité ; `normale_1991_2020` la moyenne de référence.

| Clé | Définition |
|---|---|
| `dju` | Degrés-jours unifiés de chauffage, base 18 °C : somme des (18 − température moyenne du jour) positifs, saison du 1er juillet au 30 juin, nommée par son année de fin |
| `jours_chauffes` | Nombre de jours de la saison dont la température moyenne reste sous 18 °C |
| `debourrement` | Quantième du premier jour où le cumul des (température moyenne − 5 °C) positifs depuis le 1er février atteint 80 °C·j |
| `floraison` | Idem, au seuil de 150 °C·j |
| `gelees_apres` | Nombre de jours à minimale ≤ 0 °C entre le débourrement et le 31 mai |
| `gel_destructeur` | Idem, à ≤ −2 °C |
| `gel_floraison` | Nombre de jours à minimale ≤ −1 °C après le stade floraison et avant le 31 mai |
| `tmin_apres` | Température minimale la plus basse atteinte après le débourrement |
| `fenetres` | Nombre de suites d'au moins 3 jours consécutifs à moins de 1 mm de pluie, du 1er mai au 31 juillet |
| `fenetres_larges` | Idem, pour 5 jours et plus |
| `jours_secs_utiles` | Nombre total de jours contenus dans ces suites de 3 jours et plus |
| `plus_longue_suite` | Plus longue suite de jours secs de la période mai-juillet |

`risque_gel` compare trois périodes de trente ans : part des années comptant au moins une
gelée après débourrement, part avec une gelée destructrice, part avec une gelée sur fleur
ouverte.

**Les seuils de stades sont des proxys**, calés pour que les dates médianes correspondent au
débourrement (4 avril) et à la floraison (24 avril) d'un pommier à cette altitude. Ils ne
remplacent pas une observation phénologique. La maille de 9 km lissant les minimales, les
comptages de gelées sont des minorants : ils se lisent en écart entre périodes, pas en valeur
absolue.

## `secheresse-historique.json`

Archive des niveaux de restriction sécheresse applicables au lieu, constituée jour après jour
à partir de la colonne `secheresse_niveau` du relevé quotidien, par `scripts/secheresse.py`.

| Clé | Contenu |
|---|---|
| `par_annee` | Nombre de jours passés à chaque niveau, jours relevés, jours en alerte ou au-delà, et si l'année est complète |
| `bascules` | Chaque changement de niveau, avec sa date |
| `episodes_clos` | Épisodes terminés, avec début et fin |
| `actuel` | Niveau en cours, date de début et ancienneté en jours |

**Pourquoi cette archive existe.** VigiEau publie l'état du jour et ne conserve pas
d'historique ouvert à cette maille : le paramètre de recherche par date renvoie l'arrêté
courant, et aucun jeu de données national ne rejoue la série pour la Corrèze (vérifié le
14 septembre 2026). Une journée non relevée est définitivement perdue. La série commence donc
au premier relevé et ne peut pas être reconstituée en arrière.

## `terrain.json`

Contraintes réglementaires et physiques au point du lieu, produites par `scripts/terrain.py` :
zonage sismique, potentiel radon, exposition au retrait-gonflement des argiles, cavités et
mouvements de terrain dans un rayon de 2 km, arrêtés de catastrophe naturelle, sites et sols
pollués, installations classées à moins de 6 km (Géorisques) ; document d'urbanisme en vigueur
(Géoportail de l'urbanisme) ; faisabilité des sondes géothermiques verticales et ouvrages
déclarés à la Banque du Sous-Sol (BRGM). Les valeurs de sol (`sol`) sont figées : elles
proviennent du site RMQS le plus proche, à 5,1 km, et ne sont pas interrogeables par point.

## `relief.json`

Analyse du modèle numérique de terrain LiDAR HD de l'IGN (vol du 24 août 2022), rééchantillonné
à 2 m sur une fenêtre de 2,4 km, par `scripts/relief.py`.

| Clé | Contenu |
|---|---|
| `point` | Altitude, pente locale et pente du versant ajustée sur 500 m, exposition, position topographique à 100 et 400 m, classe d'accumulation d'air froid, indice d'humidité topographique |
| `fenetre` | Altitudes extrêmes, part du terrain plus bas que le point, part de chaque classe d'air froid, part de couvert ligneux au-dessus de 3 et 10 m, profondeur de la cuvette la plus creuse, dénivelé sous le point dans 400 m |
| `poche_proche` | Distance, dénivelé et direction de la première accumulation d'air froid marquée |

L'indice d'air froid combine la profondeur de cuvette après remplissage des dépressions, la
position topographique, la surface amont et la platitude locale. **C'est un modèle d'écoulement
gravitaire, pas une mesure de température** : il classe des endroits les uns par rapport aux
autres, il ne prédit pas des degrés. Les cartes correspondantes sont `dessins/relief-airfroid.png`
et `dessins/relief-eau.png`.

## `ortho.json`

Emprise et millésimes des photographies aériennes enregistrées dans `dessins/ortho-*.jpg`
par `scripts/ortho.py` : vol du 30 juillet 1959, vol de 1972, orthophotographie actuelle,
sur 900 m de côté autour du chemin du Mons. Source : Géoplateforme IGN.

## `humidite-sol.csv` et `humidite-sol.json`
Humidité du sol au droit du lieu, **du 1er août 1958 à aujourd'hui**, tirée de la réanalyse
SIM2 (SAFRAN-ISBA) de Météo-France. La grille est de 8 km ; la maille retenue est
LAMBX 5720 / LAMBY 20410, centre à 4,2 km du chemin du Mons.
| Colonne du CSV | Définition |
|---|---|
| `date` | Jour |
| `pluie_mm` | Précipitations liquides et solides (PRELIQ + PRENEI) |
| `etp_mm` | Évapotranspiration potentielle du modèle |
| `t_c` | Température moyenne de l'air |
| `swi` | *Soil Wetness Index* — humidité du sol ramenée à la réserve utile. 1 = capacité au champ, 0 = point de flétrissement |
| `sswi_10j` | *Standardised SWI* sur dix jours, **tel que publié à la source**. Il n'est pas utilisé dans les analyses : voir l'avertissement ci-dessous |
| `drainage_mm`, `ruissellement_mm` | Drainage profond et ruissellement de surface simulés |
Le JSON, produit par `scripts/sim2.py`, en tire :
| Clé | Contenu |
|---|---|
| `actuel` | Dernier jour disponible : date, `swi`, `sswi` recalculé, et `rang_jour` = [nombre de valeurs de référence plus sèches, taille de l'échantillon] |
| `courbe` | Pour chaque jour de l'année en cours, le SWI et les quantiles 10 / 50 / 90 % du même jour calculés sur 1958-2020 |
| `annees` | Par année : jours disponibles, jours passés sous −1, −1,5 et −2 écarts-types, SWI moyen de juin à août, plus longue suite consécutive sous −1,5, et si l'année est complète |
| `rang_ete` | Rang de chaque année sur le SWI moyen de l'été, 1 étant l'été le plus sec |
| `episodes` | Suites d'au moins vingt jours consécutifs sous −1,5 écart-type, avec leur durée et le plus bas atteint |
**L'écart à la normale est recalculé, pas repris.** La colonne `sswi_10j` du fichier source
sature : le 16 décembre 1978, où le SWI vaut 0,73, et le 16 décembre 1985, où il vaut 0,57,
y portent la même valeur, −8,169 — deux états de sol différents, un seul chiffre. En hiver, où
le sol est presque toujours à sa capacité, la standardisation part en butée et fabrique des
écarts-types sans signification. Les analyses publiées ici utilisent donc un écart recalculé
par **rang normalisé** : la valeur du jour est située dans l'échantillon de toutes les journées
de 1958 à 2020 situées à moins de dix jours de la même date dans l'année (environ 1 300
valeurs), et ce rang est converti en écart-type. L'indicateur est alors borné par l'échantillon,
et un écart de −3,4 σ veut dire quelque chose de vérifiable : aucune de ces journées de
référence n'a été plus sèche. Le calcul est dans `scripts/sim2.py`, fonction `sswi_maison`.

**Pourquoi cette série en plus de la pluie.** Un cumul de précipitations ne dit pas ce qui reste
dans le sol : une même pluie d'automne recharge la réserve ou part au ruissellement selon l'état
antérieur. Le SWI intègre cet état, et le SSWI dit si le sol est sec *pour la saison* plutôt que
sec dans l'absolu — c'est l'indicateur sur lequel les services de l'État constatent une
sécheresse des sols, au seuil de −1,5.
**Limites.** La maille de 8 km porte un sol moyen : ni le replat du Mons, ni l'acidité et la
saturation en aluminium du complexe d'échange, ni la réserve utile réelle d'une parcelle donnée
n'y figurent. La série se lit en écart d'une année à l'autre, pas en valeur absolue à la
parcelle. Le fichier de mise à jour publié par Météo-France ne conserve que soixante jours ;
l'historique complet a été reconstitué fichier par fichier et n'est pas rejouable rapidement —
d'où sa publication ici.
**Source** : Météo-France, [données SIM quotidiennes](https://www.data.gouv.fr/fr/datasets/donnees-changement-climatique-sim-quotidienne/), Licence Ouverte 2.0.

## `zone-une-heure.json`, `reseau-lieux.json`, `associations.json` et `carte-zone.json`
Les quatre fichiers de la page **Le réseau**, produits par `scripts/reseau.py` et
`scripts/carte.py`. La « zone d'une heure » est approchée par un rayon de **45 km à vol
d'oiseau** autour du lieu : sur ces routes de moyenne montagne, une heure porte plus loin vers
Tulle que vers le plateau, et aucune approximation simple ne corrige cela.
| Fichier | Contenu |
|---|---|
| `zone-une-heure.json` | Les 284 communes dont le chef-lieu est dans le rayon, avec code INSEE, nom, coordonnées et population ; total et population cumulée |
| `reseau-lieux.json` | Les 191 lieux portés par des collectifs déjà référencés dans la zone : nom, commune, coordonnées, distance, catégories d'origine, carte source et date de la fiche |
| `associations.json` | Comptage des associations actives de la zone : total, par commune, par thème, par décennie de création, et la liste des noms dont l'objet apparent dépasse le cercle des membres |
| `carte-zone.json` | Paramètres de la projection équirectangulaire locale utilisée par `dessins/zone.svg`, pour replacer n'importe quel point sur la carte |
**Les lieux** viennent de [Transiscope](https://transiscope.org/), qui agrège une vingtaine de
cartes d'alternatives (Près de chez nous, Colibris, Alternatiba, réseau des ressourceries,
Longue vie aux objets). **Aucune fiche n'a été vérifiée sur place** : certaines datent de 2017,
un lieu peut avoir fermé, changé d'objet, ou ne plus vouloir y figurer. Les catégories affichées
sont celles des cartes d'origine. Toute personne concernée peut demander correction ou retrait à
contact@actitude.org ; le retrait est fait sans discussion.
**Les associations** viennent de l'[annuaire public des entreprises et
associations](https://recherche-entreprises.api.gouv.fr/), activité 94.99Z, établissements
actifs. Le classement par thème repose sur les **mots du nom déposé** : c'est un repérage
grossier, pas une qualification d'intérêt général — laquelle ne se décide ni sur un nom ni sur
un code d'activité, mais sur les faits.
**Ce qui est publié, et rien de plus** : le nom de l'association, sa commune et son année de
création, tels qu'ils figurent déjà au Journal officiel. Aucune adresse, aucun nom de dirigeant,
aucun recoupement entre sources.
**Le fond de carte** est un fichier du dépôt : aucune tuile distante, aucun traceur.
Contours communaux de [geo.api.gouv.fr](https://geo.api.gouv.fr/), simplifiés par
Douglas-Peucker à 0,0045°.

## `registre-interet-general.json`

Comptages mensuels de l'activité tournée vers l'extérieur : accueil, chantiers ouverts,
transmissions, partenariats, documentation publiée et reprise, observations naturalistes
versées aux bases publiques.

**Agrégats mensuels uniquement.** Aucune donnée nominative, aucune coordonnée.

Le format est réutilisable tel quel par d'autres collectifs : la liste `indicateurs` porte
les définitions, la liste `mois` porte les comptages.
