# Pipeline optimisé - Session 3
## Nettoyage des étapes redondantes + descriptions détaillées

**Date** : 2025-10-06  
**Objectif** : Simplifier le pipeline et ajouter des descriptions claires pour chaque étape

---

## Analyse du pipeline

### ❌ Problèmes identifiés

#### 1. Étape 3 "GÉNÉRATION VUES COURANTES" - REDONDANTE

**Constat** :
```python
# Dans scrape_kworb_songs.py (ligne 460)
def main():
    songs, last_update_kworb, role_stats = scrape_kworb_songs(KWORB_SONGS_URL)
    create_snapshot(songs, last_update_kworb, base_path)
    update_meta(spotify_data_date, last_update_kworb, role_stats, base_path)
    regenerate_current_view(base_path)  # ← Régénère songs.json ICI
```

**Problème** :
- Les scrapers appellent déjà `regenerate_current_view()` 
- L'étape 3 du pipeline ne fait que afficher un message mais n'exécute rien
- Confusion : on laisse croire qu'il y a une étape séparée alors que c'est déjà fait

**Solution** : ✅ **SUPPRIMÉE** - Pas besoin d'étape dédiée

---

#### 2. Étape 5 "ROTATION SNAPSHOTS" - REDONDANTE

**Constat** :
```python
# Dans scrape_kworb_songs.py (ligne 335)
from date_manager import (
    rotate_snapshots_atomic,
    update_meta_with_rotation,
    should_rotate
)

# La rotation est gérée automatiquement lors du scraping
if should_rotate(spotify_data_date, meta_kworb_day):
    rotate_snapshots_atomic(...)  # ← Rotation déjà gérée ICI
```

**Problème** :
- Les scrapers gèrent déjà la rotation via `date_manager.py`
- La rotation se fait automatiquement quand `kworb_day` change
- L'étape 5 du pipeline ne fait qu'afficher un message informatif

**Solution** : ✅ **TRANSFORMÉE EN INFO** - Juste un message explicatif, pas d'exécution

---

## Nouveau pipeline (3 étapes au lieu de 5)

### Avant (5 étapes)

```
[1/5] 📊 SCRAPING SONGS
[2/5] 💿 SCRAPING ALBUMS
[3/5] 📁 GÉNÉRATION VUES COURANTES  ← REDONDANT (déjà fait en 1 et 2)
[4/5] 🎨 ENRICHISSEMENT SPOTIFY
[5/5] 🔄 ROTATION SNAPSHOTS         ← REDONDANT (déjà fait en 1 et 2)
```

### Après (3 étapes + info)

```
[1/3] 📊 SCRAPING SONGS
      • Récupère données depuis Kworb
      • Crée snapshot journalier (data/history/songs/YYYY-MM-DD.json)
      • Régénère data/songs.json avec calculs (delta, badges)

[2/3] 💿 SCRAPING ALBUMS
      • Récupère données depuis Kworb
      • Crée snapshot journalier (data/history/albums/YYYY-MM-DD.json)
      • Régénère data/albums.json avec calculs (delta, badges)

[3/3] 🎨 ENRICHISSEMENT SPOTIFY
      • Lit songs.json et albums.json
      • Recherche tracks/albums manquants sur Spotify API
      • Ajoute cover_url + album_name dans les fichiers JSON
      • Incrémente covers_revision dans meta.json

🔄 ROTATION SNAPSHOTS
   Gérée automatiquement par les scrapers via date_manager.py
   • Maintient 3 jours : J (aujourd'hui), J-1, J-2
   • Rotation basée sur kworb_day (changement UTC 00:00)
```

---

## Changements effectués

### 1. `scripts/auto_refresh.py`

**Fonction `run_pipeline()`** :

