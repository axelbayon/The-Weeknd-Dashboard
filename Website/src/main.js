/**
 * Script principal - Orchestration du chargement et de l'auto-refresh
 */

(function() {
    'use strict';

    let isInitialized = false;
    let currentPage = 'songs';

    /**
     * Initialise l'application
     */
    async function init() {
        if (isInitialized) return;
        
        console.log('🚀 Initialisation du dashboard...');

        try {
            // Charger les données initiales pour la page Songs
            await window.dataRenderer.initCurrentPage('songs');
            
            isInitialized = true;
            console.log('✅ Dashboard initialisé');
        } catch (error) {
            console.error('❌ Erreur initialisation:', error);
            showLoadError();
        }

        // Écouter les changements de page
        setupPageNavigation();

        // Écouter les mises à jour de synchro
        setupAutoRefresh();
    }

    /**
     * Configure la navigation entre pages
     */
    function setupPageNavigation() {
        const navLinks = document.querySelectorAll('[data-page]');
        
        navLinks.forEach(link => {
            link.addEventListener('click', async (e) => {
                e.preventDefault();
                const pageName = link.getAttribute('data-page');
                await switchPage(pageName);
            });
        });
    }

    /**
     * Bascule vers une autre page
     */
    async function switchPage(pageName) {
        if (currentPage === pageName) return;

        console.log(`📄 Basculement vers page: ${pageName}`);

        // Mettre à jour les liens actifs
        const navLinks = document.querySelectorAll('[data-page]');
        navLinks.forEach(link => {
            if (link.getAttribute('data-page') === pageName) {
                link.classList.add('topbar__link--active');
            } else {
                link.classList.remove('topbar__link--active');
            }
        });

        // Cacher toutes les pages
        const pages = document.querySelectorAll('[data-page-content]');
        pages.forEach(page => {
            page.style.display = 'none';
        });

        // Afficher la page sélectionnée
        const targetPage = document.querySelector(`[data-page-content="${pageName}"]`);
        if (targetPage) {
            targetPage.style.display = 'block';
        }

        currentPage = pageName;
        window.dataRenderer.currentPage = pageName;

        // Charger les données si nécessaire
        if (pageName === 'songs' || pageName === 'albums') {
            try {
                await window.dataRenderer.initCurrentPage(pageName);
            } catch (error) {
                console.error(`❌ Erreur chargement page ${pageName}:`, error);
            }
        }
    }

    /**
     * Configure l'auto-refresh des données
     */
    function setupAutoRefresh() {
        // Écouter l'événement de nouvelle synchro émis par meta-refresh.js
        window.addEventListener('data-sync-updated', async (e) => {
            console.log('🔄 Nouvelle synchro détectée, rechargement des données...');
            console.log('Détails:', e.detail);

            try {
                // Invalider le cache
                window.dataLoader.invalidateCache();
                window.stickySearch.invalidateCache();

                // Recharger la page courante
                await window.dataRenderer.refreshCurrentPage();

                console.log('✅ Données rechargées');
                showRefreshNotification();
            } catch (error) {
                console.error('❌ Erreur rechargement données:', error);
                showRefreshError();
            }
        });

        // Écouter les événements de chargement/erreur
        window.addEventListener('data-loaded', (e) => {
            console.log(`📦 Données chargées: ${e.detail.type}`);
        });

        window.addEventListener('data-load-error', (e) => {
            console.error(`❌ Erreur chargement: ${e.detail.type}`, e.detail.error);
            showLoadError(e.detail.type);
        });
    }

    /**
     * Affiche une notification de rechargement réussi
     */
    function showRefreshNotification() {
        // Notification légère (optionnel)
        console.log('ℹ️ Données mises à jour');
        
        // TODO: Ajouter une notification visuelle discrète si souhaité
    }

    /**
     * Affiche une erreur de rechargement
     */
    function showRefreshError() {
        console.error('⚠️ Erreur lors du rechargement automatique');
        
        // TODO: Ajouter une notification d'erreur visuelle si souhaité
    }

    /**
     * Affiche une erreur de chargement
     */
    function showLoadError(context = 'général') {
        console.error(`⚠️ Erreur de chargement: ${context}`);
        
        // Afficher un message d'erreur léger dans l'UI
        const errorBadge = document.createElement('div');
        errorBadge.className = 'load-error-badge';
        errorBadge.textContent = `⚠️ Erreur de chargement (${context})`;
        errorBadge.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            background: rgba(244, 67, 54, 0.95);
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            z-index: 9999;
            font-size: 14px;
            animation: slideIn 0.3s ease-out;
        `;

        // Supprimer les anciens badges
        document.querySelectorAll('.load-error-badge').forEach(el => el.remove());

        document.body.appendChild(errorBadge);

        // Auto-suppression après 5 secondes
        setTimeout(() => {
            errorBadge.style.opacity = '0';
            errorBadge.style.transition = 'opacity 0.3s';
            setTimeout(() => errorBadge.remove(), 300);
        }, 5000);
    }

    // Démarrer quand le DOM est prêt
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
