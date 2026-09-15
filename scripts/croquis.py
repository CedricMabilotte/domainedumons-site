#!/usr/bin/env python3
"""Générateur de tracés « à main levée » en SVG, sans dépendance.

Chaque trait est dessiné deux fois, avec un léger tremblé et des extrémités
qui dépassent — comme un crayon qui repasse sur son trait. Graine fixe :
le résultat est toujours le même, donc versionnable.
"""
import math, random


class Crayon:
    def __init__(self, graine=7, rugosite=1.0):
        self.r = random.Random(graine)
        self.k = rugosite

    def _bruit(self, a):
        return self.r.uniform(-a, a)

    def trait(self, x1, y1, x2, y2, passes=2):
        """Un segment tremblé, repassé `passes` fois."""
        d = math.hypot(x2 - x1, y2 - y1)
        amp = min(d / 12, 3.2) * self.k
        out = []
        for i in range(passes):
            # les extrémités dépassent légèrement, comme un trait pas net
            dx, dy = (x2 - x1) / max(d, 1e-6), (y2 - y1) / max(d, 1e-6)
            e = self.r.uniform(0.5, 2.2) * self.k
            ax, ay = x1 - dx * e * 0.4 + self._bruit(amp * .5), y1 - dy * e * 0.4 + self._bruit(amp * .5)
            bx, by = x2 + dx * e + self._bruit(amp * .5), y2 + dy * e + self._bruit(amp * .5)
            # perpendiculaire pour déporter les points de contrôle
            px, py = -dy, dx
            c1 = (ax + (bx - ax) * .32 + px * self._bruit(amp), ay + (by - ay) * .32 + py * self._bruit(amp))
            c2 = (ax + (bx - ax) * .68 + px * self._bruit(amp), ay + (by - ay) * .68 + py * self._bruit(amp))
            out.append(f"M{ax:.1f} {ay:.1f}C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {bx:.1f} {by:.1f}")
        return out

    def cadre(self, x, y, w, h):
        """Un rectangle dessiné à la main : quatre traits qui ne se ferment pas bien."""
        p = []
        p += self.trait(x, y, x + w, y)
        p += self.trait(x + w, y, x + w, y + h)
        p += self.trait(x + w, y + h, x, y + h)
        p += self.trait(x, y + h, x, y)
        return p

    def fleche(self, x1, y1, x2, y2):
        p = self.trait(x1, y1, x2, y2)
        ang = math.atan2(y2 - y1, x2 - x1)
        for s in (+1, -1):
            a = ang + math.pi + s * 0.42
            p += self.trait(x2, y2, x2 + math.cos(a) * 11, y2 + math.sin(a) * 11, passes=1)
        return p

    def cercle(self, cx, cy, rx, ry=None, passes=2, n=34):
        """Un ovale tracé à la main : jamais tout à fait fermé, jamais rond."""
        ry = rx if ry is None else ry
        pts = []
        for i in range(n + 1):
            a = 2 * math.pi * i / n + self._bruit(0.03)
            pts.append((cx + math.cos(a) * rx * (1 + self._bruit(0.012)),
                        cy + math.sin(a) * ry * (1 + self._bruit(0.012))))
        return self.courbe(pts, passes=passes)

    def courbe(self, points, passes=2):
        """Une polyligne tremblée — pour un profil de terrain."""
        out = []
        for i in range(len(points) - 1):
            out += self.trait(*points[i], *points[i + 1], passes=passes)
        return out

    def hachures(self, x, y, w, h, pas=7, angle=-0.7):
        """Remplissage par hachures obliques, comme au crayon."""
        out = []
        n = int((w + h) / pas)
        for i in range(n):
            t = i * pas
            x1, y1 = x + t, y
            x2, y2 = x + t - h / math.tan(abs(angle)), y + h
            # on coupe au cadre
            if x2 < x:
                y2 = y + (x1 - x) * math.tan(abs(angle)); x2 = x
            if x1 > x + w:
                continue
            if y2 > y + h:
                continue
            out += self.trait(x1, y1, x2, y2, passes=1)
        return out


def chemin(paths, classe):
    return "\n  ".join(f'<path class="{classe}" d="{d}"/>' for d in paths)
