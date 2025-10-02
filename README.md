# The Weeknd Dashboard

Dashboard local recensant les streams Spotify de The Weeknd (Songs & Albums) via scraping Kworb. Affichage par pages avec auto-refresh toutes les 10 minutes, snapshots datés (J/J-1/J-2) pour préserver les variations, et intégration Spotify API pour les covers et métadonnées.

---

## Quoi de neuf

**2025-10-02 — Prompt 5 : Orchestrateur auto-refresh 10 min + en-têtes UI dynamiques**

*Orchestrateur automatique :*
- Script `auto_refresh.py` : exécute le pipeline complet toutes les 10 minutes (scrape Songs + Albums, régénération vues, update meta.json)
- Verrou anti-chevauchement (`.sync.lock`) pour éviter exécutions simultanées
- Jitter aléatoire ±15s pour éviter rafales exactes
- Paramétrage flexible : `REFRESH_INTERVAL_SECONDS` (env) ou `--interval` (CLI)
- Mode `--once` pour exécution unique (tests/CI)
- Fallback gracieux : conserve données valides en cas d'erreur scraping
- Rotation automatique : maintien minimum 3 snapshots (J/J-1/J-2), purge au-delà
- meta.json étendu (v1.1) : `last_sync_status` ("ok"/"error"), `last_error` (optionnel)

*En-têtes UI dynamiques :*
- `meta-refresh.js` : fetch meta.json toutes les 10s, mise à jour temps réel
- 3 indicateurs dynamiques : Dernière sync locale, Prochaine mise à jour (countdown MM:SS), Date données Spotify
- Countdown client-side décrémentant sans reload
- Badge "⚠️ Sync partielle" si `last_sync_status = "error"`
- Intégration transparente dans toutes les pages

*Intégration :*
- `start_dashboard.py` modifié : lance orchestrateur en arrière-plan + serveur web
- Auto-refresh actif dès le démarrage, synchronisation toutes les 10 minutes
- 3 snapshots maintenus : J, J-1, J-2 pour calcul variations stables

**2025-10-02 — Prompt 4 : Scraper Albums + Correctif IDs Songs (stabilité inter-jours)**

*Correctif Songs :*
- IDs Songs corrigés pour respecter le contrat stable : `kworb:<norm_title>@<norm_album>` (sans rank)
- Les chansons sans album connu utilisent `@unknown` (exemple : `kworb:blinding lights@unknown`)
- Gestion des doublons temporaires : suffixe numérique ajouté (`@unknown-2`, `@unknown-3`) en attendant les données Spotify
- 315 chansons avec IDs stables et uniques : ✅ pattern `^kworb:[^:]+@[^:]+$` respecté, 288 IDs avec `@unknown`

*Scraper Albums :*
- Scraper Albums Kworb opérationnel : extraction de 27 albums depuis https://kworb.net/spotify/artist/1Xyo4u8uXC1ZmMpatF05PJ_albums.html
- Parsing table Albums : rank, title, streams_total, streams_daily, last_update_kworb
- IDs Albums format `kworb:album:<norm_album>` (normalisation complète : lowercase, suppression caractères spéciaux/ponctuation)
- Snapshot Albums J créé dans `data/history/albums/2025-10-01.json` (27 albums, format brut)
- `data/albums.json` généré avec paliers 1 milliard (1B) : next_cap_value = multiples de 1 000 000 000
- Calculs : variation_pct (2 déc. ou "N.D."), days_to_next_cap (2 déc.)
- meta.json mis à jour avec `available_dates_albums` et timestamps
- Tests complets : 27 albums ≥ 20, IDs uniques, paliers 1B validés, dates cohérentes

