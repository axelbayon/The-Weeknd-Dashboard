# The Weeknd Dashboard

Dashboard local recensant les streams Spotify de The Weeknd (Songs & Albums) via scraping Kworb. Affichage par pages avec auto-refresh toutes les 10 minutes, snapshots datés (J/J-1/J-2) pour préserver les variations, et intégration Spotify API pour les covers et métadonnées.

---

## Quoi de neuf

**2025-10-02 — Restructuration (Website parent)**
- Restructuration complète : `Website/` devient le dossier parent du projet
- Déplacement de tous les dossiers (data/, src/, public/, scripts/, docs/) dans Website/
- Déplacement du README.md vers Website/README.md
- Conservation de `Website/global.css` comme CSS unique (960 lignes)
- `Website/.env.local` confirmé ignoré par Git (ligne 7 de .gitignore)

**2025-10-02 — Prompt 0.1-fix**
- Harmonisation CSS : conservation de `Website/global.css` comme référence unique
- Suppression du doublon `public/styles/global.css`
- Renforcement de `.gitignore` pour les secrets (patterns `.env*`, `*/.env*`, `Website/.env.local`)
- Clarification de la structure du projet

**2025-10-02 — Prompt 0.1**
- Création de l'arborescence initiale du projet
- Ajout de la documentation de base (README, sécurité-scraping, roadmap placeholder)
- Configuration Git (.gitignore, .gitattributes, LICENSE placeholder)
- Préparation des dossiers de snapshots (data/history/songs/ et albums/)

---

## Structure du repo

```
Website/                      # Dossier parent du projet
  data/
    history/
      songs/                  # Snapshots quotidiens des chansons (J, J-1, J-2)
      albums/                 # Snapshots quotidiens des albums (J, J-1, J-2)
  src/                        # Code source de l'application (à venir)
  scripts/                    # Scripts de scraping et traitement (à venir)
  public/
    styles/                   # Assets CSS (vide pour l'instant)
  docs/
    roadmap.md                # Feuille de route (à compléter)
    securité-scraping.md      # Règles de sécurité pour le scraping
  global.css                  # CSS canonique (960 lignes)
  .env.local                  # Secrets Spotify (non tracké, ignoré par Git)
  README.md                   # Ce fichier
.gitignore                    # Patterns d'exclusion Git
.gitattributes                # Normalisation des fins de ligne
LICENSE                       # Licence (placeholder MIT)
```

**Note** : `Website/` est le dossier racine du projet. CSS canonique : `Website/global.css`.

---

## Comment utiliser / Commandes

*(À compléter lors des prochains prompts)*

---

## Variables d'environnement

Les secrets (ex. clés Spotify API) doivent être stockés dans le fichier `Website/.env.local` **jamais commité**.

Exemple :
```
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
```

Le fichier `.env.local` est explicitement ignoré par Git (voir `.gitignore`).

---

## Règles de collaboration

- **Conventional Commits** : chaque commit suit le format `type(scope): message` (feat, fix, docs, chore, refactor, perf, test, build, ci, style).
- **Cycle de travail** : tests → mise à jour README → commit/push à chaque prompt.
- **Sécurité** : ne jamais committer de secrets, tokens ou clés API.

---

## Limites connues

- Projet en phase d'initialisation : aucune logique applicative implémentée pour l'instant.
- Stack technique non définie (à venir dans les prochains prompts).

---

## Tests de validation

### Test 1 - Arborescence complète
**Commande** : `Get-ChildItem -Recurse -Depth 4`  
**Objectif** : Vérifier que tous les dossiers (data/, src/, public/, scripts/, docs/) sont bien dans Website/ et qu'il n'y a plus de dossiers à la racine (sauf .git/, LICENSE, .gitignore, .gitattributes, Website/).

### Test 2 - Unicité du CSS
**Commande** : `Get-ChildItem -Filter "global.css" -Recurse`  
**Objectif** : Confirmer qu'un seul fichier global.css existe dans le projet (Website/global.css).

### Test 3 - Protection des secrets
**Commande** : `git check-ignore -v Website/.env.local`  
**Objectif** : Prouver que Website/.env.local est bien ignoré par Git (ligne 7 de .gitignore).

### Test 4 - README racine supprimé
**Commande** : `Test-Path README.md`  
**Objectif** : Confirmer que README.md n'existe plus à la racine du projet.

### Test 5 - README dans Website
**Commande** : `Test-Path Website/README.md`  
**Objectif** : Confirmer que README.md est bien déplacé dans Website/.

### Test 6 - Intégrité du CSS
**Commande** : `Measure-Object -Line Website/global.css`  
**Objectif** : Vérifier que le CSS n'a pas été tronqué lors du déplacement (960 lignes attendues).

### Test 7 - État Git propre
**Commande** : `git status --short`  
**Objectif** : Confirmer les renames détectés (R) et l'absence de fichiers .env* dans les changements.

---

## Avertissement sécurité

⚠️ **Ne jamais committer de fichiers contenant des secrets** (.env, tokens, clés API). Utiliser `.gitignore` et stocker les credentials localement uniquement.

---

## Licence

MIT (placeholder — à finaliser ultérieurement).
