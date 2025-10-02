# The Weeknd Dashboard

Dashboard local recensant les streams Spotify de The Weeknd (Songs & Albums) via scraping Kworb. Affichage par pages avec auto-refresh toutes les 10 minutes, snapshots datés (J/J-1/J-2) pour préserver les variations, et intégration Spotify API pour les covers et métadonnées.

---

## Quoi de neuf

---

**2025-10-02 — Prompt 6.6 (rev) : Tooltip/bouton perfectionné + Fix espacement SPA (hidden) + Albums meta**

*Corrections finales UI tooltip + fix architectural espacement SPA :*

**A) Carte "Prochaine MAJ" - Bouton et tooltip finalisés** :
- **Bouton "i"** : Bordure blanche (`border:1px solid #fff`) conservant position absolute top-right
- **Tooltip repositionné** : Aligné au-dessus du bouton (`inset-inline-end:0.6rem`, plus `left:50%`), flèche à droite
- **Lisibilité améliorée** : `max-inline-size` 22rem→26rem, `padding` 0.75rem/0.9rem→1rem/1.2rem
- **Style hover dynamique** : Au survol/focus du bouton, border tooltip prend couleur du chrono :
  - État attente (`.is-wait`) : border ambre `rgba(242,180,34,.65)`
  - État prêt (`.is-ready`) : border vert `rgba(24,160,88,.65)`
  - Fond plus contrasté `rgba(12,14,24,.95)`
- **Sélecteurs CSS** : Utilisation de `:has()` pour détecter état badge et appliquer style correspondant

**B) Fix architectural espacement SPA** :
- **Problème racine** : `display:none` dans main.js détruisait le flux CSS et créait "sauts" d'espacement
- **Solution** : Remplacement par attribut `hidden` (ligne 73 main.js) :
  ```javascript
  pages.forEach(page => page.hidden = true);  // Au lieu de page.style.display='none'
  targetPage.hidden = false;                   // Au lieu de targetPage.style.display='block'
  ```
- **Avantage** : Attribut HTML natif, ne modifie pas le flux de mise en page, navigation fluide
- **Nettoyage CSS** : Suppression règle temporaire `.page .table-section { margin-block-start:28px }` (devenue inutile)
- **Règle conservée** : `.table-section { margin-block-start:28px }` (espacement naturel après header-cards)

**C) Albums - Cartes meta affichées** :
- **Vérification** : Cartes Albums utilisent les mêmes `data-testid` que Songs :
  - `header-last-sync` : Dernière sync locale
  - `header-next-update` : Prochaine mise à jour (avec badge chrono)
  - `header-spotify-data-date` : Date données Spotify (J-1)
- **Mécanisme** : `meta-refresh.js` met à jour tous les éléments via `querySelector('[data-testid]')` (universel)
- **Résultat** : Albums affiche et rafraîchit automatiquement toutes les cartes meta (aucune logique à modifier)

*Fichiers modifiés :*
- `Website/src/styles/global.css` : 
  - `.nu-info` : border blanche au lieu de var(--panel-600)
  - `.nu-tooltip` : repositionné `inset-inline-end:0.6rem` (aligné bouton), padding/taille augmentés
  - `.nu-tooltip::after` : flèche repositionnée à droite (`inset-inline-end:1rem`)
  - Ajout sélecteurs hover avec `:has(.nu-badge.is-wait)` et `:has(.nu-badge.is-ready)` pour border dynamique
  - Suppression règle temporaire `.page .table-section { margin-block-start:28px }`
- `Website/src/main.js` : 
  - Remplacement `page.style.display='none'/'block'` par `page.hidden=true/false` (ligne 73)
  - Fix architectural pour espacement SPA stable
- `Website/index.html` : 
  - Cache-busting v6.6 sur CSS et tous scripts JS

