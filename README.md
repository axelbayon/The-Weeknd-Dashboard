# The Weeknd Dashboard

Dashboard local recensant les streams Spotify de The Weeknd (Songs & Albums) via scraping Kworb. Affichage par pages avec auto-refresh toutes les 10 minutes, snapshots datés (J/J-1/J-2) pour préserver les variations, et intégration Spotify API pour les covers et métadonnées.

---

## Quoi de neuf

---

**2025-10-03 — Prompt 7.2 : Caps imminents - Finitions ergonomie et francisation**

*Dernières finitions UI et traduction complète :*

**A) Couleurs rang par type** :
- Badge # coloré selon type : TITRE (rouge accent rgba(255,54,92,0.95)) | ALBUM (violet #7c6dff)
- Classes CSS `.data-table__cell--rank-song` et `.data-table__cell--rank-album` appliquées dynamiquement
- Tri numérique sur rang conservé

**B) Largeur colonne Titre réduite** :
- Titre : 320-500px → 280-400px (libère espace pour autres colonnes)
- Astérisque *, tri alpha et alignement cover/nom/album conservés

**C) Légende featuring déplacée** :
- Légende "* = featuring" maintenant dans header Titre (même ligne que "Titre")
- Style : `.data-table__header-legend` discret, italic, opacity 0.7, pointer-events:none
- Ancienne légende en bas du tableau supprimée

**D) Correction tri Type** :
- Fix mapping sortKeys dans handleSortClick() : ordre corrigé rank | title | type | days | ...
- Type trie désormais sa propre colonne (plus la colonne suivante)
- Indicateurs ▲/▼ se placent correctement

**E) Francisation complète "Songs → Titres"** :
- **Nav-bar** : Onglet "Songs" → "Titres"
- **Toggles Caps** : "Songs" → "Titres"
- **Valeurs colonne Type** : "Song" → "TITRE" | "Album" → "ALBUM"
- Cohérence linguistique totale

*Fichiers modifiés :*
- `Website/index.html` :
  - Nav "Songs" → "Titres"
  - Toggle "Songs" → "Titres"
  - Légende déplacée dans <th> Titre : `<span class="data-table__header-legend">* = featuring</span>`
  - Légende `<p class="data-table__legend">` en bas supprimée
  - Cache-busting v7.2 (CSS et JS)
- `Website/src/caps.js` :
  - `createCapsRow()` : Classes rank-song/rank-album ajoutées, "Song"/"Album" → "TITRE"/"ALBUM"
  - `handleSortClick()` : sortKeys fixé (rank, title, type, days...)
- `Website/src/styles/global.css` :
  - `.data-table__cell--rank-song` : color rouge accent
  - `.data-table__cell--rank-album` : color violet
  - `.data-table__header-legend` : style discret dans header
  - `.data-table--caps th:nth-child(2)` : min-width 320→280px, max-width 500→400px
  - Ancien `.data-table__legend` (bas tableau) supprimé

*Tests de validation :*
1. ✅ Rang # coloré : titre rouge, album violet
2. ✅ Colonne Titre plus compacte (280-400px au lieu de 320-500px)
3. ✅ Légende "* = featuring" visible à côté du header Titre
4. ✅ Tri Type fonctionne (trie sa propre colonne)
5. ✅ Indicateur tri sur Type quand trié
6. ✅ Nav "Titres", toggle "Titres", valeurs "TITRE"/"ALBUM"
7. ✅ Aucune régression tri, navigation croisée, auto-refresh

---


---

## Structure du repo