**2025-10-02 — Prompt 3 : Scraper Kworb Songs + snapshot J + data/songs.json**
- Scraper Kworb Songs fonctionnel : extraction de 315 chansons depuis https://kworb.net/spotify/artist/1Xyo4u8uXC1ZmMpatF05PJ_songs.html
- User-Agent dédié "The-Weeknd-Dashboard/1.0", throttle 1s, retry avec backoff exponentiel (3 tentatives max)
- Parsing HTML robuste avec BeautifulSoup : extraction rank, title, streams_total, streams_daily
- Détection automatique du rôle : lead (The Weeknd premier artiste) ou feat (featuring)
- Snapshot J créé dans data/history/songs/2025-10-01.json (315 chansons, format brut sans calculs)
- meta.json mis à jour automatiquement (kworb_last_update_utc, spotify_data_date, last_sync_local_iso, history.available_dates)
- data/songs.json régénéré dynamiquement avec calculs (variation_pct, next_cap_value, days_to_next_cap)
- Script generate_current_views.py rendu dynamique (utilise les dates disponibles dans meta.json)
- Toutes les validations passent : 315 id uniques, 282 lead + 33 feat, dates cohérentes, paliers corrects

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
  auto_refresh.py                  # Orchestrateur auto-refresh (pipeline 10 min, lock, jitter)
  scrape_kworb_songs.py            # Scraper Kworb Songs (extraction 315 chansons, IDs stables)
  scrape_kworb_albums.py           # Scraper Kworb Albums (extraction 27 albums)
  generate_current_views.py        # Génère data/songs.json et albums.json depuis snapshots
  validate_data.py                 # Valide conformité des données (schémas, arrondis, unicité, dates)
  test_scraper_songs.py            # Tests automatisés du scraper Songs (6 tests)
  test_scraper_albums.py           # Tests automatisés du scraper Albums (7 tests)
  test_songs_ids.py                # Tests IDs Songs (pattern, unicité, @unknown count)

Website/                           # Dossier parent du code applicatif
  index.html                       # Page principale (SPA avec 3 pages)
  src/
    app.js                         # Script JavaScript (navigation entre pages)
    meta-refresh.js                # Script de mise à jour dynamique des en-têtes (fetch meta.json)
    styles/
      global.css                   # CSS canonique (960 lignes, dark theme)
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
3. ✅ Lance un serveur HTTP sur http://localhost:8000
4. ✅ En-têtes UI se mettent à jour automatiquement (dernière sync, countdown, date données)

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

- **Données placeholder dans l'UI** : l'interface HTML affiche encore des données factices (connexion prévue dans prompts suivants).
- **Album "Unknown" pour les chansons** : Kworb ne fournit pas l'information d'album, sera résolu via Spotify API (prompt 6).
- **Variation_pct "N.D." pour toutes les chansons** : Les id ayant changé entre fixtures et scraper, aucun matching J/J-1 n'est possible pour l'instant (sera résolu au prochain scraping quotidien).
- **Pas de scraper Albums** : seules les chansons sont scrapées pour l'instant (prompt 4 : scraper albums).
- **Snapshots J-2 manquants** : seuls J et anciennes fixtures sont disponibles (se remplira progressivement).
- **Recherche non fonctionnelle** : la barre de recherche est présente mais ne filtre rien encore.
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

### Prompt 1 — Tests de l'UI Shell

### Test 1 - Arborescence complète
**Commande** : `Get-ChildItem -Recurse -Depth 4`  
**Objectif** : Vérifier la structure du projet avec README.md et .env.local à la racine, et tous les dossiers applicatifs dans Website/.

### Test 2 - README à la racine
**Commande** : `Test-Path README.md`  
**Objectif** : Confirmer que README.md est bien à la racine du projet.

### Test 3 - .env.local à la racine
**Commande** : `Test-Path .env.local`  
**Objectif** : Confirmer que .env.local est bien à la racine du projet.

### Test 4 - global.css dans src/styles
**Commande** : `Test-Path Website/src/styles/global.css`  
**Objectif** : Confirmer que global.css est bien dans Website/src/styles/.

### Test 5 - Unicité du CSS
**Commande** : `Get-ChildItem -Filter "global.css" -Recurse`  
**Objectif** : Confirmer qu'un seul fichier global.css existe dans le projet (Website/src/styles/global.css).

### Test 6 - Protection des secrets
**Commande** : `git check-ignore -v .env.local`  
**Objectif** : Prouver que .env.local à la racine est bien ignoré par Git (ligne 7 de .gitignore).

### Test 7 - Intégrité du CSS
**Commande** : `Measure-Object -Line Website/src/styles/global.css`  
**Objectif** : Vérifier que le CSS n'a pas été tronqué lors du déplacement (960 lignes attendues).

### Test 8 - .gitignore mis à jour
**Commande** : `Select-String -Pattern "\.env\.local" .gitignore`  
**Objectif** : Confirmer que .gitignore contient bien `.env.local` à la ligne 7.

---

## Avertissement sécurité

⚠️ **Ne jamais committer de fichiers contenant des secrets** (.env, tokens, clés API). Utiliser `.gitignore` et stocker les credentials localement uniquement.

---

## Licence

MIT (placeholder — à finaliser ultérieurement).
