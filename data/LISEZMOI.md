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

## `registre-interet-general.json`

Comptages mensuels de l'activité tournée vers l'extérieur : accueil, chantiers ouverts,
transmissions, partenariats, documentation publiée et reprise, observations naturalistes
versées aux bases publiques.

**Agrégats mensuels uniquement.** Aucune donnée nominative, aucune coordonnée.

Le format est réutilisable tel quel par d'autres collectifs : la liste `indicateurs` porte
les définitions, la liste `mois` porte les comptages.
