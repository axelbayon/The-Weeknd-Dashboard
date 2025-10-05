# Tests Manuels - Prompt 8.7 : Cartes calculées depuis lignes visibles

## Objectif
Vérifier que les cartes d'en-tête (Stats agrégées) se calculent depuis les lignes DOM affichées, et non depuis meta.json/Kworb.

## Tests à effectuer

### T1 : Cohérence des sommes (page Titres)
**Procédure** :
1. Ouvrir `http://localhost:8080`
2. Aller sur page "Titres" (Songs)
3. Ouvrir Console DevTools
4. Vérifier le log : `[Stats] Calcul depuis DOM - Titres visibles: {...}`
5. **Vérifier manuellement** :
   - Nombre total de titres = nombre de lignes dans le tableau
   - Somme des streams totaux cohérente
   - Somme des streams quotidiens cohérente

**Critères de réussite** :
- ✅ Log affiché avec stats calculées
- ✅ Cartes affichent les valeurs (pas de "—")
- ✅ Sommes cohérentes avec les lignes du tableau

---

### T2 : Split Solo/Lead vs Feat correct (page Titres)
**Procédure** :
1. Sur page "Titres"
2. Vérifier visuellement :
   - Titres commençant par `*` = Feat
   - Titres sans `*` = Solo/Lead
3. Compter manuellement quelques lignes
4. Vérifier les cartes split :
   - "Titres en Solo / Lead" → Nombre correct
   - "Titres en featuring" → Nombre correct

**Critères de réussite** :
- ✅ Détection astérisque correcte
- ✅ Sommes Solo + Feat = Total
- ✅ Streams Solo + Streams Feat = Streams Total

---

### T3 : Cohérence des sommes (page Albums)
**Procédure** :
1. Aller sur page "Albums"
2. Ouvrir Console DevTools
3. Vérifier le log : `[Stats] Calcul depuis DOM - Albums visibles: {...}`
4. **Vérifier manuellement** :
   - Nombre total d'albums = nombre de lignes
   - Somme des streams cohérente

**Critères de réussite** :
- ✅ Log affiché avec stats calculées
- ✅ Cartes affichent les valeurs
- ✅ Pas de split (Albums n'ont pas Solo/Feat)

---

### T4 : Le tri ne recalcule PAS les agrégats
**Procédure** :
1. Sur page "Titres"
2. Noter les valeurs des cartes
3. Cliquer sur en-tête de colonne pour trier (ex: "Titre")
4. Vérifier Console : pas de nouveau log `[Stats] Calcul depuis DOM`
5. Vérifier que les cartes n'ont PAS changé

**Critères de réussite** :
- ✅ Pas de log de recalcul après tri
- ✅ Valeurs des cartes identiques avant/après tri

---

### T5 : Recalcul après refresh auto
**Procédure** :
1. Attendre le prochain refresh automatique (badge "Prochaine mise à jour" à 00:00)
2. OU déclencher manuellement en modifiant `data/meta.json` (changer `last_sync_local_iso`)
3. Observer Console : événement `data-sync-updated`
4. Vérifier nouveau log : `[Stats] Calcul depuis DOM`
5. Vérifier que les cartes sont recalculées

**Critères de réussite** :
- ✅ Événement détecté
- ✅ Log de recalcul affiché
- ✅ Cartes mises à jour

---

### T6 : Recalcul après changement de page
**Procédure** :
1. Sur page "Titres"
2. Cliquer sur "Albums"
3. Vérifier log : `[Stats] Calcul depuis DOM - Albums visibles`
4. Retour sur "Titres"
5. Vérifier log : `[Stats] Calcul depuis DOM - Titres visibles`

**Critères de réussite** :
- ✅ Log affiché à chaque changement de page
- ✅ Cartes correctes pour chaque page

---

### T7 : Résilience (valeurs nulles/invalides)
**Procédure** :
1. Vérifier Console : pas d'erreurs JavaScript
2. Vérifier que `parseStreamValue()` gère :
   - Valeurs nulles → 0
   - "—" ou "-" → 0
   - Espaces dans les nombres → parsing correct

**Critères de réussite** :
- ✅ Aucune erreur `NaN` ou `undefined` dans les cartes
- ✅ Pas d'erreur dans la console

---

## Checklist finale
- [ ] T1 : Cohérence sommes Titres
- [ ] T2 : Split Feat/Solo correct
- [ ] T3 : Cohérence sommes Albums
- [ ] T4 : Tri ne recalcule pas
- [ ] T5 : Refresh auto recalcule
- [ ] T6 : Changement page recalcule
- [ ] T7 : Résilience valeurs invalides

## Notes
- Les valeurs peuvent différer légèrement de Kworb si le tableau est trié différemment
- Le calcul DOM est **la source de vérité** maintenant (pas meta.json)
- Si une ligne est cachée (display:none), elle ne sera pas comptée (offsetParent === null)