*Tests de validation :*
1. ✅ Bouton "i" bordure blanche, position top-right inchangée
2. ✅ Tooltip aligné au-dessus du bouton (pas centré sur carte), flèche pointant vers bouton
3. ✅ Tooltip plus large (26rem), plus lisible (padding 1rem/1.2rem)
4. ✅ Au hover/focus : border tooltip ambre (attente) ou vert (prêt), fond plus contrasté
5. ✅ Navigation Songs ↔ Albums ↔ Songs : espacement 28px stable (plus de "saut")
6. ✅ Albums affiche Dernière sync locale, Date Spotify, badge chrono (via data-testid)
7. ✅ Date J-1 inchangée, logique meta.spotify_data_date conservée

---

**2025-10-02 — Prompt 6.5 : UI polish "Prochaine MAJ" (icône/tooltip/chrono) + Espacements SPA + Date J-1**

*Polish final de la carte "Prochaine mise à jour" et corrections UI :*

**A) Refonte complète carte "Prochaine MAJ"** :
- **Markup** : Nouvelle structure `.nu-card` avec `.nu-header` (titre + bouton i) et `.nu-body` (badge)
- **Icône "i" pure CSS** : Suppression de l'emoji ℹ️, bouton `.nu-info` en `position:absolute` (top-right) avec `::before { content:"i" }`
- **Badge sobre** : Style conforme aux captures (fond panel-800, border panel-600, min-width 4.25rem)
- **Classes badge** : `.is-ready` (vert rgba(24,160,88,.18)), `.is-wait` (orange rgba(242,180,34,.12))
- **Tooltip centré** : Position `left:50% + translateX(-50%)` au-dessus de la carte, flèche centrée avec `::after`

**B) JS meta-refresh amélioré** :
- **updateCountdown()** : Format strict MM:SS, suppression mise à jour .nu-eta en boucle (seulement dans tooltip)
- **setupTooltips()** : Remplissage `.nu-eta` (HH:MM:SS) uniquement au moment de l'ouverture du tooltip (hover/focus)
- Événements : `mouseenter/mouseleave` + `focusin/focusout` pour accessibilité clavier

**C) Espacements SPA persistants** :
- **CSS direct** : Ajout `.page .table-section { margin-block-start:28px }` (règle non fragile, pas de sélecteur adjacent)
- **Vérification code** : `data-renderer.js` ne manipule que `tbody.innerHTML`, jamais `.header-cards` ou `.table-section`
- **Résultat** : Espacement 28px garanti après navigation Songs ↔ Albums, aucun "saut" CSS

**D) Date Spotify strict J-1** :
- **Vérification** : `meta-refresh.js` ligne 165 utilise uniquement `meta.spotify_data_date`
- Aucune référence à `kworb_last_update_utc` pour cette carte
- Format FR `DD/MM/YYYY` conservé

*Fichiers modifiés :*
- `Website/index.html` : 
  - Refonte markup cartes "Prochaine MAJ" (Songs & Albums) avec `.nu-card`, `.nu-header`, `.nu-body`
  - Tooltip repositionné au-dessus (avant .nu-header)
  - Cache-busting v6.5 sur CSS et tous scripts JS
