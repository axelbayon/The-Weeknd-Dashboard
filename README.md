# The Weeknd Dashboard

Dashboard local recensant les streams Spotify de The Weeknd (Songs & Albums) via scraping Kworb. Affichage par pages avec auto-refresh toutes les 10 minutes, snapshots datés (J/J-1/J-2) pour préserver les variations, et intégration Spotify API pour les covers et métadonnées.

---

## Quoi de neuf

---

**2025-10-05 — Prompt 8.7 : Cartes d'en-tête calculées depuis les lignes visibles du tableau**

**Problématique** : Les cartes d'agrégats (Nombre de titres, Streams totaux, Streams quotidiens) étaient calculées depuis `meta.json.songs_role_stats` ou depuis les données JSON chargées. Résultat : pas de cohérence avec ce qui est **réellement affiché** dans le tableau (après filtrage potentiel).

**Règle métier** :
- Les cartes d'en-tête doivent refléter **exactement** les lignes visibles du tableau
- Split Feat/Solo détecté par astérisque en début de titre (`title.startsWith('*')`)
- Recalcul après : render initial, changement de page, auto-refresh
- **PAS** de recalcul après tri (ordre des lignes ne change pas les sommes)

**Solution** :
1. **Nouvelles fonctions dans `data-renderer.js`** :
   - `calculateSongsStatsFromDOM()` : lit les `tr[data-row-id]` visibles (via `offsetParent !== null`)
     - Parse `title` pour détecter Feat (astérisque)
     - Parse `streams_total` et `streams_daily` depuis cellules td
     - Agrège : total, totalStreams, dailyStreams, lead, feat
   - `calculateAlbumsStatsFromDOM()` : même principe sans split Feat/Solo
   - `parseStreamValue(text)` : convertit "1 234 567" → 1234567, gère "—" et valeurs nulles

2. **Modifications lifecycle** :
   - `renderSongsAggregates()` et `renderAlbumsAggregates()` : 
     - Ne chargent **plus** `meta.json` ou `songs.json`
     - Appellent directement `calculateFromDOM()`
     - Vérifient que le tableau est rendu avant calcul
   - `renderSongsTable()` et `renderAlbumsTable()` :
     - Appellent `renderAggregates()` **après** le render du tableau (dans RAF)
     - Garantit que les lignes DOM existent avant calcul
   - `initCurrentPage()` : 
     - Suppression du `Promise.all([renderAggregates(), renderTable()])`
     - Appel séquentiel : `renderTable()` qui déclenchera `renderAggregates()` dans RAF

