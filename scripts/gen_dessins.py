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

# ------------------------------------------- le verger : la course du gel
c5 = Crayon(graine=73, rugosite=1.2)
v = []
v += c5.trait(70, 232, 600, 232)                 # l'axe du temps
for x, _lab in ((110, "1er mars"), (280, "1er avril"), (450, "1er mai"), (600, "1er juin")):
    v += c5.trait(x, 228, x, 238, passes=1)
v += c5.trait(96, 96, 470, 96, passes=1)         # la ligne de la période ancienne
v += c5.trait(96, 168, 470, 168, passes=1)       # la ligne de la période récente
v += c5.cercle(300, 96, 9, 9, passes=2, n=16)    # gelée, années 1960
v += c5.cercle(420, 96, 9, 9, passes=2, n=16)    # floraison, années 1960
v += c5.cercle(261, 168, 9, 9, passes=2, n=16)   # gelée, aujourd'hui
v += c5.cercle(382, 168, 9, 9, passes=2, n=16)   # floraison, aujourd'hui
v += c5.fleche(300, 78, 261, 78)                 # le recul de la gelée
v += c5.fleche(420, 186, 382, 186)               # l'avance de la floraison
v += c5.trait(311, 96, 409, 96, passes=1)        # l'écart, en haut
v += c5.trait(272, 168, 371, 168, passes=1)      # l'écart, en bas
course = f'''<svg viewBox="0 0 640 262" role="img" aria-labelledby="t-cou d-cou" class="croquis">
  <title id="t-cou">La course entre la gelée et la floraison</title>
  <desc id="d-cou">La dernière gelée de printemps recule de 2,3 jours par décennie et la floraison avance de 2,5 jours par décennie. Les deux se déplacent vers le début de l&#39;année à peu près à la même vitesse, donc l&#39;écart entre elles ne se creuse pas.</desc>
  {chemin(v, "trait-croquis")}
  <g class="texte-croquis">
    <text x="18" y="100" class="fort">1961-1990</text>
    <text x="18" y="172" class="fort">1996-2025</text>
    <text x="252" y="64">dernière gelée</text>
    <text x="392" y="64">floraison</text>
    <text x="330" y="118">l&#39;écart</text>
    <text x="292" y="190">le même écart</text>
    <text x="96" y="254">mars</text>
    <text x="266" y="254">avril</text>
    <text x="436" y="254">mai</text>
  </g>
</svg>'''

# --------------------------------- l'eau : ce que la station mesure, ou non
c6 = Crayon(graine=91, rugosite=1.25)
e = []
pente = [(30, 96), (110, 118), (190, 150), (280, 186), (390, 214), (500, 232), (614, 244)]
e += c6.courbe(pente, passes=2)                  # le versant
e += c6.courbe([(96, 112), (150, 136), (208, 158)], passes=1)   # le chevelu, en pointillé de trait
e += c6.courbe([(300, 196), (400, 222), (520, 240), (614, 250)], passes=2)  # la Montane
e += c6.cadre(486, 168, 108, 46)                 # la station
e += c6.fleche(540, 216, 540, 236)
e += c6.trait(150, 130, 168, 118, passes=1)      # le trait de rappel vers la source
e += c6.cercle(120, 120, 7, 7, passes=2, n=14)   # la source
mesure = f'''<svg viewBox="0 0 640 286" role="img" aria-labelledby="t-mes d-mes" class="croquis">
  <title id="t-mes">Ce que la station mesure</title>
  <desc id="d-mes">La station hydrométrique mesure la Montane à l&#39;aval, sur un bassin de 43 km². Les sources et le petit chevelu de tête de bassin s&#39;arrêtent bien avant, et personne ne les mesure.</desc>
  {chemin(e, "trait-croquis")}
  <g class="texte-croquis">
    <text x="136" y="104" class="fort">la source, le ruisseau de tête</text>
    <text x="136" y="126">ils s&#39;arrêtent les premiers — et personne ne les mesure</text>
    <text x="300" y="178" class="fort">la Montane</text>
    <text x="496" y="194" class="fort">la station</text>
    <text x="496" y="212">43 km² à l&#39;aval</text>
    <text x="30" y="272">Deux échelles d&#39;eau, un seul appareil de mesure.</text>
  </g>
</svg>'''

