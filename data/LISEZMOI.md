# Données ouvertes — Domaine du Mons

Publiées sous **Licence Ouverte 2.0** (Etalab). Réutilisation libre, y compris commerciale,
avec mention de la source : « Collectif expérimental du Domaine du Mons ».

## `climat-annuel.csv` et `climat.json`

Indicateurs climatiques annuels au point 45,3706 N / 1,938 E (Vitrac-sur-Montane, Corrèze),
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
9 km, altitude du point de modèle 576 m. Les tendances du fichier JSON sont calculées par
test de Mann-Kendall et pente de Sen, avec intervalle de confiance à 95 %.

**Limite à connaître.** Une réanalyse de cette maille ne résout pas un fond de vallée.
Par nuit claire et calme, la température réelle au sol peut descendre 3 à 6 °C sous la valeur
modélisée. Ces séries sont valables pour une **tendance de long terme**, pas pour une alerte
au gel ni pour une valeur ponctuelle.

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