3. **Points de recalcul** :
   - ✅ Après `renderSongsTable()` / `renderAlbumsTable()` (render initial)
   - ✅ Après changement de page via `switchPage()` → `initCurrentPage()`
   - ✅ Après auto-refresh via `data-sync-updated` → `refreshCurrentPage()`
   - ❌ **PAS** après tri (tri dispatch `table:rows-updated` mais on ne l'écoute pas)

**Avantages** :
- ✅ Cartes toujours cohérentes avec le tableau affiché
- ✅ Pas de dépendance à `meta.json.songs_role_stats` (peut être obsolète)
- ✅ Détection Feat par astérisque côté client (plus flexible que `role` backend)
- ✅ Prêt pour futur filtrage/recherche avancée

**Fichiers modifiés** :
- `Website/src/data-renderer.js` :
  - `calculateSongsStatsFromDOM()` : nouvelle fonction (70 lignes)
  - `calculateAlbumsStatsFromDOM()` : nouvelle fonction (40 lignes)
  - `parseStreamValue()` : helper parsing (10 lignes)
  - `renderSongsAggregates()` : refactorisé pour DOM
  - `renderAlbumsAggregates()` : refactorisé pour DOM
  - `renderSongsTable()` : ajout appel `renderAggregates()` dans RAF
  - `renderAlbumsTable()` : ajout appel `renderAggregates()` dans RAF
  - `initCurrentPage()` : suppression `Promise.all`, render séquentiel

**Tests manuels** : Voir `TESTS_PROMPT_8_7.md`
- T1 : Cohérence sommes Titres
- T2 : Split Feat/Solo correct (astérisque)
- T3 : Cohérence sommes Albums
- T4 : Tri ne recalcule pas
- T5 : Refresh auto recalcule
- T6 : Changement page recalcule
- T7 : Résilience valeurs invalides

**Cache-busting** : Aucun (calcul côté client uniquement)

---

**2025-10-05 — Prompt 8.6 : Rotation J/J-1/J-2 basée sur la vraie date Spotify (indépendante de l'horloge locale)**

**Problématique** : La rotation des snapshots et la `spotify_data_date` étaient calculées avec `datetime.now() - 1 jour`, dépendant de l'horloge locale de la machine. Résultat : un scrape à 2h du matin locale pouvait créer un nouveau jour alors que Kworb n'avait pas encore basculé, causant des incohérences.

**Règle métier** : 
- Si Kworb affiche "Last updated: D", alors `spotify_data_date = D - 1 jour` (calendaire)
- On ne bascule vers D que quand Kworb passe son "Last updated" à D+1
- **Source de vérité unique** : `meta.json.kworb_last_update_utc` (timestamp UTC extrait de Kworb)

**Solution** :
1. **Module `date_manager.py`** : gestionnaire centralisé de dates et rotation
   - `extract_kworb_last_update(html)` : parse "Last updated: YYYY/MM/DD" depuis HTML Kworb
   - `calculate_spotify_data_date(kworb_utc)` : calcule `kworb_day - 1 jour` (calendaire UTC)
   - `should_rotate(meta, new_date)` : compare `new_date > history.latest_date` (strict)
   - `rotate_snapshots_atomic()` : rotation idempotente J→J-1→J-2
     - Si nouveau jour : renommer J→J-1, créer nouveau J, purger J-2 ancien
     - Sinon : réécrire seulement le J actuel (idempotence)
   - `update_meta_with_rotation()` : met à jour `meta.json` avec history cohérent
   - `log_rotation_decision()` : log clair des décisions (rotation ou pas)

2. **Scrapers modifiés** (`scrape_kworb_songs.py`, `scrape_kworb_albums.py`) :
   - Import du `date_manager`
   - Extraction du timestamp Kworb depuis HTML : `Last updated: 2025/10/05`
   - Fallback sur `datetime.now(UTC)` si extraction échoue
   - Calcul `spotify_data_date` via `calculate_spotify_data_date()`
   - Rotation automatique via `rotate_snapshots_atomic()` et `update_meta_with_rotation()`
   - Log détaillé : "Kworb Day = 2025-10-05 → Spotify Data Date = 2025-10-04"

3. **Orchestrateur (`auto_refresh.py`)** :
   - Suppression de l'ancienne fonction `rotate_snapshots()` (obsolète)
   - Rotation désormais gérée par les scrapers eux-mêmes
   - Étape 5 : "Rotation gérée automatiquement par les scrapers"

4. **Tests de validation** (`test_date_rotation.py`) :
   - **T1 (Pas de bascule nocturne locale)** : 
     - Kworb = 2025-10-05T23:50Z, latest_date = 2025-10-04
     - Résultat : spotify_data_date = 2025-10-04, **aucune rotation**
   - **T2 (Changement de jour Kworb)** :
     - Kworb passe à 2025-10-06T00:10Z
     - Résultat : spotify_data_date = 2025-10-05, **rotation effectuée**
   - **T3 (Idempotence)** :
     - Rejouer T2 : latest_date = 2025-10-05 = spotify_data_date
     - Résultat : **aucune nouvelle rotation**, réécriture J uniquement
   - **T4 (Front cohérent)** :
     - Vérification : `spotify_data_date = kworb_day - 1` dans meta.json
   - **T5 (Fallback parsing)** :
     - Timestamp invalide → `parse_kworb_timestamp()` retourne `None`
     - Fallback : `datetime.now(UTC)` utilisé
   - ✅ **Tous les tests PASSED**

**Critères d'acceptation** :
- ✅ `spotify_data_date` ne change pas tant que `kworb_day` n'a pas changé, même en pleine nuit locale
- ✅ À changement de `kworb_day`, rotation J/J-1/J-2 correcte et idempotente
- ✅ `meta.json` mis à jour de façon cohérente (`spotify_data_date`, `history.latest_date`, `available_dates`)
- ✅ Le front affiche toujours `spotify_data_date = kworb_day - 1` (cohérence garantie)
- ✅ Tests T1-T5 validés

**Fichiers modifiés** :
- **Nouveau** : `scripts/date_manager.py` (355 lignes) : module de gestion dates/rotation
- `scripts/scrape_kworb_songs.py` :
  - Import `date_manager`
  - Extraction timestamp Kworb depuis HTML (pattern "Last updated: YYYY/MM/DD")
  - Fonction `create_snapshot()` utilise rotation atomique
  - Fonction `update_meta()` délègue au `date_manager`
- `scripts/scrape_kworb_albums.py` : mêmes modifications que songs
- `scripts/auto_refresh.py` : suppression appel `rotate_snapshots()`, rotation gérée par scrapers
- **Nouveau** : `test_date_rotation.py` : tests T1-T5 complets

**Cache-busting** : Aucun (backend only)

**Règles de rotation** :
```python
# Calcul de la date Spotify
kworb_day = datetime.strptime("2025/10/05", "%Y/%m/%d").date()  # Extrait de Kworb
spotify_data_date = kworb_day - timedelta(days=1)  # = 2025-10-04

# Décision de rotation
should_rotate = spotify_data_date > meta["history"]["latest_date"]

# Si rotation nécessaire :
#   1. Purger ancien J-2
#   2. J actuel devient J-1 (gardé avec son nom)
#   3. Créer nouveau J = spotify_data_date.json
#   4. Mettre à jour meta.json

# Si pas de rotation (idempotence) :
#   - Réécrire J actuel avec nouvelles données
#   - Aucun rename
```

**Avantages** :
- ✅ **Indépendant du fuseau horaire machine** : seul le timestamp Kworb compte
- ✅ **Gel automatique** : si Kworb pas à jour (weekend, maintenance), spotify_data_date reste fixe
- ✅ **Idempotent** : relancer 10 fois le même jour = 1 seul snapshot créé
- ✅ **Atomique** : rotation complète ou rollback, pas d'état intermédiaire
- ✅ **Fallback sécurisé** : si parsing Kworb échoue, utilise `datetime.now(UTC)` (safe)
- ✅ **Log clair** : chaque décision (rotate ou pas) est journalisée avec contexte

---

**2025-10-05 — Prompt 8.2 : Indicateur de mouvement de rang (J vs J-1) avec flèches ▲/▼**

**Problématique** : Les utilisateurs ne pouvaient pas voir rapidement quelles chansons/albums avaient gagné ou perdu des places au classement entre J (aujourd'hui) et J-1 (hier).

**Solution** :
1. **Calcul automatique des mouvements** (`scripts/generate_current_views.py`) :
   - Ajout de `rank_prev` (rang à J-1) depuis le snapshot précédent
   - Calcul de `rank_delta = rank_prev - rank` :
     - Positif = gain de places (ex: +3 → chanson montée de 3 positions)
     - Négatif = perte de places (ex: −2 → chanson descendue de 2 positions)
     - Null = pas de données J-1 (chanson absente hier ou premier jour)
   - Intégration dans le même pipeline que `variation_pct`, `next_cap_value`, etc.

2. **Affichage visuel des badges** (`Website/src/data-renderer.js` + `global.css`) :
   - Badge positionné **à gauche du tableau**, avant la colonne `#`
   - **Gain** : flèche ▲ + nombre en turquoise (`#4ae3c8`)
   - **Perte** : flèche ▼ + nombre en rouge saumon (`#ff8678`)
   - **Stable ou inconnu** : aucun badge (pas d'espace réservé)
   - Accessibilité : `aria-label` et `title` avec texte explicite ("+3 places", "−2 places")
   - Badge en `position: absolute` avec `left: -60px`, ne perturbe pas la structure du tableau

3. **Données enrichies** :
   - `songs.json` : 317/317 chansons avec `rank_prev` et `rank_delta`
   - `albums.json` : 25/25 albums avec `rank_prev` et `rank_delta`
   - Source de vérité : `rank` de Kworb (J) vs `rank` du snapshot J-1

4. **Tests validés** :
   - ✅ **Take My Breath** : #71 (était #72) → **▲ 1** (gain)
   - ✅ **Double Fantasy** : #72 (était #71) → **▼ 1** (perte)
   - ✅ Inversion symétrique détectée et affichée correctement
   - ✅ 4 mouvements détectés (2 gains ↑, 2 pertes ↓)
   - ✅ Non-régression : tri, recherche, sticky #, auto-refresh OK

**Critères d'acceptation** :
- ✅ `rank_prev` et `rank_delta` présents dans `songs.json` et `albums.json`
- ✅ Badge vert ▲ n pour les gains, rouge ▼ n pour les pertes, rien pour stable/inconnu
- ✅ Affiché sur pages Titres et Albums
- ✅ Accessibilité avec `aria-label`/`title` explicites
- ✅ Tests OK (mouvements détectés, cas symétrique, non-régression)

**Fichiers modifiés** :
- `scripts/generate_current_views.py` : calcul `rank_prev` et `rank_delta` dans `generate_current_view()`
- `Website/src/data-renderer.js` :
  - Fonction `createRankDeltaBadge(item)` : génère badge avec flèche + delta
  - Intégration dans `createSongRow()` et `createAlbumRow()`
- `Website/src/styles/global.css` : classes `.rank-delta`, `.is-up`, `.is-down` avec positionnement absolu
- `Website/index.html` : cache-busting v8.2 (data-renderer, global.css)

**Cache-busting** : v8.2 (`index.html`)

---

**2025-01-27 — Prompt 7.9 : Caps clic plein-surface Titre + Variations unifiées (3 pages) + Albums tri/légende compilation (^)**

**Problématique** : Header Titre dans Caps n'est cliquable que sur le bouton interne (pas plein-surface comme #). Variations (%) utilisent des formats différents entre pages : Caps avec `.toFixed(2)` (point décimal anglais), Songs/Albums avec `formatPercent` (virgule FR). Albums n'ignorent pas le symbole ^ (compilation) lors du tri alphabétique, et pas de légende explicative pour ^.

**Solution** :
1. **Caps : clic plein-surface sur Titre** :
   - Refactorisation `caps.js` : écoute clic au niveau `<thead>`, résolution avec `event.target.closest('th[data-sort-key]')`
   - Header Titre avec `data-sort-key="title"` (déjà en place)
   - `pointer-events: none` déjà en place sur éléments décoratifs (header-text, sort-icon, legend) depuis 7.6
   - Toute la surface du `<th>` déclenche le tri Titre

2. **Variations (%) unifiées sur 3 pages** :
   - **Caps** : migration de `.toFixed(2)` vers `formatPercent()` (format FR avec virgule)
   - **Songs/Albums** : déjà avec `formatPercent` depuis 7.8
   - **Pipeline unifié** : 2 décimales FR + signe (+X,XX % / −X,XX %)
     - Valeurs numériques : `formatPercent()` avec classes positive (vert) / negative (rouge) / neutral (gris)
     - Valeurs manquantes : "N.D." avec classe `data-table__delta--na` (gris neutre)
   - **Résultat** : Format identique sur Songs, Albums, Caps (virgule, 2 déc, signe, N.D. grisé)

3. **Albums : tri ignore ^ + légende compilation** :
   - **Tri alphabétique** : `normalizeTitle()` modifié pour ignorer `^[*^]\s*` en tête (featuring * ou compilation ^)
   - Appliqué dans `table-sort.js` (Songs/Albums) et `caps.js` (Caps)
   - Affichage conservé : titres avec ^ ou * visibles, mais ignorés pour le tri
   - **Header Albums** :
     - Label "Titre" → "Albums"
     - Légende "* = featuring" → "^ = compilation"
     - Style identique à légende featuring (pointer-events:none, même classes)
   - **Header Songs et Caps** : "Titre" → "Titres" (ajout du "s")

**Critères de validation** :
- ✅ Caps : clic n'importe où dans header Titre déclenche le tri, indicateur ▲/▼ sur Titre
- ✅ Variations (%) : format FR unifié (+X,XX % vert, −X,XX % rouge, N.D. gris) sur les 3 pages
- ✅ Albums : tri alphabétique ignore ^ (comme *), légende "^ = compilation" visible
- ✅ Songs/Caps : légende "* = featuring" inchangée, headers "Titres" avec "s"
- ✅ Aucune régression (tri #, autres colonnes, sticky, widths, couleurs rangs, auto-refresh)

**Fichiers modifiés** :
- `Website/src/caps.js` :
  - Lignes 94-100 : refactorisation écoute thead + `closest('th[data-sort-key]')`
  - Lignes 103-118 : `handleSortClick()` avec plein-surface
  - Lignes 181-184 : tri Titre ignore `^[*^]\s*` (featuring/compilation)
  - Lignes 377-403 : pipeline Variation unifié avec `formatPercent()`
- `Website/src/table-sort.js` :
  - Lignes 59-68 : `normalizeTitle()` ignore `^[*^]\s*` en tête
- `Website/index.html` :
  - Lignes 129-137 : header Songs "Titre" → "Titres"
  - Lignes 291-299 : header Albums "Titre" → "Albums" + légende "^ = compilation"
  - Lignes 466-474 : header Caps "Titre" → "Titres"
  - Ligne 8 : cache-busting CSS v7.9
  - Lignes 540-542 : cache-busting JS v7.9 (table-sort, caps)

**Cache-busting** : v7.9 (`index.html`)

---

**2025-10-03 — Prompt 7.10 : Variation 0% neutre (Songs/Albums) + tri Albums ignore ^ (compilation)**

**Problématique** : Les variations à 0% étaient affichées en vert (positif) sur Songs et Albums, alors qu'elles doivent être neutres/grises comme sur Caps imminents. Le tri Albums doit ignorer le préfixe ^ (compilation) pour l'ordre alphabétique, mais l'affichage doit conserver le symbole.

**Solution** :
1. **Variation (%) 0% neutre/grise** :
   - Correction du pipeline Songs/Albums dans `data-renderer.js` : passage d'une condition binaire (`value >= 0`) à une condition triple (`>0` vert, `<0` rouge, `=0` gris).
   - 0% s'affiche désormais en gris neutre (`data-table__delta--neutral`), identique à Caps.
   - N.D. reste grisé (`data-table__delta--na`).

2. **Tri Albums ignore ^ (compilation)** :
   - Vérification que `normalizeTitle()` dans `table-sort.js` retire bien le préfixe ^ ou * pour le tri alphabétique.
   - Exemple validé : "Avatar" < "After Hours" < "After Hours (Deluxe)" < "^ Compilation Album".

3. **Cache-busting** :
   - Passage de v7.9 à v7.10 pour CSS et JS dans `index.html`.

**Critères de validation** :
- ✅ Songs/Albums : variations à 0% affichées en gris neutre, positives en vert, négatives en rouge, N.D. en gris
- ✅ Tri Albums : ^ ignoré pour le tri, affiché dans la cellule
- ✅ Aucune régression sur le tri, le format, les couleurs ou l'interaction

**Fichiers modifiés** :
- `Website/src/data-renderer.js` : pipeline variation Songs/Albums (condition triple)
- `Website/src/table-sort.js` : tri Albums (normalizeTitle)
- `Website/index.html` : cache-busting v7.10

---

**2025-10-04 — Prompt 8.0 : Affichage covers Spotify (Titres, Albums, Caps) + Résolveur business rules**

**Problématique** : Les covers des chansons et albums sont affichées avec des émojis placeholder (🎵/💿). Il faut intégrer les vraies covers Spotify avec des règles métier strictes pour gérer les cas complexes : albums Original vs Deluxe, feat songs vers albums d'autres artistes, Trilogy allowlist, blacklists, mixtapes originales, BOF, live albums, etc.

**Solution** :
1. **Client Spotify API** (`scripts/spotify_client.py`) :
   - Client Credentials Flow avec token caching (expiration 1h, marge 5min)
   - Méthodes : `search_track()`, `search_album()`, `get_album()`
   - Cache MD5 persistant dans `data/cache/spotify_api_cache.json`
   - Rate limiting : retry 429 avec Retry-After header + backoff exponentiel
   - Market : "US" (configurable via `SPOTIFY_MARKET`)

2. **Résolveur business rules** (`scripts/cover_resolver.py`) :
   - **Blacklist** : "The Highlights" jamais utilisé pour les songs
   - **Removals** : Albums "Avatar" et "Music" supprimés complètement de l'affichage (25 albums au lieu de 27)
   - **Trilogy Allowlist** : Seulement 3 chansons utilisent la cover Trilogy : "Twenty Eight", "Valerie", "Till Dawn (Here Comes the Sun)"
   - **Explicit Mappings (45+)** : Mappings directs pour cas spéciaux
     - **Mixtapes originales** : "Wicked Games" → "House Of Balloons (Original)", "Lonely Star" → "Thursday (Original)", "D.D." → "Echoes Of Silence (Original)"
     - **Feat songs** : "*Love Me Harder" → "My Everything (Deluxe)" (Ariana Grande), "*Moth To A Flame" → "Paradise Again" (Swedish House Mafia), "*Wild Love" → "9" (Cashmere Cat)
     - **BO Soundtracks** : "Elastic Heart" → "Hunger Games OST", "Where You Belong" → "Fifty Shades OST", "Nothing Is Lost" → "Avatar OST"
     - **Singles** : "Dancing In The Flames", "Timeless", "Double Fantasy"
     - **Cas spéciaux** : "Save Your Tears" → After Hours (original), "Save Your Tears (Remix)" → After Hours (Deluxe)
   - **Artist Overrides** : Pour feat songs et OST, cherche avec l'artiste correct (Ariana Grande, Swedish House Mafia, Cashmere Cat, Various Artists)
   - **Direct Album IDs** : Pour albums difficiles à trouver (OST), utilise IDs Spotify directs
   - **Scoring heuristique** :
     - album_type : album studio (100), single (50), compilation (10)
     - Pénalités : Deluxe -30 (sauf si remix), Live -50 (sauf si "live" dans titre cherché)
     - Bonus : Popularité ×0.1, match nom album dans titre +30
   - **Titre normalization** : Retire `^[*^]\s*` (feat/compilation), supprime " - from..." segments, conserve (Remix), (Live), (Instrumental)

3. **Script d'enrichissement** (`scripts/enrich_covers.py`) :
   - Charge credentials depuis `.env.local` (SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
   - Enrichit `data/songs.json` et `data/albums.json` avec 2 nouveaux champs :
     - `spotify_album_id` : ID Spotify de l'album source
     - `cover_url` : URL HD de la cover (640×640)
   - Filtrage Avatar/Music AVANT enrichissement (suppression complète)
   - Détection lead/feat basée sur préfixe `*` dans le titre
   - Gestion gracieuse des échecs (N/A si cover introuvable)

4. **Intégration UI** :
   - `Website/src/data-renderer.js` : Affichage conditionnel dans `renderSongsTable()` et `renderAlbumsTable()`
     - Si `cover_url` présent : `<img src="..." class="cover-image">`
     - Sinon : placeholder emoji `<div class="cover-placeholder">🎵</div>`
   - `Website/src/styles/global.css` : Classe `.cover-image` (border-radius 12px, object-fit cover, 100% dimensions)
   - Cache-busting v8.0 pour CSS et JS

**Critères de validation** :
- ✅ Songs : 316/317 enrichis (99.68%), 1 seul échec (Love Me Harder - Gregor Salto Amsterdam Mix introuvable)
- ✅ Albums : 24/25 enrichis (96%), Avatar/Music supprimés (total 25 au lieu de 27)
- ✅ Cas spécifiques validés :
  - Save Your Tears → After Hours (original, pas Deluxe)
  - Save Your Tears (Remix) → After Hours (Deluxe)
  - Trilogy allowlist : Twenty Eight ✅, Valerie ✅, Till Dawn ✅ (autres chansons → mixtapes originales)
  - Mixtapes : Wicked Games → House Of Balloons (Original), Lonely Star → Thursday (Original), D.D. → Echoes Of Silence (Original)
  - Love Me Harder → My Everything (Deluxe) (Ariana Grande)
  - Moth To A Flame → Paradise Again (Swedish House Mafia)
  - Wild Love → 9 (Cashmere Cat)
  - Elastic Heart → Hunger Games OST
  - Where You Belong → Fifty Shades OST
  - Nothing Is Lost → Avatar OST
  - Live versions → Live At SoFi Stadium
  - Devil May Cry → Hunger Games OST
- ✅ The Highlights jamais utilisé pour songs (blacklist fonctionne)
- ✅ Avatar/Music absents de la liste albums (2 supprimés)
- ✅ After Hours ≠ After Hours (Deluxe) : covers distinctes
- ✅ Covers HD (640×640) affichées avec border-radius 12px

**Commandes** :
```bash
# Enrichir covers (nécessite .env.local avec credentials Spotify)
python scripts/enrich_covers.py

# Credentials requis dans .env.local :
SPOTIFY_CLIENT_ID=your_id
SPOTIFY_CLIENT_SECRET=your_secret
SPOTIFY_MARKET=US  # optionnel, défaut US
```

**Fichiers créés** :
- `scripts/spotify_client.py` (204 lignes) : Client Spotify API
- `scripts/cover_resolver.py` (323 lignes) : Résolveur business rules avec 45+ mappings explicites
- `scripts/enrich_covers.py` (179 lignes) : Orchestrateur enrichissement

**Fichiers modifiés** :
- `Website/src/data-renderer.js` : Rendu conditionnel covers (lignes 316-327, 462-473)
- `Website/src/styles/global.css` : Classe .cover-image (lignes 855-861)
- `Website/index.html` : Cache-busting v8.0 (lignes 8, 543)

**Cache-busting** : v8.0 (`index.html`)

**Structure cache** :
- `data/cache/spotify_api_cache.json` : Cache API Spotify (clés MD5, réponses complètes)
- Pas de fichier covers séparé : `spotify_album_id` + `cover_url` directement dans songs.json/albums.json

---

**2025-10-04 — Prompt 8.1 : Nom d'album affiché pour chaque titre (Titres, Albums, Caps)**

**Problématique** : Les titres affichent "Unknown" sous le nom de la chanson dans les tableaux, même après l'enrichissement Spotify. L'utilisateur veut voir le nom d'album exact (celui de la cover) au lieu de "Unknown".

**Solution** :
1. **Backend : Sauvegarde album_name** :
   - `scripts/enrich_covers.py` modifié : ajout de `song["album_name"]` et `song["album_type"]` lors de l'enrichissement
   - Ces champs sont maintenant persistés dans `data/songs.json` et `data/albums.json`
   - Source de vérité unique : le même album choisi pour la cover

2. **Frontend : Affichage avec fallback "Inconnu"** :
   - `Website/src/data-renderer.js` : Utilisation de `song.album_name || 'Inconnu'` au lieu de `song.album`
   - `Website/src/caps.js` : Idem pour la page Caps imminents (lignes Type = TITRE)
   - Attribute `title` ajouté pour afficher le nom complet au survol (ellipsis)

3. **Résultats** :
   - 316/317 chansons enrichies ont un `album_name` affiché
   - 1 échec (Love Me Harder - Gregor Salto Amsterdam Mix) affiche "Inconnu" comme prévu
   - Format unifié sur les 3 pages : "After Hours", "After Hours (Deluxe)", "Paradise Again", "My Everything (Deluxe)", "Thursday (Original)", etc.

**Critères de validation** :
- ✅ Save Your Tears → After Hours (pas After Hours Deluxe)
- ✅ Save Your Tears (Remix) → After Hours (Deluxe)
- ✅ *Moth To A Flame → Paradise Again (Swedish House Mafia)
- ✅ *Love Me Harder → My Everything (Deluxe) (Ariana Grande)
- ✅ Lonely Star → Thursday (Original)
- ✅ *Elastic Heart → The Hunger Games: Catching Fire OST
- ✅ Love Me Harder - Gregor Salto Amsterdam Mix → "Inconnu" (échec enrichissement attendu)
- ✅ Aucune régression sur tri, sticky, recherche, variations %

**Fichiers modifiés** :
- `scripts/enrich_covers.py` : Ajout `album_name` et `album_type` dans enrichissement songs/albums
- `Website/src/data-renderer.js` : Rendu `song.album_name || 'Inconnu'` avec title attribute
- `Website/src/caps.js` : Idem pour page Caps (lignes titre)

**Commandes** :
```bash
# Ré-enrichir pour ajouter album_name à toutes les chansons
python scripts/enrich_covers.py
```

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
  songs.json                       # Vue courante des chansons (317 items avec calculs)
  albums.json                      # Vue courante des albums (27 items avec calculs)
  meta.json                        # Métadonnées globales (dates, historique)
  history/                         # Snapshots journaliers
    songs/                         # Snapshots quotidiens des chansons (J, J-1, J-2)
      2025-09-29.json              # Fixture J-2
      2025-09-30.json              # Fixture J-1
      2025-10-01.json              # Snapshot J actuel (317 chansons, IDs stables)
    albums/                        # Snapshots quotidiens des albums
      2025-09-29.json              # Fixture J-2
      2025-09-30.json              # Fixture J-1
      2025-10-01.json              # Snapshot J actuel (27 albums)
  album_detail/                    # Détails albums Spotify (à remplir plus tard)

scripts/                           # Scripts Python de scraping, génération et validation
  start_dashboard.py               # 🚀 Script de lancement complet (orchestrateur + serveur web)
  auto_refresh.py                  # Orchestrateur auto-refresh (pipeline 10 min, lock, jitter, rotation J/J-1/J-2)
  scrape_kworb_songs.py            # Scraper Kworb Songs (extraction 317 chansons, IDs stables)
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

Récupère 317 chansons depuis Kworb, crée snapshot dans `data/history/songs/{date}.json`, met à jour `data/songs.json` avec paliers 100M.

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
