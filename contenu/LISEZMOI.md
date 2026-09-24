# contenu/ — la source des pages

Depuis le 24 septembre 2026, **aucune page de la racine ne s'écrit à la main**.
On écrit ici, puis `python3 scripts/construire.py`.

| Dossier | Ce qu'il contient |
|---|---|
| `pages/` | Une page = un fragment : un en-tête JSON (`titre`, `description`, et au besoin `gabarit`, `classe`, `leaflet`), le corps, puis `<!--scripts-->` et ses scripts. |
| `modules/` | Des blocs partagés par plusieurs pages, insérés par `<!--#module nom-->`. Une rédaction, plusieurs pages. |
| `grain/` | Les fiches du Grain, exportées du corpus avec leur en-tête. Le corpus reste la source : corriger là-bas, réexporter ici. |

## Directives

- `<!--#module nom-->` — insère `modules/nom.html`
- `<!--#sans-js data/a.json data/b.json-->` — le bloc « Sans JavaScript », daté depuis les fichiers
- `<!--#inclure chemin-->`, `<!--#script chemin-->` — un fichier du dépôt, tel quel ou dans `<script>`
- `<!--#nouvelles 6-->` — les dernières entrées des journaux des versions de toutes les pages

## Gabarits

`accueil`, `recit`, `planche`, `registre`, `portail`, `fiche` — voir l'en-tête de `scripts/gabarit.py`.
Le gabarit se déduit du nom de la page ; l'en-tête peut le forcer.

## Les sorties qui se déduisent des pages

- `flux.xml` (Atom) et `sitemap.xml` — des journaux des versions et des dates de fiches ;
- `relayer.html` et `partage/extraits.json` — les extraits à publier, textes par canal (`scripts/partage.py`) ;
- `editions/*.html` — les éditions paginées (Paged.js) ; `editions/pdf/` après `scripts/editions.py --rendre` ;
- `visuels/<format>/*.png` — les visuels des réseaux, découpés des planches `visuels/<format>.html`.

`scripts/editions.py --rendre` demande Chromium et le module Python `playwright`. À relancer quand un texte publié change, ou quand `verifier.py` signale une vignette absente.
