/**
 * Meta Refresh - Mise à jour dynamique des en-têtes du dashboard
 * Fetch périodique de data/meta.json pour mettre à jour :
 * - Dernière synchronisation locale
 * - Date des données Spotify  
 * - Compte à rebours jusqu'au prochain refresh (10 minutes)
 */

(function() {
    'use strict';
    
    // Configuration
    const FETCH_INTERVAL_MS = 10000; // 10 secondes
    const REFRESH_INTERVAL_S = 600; // 10 minutes (par défaut)
    const META_JSON_PATH = '/data/meta.json';
    
    // État
    let lastSyncTimestamp = null;
    let nextUpdateTime = null;
    let countdownInterval = null;
    let previousSyncTimestamp = null; // Pour détecter les changements
    
    /**
     * Formate un timestamp ISO en format lisible court
     * Ex: "2025-10-02 17:14:23"
     */
    function formatTimestamp(isoString) {
        try {
            const date = new Date(isoString);
            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const day = String(date.getDate()).padStart(2, '0');
            const hours = String(date.getHours()).padStart(2, '0');
            const minutes = String(date.getMinutes()).padStart(2, '0');
            const seconds = String(date.getSeconds()).padStart(2, '0');
            return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
        } catch (e) {
            return isoString;
        }
    }
    
    /**
     * Formate une date YYYY-MM-DD en format lisible
     * Ex: "01/10/2025"
     */
    function formatDate(dateString) {
        try {
            const [year, month, day] = dateString.split('-');
            return `${day}/${month}/${year}`;
        } catch (e) {
            return dateString;
        }
    }
    
    /**
     * Formate un compte à rebours en MM:SS
     */
    function formatCountdown(seconds) {
        if (seconds <= 0) return "00:00";
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    }
    
    /**
     * Met à jour un élément du DOM si il existe
     * Cherche .stat-card__value à l'intérieur du data-testid
     * Mise à jour de TOUS les éléments ayant ce testid (Songs + Albums)
     */
    function updateElement(testId, content) {
        const cards = document.querySelectorAll(`[data-testid="${testId}"]`);
        cards.forEach(card => {
            const valueEl = card.querySelector('.stat-card__value');
            if (valueEl) {
                valueEl.textContent = content;
            }
        });
    }
    
    /**
     * Calcule et met à jour le compte à rebours avec badge (format MM:SS)
     */
    function updateCountdown() {
        if (!nextUpdateTime) return;
        
        const now = Date.now();
        const remainingMs = nextUpdateTime - now;
        const remainingS = Math.max(0, Math.floor(remainingMs / 1000));
        
        // Trouver tous les badges (Songs et Albums)
        const badges = document.querySelectorAll('.nu-badge');
        
        badges.forEach(badge => {
            if (remainingS <= 0) {
                badge.textContent = 'Prête';
                badge.classList.remove('is-wait');
                badge.classList.add('is-ready');
            } else {
                badge.textContent = formatCountdown(remainingS); // MM:SS
                badge.classList.remove('is-ready');
                badge.classList.add('is-wait');
            }
        });
        
        // Si le compte à rebours atteint 0, recharger les métadonnées
        if (remainingS === 0) {
            console.log('[Meta-Refresh] Countdown reached 0, fetching meta...');
            fetchMeta();
        }
    }
    
    /**
     * Démarre le compte à rebours client-side
     */
    function startCountdown() {
        // Nettoyer l'ancien interval si existant
        if (countdownInterval) {
            clearInterval(countdownInterval);
        }
        
        // Démarrer nouveau compte à rebours (update chaque seconde)
        countdownInterval = setInterval(updateCountdown, 1000);
        updateCountdown(); // Update immédiat
    }
    
    /**
     * Fetch meta.json et met à jour le DOM
     */
    async function fetchMeta() {
        try {
            const response = await fetch(META_JSON_PATH + '?t=' + Date.now());
            
            if (!response.ok) {
                console.warn('[Meta-Refresh] Failed to fetch meta.json:', response.status);
                return;
            }
            
            const meta = await response.json();
            
            // Mettre à jour les en-têtes
            if (meta.last_sync_local_iso) {
                updateElement('header-last-sync', formatTimestamp(meta.last_sync_local_iso));
                
                // Détecter changement de sync et émettre événement
                if (previousSyncTimestamp && previousSyncTimestamp !== meta.last_sync_local_iso) {
                    console.log('[Meta-Refresh] 🔄 Nouvelle synchronisation détectée');
                    const event = new CustomEvent('data-sync-updated', {
                        detail: {
                            previousSync: previousSyncTimestamp,
                            currentSync: meta.last_sync_local_iso,
                            timestamp: Date.now()
                        }
                    });
                    window.dispatchEvent(event);
                }
                
                previousSyncTimestamp = meta.last_sync_local_iso;
                
                // Calculer le prochain refresh
                const lastSync = new Date(meta.last_sync_local_iso);
                nextUpdateTime = lastSync.getTime() + (REFRESH_INTERVAL_S * 1000);
                startCountdown();
            }
            
            if (meta.spotify_data_date) {
                updateElement('header-spotify-data-date', formatDate(meta.spotify_data_date));
                
                // Mettre à jour les dates entre parenthèses dans les cartes "Streams quotidiens"
                const dailyStreamsDateSongs = document.querySelector('[data-testid="daily-streams-date"]');
                const dailyStreamsDateAlbums = document.querySelector('[data-testid="daily-streams-date-albums"]');
                const formattedDate = formatDate(meta.spotify_data_date);
                
                if (dailyStreamsDateSongs) {
                    dailyStreamsDateSongs.textContent = `(${formattedDate})`;
                }
                if (dailyStreamsDateAlbums) {
                    dailyStreamsDateAlbums.textContent = `(${formattedDate})`;
                }
            }
            
            // Badge d'erreur si sync partielle
            if (meta.last_sync_status === 'error') {
                const nextUpdateCard = document.querySelector('[data-testid="header-next-update"]');
                const nextUpdateValue = nextUpdateCard ? nextUpdateCard.querySelector('.stat-card__value') : null;
                
                if (nextUpdateValue && !nextUpdateValue.querySelector('.sync-error-badge')) {
                    const badge = document.createElement('span');
                    badge.className = 'sync-error-badge';
                    badge.textContent = ' ⚠️ Sync partielle';
                    badge.style.cssText = 'margin-left: 8px; color: #ff9800; font-size: 0.85em;';
                    nextUpdateValue.appendChild(badge);
                }
            } else {
                // Retirer le badge si présent
                const badge = document.querySelector('.sync-error-badge');
                if (badge) badge.remove();
            }
            
            console.log('[Meta-Refresh] Updated at', new Date().toLocaleTimeString());
            
        } catch (error) {
            console.error('[Meta-Refresh] Error fetching meta:', error);
        }
    }
    
    /**
     * Configure les tooltips interactifs (survol + focus)
     * Remplit l'ETA au moment de l'ouverture
     */
    function setupTooltips() {
        const infoButtons = document.querySelectorAll('.nu-info');
        
        infoButtons.forEach(button => {
            const tooltipId = button.getAttribute('aria-describedby');
            const tooltip = document.getElementById(tooltipId);
            
            if (!tooltip) return;
            
            const showTooltip = () => {
                // Remplir l'ETA avec l'heure locale (HH:MM:SS)
                if (nextUpdateTime) {
                    const nextDate = new Date(nextUpdateTime);
                    const hours = String(nextDate.getHours()).padStart(2, '0');
                    const minutes = String(nextDate.getMinutes()).padStart(2, '0');
                    const seconds = String(nextDate.getSeconds()).padStart(2, '0');
                    
                    const etaEl = tooltip.querySelector('.nu-eta');
                    if (etaEl) {
                        etaEl.textContent = `${hours}:${minutes}:${seconds}`;
                    }
                }
                tooltip.hidden = false;
            };
            
            const hideTooltip = () => {
                tooltip.hidden = true;
            };
            
            // Afficher au survol
            button.addEventListener('mouseenter', showTooltip);
            button.addEventListener('mouseleave', hideTooltip);
            
            // Afficher au focus (accessibilité clavier)
            button.addEventListener('focusin', showTooltip);
            button.addEventListener('focusout', hideTooltip);
        });
    }
    
    /**
     * Initialisation au chargement de la page
     */
    function init() {
        console.log('[Meta-Refresh] Initializing...');
        console.log('[Meta-Refresh] Fetch interval:', FETCH_INTERVAL_MS / 1000, 'seconds');
        console.log('[Meta-Refresh] Refresh interval:', REFRESH_INTERVAL_S / 60, 'minutes');
        
        // Configurer les tooltips
        setupTooltips();
        
        // Premier fetch immédiat
        fetchMeta();
        
        // Fetch périodique
        setInterval(fetchMeta, FETCH_INTERVAL_MS);
    }
    
    // Démarrer quand le DOM est prêt
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
})();