- `Website/src/styles/global.css` : 
  - Réécriture complète section badge/tooltip (~130 lignes)
  - `.nu-info` avec `::before content:"i"` (pas d'emoji)
  - `.nu-tooltip` centré avec `transform:translateX(-50%)`
  - `.nu-badge` avec border et fond sobre
  - Ajout `.page .table-section { margin-block-start:28px }` (SPA-proof)
- `Website/src/meta-refresh.js` : 
  - Simplification `updateCountdown()` : suppression màj .nu-eta en boucle
  - Amélioration `setupTooltips()` : remplissage ETA uniquement au showTooltip

*Tests de validation :*
1. ✅ Icône "i" sans emoji, position absolute top-right
2. ✅ Tooltip centré horizontalement au-dessus de la carte
3. ✅ Badge alterne "Prête" (vert) / "MM:SS" (orange) selon countdown
4. ✅ ETA (HH:MM:SS) affiché uniquement dans tooltip au hover/focus
5. ✅ Espacements 28px persistants après navigation Songs ↔ Albums
6. ✅ Date Spotify = `meta.spotify_data_date` uniquement (pas de kworb_last_update)

---

**2025-10-02 — Prompt 6.4 : Espacement SPA + Centrage cellules (override) + Badge/Tooltip "Prochaine MAJ"**

*Corrections finales UI après Prompts 6.2 et 6.3 :*

**A) Fix espacement SPA (structure DOM stable)** :
- **Problème** : Espacement 28px entre header cards et tables "sautait" parfois lors de la navigation Songs ↔ Albums
- **Solution** : Ajout de `margin-block-start: 28px` directement sur `.table-section` dans global.css au lieu de sélecteurs adjacents fragiles
- **Vérification** : `data-renderer.js` ne remplace QUE le `<tbody>`, pas le wrapper `.table-section` (DOM stable)
- **Résultat** : Espacement robuste et persistant après navigation, aucun "saut" visuel

**B) Fix centrage cellules (override text-align)** :
- **Problème** : Certaines cellules numériques n'étaient pas parfaitement centrées (horizontal + vertical) malgré le CSS de Prompt 6.3
- **Solution** : Nouveau contrat CSS avec classes explicites :
  - Base : `th, td` centrés par défaut (`text-align: center; vertical-align: middle;`)
  - `.col-title` : Titre aligné à gauche
  - `.cell-num` : Centrage fort avec `display: flex; align-items: center; justify-content: center;`
- **HTML** : Ajout classes `col-title` sur colonne Titre, `cell-num` sur toutes cellules numériques (Songs & Albums)
- **Résultat** : Centrage parfait de toutes les valeurs numériques (# / Streams / Variation / Prochain cap / Prochain palier), Titre reste à gauche

**C) Date Spotify = meta.spotify_data_date (déjà correct)** :
- **Vérification** : `meta-refresh.js` ligne 152 utilise bien `meta.spotify_data_date` (J-1 de kworb_last_update_utc)
- Affichage format FR : `01/10/2025` au lieu de `2025-10-01`
- Aucune modification requise, implémentation déjà conforme