# -------------------------------------- le terrain : la coupe de l'air froid
c7 = Crayon(graine=113, rugosite=1.25)
a = []
sol2 = [(20, 132), (120, 128), (210, 136), (300, 168), (380, 214), (450, 244), (530, 252), (614, 248)]
a += c7.courbe(sol2, passes=2)
a += c7.fleche(160, 104, 300, 150)               # l'air froid qui s'écoule
a += c7.fleche(330, 150, 430, 216)
a += c7.fleche(470, 222, 520, 238)
for x in (486, 498, 510, 522):                   # la haie en travers
    a += c7.trait(x, 250, x - c7.r.uniform(1, 4), 250 - c7.r.uniform(16, 26), passes=1)
a += c7.cadre(78, 96, 84, 32)                    # le bâti sur le replat
airfroid = f'''<svg viewBox="0 0 640 300" role="img" aria-labelledby="t-air d-air" class="croquis">
  <title id="t-air">Comment l&#39;air froid s&#39;écoule</title>
  <desc id="d-air">La nuit, l&#39;air refroidi devient plus dense et descend la pente. Il quitte le replat où se trouve le bâti, s&#39;accumule dans la cuvette en contrebas, et une haie plantée en travers de la pente le retient en amont.</desc>
  {chemin(a, "trait-croquis")}
  <g class="texte-croquis">
    <text x="82" y="88" class="fort">le replat</text>
    <text x="82" y="118">il se vide</text>
    <text x="196" y="106">l&#39;air froid coule</text>
    <text x="330" y="204">la cuvette se remplit</text>
    <text x="446" y="292">une haie en travers le retient</text>
  </g>
</svg>'''

# ------------------------------------ construire : la coupe de principe
c8 = Crayon(graine=131, rugosite=1.2)
b2 = []
b2 += c8.trait(40, 176, 600, 176)                # le terrain naturel
b2 += c8.cadre(180, 96, 240, 80)                 # le volume habité
b2 += c8.cadre(180, 176, 240, 40)                # le vide sanitaire
b2 += c8.trait(180, 216, 180, 252, passes=2)     # les semelles
b2 += c8.trait(420, 216, 420, 252, passes=2)
b2 += c8.trait(176, 252, 424, 252, passes=1)
b2 += c8.fleche(150, 196, 196, 196)              # la ventilation qui traverse
b2 += c8.fleche(404, 196, 452, 196)
b2 += c8.trait(120, 176, 180, 176, passes=1)     # le trottoir périphérique
b2 += c8.trait(420, 176, 480, 176, passes=1)
b2 += c8.fleche(300, 268, 300, 176)              # le radon qui monte
coupe_bati = f'''<svg viewBox="0 0 640 300" role="img" aria-labelledby="t-bat d-bat" class="croquis">
  <title id="t-bat">Coupe de principe d&#39;une construction ici</title>
  <desc id="d-bat">Le radon remonte du granite. Un vide sanitaire ventilé de part en part et une dalle étanche l&#39;évacuent avant qu&#39;il n&#39;entre. Les semelles descendent à quatre-vingts centimètres au moins à cause du retrait-gonflement des argiles, et un trottoir périphérique éloigne l&#39;eau du pied des murs.</desc>
  {chemin(b2, "trait-croquis")}
  <g class="texte-croquis">
    <text x="196" y="130" class="fort">l&#39;habitation</text>
    <text x="196" y="152">pas de pièce de vie en dessous</text>
    <text x="196" y="202" class="fort">vide sanitaire ventilé</text>
    <text x="34" y="192">l&#39;air entre</text>
    <text x="462" y="192">et ressort</text>
    <text x="196" y="242">semelles à 0,80 m au moins</text>
    <text x="316" y="286">le radon remonte du granite</text>
  </g>
</svg>'''
for nom, svg in (("course", course), ("mesure", mesure), ("airfroid", airfroid), ("coupe-bati", coupe_bati)):
    open("dessins/%s.svg" % nom, "w", encoding="utf-8").write(svg)
    print("  dessins/%s.svg : %d octets" % (nom, len(svg)))
