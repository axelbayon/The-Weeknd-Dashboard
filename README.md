# The Weeknd Dashboard

Dashboard local recensant les streams Spotify de The Weeknd (Songs & Albums) via scraping Kworb. Affichage par pages avec auto-refresh toutes les 10 minutes, snapshots datés (J/J-1/J-2) pour préserver les variations, et intégration Spotify API pour les covers et métadonnées.

---

## Quoi de neuf

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
data/
  history/
    songs/        # Snapshots quotidiens des chansons (J, J-1, J-2)
    albums/       # Snapshots quotidiens des albums (J, J-1, J-2)
src/              # Code source de l'application (à venir)
scripts/          # Scripts de scraping et traitement (à venir)
Website/
  global.css      # CSS canonique (pour l'instant)
  .env.local      # Secrets Spotify (non tracké, ignoré par Git)
docs/
  roadmap.md              # Feuille de route (à compléter)
  securité-scraping.md    # Règles de sécurité pour le scraping
README.md         # Ce fichier
.gitignore        # Patterns d'exclusion Git
.gitattributes    # Normalisation des fins de ligne
LICENSE           # Licence (placeholder MIT)
```

**Note** : CSS canonique : `Website/global.css` (pour l'instant).

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

## Avertissement sécurité

⚠️ **Ne jamais committer de fichiers contenant des secrets** (.env, tokens, clés API). Utiliser `.gitignore` et stocker les credentials localement uniquement.

---

## Licence

MIT (placeholder — à finaliser ultérieurement).
