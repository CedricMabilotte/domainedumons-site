#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from croquis import Crayon, chemin

# ---------------------------------------------------------------- le montage
c = Crayon(graine=11, rugosite=1.4)
p = []
p += c.cadre(14, 16, 250, 92)          # fonds de dotation
p += c.cadre(352, 24, 268, 92)         # association
p += c.cadre(120, 222, 400, 100)       # le foncier
p += c.fleche(138, 110, 250, 218)
p += c.fleche(480, 118, 392, 218)
# la terre : des touffes sous la boite, d'espacement et de hauteur irreguliers
x = 130.0
while x < 512:
    h = c.r.uniform(8, 17)
    p += c.trait(x, 322, x - c.r.uniform(1, 5), 322 + h, passes=1)
    if c.r.random() < 0.75:
        p += c.trait(x + c.r.uniform(2, 5), 322, x + c.r.uniform(4, 9), 322 + h * c.r.uniform(.6, 1.05), passes=1)
    if c.r.random() < 0.4:
        p += c.trait(x + c.r.uniform(1, 4), 322, x + c.r.uniform(-1, 2), 322 + h * c.r.uniform(.5, .8), passes=1)
    x += c.r.uniform(9, 26)

montage = f'''<svg viewBox="0 0 640 348" role="img" aria-labelledby="t-mont d-mont" class="croquis">
  <title id="t-mont">Le montage, dessiné</title>
  <desc id="d-mont">Un fonds de dotation détient la nue-propriété du foncier et ne peut pas le vendre. Une association d'intérêt général, autogérée par ses membres, en détient l'usage. Les deux se rattachent à la même terre.</desc>
  {chemin(p[:len(p)-0], "trait-croquis")}
  <g class="texte-croquis">
    <text x="32" y="44" class="sur">le fonds de dotation</text>
    <text x="32" y="70" class="fort">la nue-propriété</text>
    <text x="32" y="93">il détient le titre, il ne vend pas</text>
    <text x="370" y="52" class="sur">l'association</text>
    <text x="370" y="78" class="fort">l'usage</text>
    <text x="370" y="101">autogérée par ses membres</text>
    <text x="140" y="256" class="sur">la terre</text>
    <text x="140" y="284" class="fort">le Domaine du Mons</text>
    <text x="140" y="308">habiter, cultiver, transformer, accueillir</text>
  </g>
</svg>'''

# ------------------------------------------------------- la coupe du terrain
c2 = Crayon(graine=23, rugosite=1.25)
sol = [(8, 250), (70, 236), (130, 214), (200, 178), (270, 150), (340, 140),
       (430, 137), (500, 142), (560, 160), (612, 186)]
q = c2.courbe(sol, passes=2)
q += c2.trait(8, 250, 8, 262, passes=1)
# le lit de la Montane, en bas à gauche
q += c2.courbe([(14, 258), (40, 254), (66, 257), (92, 253)], passes=1)
# le repère du lieu : un trait qui descend sur un point marqué au sol
q += c2.trait(392, 96, 392, 132, passes=2)
q += c2.courbe([(386, 124), (392, 134), (398, 124)], passes=1)
q += c2.courbe([(384, 139), (400, 139)], passes=2)
q += c2.courbe([(386, 136), (398, 143)], passes=1)
q += c2.courbe([(398, 136), (386, 143)], passes=1)
# flèche de l'air froid qui descend
q += c2.fleche(300, 176, 168, 232)
# le soleil, au sud
q += c2.courbe([(560, 58), (572, 46), (588, 44), (600, 54), (600, 70), (586, 78), (570, 74), (562, 62)], passes=1)
for a in ((548, 60, 536, 58), (566, 38, 562, 26), (596, 36, 604, 24), (612, 62, 624, 62), (596, 88, 604, 98)):
    q += c2.trait(*a, passes=1)

coupe = f'''<svg viewBox="0 0 640 280" role="img" aria-labelledby="t-coupe d-coupe" class="croquis">
  <title id="t-coupe">Coupe du terrain</title>
  <desc id="d-coupe">Le Domaine du Mons occupe un replat à 588 mètres, exposé au sud. Le terrain descend vers la vallée de la Montane. L'air froid des nuits claires s'écoule du replat vers les bas-fonds, qui gèlent donc plus fort que le lieu lui-même.</desc>
  {chemin(q, "trait-croquis")}
  <g class="texte-croquis">
    <text x="392" y="86" class="fort" text-anchor="middle">le replat, 588 m</text>
    <text x="584" y="104" class="petit" text-anchor="middle">plein sud</text>
    <text x="14" y="278" class="petit">la vallée de la Montane</text>
    <text x="176" y="216" class="petit">l'air froid descend</text>
  </g>
</svg>'''

