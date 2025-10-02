# The Weeknd Dashboard

Dashboard local recensant les streams Spotify de The Weeknd (Songs & Albums) via scraping Kworb. Affichage par pages avec auto-refresh toutes les 10 minutes, snapshots datés (J/J-1/J-2) pour préserver les variations, et intégration Spotify API pour les covers et métadonnées.

---

## Quoi de neuf

**2025-10-02 — Prompt 0.2 : Gestion des secrets Spotify**
- Ajout de `SPOTIFY_REDIRECT_URI` dans `.env.local` (3 clés Spotify complètes)
- Complétion de `.gitignore` : ajout de `*/.env.local` (7 patterns de protection au total)
- Création de la section "Variables d'environnement (Spotify)" dans le README
- Documentation complète : emplacement, clés attendues, avertissements, process d'obtention
- Validation : .env.local ignoré, aucun .env* tracké, 3 clés présentes (valeurs masquées)

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
