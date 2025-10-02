# The Weeknd Dashboard

Dashboard local recensant les streams Spotify de The Weeknd (Songs & Albums) via scraping Kworb. Affichage par pages avec auto-refresh toutes les 10 minutes, snapshots datés (J/J-1/J-2) pour préserver les variations, et intégration Spotify API pour les covers et métadonnées.

---

## Quoi de neuf

**2025-10-02 — Réorganisation finale de l'arborescence**
- Déplacement du README.md à la racine du projet (avant Website/)
- Déplacement de .env.local à la racine du projet
- Réorganisation du CSS : Website/global.css → Website/src/styles/global.css
- Mise à jour de .gitignore : `.env.local` remplace `Website/.env.local` (ligne 7)
- Structure finale : fichiers de config à la racine, code applicatif dans Website/

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
README.md                     # Ce fichier (documentation du projet)
.env.local                    # Secrets Spotify (non tracké, ignoré par Git)
.gitignore                    # Patterns d'exclusion Git
.gitattributes                # Normalisation des fins de ligne
LICENSE                       # Licence (placeholder MIT)
Website/                      # Dossier parent du code applicatif
  data/
    history/
      songs/                  # Snapshots quotidiens des chansons (J, J-1, J-2)
      albums/                 # Snapshots quotidiens des albums (J, J-1, J-2)
  src/
    styles/
      global.css              # CSS canonique (960 lignes)
    .gitkeep                  # Préserve le dossier src/
  scripts/                    # Scripts de scraping et traitement (à venir)
  public/
    styles/                   # Assets CSS additionnels (vide pour l'instant)
  docs/
    roadmap.md                # Feuille de route (à compléter)
    securité-scraping.md      # Règles de sécurité pour le scraping
```

**Note** : Fichiers de configuration et documentation à la racine, code applicatif dans `Website/`. CSS canonique : `Website/src/styles/global.css`.

---

## Comment utiliser / Commandes

*(À compléter lors des prochains prompts)*

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