# -------------------------------------------------------------- un filet
c3 = Crayon(graine=41, rugosite=1.4)
filet = f'''<svg viewBox="0 0 640 14" class="filet-croquis" aria-hidden="true">
  {chemin(c3.trait(6, 7, 634, 7, passes=2), "trait-croquis")}
</svg>'''

open("dessins/montage.svg", "w", encoding="utf-8").write(montage)
open("dessins/coupe.svg", "w", encoding="utf-8").write(coupe)
open("dessins/filet.svg", "w", encoding="utf-8").write(filet)
for f, s in (("montage", montage), ("coupe", coupe), ("filet", filet)):
    print(f"  {f}.svg : {len(s)} octets")

# ------------------------------------------------- marcher libre : les cercles
c3 = Crayon(graine=41, rugosite=1.15)
r = []
r += c3.cercle(320, 210, 305, 195)          # le dehors
r += c3.cercle(300, 215, 215, 130)          # le collectif
r += c3.cercle(240, 220, 100, 72)           # chacun
cercles = f'''<svg viewBox="0 0 640 420" role="img" aria-labelledby="t-cer d-cer" class="croquis">
  <title id="t-cer">Trois cercles emboîtés</title>
  <desc id="d-cer">Un cercle intérieur pour ce qui reste à chacun, un cercle intermédiaire pour ce que le collectif met en commun, un cercle extérieur pour ce qui est ouvert au dehors. Les trois se contiennent sans se confondre.</desc>
  {chemin(r, "trait-croquis")}
  <g class="texte-croquis">
    <text x="214" y="46" class="fort">le dehors</text>
    <text x="214" y="68">l&#39;accueil, les chantiers, ce qui se transmet</text>
    <text x="352" y="198" class="fort">le collectif</text>
    <text x="352" y="220">la terre, les outils,</text>
    <text x="352" y="241">les décisions, la table</text>
    <text x="182" y="208" class="fort">chacun</text>
    <text x="160" y="230">la chambre, le revenu,</text>
    <text x="160" y="251">les liens, le silence</text>
  </g>
</svg>'''

# --------------------------------------- marcher libre : la boucle de décision
c4 = Crayon(graine=57, rugosite=1.3)
b = []
b += c4.cadre(20, 20, 176, 76)        # une proposition
b += c4.cadre(432, 20, 188, 76)       # les objections
b += c4.cadre(432, 210, 188, 76)      # on tranche
b += c4.cadre(20, 210, 176, 76)       # on revoit à date
b += c4.fleche(200, 58, 426, 58)
b += c4.fleche(526, 100, 526, 206)
b += c4.fleche(428, 248, 202, 248)
b += c4.fleche(108, 206, 108, 102)
boucle = f'''<svg viewBox="0 0 640 306" role="img" aria-labelledby="t-bou d-bou" class="croquis">
  <title id="t-bou">La boucle d'une décision</title>
  <desc id="d-bou">Une proposition est écrite, les objections sont recueillies et intégrées, la décision est tranchée puis consignée, et une date de réexamen est fixée dès le départ.</desc>
  {chemin(b, "trait-croquis")}
  <g class="texte-croquis">
    <text x="38" y="50" class="fort">une proposition</text>
    <text x="38" y="74">écrite, datée, signée</text>
    <text x="450" y="50" class="fort">les objections</text>
    <text x="450" y="74">recueillies, puis intégrées</text>
    <text x="450" y="240" class="fort">on tranche</text>
    <text x="450" y="264">et on consigne le motif</text>
    <text x="38" y="240" class="fort">on revoit à date</text>
    <text x="38" y="264">fixée dès le départ</text>
  </g>
</svg>'''
open("dessins/cercles.svg", "w", encoding="utf-8").write(cercles)
open("dessins/boucle.svg", "w", encoding="utf-8").write(boucle)
print("dessins écrits :", ", ".join(sorted(os.listdir("dessins"))))