**D) Style badge + tooltip "Prochaine MAJ"** :
- **HTML** : Markup `.next-update` avec `.nu-badge`, `.nu-info` (bouton ℹ️), `.nu-tooltip` sur Songs et Albums
- **CSS** : 
  - `.nu-badge.is-ready` : Fond vert (#10b981), texte "Prête" quand timeLeft <= 0
  - `.nu-badge.is-wait` : Fond orange (#f59e0b), texte "MM:SS" (countdown)
  - `.nu-info` : Bouton rond 1.75rem, bordure au survol/focus
  - `.nu-tooltip` : Positionné en bas du badge, flèche, fond sombre, z-index 1000
- **JS** : 
  - `updateCountdown()` dans meta-refresh.js : Calcule timeLeft, met à jour badge et `.nu-eta` (ETA au format HH:MM:SS)
  - `setupTooltips()` : Gère `mouseenter/mouseleave` et `focusin/focusout` pour afficher/cacher tooltip (accessible clavier)
  - Tooltip affiche : "La synchro est limitée par un délai de sécurité. Prochaine mise à jour estimée à **19:09:55**."
- **Résultat** : Badge interactif vert/orange, tooltip accessible au survol et focus, ETA précise affichée

*Fichiers modifiés :*
- `Website/src/styles/global.css` : 
  - Ajout `margin-block-start: 28px` sur `.table-section`
  - Nouveau CSS `.col-title` et `.cell-num` pour centrage robuste
  - Styles complets `.next-update`, `.nu-badge`, `.nu-info`, `.nu-tooltip` (~80 lignes)
- `Website/src/data-renderer.js` : Ajout classes `cell-num` et `col-title` dans `createSongRow()` et `createAlbumRow()`
- `Website/src/meta-refresh.js` : 
  - Refactoring `updateCountdown()` pour gérer badge + ETA
  - Ajout `setupTooltips()` pour interactivité mouseenter/focusin
- `Website/index.html` : 
  - Ajout classes `cell-num`/`col-title` dans headers `<th>` Songs (lignes 119-154)
  - Remplacement markup carte "Prochaine mise à jour" par `.next-update` avec badge+tooltip sur Songs (nu-tip-songs) et Albums (nu-tip-albums)

*Impact technique :*
- Espacement stable en SPA sans sélecteurs CSS fragiles
- Centrage cellules numériques parfait avec classes explicites (pas de `:nth-child` cassant)
- Badge "Prochaine MAJ" avec countdown visuel (vert/orange) et tooltip accessible (WCAG conforme)
- Date Spotify affichée au format FR (DD/MM/YYYY), toujours J-1 de la date Kworb

---

**2025-10-02 — Prompt 6.3 : Fix Lead/Feat meta.json + Centrage parfait th/td + Date Spotify (J-1) + Espacement navigation**

*Corrections finales UI après Prompt 6.2 :*

**A) Fix cartes Lead/Feat (valeurs meta.json exactes)** :
- **Problème** : Après `data-sync-updated`, les cartes "Solo / Lead" et "Featuring" affichaient des valeurs recalculées depuis `songs[]` au lieu des stats Kworb exactes de `meta.json.songs_role_stats`
- **Cause** : `calculateSongsStats()` utilisait le cache `window.dataLoader.cachedData.meta` (invalidé après event), `renderSongsAggregates()` chargeait uniquement `loadSongs()` sans recharger `meta.json`
- **Solution** : Modification de `renderSongsAggregates()` pour utiliser `Promise.all([loadSongs(), loadMeta()])` → fetch explicite de `meta.json` à chaque render
- **Résultat** : Cartes Lead/Feat affichent toujours les valeurs Kworb exactes (237 lead, 78 feat) même après refresh automatique

**B) Centrage parfait des cellules (th + td)** :
- **Problème** : Seules les cellules `td` étaient centrées verticalement (via flex), les headers `th` n'avaient que text-align:center
- **Solution** : Modification du sélecteur CSS de `.data-table td` vers `.data-table th, .data-table td` pour appliquer `display: flex; align-items: center; justify-content: center;` sur headers ET cellules
- **Exception** : Colonne Titre (`:nth-child(2)`) conserve `justify-content: flex-start;` pour alignement gauche
- **Résultat** : Headers et cellules numériques parfaitement centrés verticalement et horizontalement

**C) Date Spotify = J-1 (déjà correct)** :
- **Vérification** : `meta-refresh.js` ligne 152 affiche bien `meta.spotify_data_date` (pas `kworb_last_update_utc`)
- Aucune modification requise, code déjà conforme

**D) Espacement navigation robuste** :
- **Vérification** : CSS `.page-header--aggregate, .page-header--split { margin-bottom: 28px; }` déjà appliqué
- Pages Songs et Albums sont persistantes (divs non reconstruites au switch)
- Aucune modification requise, espacement déjà robuste

**E) Badge "Prochaine MAJ" + tooltip (DEFERRED)** :
- Feature complexe nécessitant badge conditionnel (vert "Prête" / orange "MM:SS"), tooltip accessible (role="tooltip", aria-describedby), calcul ETA (nextTickAt = last_sync + interval + jitter)
- Reportée à un prompt ultérieur si critique

*Fichiers modifiés :*
- `Website/src/data-renderer.js` : Ajout paramètre `meta` à `calculateSongsStats()`, refactoring `renderSongsAggregates()` avec `Promise.all()`, console logs détaillés Lead/Feat
- `Website/src/styles/global.css` : Changement sélecteur `.data-table td` → `.data-table th, .data-table td` pour centrage flex sur headers