**Modifications** :
- **5 étapes → 3 étapes** (suppression étapes 3 et 5 redondantes)
- **Ajout descriptions détaillées** sous chaque titre d'étape
- **Étape rotation** transformée en bloc informatif (pas d'exécution)
- **Docstring** mise à jour avec pipeline simplifié

**Exemple avant/après** :

```python
# AVANT
print("│ [1/5] 📊 SCRAPING SONGS                                         │")
print("│ ✅ Songs scraped avec succès")

# APRÈS
print("│ [1/3] 📊 SCRAPING SONGS                                         │")
print("│                                                                 │")
print("│ • Récupère données depuis Kworb                                 │")
print("│ • Crée snapshot journalier (data/history/songs/YYYY-MM-DD.json)│")
print("│ • Régénère data/songs.json avec calculs (delta, badges)        │")
print("│ ✅ Songs scraped avec succès")
```

---

### 2. `scripts/start_dashboard.py`

**Message de démarrage** :

**Modifications** :
- **Liste numérotée** avec emojis (1️⃣ 2️⃣ 3️⃣)
- **Détails pour chaque étape** (ce qu'elle fait concrètement)
- **Rotation** marquée comme automatique avec emoji 🔄

**Exemple avant/après** :

```
# AVANT
│ L'orchestrateur gère automatiquement :
│   • Scraping Kworb (Songs + Albums)
│   • Génération vues courantes (songs.json, albums.json)
│   • Enrichissement Spotify (covers + métadonnées)
│   • Rotation snapshots historiques (J, J-1, J-2)
│   • Mise à jour meta.json (dates, stats, covers_revision)

# APRÈS
│ Pipeline d'actualisation (toutes les 5 minutes) :
│
│   1️⃣  SCRAPING SONGS
│      → Récupère données Kworb
│      → Crée snapshot journalier
│      → Régénère songs.json (calculs delta, badges)
│
│   2️⃣  SCRAPING ALBUMS
│      → Récupère données Kworb
│      → Crée snapshot journalier
│      → Régénère albums.json (calculs delta, badges)
│
│   3️⃣  ENRICHISSEMENT SPOTIFY
│      → Ajoute covers dans songs.json et albums.json
│      → Incrémente covers_revision
│
│   🔄 ROTATION SNAPSHOTS (automatique)
│      → Maintient 3 jours : J, J-1, J-2
```

---

## Comparaison console

### AVANT (confus)

```
═══════════════════════════════════════════════════════════════════════
                        🔄 CYCLE #1 — 23:59:17
═══════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────┐
│ [1/5] 📊 SCRAPING SONGS                                         │
└─────────────────────────────────────────────────────────────────┘
│ ✅ Songs scraped avec succès

┌─────────────────────────────────────────────────────────────────┐
│ [2/5] 💿 SCRAPING ALBUMS                                        │
└─────────────────────────────────────────────────────────────────┘
│ ✅ Albums scraped avec succès

┌─────────────────────────────────────────────────────────────────┐
│ [3/5] 📁 GÉNÉRATION VUES COURANTES                              │  ← REDONDANT
└─────────────────────────────────────────────────────────────────┘
│ ✅ data/songs.json et data/albums.json régénérés                   (déjà fait!)

┌─────────────────────────────────────────────────────────────────┐
│ [4/5] 🎨 ENRICHISSEMENT SPOTIFY                                 │
└─────────────────────────────────────────────────────────────────┘
│ ✅ Covers enrichies avec succès

┌─────────────────────────────────────────────────────────────────┐
│ [5/5] 🔄 ROTATION SNAPSHOTS                                     │  ← REDONDANT
└─────────────────────────────────────────────────────────────────┘
│ ✅ Rotation automatique basée sur kworb_day                        (déjà fait!)
```

---

### APRÈS (clair et concis)

```
═══════════════════════════════════════════════════════════════════════
                        🔄 CYCLE #1 — 00:15:32
═══════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────┐
│ [1/3] 📊 SCRAPING SONGS                                         │
│                                                                 │
│ • Récupère données depuis Kworb                                 │
│ • Crée snapshot journalier (data/history/songs/YYYY-MM-DD.json)│
│ • Régénère data/songs.json avec calculs (delta, badges)        │
└─────────────────────────────────────────────────────────────────┘
│ ✅ Songs scraped avec succès

┌─────────────────────────────────────────────────────────────────┐
│ [2/3] 💿 SCRAPING ALBUMS                                        │
│                                                                 │
│ • Récupère données depuis Kworb                                 │
│ • Crée snapshot journalier (data/history/albums/YYYY-MM-DD.json│
│ • Régénère data/albums.json avec calculs (delta, badges)       │
└─────────────────────────────────────────────────────────────────┘
│ ✅ Albums scraped avec succès

┌─────────────────────────────────────────────────────────────────┐
│ [3/3] 🎨 ENRICHISSEMENT SPOTIFY                                 │
│                                                                 │
│ • Lit songs.json et albums.json                                 │
│ • Recherche tracks/albums manquants sur Spotify API             │
│ • Ajoute cover_url + album_name dans les fichiers JSON         │
│ • Incrémente covers_revision dans meta.json                     │
└─────────────────────────────────────────────────────────────────┘
│ ✅ Covers enrichies avec succès

┌─────────────────────────────────────────────────────────────────┐
│ 🔄 ROTATION SNAPSHOTS                                           │
│                                                                 │
│ Gérée automatiquement par les scrapers via date_manager.py     │
│ • Maintient 3 jours : J (aujourd'hui), J-1, J-2                │
│ • Rotation basée sur kworb_day (changement UTC 00:00)          │
└─────────────────────────────────────────────────────────────────┘
│ ✅ Rotation automatique active
```

---

## Avantages du nouveau pipeline

| Aspect | Avant | Après |
|--------|-------|-------|
| **Nombre d'étapes** | 5 étapes | 3 étapes + 1 info |
| **Clarté** | ❌ 2 étapes redondantes | ✅ Toutes utiles |
| **Descriptions** | ❌ Titres seuls | ✅ Détails sous chaque étape |
| **Traçabilité** | 🟡 Confusion (qu'est-ce qui fait quoi?) | ✅ Clair (chaque tâche expliquée) |
| **Maintenance** | ❌ Doit synchroniser avec scrapers | ✅ Reflète la réalité du code |

---

## Tests de validation

### ✅ Test 1 : Vérifier pipeline 3 étapes
```powershell
python scripts/auto_refresh.py --once
```
**Attendu** :
- Header "[1/3] 📊 SCRAPING SONGS" avec 3 lignes de description
- Header "[2/3] 💿 SCRAPING ALBUMS" avec 3 lignes de description
- Header "[3/3] 🎨 ENRICHISSEMENT SPOTIFY" avec 4 lignes de description
- Bloc "🔄 ROTATION SNAPSHOTS" avec 3 lignes d'info (pas d'exécution)

### ✅ Test 2 : Vérifier message démarrage
```powershell
python scripts/start_dashboard.py
```
**Attendu** :
- Liste avec 1️⃣ 2️⃣ 3️⃣ 🔄
- Sous-tâches avec flèches →
- Message "(automatique)" pour rotation

### ✅ Test 3 : Vérifier fonctionnement
**Attendu** :
- data/songs.json et data/albums.json mis à jour après cycle
- Covers présentes dans les JSON
- Snapshots J, J-1, J-2 maintenus dans data/history/

---

## Commit recommandé

```bash
git add scripts/auto_refresh.py
git add scripts/start_dashboard.py

git commit -m "refactor(pipeline): simplification 5→3 étapes + descriptions détaillées

- Supprimé étape 3 'GÉNÉRATION VUES' (redondante avec scrapers)
- Transformé étape 5 'ROTATION' en bloc informatif (déjà gérée)
- Ajout descriptions détaillées sous chaque étape du pipeline
- Message démarrage restructuré avec 1️⃣ 2️⃣ 3️⃣ et sous-tâches
- Pipeline plus clair : 3 étapes actives + 1 info rotation

Impact: +Clarté +Maintenance -Redondance"
```

---

**Statut** : ✅ Pipeline optimisé et documenté  
**Étapes actives** : 3 (au lieu de 5)  
**Gain clarté** : Descriptions détaillées pour chaque tâche  
**Gain maintenance** : Reflète la réalité du code (plus de fausses étapes)