```
README.md                          # Ce fichier (documentation du projet)
.env.local                         # Secrets Spotify (non tracké, ignoré par Git)
.gitignore                         # Patterns d'exclusion Git
.gitattributes                     # Normalisation des fins de ligne
LICENSE                            # Licence (placeholder MIT)

data/                              # Données du dashboard
  schemas/                         # Schémas JSON Schema v1.0 (contrats de données)
    songs-schema.json              # Schéma pour data/songs.json
    albums-schema.json             # Schéma pour data/albums.json
    meta-schema.json               # Schéma pour data/meta.json
    snapshot-songs-schema.json     # Schéma pour snapshots songs
    snapshot-albums-schema.json    # Schéma pour snapshots albums
  songs.json                       # Vue courante des chansons (315 items avec calculs)
  albums.json                      # Vue courante des albums (27 items avec calculs)
  meta.json                        # Métadonnées globales (dates, historique)
  history/                         # Snapshots journaliers
    songs/                         # Snapshots quotidiens des chansons (J, J-1, J-2)
      2025-09-29.json              # Fixture J-2
      2025-09-30.json              # Fixture J-1
      2025-10-01.json              # Snapshot J actuel (315 chansons, IDs stables)
    albums/                        # Snapshots quotidiens des albums
      2025-09-29.json              # Fixture J-2
      2025-09-30.json              # Fixture J-1
      2025-10-01.json              # Snapshot J actuel (27 albums)
  album_detail/                    # Détails albums Spotify (à remplir plus tard)

scripts/                           # Scripts Python de scraping, génération et validation
  start_dashboard.py               # 🚀 Script de lancement complet (orchestrateur + serveur web)
  auto_refresh.py                  # Orchestrateur auto-refresh (pipeline 10 min, lock, jitter, rotation J/J-1/J-2)
  scrape_kworb_songs.py            # Scraper Kworb Songs (extraction 315 chansons, IDs stables)
  scrape_kworb_albums.py           # Scraper Kworb Albums (extraction 27 albums)
  generate_current_views.py        # Génère data/songs.json et albums.json depuis snapshots
  validate_data.py                 # Valide conformité des données (schémas, arrondis, unicité, dates)
  test_scraper_songs.py            # Tests automatisés du scraper Songs (6 tests)
  test_scraper_albums.py           # Tests automatisés du scraper Albums (7 tests)
  test_songs_ids.py                # Tests IDs Songs (pattern, unicité, @unknown count)

Website/                           # Dossier parent du code applicatif
  index.html                       # Page principale (SPA avec 3 pages : Songs, Albums, Caps)
  src/
    main.js                        # Orchestration chargement, auto-refresh, navigation
    app.js                         # Script JavaScript (navigation entre pages)
    data-loader.js                 # Module chargement JSON (cache, retry, événements)
    data-renderer.js               # Module rendu tables/agrégats (calculs, formatage, DOM)
    formatters.js                  # Module formatage FR (nombres, %, jours, M/B avec formatCap)
    search.js                      # Recherche sticky avec suggestions et navigation
    table-sort.js                  # Système tri cliquable (flèches, ARIA, tri alpha ignore *)
    meta-refresh.js                # Script de mise à jour dynamique des en-têtes (fetch meta.json)
    caps.js                        # Module page Caps imminents (filtrage, tri, ETA, navigation croisée)
    styles/
      global.css                   # CSS canonique (1480+ lignes, dark theme, styles Caps inclus)
  public/
    styles/                        # Assets CSS additionnels (vide pour l'instant)

docs/                              # Documentation complémentaire
  roadmap.md                       # Feuille de route (à compléter)
  securité-scraping.md             # Règles de sécurité pour le scraping
```

**Note** : Fichiers de configuration et documentation à la racine, code applicatif dans `Website/`, données et scripts dans `data/` et `scripts/`. CSS canonique : `Website/src/styles/global.css`.

---

## Comment utiliser / Commandes

### 🚀 Lancement complet en une commande (recommandé)

Pour scraper les données ET lancer le dashboard en une seule commande :

```bash
python scripts/start_dashboard.py
```