*Impact technique :*
- Lead/Feat toujours synchronisés avec `meta.json.songs_role_stats` (source de vérité Kworb)
- Centrage UI parfait (vertical + horizontal) sur toutes les colonnes numériques (headers + cellules)
- Date Spotify et espacement navigation confirmés corrects (aucun bug)

---

**2025-10-02 — Prompt 6.2 : Stats Lead/Feat exactes + Nombres entiers FR + Tri/Rang/Centrage perfectionnés**

*Extraction stats Kworb exactes (scrape_kworb_songs.py) :*
- Parse la **table de stats agrégées** HTML Kworb (avant la table sortable)
- Extrait 6 valeurs depuis les colonnes "As lead" et "As feature (*)" :
  - Lead : count (237), streams_total (68 403 452 747), streams_daily (34 346 197)
  - Feat : count (78), streams_total (16 596 277 670), streams_daily (7 055 853)
- Stockage dans `meta.json` → `songs_role_stats: { lead: {...}, feat: {...} }`
- Scraper retourne maintenant `(songs, last_update_kworb, role_stats)` au lieu de tuple 2 éléments
- `update_meta()` accepte `role_stats` et l'écrit dans meta.json
- **Correction encodage** : emojis remplacés par `[GET]`, `[Stats]`, `[OK]` pour éviter UnicodeDecodeError Windows
- Ajout `encoding='utf-8'` dans subprocess.run() pour fiabilité

*Format nombres entiers FR complets (formatters.js) :*
- **Nouveau** : `formatIntFr(value)` utilise `Intl.NumberFormat('fr-FR', {maximumFractionDigits: 0, useGrouping: true})`
- Affiche nombres entiers COMPLETS avec espaces (ex: "5 050 786 130" au lieu de "5,1 B")
- **Remplace formatStreams()** : Toutes les colonnes streams_total et streams_daily affichent maintenant le format entier
- Appliqué sur : stats agrégées (header cards), cellules tables Songs/Albums

*UI affiche stats Kworb directes (data-renderer.js) :*
- `calculateSongsStats()` : Lit `meta.songs_role_stats` **au lieu de recalculer** depuis songs[]
- Fallback : Si `songs_role_stats` absent, recalcul manuel avec console.warn
- Calcul Total = Lead + Feat (count, streams_total, streams_daily)
- `updateSongsAggregatesUI()`, `updateAlbumsAggregatesUI()` : Appel `formatIntFr()` au lieu de `formatStreams()`/`formatDailyStreams()`
- `createSongRow()`, `createAlbumRow()` : Colonnes streams_total/streams_daily formatées avec `formatIntFr()`

*Tri "Prochain palier" numérique correct :*
- `data-sort-raw` de la colonne "Prochain palier" utilise maintenant `song.next_cap_value` (numérique)
- Avant : `formatCap(song.next_cap_value)` (texte) → tri alphabétique incorrect ("2,8 B" avant "300 M")
- Après : Valeur numérique brute → tri croissant correct (millions < milliards)

*Rang # figé au rang Kworb :*
- **Suppression** de `updateRankNumbers()` dans table-sort.js
- Suppression de l'appel depuis `sortTable()`
- Commentaire explicatif : "Ne PAS mettre à jour les rangs visuels - ils doivent rester figés au rang Kworb d'origine"
- Résultat : Colonne # conserve le rang d'origine même après tri sur autres colonnes

*Centrage vertical parfait (global.css) :*
- `.data-table td` : Ajout `display: flex; align-items: center; justify-content: center;`
- `.data-table td:nth-child(2)` : Exception avec `justify-content: flex-start;` pour Titre aligné à gauche
- Centrage horizontal (text-align: center) déjà existant depuis Prompt 6.1
- Résultat : Tous les nombres/textes centrés parfaitement verticalement ET horizontalement

*Albums conformes :*
- `margin-bottom: 28px` déjà appliqué sur `.page-header--aggregate` (global)
- Headers dynamiques (data-testid) déjà présents dans index.html
- meta-refresh.js met à jour automatiquement les 3 cards (last sync, next update, spotify date)
- Format entier FR appliqué sur toutes les colonnes streams Albums
- data-sort-raw "Prochain palier" numérique comme Songs

