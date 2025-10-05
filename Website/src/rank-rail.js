/**
 * Module de gestion du rail de badges de mouvement de rang
 * Utilise un système robuste de rebuild avec MutationObserver + événements custom
 */

class RankRail {
    constructor() {
        this.rail = null;
        this.section = null;
        this.wrapper = null;
        this.tbody = null;
        this.observer = null;
        this.badgesData = [];
        this.rebuildTimeout = null;
    }

    /**
     * Monte le rail dans une section de table
     * @param {string} sectionSelector - Sélecteur de la .table-section
     */
    mount(sectionSelector) {
        this.section = document.querySelector(sectionSelector);
        
        if (!this.section) {
            console.warn(`⚠️ [RankRail] Section introuvable: ${sectionSelector}`);
            return;
        }

        this.wrapper = this.section.querySelector('.table-wrapper');
        this.tbody = this.section.querySelector('tbody');

        if (!this.wrapper || !this.tbody) {
            console.warn('⚠️ [RankRail] Wrapper ou tbody introuvable');
            return;
        }

        // Créer le rail s'il n'existe pas
        this.rail = this.section.querySelector('.rank-rail');
        if (!this.rail) {
            this.rail = document.createElement('div');
            this.rail.className = 'rank-rail';
            this.rail.setAttribute('aria-hidden', 'true');
            this.section.style.position = 'relative';
            this.section.appendChild(this.rail);
        }

        console.log(`✅ [RankRail] Monté sur ${sectionSelector}`);
    }

    /**
     * Attache les écoutes d'événements
     */
    bind() {
        if (!this.wrapper || !this.tbody) {
            console.warn('⚠️ [RankRail] Impossible de bind: wrapper/tbody manquant');
            return;
        }

        // Écouter l'événement custom table:rows-updated
        this.wrapper.addEventListener('table:rows-updated', () => {
            console.log('📡 [RankRail] Event table:rows-updated reçu');
            this.debouncedRebuild();
        });

        // Écouter le scroll vertical (wrapper peut scroller)
        this.wrapper.addEventListener('scroll', () => {
            this.debouncedRebuild(50);
        });

        // MutationObserver sur tbody (filet de sécurité)
        this.observer = new MutationObserver(() => {
            console.log('👀 [RankRail] Mutation détectée sur tbody');
            this.debouncedRebuild(100);
        });

        this.observer.observe(this.tbody, {
            childList: true,
            subtree: false,
            attributes: true,
            attributeFilter: ['style'] // Détecter si lignes masquées/affichées
        });

        console.log('✅ [RankRail] Événements bindés (custom event + observer)');
    }

    /**
     * Rebuild avec debounce
     * @param {number} delay - Délai en ms (par défaut 50ms)
     */
    debouncedRebuild(delay = 50) {
        clearTimeout(this.rebuildTimeout);
        this.rebuildTimeout = setTimeout(() => {
            // Prompt 8.8: récupérer meta depuis dataLoader pour validation date
            const meta = window.dataLoader?.cache?.meta;
            this.rebuild(this.badgesData, meta);
        }, delay);
    }

    /**
     * Reconstruit tous les badges selon l'ordre actuel du DOM
     * Prompt 8.8: Valide delta_for_date avant affichage badge
     * @param {Array} items - Données avec id, rank_delta, rank_prev, delta_for_date
     * @param {Object} meta - Metadata avec spotify_data_date pour validation
     */
    rebuild(items, meta = null) {
        if (!this.rail || !this.wrapper || !items) {
            return;
        }

        // Sauvegarder les données pour les futurs rebuilds
        this.badgesData = items;

        // Vider le rail
        this.rail.innerHTML = '';

        // Calculer offset du wrapper dans la section
        const wrapperTop = this.wrapper.offsetTop;

        let badgeCount = 0;

        // Pour chaque item avec mouvement de rang
        items.forEach(item => {
            // Prompt 8.8: Valider que le delta est bien pour le jour courant
            if (meta?.spotify_data_date && item.delta_for_date) {
                if (item.delta_for_date !== meta.spotify_data_date) {
                    // Badge périmé : delta calculé pour un jour différent
                    return;
                }
            }
            
            if (!item.rank_delta || item.rank_delta === 0) return;

            // Trouver la ligne correspondante dans le DOM actuel
            const tr = this.tbody.querySelector(`tr[data-row-id="${item.id}"]`);
            
            if (!tr) return;

            // Vérifier si la ligne est visible (pas masquée par filtre)
            if (tr.offsetParent === null) {
                // Ligne masquée (display: none ou visibility: hidden)
                return;
            }

            // Mesurer position de la ligne
            const top = tr.offsetTop;
            const height = tr.offsetHeight;
            const centerY = wrapperTop + top + (height / 2);

            // Créer le badge
            const badge = document.createElement('span');
            badge.className = `rank-badge ${item.rank_delta > 0 ? 'is-up' : 'is-down'}`;
            badge.style.top = `${centerY}px`;
            
            const arrow = item.rank_delta > 0 ? '▲' : '▼';
            const deltaAbs = Math.abs(item.rank_delta);
            badge.innerHTML = `<span class="rank-badge__arrow">${arrow}</span> ${deltaAbs}`;

            this.rail.appendChild(badge);
            badgeCount++;
        });

        console.log(`✅ [RankRail] Rebuild terminé: ${badgeCount} badges positionnés`);
    }

    /**
     * Démonte le rail et nettoie les écoutes
     */
    unmount() {
        if (this.observer) {
            this.observer.disconnect();
            this.observer = null;
        }

        if (this.rail && this.rail.parentNode) {
            this.rail.parentNode.removeChild(this.rail);
        }

        clearTimeout(this.rebuildTimeout);

        this.rail = null;
        this.section = null;
        this.wrapper = null;
        this.tbody = null;
        this.badgesData = [];

        console.log('✅ [RankRail] Démonté');
    }
}

// Instances pour Songs et Albums
const rankRailSongs = new RankRail();
const rankRailAlbums = new RankRail();

window.rankRailSongs = rankRailSongs;
window.rankRailAlbums = rankRailAlbums;

// Export pour utilisation dans data-renderer.js
window.RankRail = RankRail;
