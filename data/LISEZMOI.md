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

## `registre-interet-general.json`

Comptages mensuels de l'activité tournée vers l'extérieur : accueil, chantiers ouverts,
transmissions, partenariats, documentation publiée et reprise, observations naturalistes
versées aux bases publiques.

**Agrégats mensuels uniquement.** Aucune donnée nominative, aucune coordonnée.

Le format est réutilisable tel quel par d'autres collectifs : la liste `indicateurs` porte
les définitions, la liste `mois` porte les comptages.
