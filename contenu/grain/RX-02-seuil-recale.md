---
type: retex
code: RX-02
généricité: GÉNÉRIQUE
licence: CC BY-SA 4.0
date: 2026-09-14
source: claude/grain/retex/RX-02-seuil-recale.md, exporté le 2026-09-24
---

# RX-02 — Un seuil repris de la littérature a produit un résultat nul, qu'on a failli prendre pour une bonne nouvelle

*Retour d'expérience. Une analyse climatique locale, deux versions du même calcul, deux conclusions opposées.*

---

## Ce qui devait arriver

Vérifier localement une affirmation bien établie : le débourrement des arbres fruitiers avance plus vite que la dernière gelée de printemps ne recule, donc l'exposition au gel augmente alors même qu'il gèle moins souvent. Le chiffre national — 3 à 6 jours d'avance par décennie — circule partout ; personne ne l'avait recalculé sur ce point de la Corrèze.

La méthode était écrite d'avance dans le document de travail : croiser une **somme de températures** (proxy du débourrement : ~250 °C·j base 5 depuis le 1ᵉʳ février pour un pommier) avec les gelées postérieures, année par année depuis 1950.

## Ce qui s'est passé

Le calcul a tourné et a donné : **débourrement médian au 12 mai**, et **3 % des années** comptant une gelée après ce stade, sans tendance, sur les trois périodes de trente ans comparées.

Résultat parfaitement présentable. Il aurait tenu dans une page du site : *« contrairement à ce qu'on lit, l'exposition au gel de printemps n'augmente pas ici. »*

Il était faux. Un débourrement médian au 12 mai est absurde pour un pommier à 590 m en Corrèze — le stade réel se situe fin mars ou début avril. Le seuil plaçait le stade **après** la fenêtre où il gèle encore. L'analyse comptait donc des gelées dans une période où il n'y en a plus, et ne pouvait produire qu'un résultat nul.

Recalage : le seuil qui place la médiane au 4 avril est **80 °C·j**, et non 250. Le seuil qui place la floraison au 24 avril est 150.

Avec les bons seuils, la conclusion s'inverse :

| | Seuil 250 °C·j | Seuils 80 / 150 °C·j |
|---|---|---|
| Débourrement médian | 12 mai | 4 avril |
| Années avec gelée après débourrement | 3 % | **47 à 60 %** |
| Années avec gelée sur fleur ouverte, 1961-1990 | — | 3 % |
| Années avec gelée sur fleur ouverte, 1996-2025 | — | **17 %** |

## Pourquoi l'écart

Une somme de températures n'est pas une grandeur physique unique : elle dépend de **la base** (0, 5, 10 °C), de **la date de départ** (1ᵉʳ janvier, 1ᵉʳ février, date de fin de dormance), et de **la méthode de cumul** (moyenne simple, méthode sinusoïdale, troncature des minimales sous la base). Deux publications sérieuses peuvent citer 250 et 80 pour le même stade sans qu'aucune ne se trompe — elles ne comptent pas la même chose.

Le chiffre repris avait perdu ses conventions en route. C'est le sort ordinaire d'un seuil qui voyage de source en source.

**Et le mode de défaillance est le pire possible.** Un seuil trop haut ne provoque ni erreur, ni valeur aberrante, ni série vide. Il produit un résultat propre, calculé sur 76 ans, avec son test statistique et son intervalle de confiance — et ce résultat est *rassurant*. Rien dans la sortie ne signale le problème. Seule la confrontation de la date médiane au bon sens agronomique l'a fait apparaître.

## Ce qu'on en apprend

**1. Un seuil repris d'ailleurs se recale sur la série locale avant d'en tirer quoi que ce soit.** Le recalage le plus économique : vérifier que la grandeur intermédiaire — ici la date médiane du stade — tombe où un praticien du lieu l'attend. Cinq minutes, et c'est ce qui a sauvé l'analyse.

**2. Toujours sortir les grandeurs intermédiaires, pas seulement le résultat.** Si le script n'avait affiché que « 3 % des années », l'erreur passait. Il affichait aussi la date médiane, et c'est elle qui a alerté.

**3. Se méfier particulièrement des résultats nuls et rassurants.** Une analyse qui ne trouve rien mérite la même vérification qu'une analyse qui trouve un effet spectaculaire — et elle la reçoit rarement, parce qu'elle ne surprend personne. C'est l'asymétrie qui laisse passer les erreurs.

**4. Un paramètre sans ses conventions n'est pas un paramètre.** Toute somme de températures citée dans le corpus porte désormais sa base, sa date de départ et sa méthode de cumul, ou n'est pas citée.

## Ce qu'on change

- Tout seuil biologique ou agronomique importé est **recalé** sur la série locale, et le recalage est écrit dans la méthode publiée.
- Les scripts d'analyse **affichent les grandeurs intermédiaires** en plus du résultat.
- Le corpus ne cite pas de somme de températures sans base, date de départ et méthode de cumul.
- Une conclusion négative (« pas de tendance », « pas d'effet ») déclenche une vérification de la chaîne de calcul, au même titre qu'une conclusion positive forte.

## Portée

Générique, et pas limitée au climat. Le même mode de défaillance guette tout indicateur à seuil repris d'une source extérieure : seuils de tension d'un sol, périodes de retour hydrologiques, ratios financiers, critères d'éligibilité. **Un seuil mal calé ne casse rien — il rend l'instrument aveugle.**

## Fiches liées

[[RX-01-deux-passes]] · [[PA-02-preuve-par-les-faits]]