**Ce que fait cette commande** :
1. ✅ Démarre l'orchestrateur auto-refresh en arrière-plan (toutes les 10 minutes)
2. ✅ Synchronise les données immédiatement (Songs + Albums)
3. ✅ Lance un serveur HTTP sur http://localhost:8000/Website/
4. ✅ En-têtes UI se mettent à jour automatiquement (dernière sync, countdown, date données)
5. ✅ Tables Songs et Albums se remplissent avec les vraies données (auto-refresh à chaque synchro)
6. ✅ Recherche sticky active pour naviguer rapidement vers n'importe quelle chanson

**Note** : Appuyez sur `Ctrl+C` pour arrêter le serveur (l'orchestrateur s'arrête automatiquement).

---

### Orchestrateur auto-refresh (mode manuel)

Pour lancer uniquement l'orchestrateur sans le serveur web :

**Mode continu (refresh toutes les 10 min)** :
```bash
python scripts/auto_refresh.py
```

**Mode --once (une seule exécution, utile pour tests)** :
```bash
python scripts/auto_refresh.py --once
```

**Personnaliser l'intervalle** :
```bash
# Via variable d'environnement (8 secondes pour tests rapides)
$env:REFRESH_INTERVAL_SECONDS=8
python scripts/auto_refresh.py

# Via paramètre CLI
python scripts/auto_refresh.py --interval 30
```

**Fonctionnalités** :
- Verrou anti-chevauchement (`.sync.lock`)
- Jitter aléatoire ±15s
- Rotation automatique J/J-1/J-2
- Fallback gracieux en cas d'erreur
- Statut dans `meta.json` (`last_sync_status`, `last_error`)

---

### Lancement des scrapers individuels

**Scraper Songs** :
```bash
python scripts/scrape_kworb_songs.py
```

Récupère 315 chansons depuis Kworb, crée snapshot dans `data/history/songs/{date}.json`, met à jour `data/songs.json` avec paliers 100M.

**Scraper Albums** :
```bash
python scripts/scrape_kworb_albums.py
```

Récupère 27 albums depuis Kworb, crée snapshot dans `data/history/albums/{date}.json`, met à jour `data/albums.json` avec paliers 1B.

**Note** : Les scrapers utilisent un User-Agent dédié, throttle 1s, et retry avec backoff exponentiel (3 tentatives max).

### Génération manuelle des vues courantes

Si vous souhaitez régénérer `data/songs.json` et `data/albums.json` à partir des snapshots existants :

```bash
python scripts/generate_current_views.py
```

### Validation des données

Pour valider la conformité des données aux schémas JSON :

```bash
python scripts/validate_data.py
```

### Lancement local de l'interface

1. Ouvrir `Website/index.html` dans un navigateur web
2. Naviguer entre les pages via la barre de navigation (Songs / Albums / Caps imminents)
3. L'interface est fonctionnelle mais les données sont des placeholders (aucune logique métier implémentée)

**Note** : Pour l'instant, aucun serveur ni build n'est requis. L'application fonctionne directement en ouvrant le fichier HTML.

---

## Variables d'environnement

Les secrets (ex. clés Spotify API) doivent être stockés dans le fichier `.env.local` à la racine du projet, **jamais commité**.

Exemple :
```
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
```

Le fichier `.env.local` est explicitement ignoré par Git (voir `.gitignore` ligne 7).

---

## Variables d'environnement (Spotify)

**Emplacement** : `.env.local` à la racine du projet

**Clés attendues** (sans valeurs, à renseigner) :
```bash
SPOTIFY_CLIENT_ID=         # ID client de votre app Spotify
SPOTIFY_CLIENT_SECRET=     # Secret client de votre app Spotify
SPOTIFY_REDIRECT_URI=      # URI de redirection (ex: http://localhost:8888/callback)
```

**Avertissements** :
- ⚠️ **Ne jamais committer** ces valeurs dans Git
- ⚠️ **Ne jamais logger** ces valeurs dans les fichiers de log ou la console
- Ces clés seront utilisées ultérieurement lors de l'intégration Spotify API (récupération des covers, métadonnées, tracklists)
- Le fichier `.env.local` est ignoré par Git via `.gitignore` (7 patterns de protection)

