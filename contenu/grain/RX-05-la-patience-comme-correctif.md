---
type: retex
code: RX-05
généricité: GÉNÉRIQUE
licence: CC BY-SA 4.0
date: 2026-09-17
source: claude/grain/retex/RX-05-la-patience-comme-correctif.md, exporté le 2026-09-24
---

# RX-05 — Le correctif était d'attendre, pas de changer de code

*Retour d'expérience. Une extraction de données abandonnée un jour, réussie le lendemain sans qu'une ligne de la requête ait changé.*

---

## Ce qui devait arriver

Ajouter l'eau — rivières, plans d'eau — au fond de la carte du réseau, en l'extrayant d'OpenStreetMap par l'API Overpass au moment de la publication. Le code était écrit et testé sur les couches précédentes, routes et toponymes, qui étaient passées sans incident.

## Ce qui s'est passé

L'extraction a rendu `504 Gateway Timeout`. Réessai immédiat : `504`. Découpage en seize morceaux au lieu d'un : `504`.

J'ai arrêté là, et j'ai consigné : *« l'extraction a échoué sur un délai dépassé d'Overpass »*, en ajoutant que c'était une ressource bénévole et que j'y avais déjà beaucoup puisé ce jour-là. La formulation était courtoise et le diagnostic était faux. J'avais rangé l'échec du côté de *la requête ne passe pas ici* — d'où l'idée, pour la reprise, de chercher une autre instance ou d'alléger encore la requête.

Le lendemain, la même requête a abouti. Sur les trente-six morceaux :

| | premier essai | deuxième | troisième |
|---|---|---|---|
| morceaux aboutis | 24 sur 36 | 34 sur 36 | **36 sur 36** |

Un tiers ont échoué d'abord, **aucun au troisième essai**. Le seul changement de fond : l'attente entre deux tentatives, portée de 8 secondes fixes à 15, puis 30, puis 60, puis 120.

Entre-temps, une mesure qui aurait dû être la première : `ping` vers l'instance, **100 ms aller-retour, 0 % de perte**. La liaison depuis ici était effectivement mauvaise ces jours-là — elle n'était pour rien dans cet échec.

## Ce qu'on en apprend

**1. Un `504` ne décrit pas votre requête, il décrit l'état du serveur.** C'est une information sur l'autre, pas sur soi. Les codes qui parlent de la requête — 400, 404, 422 — appellent une correction ; ceux qui parlent de la charge — 429, 502, 503, 504 — appellent une attente. Les traiter pareil conduit à modifier du code qui marche.

**2. Réessayer vite est la seule réaction qui aggrave la panne qu'on constate.** Une instance saturée l'est par la somme des demandes qu'elle reçoit. Trois essais en dix secondes ajoutent à ce qui bloque. L'attente qui double n'est pas de la résignation, c'est la seule contribution utile qu'un client puisse apporter à sa propre réussite.

**3. Mesurer la liaison avant de l'accuser.** « Le réseau est mauvais » était vrai de la maison et faux de cette panne. Deux commandes auraient tranché avant qu'une journée ne soit perdue à imaginer des contournements.

**4. Un travail long sur une ressource distante doit être reprenable.** Chaque morceau obtenu est désormais gardé sur disque. Reprendre repart du morceau qui a échoué, et surtout **ne redemande pas à l'instance ce qu'elle a déjà rendu** — la politesse et l'efficacité vont ici dans le même sens. Sans ce cache, la reconstruction du fichier, refaite trois fois ce jour-là pour en ajuster le contenu, aurait coûté trois extractions complètes ; elle n'a coûté aucun appel.

**5. L'abandon documenté est meilleur que l'abandon silencieux, et moins bon que le diagnostic.** Avoir écrit ce qui manquait a permis de reprendre proprement. Mais la note portait une cause supposée, présentée sans marque de doute, et cette cause a orienté la reprise dans la mauvaise direction. **Consigner ce qu'on a observé — le code d'erreur, le nombre d'essais, l'état de la liaison — plutôt que ce qu'on en déduit.**

## Ce qu'on change

- Distinguer, dans tout appel à un service distant, les codes qui disent *votre demande* de ceux qui disent *ma charge*. Les seconds déclenchent une attente qui double, jamais une modification de la demande.
- Cinq essais au moins, espacés de 15, 30, 60 et 120 secondes, avant de conclure qu'une ressource distante est indisponible.
- Toute extraction en plusieurs morceaux garde chaque réponse obtenue, hors du dépôt, et reprend là où elle s'est arrêtée.
- Avant d'incriminer la liaison : la mesurer, et noter le chiffre.
- Une note d'abandon consigne les faits observés. La cause supposée, si elle est écrite, l'est comme hypothèse.

## Portée

Générique. Vaut pour toute API publique ou bénévole — Overpass, Hub'Eau, les services de la Géoplateforme, les points d'accès d'open data —, et plus largement pour tout travail long mené à travers une liaison qu'on ne maîtrise pas. Le motif se reconnaît à ceci : **l'échec est intermittent et l'erreur ne parle pas de vous.** Dans ce cas, le correctif est du temps, pas du code.

## Fiches liées

[[RX-01-deux-passes]] · [[RX-04-source-hors-de-son-domaine]] · [[PA-02-preuve-par-les-faits]]