*Résultats validés :*
- **Stats Lead/Feat exactes** : 237 lead (68 403 452 747 total, 34 346 197 daily), 78 feat (16 596 277 670 total, 7 055 853 daily)
- **Lead + Feat = Total** : 237 + 78 = 315 songs, 68,4B + 16,6B = 85,0B streams
- **Nombres entiers FR** : "5 050 786 130" au lieu de "5,1 B", espaces insécables
- **Tri "Prochain palier"** : Ordre croissant correct (100M, 200M, ..., 1B, 2B, ...)
- **Rang # figé** : Tri par Titre/Streams ne modifie pas la colonne #
- **Centrage parfait** : Toutes cellules centrées verticalement et horizontalement (sauf Titre à gauche)
- Dashboard fonctionnel, tri multi-colonnes, formatage cohérent Songs/Albums

*Fichiers modifiés :*
- `scripts/scrape_kworb_songs.py` (extraction stats agrégées, encoding, meta.json)
- `Website/src/formatters.js` (+formatIntFr)
- `Website/src/data-renderer.js` (lecture meta.songs_role_stats, formatIntFr, data-sort-raw numérique)
- `Website/src/table-sort.js` (-updateRankNumbers)
- `Website/src/styles/global.css` (flex centering sur td)

---

**2025-10-02 — Prompt 6.1 : Fix UI (espacements, centrage, tri + flèches, libellés) + Stats Lead/Feat Kworb**