**Comment obtenir ces clés** :
1. Créer une app sur [Spotify for Developers](https://developer.spotify.com/dashboard)
2. Récupérer le Client ID et Client Secret
3. Configurer l'URI de redirection dans les paramètres de l'app

---

## Contrats de données

### Vue d'ensemble

Les données du dashboard sont structurées selon des schémas JSON stricts (version 1.0) pour assurer la cohérence et la validité des calculs. Tous les schémas sont disponibles dans `data/schemas/`.

### data/songs.json (vue courante)

**Champs clés** :

| Champ | Type | Description |
|-------|------|-------------|
| `id` | string | Clé stable interne : `kworb:<norm_title>@<norm_album>` |
| `rank` | integer | Position dans le classement Kworb (≥1) |
| `title` | string | Titre original de la chanson |
| `album` | string | Album d'origine |
| `role` | enum | `"lead"` ou `"feat"` (The Weeknd premier artiste = lead) |
| `streams_total` | number | Nombre total de streams cumulés |
| `streams_daily` | number | Streams quotidiens du jour J |
| `streams_daily_prev` | number\|null | Streams quotidiens du jour J-1 (null si non dispo) |
| `variation_pct` | number\|"N.D." | Variation % entre J et J-1 (2 déc.) ou "N.D." |
| `next_cap_value` | number | Prochain palier absolu (multiple de 100M) |
| `days_to_next_cap` | number\|"N.D." | Jours estimés pour atteindre le palier (2 déc.) ou "N.D." |
| `last_update_kworb` | string | Timestamp ISO de la dernière mise à jour Kworb |
| `spotify_data_date` | string | Date des données Spotify (YYYY-MM-DD) |
| `spotify_track_id` | string\|null | ID Spotify du track (à remplir ultérieurement) |
| `spotify_album_id` | string\|null | ID Spotify de l'album (à remplir ultérieurement) |

**Exemple** (2 lignes) :
```json
[
  {
    "id": "kworb:blinding lights@after hours",
    "rank": 1,
    "title": "Blinding Lights",
    "album": "After Hours",
    "role": "lead",
    "streams_total": 4290300000,
    "streams_daily": 5300000,
    "streams_daily_prev": 5120000,
    "variation_pct": 3.52,
    "next_cap_value": 4300000000,
    "days_to_next_cap": 1.83,
    "spotify_data_date": "2025-09-30"
  },
  {
    "id": "kworb:save your tears@after hours",
    "rank": 4,
    "title": "Save Your Tears",
    "streams_daily_prev": 0,
    "variation_pct": "N.D.",
    "days_to_next_cap": 6.14
  }
]
```

### data/albums.json (vue courante)

**Champs similaires à songs.json** sans `role`, avec paliers à **1 000 000 000** (1B).

### data/meta.json (métadonnées globales)

| Champ | Type | Description |
|-------|------|-------------|
| `kworb_last_update_utc` | string | Timestamp ISO de la dernière mise à jour Kworb |
| `spotify_data_date` | string | Date des données Spotify (YYYY-MM-DD) |
| `last_sync_local_iso` | string | Timestamp ISO de la dernière synchronisation locale |
| `history.available_dates` | string[] | Liste des dates disponibles dans data/history (YYYY-MM-DD, triée décroissant) |
| `history.latest_date` | string | Date la plus récente (YYYY-MM-DD) |

### Snapshots journaliers

**Format** : `data/history/songs/YYYY-MM-DD.json` et `data/history/albums/YYYY-MM-DD.json`

Contiennent les mêmes champs que les vues courantes **sans** `streams_daily_prev`, `variation_pct`, `next_cap_value`, `days_to_next_cap` (ces valeurs sont calculées lors de la génération des vues courantes).

### Règles de calcul

#### 1. Clé d'alignement (id)

**Format** : `kworb:<norm_title>@<norm_album>`

**Normalisation** :
- Lowercasing
- Trim
- Suppression ponctuation (`.,:;!?'"-`)
- Patterns de featuring retirés : `feat.`, `feat`, `featuring`, `ft.`, `ft`, `with`, `x`, `&`, `and`
- Parenthèses et leur contenu retirés

**Exemple** :
- Titre : "Blinding Lights"
- Album : "After Hours"
- → id = `"kworb:blinding lights@after hours"`

#### 2. Variation % (2 décimales)

**Formule** :
```
si streams_daily_prev > 0 :
    variation_pct = ((streams_daily - streams_daily_prev) / streams_daily_prev) × 100
    arrondi à 2 décimales
sinon :
    variation_pct = "N.D."
```

**Exemples** :
- J: 5 300 000, J-1: 5 120 000 → **+3.52%**
- J: 4 200 000, J-1: 4 350 000 → **-3.45%**
- J: 2 800 000, J-1: 0 → **"N.D."**

#### 3. Paliers (next_cap_value)

**Songs** : prochain multiple de **100 000 000** (100M) supérieur strict à `streams_total`

**Albums** : prochain multiple de **1 000 000 000** (1B) supérieur strict à `streams_total`

**Exemple** :
- streams_total = 4 290 300 000 → next_cap_value = **4 300 000 000**

#### 4. Jours restants (2 décimales)

**Formule** :
```
si streams_daily > 0 :
    days_to_next_cap = (next_cap_value - streams_total) / streams_daily
    arrondi à 2 décimales
sinon :
    days_to_next_cap = "N.D."
```

**Exemple** :
- next_cap: 4 300 000 000, streams_total: 4 290 300 000, streams_daily: 5 300 000
- → (9 700 000 / 5 300 000) = **1.83 jours**

#### 5. Date des données Spotify

**Formule** :
```
spotify_data_date = (last_update_kworb en UTC) - 1 jour
```

**Exemple** :
- last_update_kworb = `2025-10-01T00:00:00Z`
- → spotify_data_date = `"2025-09-30"`

### Validation des données

**Script** : `scripts/validate_data.py`

**Commande** :
```bash
python scripts/validate_data.py
```

**Validations effectuées** :
1. ✅ Conformité aux schémas JSON (champs requis, types, contraintes)
2. ✅ Arrondis à 2 décimales pour `variation_pct` et `days_to_next_cap`
3. ✅ Unicité des `id` dans songs.json et albums.json
4. ✅ Cohérence des dates (`spotify_data_date` = `meta.history.latest_date`)
5. ✅ Validité des paliers (multiples de 100M ou 1B, supérieurs à streams_total)

**Fixtures disponibles** :
- `data/history/songs/2025-09-29.json` (J-1) : 5 chansons
- `data/history/songs/2025-09-30.json` (J) : 5 chansons
- `data/history/albums/2025-09-29.json` (J-1) : 3 albums
- `data/history/albums/2025-09-30.json` (J) : 3 albums

**Génération des vues courantes** :
```bash
python scripts/generate_current_views.py
```

Ce script lit les snapshots J et J-1, applique les règles de calcul, et produit `data/songs.json` et `data/albums.json`.

---

## Règles de collaboration

- **Conventional Commits** : chaque commit suit le format `type(scope): message` (feat, fix, docs, chore, refactor, perf, test, build, ci, style).
- **Cycle de travail** : tests → mise à jour README → commit/push à chaque prompt.
- **Sécurité** : ne jamais committer de secrets, tokens ou clés API.

---

## Limites connues

- **Album "Unknown" pour les chansons** : Kworb ne fournit pas l'information d'album (288 chansons sur 315), sera résolu via Spotify API (prompt 7).
- **Variation_pct "N.D." pour beaucoup de chansons** : Les données J-1 ne correspondent pas toujours aux IDs actuels (sera amélioré au prochain scraping quotidien).
- **Snapshots J-2 manquants** : seuls J et anciennes fixtures sont disponibles (se remplira progressivement).
- **Page "Caps imminents" non fonctionnelle** : contient uniquement des placeholders (implémentation prévue prompt 7+).
- **Covers placeholder** : émojis 🎵/💿 en attendant intégration Spotify API (covers réelles en prompt 7).
- **Stack technique** : HTML/CSS/JS vanilla (SPA simple), scripts Python pour scraping/génération/validation.

---

## Tests de validation

### Scripts de test disponibles

#### `scripts/validate_data.py` — Validation complète des contrats de données
**Fonction** : Valide la conformité de tous les fichiers JSON aux schémas définis
**Tests effectués** :
- Conformité aux schémas JSON (songs, albums, meta, snapshots)
- Arrondis à 2 décimales pour variation_pct et days_to_next_cap
- Unicité des clés id dans songs.json et albums.json
- Cohérence des dates (spotify_data_date = latest_date)
- Validité des paliers (multiples de 100M pour songs, 1B pour albums)

**Commande** :
```bash
python scripts/validate_data.py
```

**Résultat attendu** : "✅ Toutes les validations sont passées avec succès!"

---

#### `scripts/test_scraper_songs.py` — Tests du scraper Kworb Songs
**Fonction** : Vérifie l'intégrité et la qualité des données scrapées depuis Kworb
**Tests effectués** :
- Comptage minimum de chansons (>= 200 requis, 315 constatés)
- Présence de variations numériques avec arrondis à 2 décimales
- Détection de cas "N.D." pour variations non calculables
- Présence des rôles "lead" et "feat" (282 lead + 33 feat)
- Cohérence des dates entre meta.json et songs.json
- Unicité des clés id

**Commande** :
```bash
python scripts/test_scraper_songs.py
```

**Résultats attendus** :
- Test 1 : 315 chansons (PASS)
- Test 2-3 : Variations avec 2 décimales ou "N.D." (PASS)
- Test 4 : Rôles lead/feat présents (PASS)
- Test 5 : Dates cohérentes (PASS)
- Test 6 : Unicité des id (PASS)

---

#### `scripts/test_scraper_albums.py` — Tests du scraper Kworb Albums
**Fonction** : Vérifie l'intégrité et la qualité des données albums scrapées depuis Kworb
**Tests effectués** :
- Comptage minimum d'albums (>= 20 requis, 27 constatés)
- Pattern des IDs Albums : `^kworb:album:[a-z0-9\s]+(-\d+)?$`
- Unicité des clés id (27 IDs uniques)
- Variations numériques (2 décimales) ou "N.D." pour données manquantes
- Paliers 1B : next_cap_value multiples de 1 000 000 000
- Jours restants (days_to_next_cap) avec arrondis 2 décimales
- Cohérence des dates (spotify_data_date, latest_date, available_dates_albums)

**Commande** :
```bash
python scripts/test_scraper_albums.py
```

**Résultats attendus** :
- Test 1 : 27 albums ≥ 20 (PASS)
- Test 2 : Pattern IDs valide (PASS)
- Test 3 : Unicité des IDs (PASS)
- Test 4-5 : Variations et paliers 1B (PASS)
- Test 6-7 : Jours restants et dates cohérentes (PASS)

---

#### `scripts/test_songs_ids.py` — Validation IDs Songs (Prompt 4)
**Fonction** : Vérifie que les IDs Songs respectent le format stable après correctif Prompt 4
**Tests effectués** :
- Pattern correct : `^kworb:[^:]+@[^:]+$` (sans rank)
- Comptage des IDs avec `@unknown` (288 sur 315)
- Absence de 'rank' dans les IDs
- Unicité absolue des IDs (315 uniques)

**Commande** :
```bash
python scripts/test_songs_ids.py
```

**Résultats attendus** :
- Pattern valide : 315/315 (PASS)
- IDs avec @unknown : 288 (PASS)
- Aucun 'rank' dans IDs (PASS)
- Unicité : 315 uniques (PASS)

---

### Tests UI — Page Caps imminents (Prompts 7.0 & 7.1)

**Navigation** : Ouvrir http://localhost:8000/Website/ → Cliquer onglet "Caps imminents"

#### Test 1 : Ordre et présence des colonnes
**Objectif** : Vérifier l'ordre exact des colonnes et la présence de tous les éléments
**Actions** :
1. Observer l'ordre des en-têtes de colonnes
2. Vérifier la présence de la légende sous le tableau

**Résultats attendus** :
- Colonnes dans l'ordre : # | Titre | Type | Prochain cap (j) | Streams totaux | Streams quotidiens | Variation (%) | Prochain palier | ETA
- Légende "* = featuring" présente sous le tableau

#### Test 2 : Largeurs colonnes et lisibilité
**Objectif** : Vérifier la hiérarchie visuelle (Titre large, numériques resserrées)
**Actions** :
1. Comparer visuellement la largeur de la colonne Titre vs colonnes numériques
2. Vérifier la taille du texte du titre

**Résultats attendus** :
- Colonne Titre visiblement plus large (environ 2-3× les colonnes numériques)
- Texte titre plus grand que les autres colonnes (1rem vs 0.9rem)

#### Test 3 : Format "Prochain palier" (M/B)
**Objectif** : Vérifier l'affichage en millions/milliards comme Songs/Albums
**Actions** :
1. Observer les valeurs de la colonne "Prochain palier"
2. Comparer avec la colonne identique dans Songs ou Albums

**Résultats attendus** :
- Valeurs affichées en M/B : "5,1 B", "300 M", "2,8 B"
- Format identique à Songs/Albums (pas de nombres longs)

#### Test 4 : Cartes header avec fenêtre dynamique
**Objectif** : Vérifier les labels et mise à jour dynamique de la fenêtre temporelle
**Actions** :
1. Observer les labels des 3 cartes compteurs
2. Changer le sélecteur de fenêtre (30j → 7j)
3. Observer les labels des cartes titres/albums

**Résultats attendus** :
- Labels initiaux : "Nombre total d'éléments" | "Nombre de titres (30 j)" | "Nombre d'albums (30 j)"
- Après changement 7j : "Nombre de titres (7 j)" | "Nombre d'albums (7 j)"
- Compteurs se mettent à jour (nombre d'items diminue avec fenêtre plus courte)

#### Test 5 : Sélecteur fenêtre rapproché
**Objectif** : Vérifier que le sélecteur est visuellement proche du tableau
**Actions** :
1. Mesurer visuellement l'espace entre le sélecteur et le tableau
2. Comparer avec l'espace entre les cartes header et le sélecteur

**Résultats attendus** :
- Espace sélecteur → tableau nettement plus petit que cartes → sélecteur
- Environ 0.75rem vs 1.5rem (visuellement compact)

#### Test 6 : Tri et navigation
**Objectif** : Vérifier que tri et navigation croisée fonctionnent toujours
**Actions** :
1. Cliquer sur colonne "Titre" → Observer indicateur tri (▲/▼)
2. Cliquer sur colonne "#" → Observer réordonnancement
3. Cliquer sur une ligne → Observer navigation vers Songs/Albums + highlight

**Résultats attendus** :
- Indicateur tri se déplace et pointe la bonne colonne
- Lignes se réordonnent correctement (rang numérique, titre alpha ignore *)
- Navigation ouvre la bonne page + scroll + highlight 2s visible

---

## Avertissement sécurité

⚠️ **Ne jamais committer de fichiers contenant des secrets** (.env, tokens, clés API). Utiliser `.gitignore` et stocker les credentials localement uniquement.

---

## Licence

MIT (placeholder — à finaliser ultérieurement).
