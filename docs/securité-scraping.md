# Règles de sécurité et respect pour le scraping

Ce document liste les bonnes pratiques à appliquer lors du scraping de Kworb.

## Règles à respecter

- **Throttle / Rate limiting** : espacer les requêtes (ex. 1–2 secondes minimum entre chaque appel) pour ne pas surcharger le serveur.
- **User-Agent explicite** : déclarer un User-Agent identifiable (nom du projet + email de contact) pour permettre au site de nous contacter en cas de problème.
- **Retry avec backoff exponentiel** : en cas d'erreur 429 (Too Many Requests) ou 5xx, attendre progressivement plus longtemps avant de réessayer.
- **Respect des heures creuses** : privilégier les heures de faible trafic (nuit/tôt le matin en heure locale du serveur) si possible.
- **Vérification robots.txt** : consulter `/robots.txt` du site pour vérifier qu'il n'y a pas de restriction explicite (même si Kworb n'en a généralement pas).
- **Cache local** : stocker les données scrapées localement (snapshots J/J-1/J-2) pour limiter le nombre de requêtes répétées.
- **Monitoring des erreurs** : logger les erreurs HTTP pour détecter tout blocage ou changement de structure du site.
- **Durée de timeout raisonnable** : définir un timeout (ex. 10–15 secondes) pour éviter de bloquer indéfiniment en cas de non-réponse.

---

Ces règles garantissent un scraping éthique et pérenne.