*Ergonomie nettoyée :*
- **Espacements** : marge 28px entre tuiles et tableaux, gaps 1rem/1.25rem entre tuiles
- **Centrage** : toutes les colonnes centrées par défaut, sauf colonne Titre (gauche)
- **Prochain palier** : libellé en minuscules (pas d'uppercase forcé), affiche "Prochain palier"
- **Légende** : note discrète "* = featuring" sous les tables Songs et Albums (classe table-legend)

*Tri cliquable (table-sort.js) :*
- Toutes les colonnes utiles triables : #, Titre, Streams totaux/quotidiens, Variation (%), Prochain cap (j), Prochain palier
- Clic header → alterne ascendant/descendant, flèches ▲/▼ visibles, état actif (couleur accent + fond)
- ARIA : role="columnheader" + aria-sort dynamique (ascending/descending/none)
- Tri alphabétique Titre : ignore * initial (featuring) mais affiche *, utilise Collator FR pour accents
- Tri par défaut : streams_total desc avec indicateur visuel actif
- Intégré dans data-renderer.js : réinitialisation après chaque rendu de table

*Stats Lead/Feat depuis Kworb :*
- Rappel : champ `role` dans `songs.json` reflète déjà la classification Kworb ("lead" / "feat")
- Agrégats Lead/Feat calculés à partir de `role` = agrégats "as lead artist" et "as featured artist" de Kworb
- Solo / Lead = tous les titres avec role="lead" (correspond à "as lead artist" Kworb)
- Feat = tous les titres avec role="feat" (correspond à "as featured artist" Kworb)
- Validation : `lead_count + feat_count = total_count`

*Technique :*
- CSS : .page-header--aggregate margin-bottom 28px, gap 1rem/row-gap 1.25rem, td text-align center (sauf th/td:nth-child(2) left)
- Retrait text-transform uppercase du thead, ajout sur .data-table__header-text pour garder cohérence
- table-sort.js : normalizeTitle() ignore *, compareValues() gère number/title/text, updateHeaderStates() applique .is-sorted
- data-sort-value et data-sort-raw ajoutés sur chaque <td> pour tri stable
- Légende HTML avec classe .table-legend insérée après .table-wrapper

---

**2025-10-02 — Prompt 6 : Connexion UI aux données + Recherche sticky + Formats FR**

*Connexion UI/données :*
- Tables Songs (315 lignes) et Albums (27 lignes) connectées aux fichiers `data/songs.json` et `data/albums.json`
- Auto-refresh des tables : rechargement automatique sans reload page quand `last_sync_local_iso` change
- Cache intelligent avec retry (3 tentatives, backoff exponentiel) via `data-loader.js`
- Gestion erreurs douce : badge d'alerte si erreur fetch, conservation cache, aucune cassure UI

*Agrégats dynamiques :*
- **Songs** : 6 indicateurs (Total titres, Streams totaux, Streams quotidiens + splits Lead/Feat avec counts et sommes)
- **Albums** : 3 indicateurs (Total albums, Streams totaux, Streams quotidiens)
- Validation : `lead_count + feat_count = total_count`
- Formats FR : espaces fines (milliers), virgule décimale, suffixes M/B

*Formats français (formatters.js) :*
- **Nombres** : séparateur milliers (espace fine `\u202F`), virgule décimale (ex: `1 664 001`, `3,52`)
- **Pourcentages** : signe +/- avec 2 décimales (ex: `+3,52 %`, `-1,07 %`) ou `N.D.`
- **Jours** : 2 décimales + suffixe `j` (ex: `23,84 j`) ou `N.D.`
- **Paliers** : M/B avec virgule (ex: `5,1 B`, `300 M`)
- **Streams** : formatage intelligent selon magnitude (B/M/K)

*Recherche sticky (search.js) :*
- Barre recherche en bas (sticky), active depuis n'importe quelle page
- Saisie ≥2 caractères → dropdown 10 résultats max (titre + album)
- Navigation : Enter ou clic → bascule page Songs + scroll vers ligne + highlight 3 secondes
- Normalisation accents, highlight correspondances, navigation clavier (↑↓ Enter Escape)
- Cache partagé avec data-loader

*Architecture modules :*
- `data-loader.js` : fetch avec cache 5s, retry, événements `data-loaded`/`data-load-error`
- `formatters.js` : fonctions formatNumber, formatPercent, formatDays, formatCap, formatStreams
- `data-renderer.js` : calcul stats, rendu tables/agrégats, tri streams_total desc
- `search.js` : recherche sticky avec suggestions dropdown et navigation
- `main.js` : orchestration chargement, auto-refresh, gestion pages
- `meta-refresh.js` : émet événement `data-sync-updated` quand nouvelle sync détectée

*Technique :*
- Serveur HTTP depuis racine projet (accès `/Website/` et `/data/`)
- Base href `/Website/` pour chemins relatifs assets
- data-testid ajoutés : songs-total-count, songs-streams-total/daily, songs-lead/feat-*, albums-*, songs-row, albums-row, search-suggestions
- Colonnes #/Titre collantes (CSS existant), data-row-id sur chaque `<tr>`
- Tri stable par streams_total décroissant

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
  index.html                       # Page principale (SPA avec 3 pages, base href="/Website/")
  src/
    main.js                        # Orchestration chargement, auto-refresh, navigation
    app.js                         # Script JavaScript (navigation entre pages)
    data-loader.js                 # Module chargement JSON (cache, retry, événements)
    data-renderer.js               # Module rendu tables/agrégats (calculs, formatage, DOM)
    formatters.js                  # Module formatage FR (nombres, %, jours, M/B)
    search.js                      # Recherche sticky avec suggestions et navigation
    table-sort.js                  # Système tri cliquable (flèches, ARIA, tri alpha ignore *)
    meta-refresh.js                # Script de mise à jour dynamique des en-têtes (fetch meta.json)
    styles/
      global.css                   # CSS canonique (980 lignes, dark theme, espacements/centrage fixés)
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

## Avertissement sécurité

⚠️ **Ne jamais committer de fichiers contenant des secrets** (.env, tokens, clés API). Utiliser `.gitignore` et stocker les credentials localement uniquement.

---

## Licence

MIT (placeholder — à finaliser ultérieurement).
