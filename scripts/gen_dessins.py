#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from croquis import Crayon, chemin

# ---------------------------------------------------------------- le montage
c = Crayon(graine=11, rugosite=1.15)
p = []
p += c.cadre(14, 16, 250, 92)          # fonds de dotation
p += c.cadre(352, 24, 268, 92)         # association
p += c.cadre(120, 224, 400, 104)       # le foncier
p += c.hachures(126, 230, 388, 92, pas=13, angle=-0.72)
p += c.fleche(138, 110, 250, 220)
p += c.fleche(480, 118, 392, 220)

montage = f'''<svg viewBox="0 0 640 350" role="img" aria-labelledby="t-mont d-mont" class="croquis">
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
c2 = Crayon(graine=23, rugosite=1.0)
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
