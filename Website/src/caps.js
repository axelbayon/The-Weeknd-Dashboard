/**
 * Caps Module - Gestion de la page "Caps imminents"
 * Affiche les titres et albums proches d'atteindre leur prochain palier de streams
 */

(function() {
    'use strict';

    // État du module
    let allSongs = [];
    let allAlbums = [];
    let spotifyDataDate = null;
    let currentWindow = 30; // Fenêtre par défaut : 30 jours
    let showSongs = true;
    let showAlbums = true;
    let currentSortKey = 'days_to_next_cap';
    let currentSortDirection = 'asc';

    /**
     * Initialise le module Caps au chargement de la page
     */
    function init() {
        // Charger les données initiales
        loadAllData();

        // Écouter les changements de contrôles
        setupControls();

        // Écouter les auto-refresh depuis meta-refresh.js
        window.addEventListener('data-sync-updated', handleDataSyncUpdated);

        console.log('[Caps] Module initialized');
    }

    /**
     * Charge toutes les données nécessaires (songs, albums, meta)
     */
    async function loadAllData() {
        try {
            const [songsResponse, albumsResponse, metaResponse] = await Promise.all([
                fetch('/data/songs.json?t=' + Date.now()),
                fetch('/data/albums.json?t=' + Date.now()),
                fetch('/data/meta.json?t=' + Date.now())
            ]);

            if (!songsResponse.ok || !albumsResponse.ok || !metaResponse.ok) {
                console.error('[Caps] Failed to fetch data');
                return;
            }

            allSongs = await songsResponse.json();
            allAlbums = await albumsResponse.json();
            const meta = await metaResponse.json();
            
            spotifyDataDate = meta.spotify_data_date;

            // Rendre le tableau
            renderCapsTable();

        } catch (error) {
            console.error('[Caps] Error loading data:', error);
        }
    }

    /**
     * Configure les écouteurs d'événements pour les contrôles
     */
    function setupControls() {
        const windowSelect = document.getElementById('caps-window-select');
        const songsToggle = document.getElementById('caps-toggle-songs');
        const albumsToggle = document.getElementById('caps-toggle-albums');

        if (windowSelect) {
            windowSelect.addEventListener('change', (e) => {
                currentWindow = parseInt(e.target.value, 10);
                renderCapsTable();
            });
        }

        if (songsToggle) {
            songsToggle.addEventListener('change', (e) => {
                showSongs = e.target.checked;
                renderCapsTable();
            });
        }

        if (albumsToggle) {
            albumsToggle.addEventListener('change', (e) => {
                showAlbums = e.target.checked;
                renderCapsTable();
            });
        }

        // Écouter les clics sur les en-têtes triables (Prompt 7.9: plein-surface)
        const table = document.querySelector('[data-testid="caps-table"]');
        if (table) {
            const thead = table.querySelector('thead');
            if (thead) {
                thead.addEventListener('click', handleSortClick);
            }
        }
    }

    /**
     * Gère le clic sur les en-têtes triables (Prompt 7.9: plein-surface)
     */
    function handleSortClick(event) {
        // Résoudre le <th> cliqué via closest (plein-surface)
        const th = event.target.closest('th[data-sort-key]');
        if (!th) return;
        
        // Lecture de la clé de tri depuis l'attribut data-sort-key (source de vérité unique)
        const sortKey = th.dataset.sortKey;
        
        if (!sortKey) {
            console.warn('data-sort-key manquant sur', th);
            return;
        }
        
        // Inverser la direction si on clique sur la même colonne
        if (currentSortKey === sortKey) {
            currentSortDirection = currentSortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            currentSortKey = sortKey;
            currentSortDirection = 'asc';
        }

        renderCapsTable();
    }

    /**
     * Filtre les données selon la fenêtre et les toggles
     */
    function filterData() {
        const filteredData = [];

        // Filtrer les songs
        if (showSongs) {
            allSongs.forEach(song => {
                if (typeof song.days_to_next_cap === 'number' && 
                    !isNaN(song.days_to_next_cap) &&
                    song.days_to_next_cap <= currentWindow) {
                    filteredData.push({
                        type: 'song',
                        ...song
                    });
                }
            });
        }

        // Filtrer les albums
        if (showAlbums) {
            allAlbums.forEach(album => {
                if (typeof album.days_to_next_cap === 'number' && 
                    !isNaN(album.days_to_next_cap) &&
                    album.days_to_next_cap <= currentWindow) {
                    filteredData.push({
                        type: 'album',
                        ...album
                    });
                }
            });
        }

        return filteredData;
    }

    /**
     * Trie les données filtrées
     */
    function sortData(data) {
        return data.sort((a, b) => {
            let aVal = a[currentSortKey];
            let bVal = b[currentSortKey];

            // Cas spéciaux
            if (currentSortKey === 'rank') {
                // Tri numérique sur le rang
                aVal = parseInt(aVal) || Infinity; // Si pas de rang, mettre à la fin
                bVal = parseInt(bVal) || Infinity;
            } else if (currentSortKey === 'title') {
                // Ignorer * et ^ pour le tri (featuring / compilation, Prompt 7.9)
                aVal = (a.title || '').replace(/^[\*\^]\s*/, '').toLowerCase();
                bVal = (b.title || '').replace(/^[\*\^]\s*/, '').toLowerCase();
            } else if (currentSortKey === 'variation_pct') {
                // Gérer "N.D."
                aVal = (typeof aVal === 'string' && aVal === 'N.D.') ? -Infinity : parseFloat(aVal);
                bVal = (typeof bVal === 'string' && bVal === 'N.D.') ? -Infinity : parseFloat(bVal);
            } else if (currentSortKey === 'eta') {
                // Calculer ETA pour tri
                aVal = calculateETA(a.days_to_next_cap).getTime();
                bVal = calculateETA(b.days_to_next_cap).getTime();
            }

            // Comparaison
            if (aVal < bVal) return currentSortDirection === 'asc' ? -1 : 1;
            if (aVal > bVal) return currentSortDirection === 'asc' ? 1 : -1;
            return 0;
        });
    }

    /**
     * Calcule la date ETA
     * @param {number} days - Nombre de jours (avec décimales)
     * @returns {Date} - Date ETA
     */
    function calculateETA(days) {
        if (!spotifyDataDate || typeof days !== 'number') {
            return new Date();
        }

        const [year, month, day] = spotifyDataDate.split('-').map(Number);
        const baseDate = new Date(year, month - 1, day);
        const daysToAdd = Math.ceil(days);
        
        const etaDate = new Date(baseDate);
        etaDate.setDate(etaDate.getDate() + daysToAdd);
        
        return etaDate;
    }

    /**
     * Formate la date ETA en JJ/MM/YYYY
     * @param {Date} date - Date à formater
     * @returns {string} - Date formatée
     */
    function formatETA(date) {
        const day = String(date.getDate()).padStart(2, '0');
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const year = date.getFullYear();
        return `${day}/${month}/${year}`;
    }

    /**
     * Rend le tableau des caps imminents
     */
    function renderCapsTable() {
        const tbody = document.querySelector('[data-testid="caps-table"] tbody');
        if (!tbody) return;

        // Filtrer et trier les données
        const filteredData = filterData();
        const sortedData = sortData(filteredData);

        // Compter les éléments
        const songsCount = sortedData.filter(item => item.type === 'song').length;
        const albumsCount = sortedData.filter(item => item.type === 'album').length;
        const totalCount = sortedData.length;

        // Mettre à jour les compteurs
        updateCounter('caps-total-count', totalCount);
        updateCounter('caps-songs-count', songsCount);
        updateCounter('caps-albums-count', albumsCount);

        // Mettre à jour les labels avec la fenêtre temporelle
        updateCardLabels();

        // Mettre à jour les indicateurs de tri
        updateSortIndicators();

        // Vider le tableau
        tbody.innerHTML = '';

        // Remplir le tableau
        sortedData.forEach(item => {
            const row = createCapsRow(item);
            tbody.appendChild(row);
        });

        console.log(`[Caps] Rendered ${totalCount} items (${songsCount} songs, ${albumsCount} albums)`);
    }

    /**
     * Crée une ligne du tableau
     */
    function createCapsRow(item) {
        const row = document.createElement('tr');
        row.setAttribute('data-testid', 'caps-row');
        row.setAttribute('data-type', item.type);
        row.setAttribute('data-id', item.id);
        row.style.cursor = 'pointer';

        // Calculer ETA
        const etaDate = calculateETA(item.days_to_next_cap);
        const etaFormatted = formatETA(etaDate);

        // Rang (#) - avec couleur selon type
        const rankCell = document.createElement('td');
        rankCell.className = 'data-table__cell--numeric data-table__cell--rank';
        
        // Ajouter classe pour couleur selon type
        if (item.type === 'song') {
            rankCell.classList.add('data-table__cell--rank-song');
        } else {
            rankCell.classList.add('data-table__cell--rank-album');
        }
        
        rankCell.textContent = item.rank || '—';
        row.appendChild(rankCell);

        // Titre (avec cover)
        const titleCell = document.createElement('td');
        titleCell.className = 'data-table__cell--title';
        const titleWrapper = document.createElement('div');
        titleWrapper.className = 'data-table__title-wrapper';
        
        const cover = document.createElement('div');
        cover.className = 'data-table__title-cover';
        
        if (item.cover_url) {
            const img = document.createElement('img');
            img.src = item.cover_url;
            img.alt = item.title;
            img.className = 'data-table__cover-image';
            cover.appendChild(img);
        } else {
            const placeholder = document.createElement('div');
            placeholder.className = 'cover-placeholder';
            placeholder.textContent = item.type === 'song' ? '🎵' : '💿';
            cover.appendChild(placeholder);
        }
        
        const titleMeta = document.createElement('div');
        titleMeta.className = 'data-table__title-meta';
        
        const titleName = document.createElement('div');
        titleName.className = 'data-table__song-name';
        titleName.textContent = item.title;
        
        titleMeta.appendChild(titleName);
        
        // Pour les songs, afficher l'album
        if (item.type === 'song' && item.album) {
            const albumName = document.createElement('div');
            albumName.className = 'data-table__album';
            albumName.textContent = item.album;
            titleMeta.appendChild(albumName);
        }
        
        titleWrapper.appendChild(cover);
        titleWrapper.appendChild(titleMeta);
        titleCell.appendChild(titleWrapper);
        row.appendChild(titleCell);

        // Type
        const typeCell = document.createElement('td');
        const typeBadge = document.createElement('span');
        typeBadge.className = item.type === 'song' ? 'flag-chip flag-chip--song' : 'flag-chip flag-chip--album';
        typeBadge.textContent = item.type === 'song' ? 'TITRE' : 'ALBUM';
        typeBadge.setAttribute('data-testid', 'caps-type-badge');
        typeCell.appendChild(typeBadge);
        row.appendChild(typeCell);

        // Prochain cap (j) - avec 2 décimales
        const daysCell = document.createElement('td');
        daysCell.className = 'data-table__cell--numeric';
        daysCell.textContent = item.days_to_next_cap.toFixed(2) + ' j';
        row.appendChild(daysCell);

        // Date prévue (ETA)
        const etaCell = document.createElement('td');
        etaCell.className = 'data-table__cell--numeric';
        etaCell.textContent = etaFormatted;
        etaCell.setAttribute('data-testid', 'caps-eta');
        row.appendChild(etaCell);

        // Streams totaux
        const streamsCell = document.createElement('td');
        streamsCell.className = 'data-table__cell--numeric';
        streamsCell.textContent = window.formatNumber ? window.formatNumber(item.streams_total) : item.streams_total.toLocaleString('fr-FR');
        row.appendChild(streamsCell);

        // Streams quotidiens
        const dailyCell = document.createElement('td');
        dailyCell.className = 'data-table__cell--numeric';
        dailyCell.textContent = window.formatNumber ? window.formatNumber(item.streams_daily) : item.streams_daily.toLocaleString('fr-FR');
        row.appendChild(dailyCell);

        // Variation (%) - Pipeline unifié formatPercent (Prompt 7.9)
        const variationCell = document.createElement('td');
        variationCell.className = 'data-table__cell--numeric';
        const variationSpan = document.createElement('span');
        
        const variationValue = item.variation_pct;
        const isValidNumber = variationValue !== null && variationValue !== undefined && 
                              variationValue !== 'N.D.' && !isNaN(parseFloat(variationValue));
        
        if (isValidNumber) {
            const variation = parseFloat(variationValue);
            const variationText = window.formatters.formatPercent(variation);
            
            if (variation > 0) {
                variationSpan.className = 'data-table__delta--positive';
            } else if (variation < 0) {
                variationSpan.className = 'data-table__delta--negative';
            } else {
                variationSpan.className = 'data-table__delta--neutral';
            }
            variationSpan.textContent = variationText;
        } else {
            // N.D. : classe neutre/grisée
            variationSpan.className = 'data-table__delta--na';
            variationSpan.textContent = 'N.D.';
        }
        
        variationCell.appendChild(variationSpan);
        row.appendChild(variationCell);

        // Prochain palier (format M/B)
        const capCell = document.createElement('td');
        capCell.className = 'data-table__cell--numeric';
        // Utiliser formatCap du module formatters si disponible, sinon formatNumber
        if (window.formatters && window.formatters.formatCap) {
            capCell.textContent = window.formatters.formatCap(item.next_cap_value);
        } else if (window.formatNumber) {
            capCell.textContent = window.formatNumber(item.next_cap_value);
        } else {
            capCell.textContent = item.next_cap_value.toLocaleString('fr-FR');
        }
        row.appendChild(capCell);

        // Navigation croisée au clic
        row.addEventListener('click', () => {
            navigateToItem(item);
        });

        return row;
    }

    /**
     * Met à jour un compteur
     */
    function updateCounter(testId, value) {
        const element = document.querySelector(`[data-testid="${testId}"]`);
        if (element) {
            element.textContent = value;
        }
    }

    /**
     * Met à jour les labels des cartes avec la fenêtre temporelle
     */
    function updateCardLabels() {
        const songsLabel = document.querySelector('[data-caps-label="songs"]');
        const albumsLabel = document.querySelector('[data-caps-label="albums"]');
        
        if (songsLabel) {
            songsLabel.textContent = `Nombre de titres (${currentWindow} j)`;
        }
        if (albumsLabel) {
            albumsLabel.textContent = `Nombre d'albums (${currentWindow} j)`;
        }
    }

    /**
     * Met à jour les indicateurs de tri dans les en-têtes
     */
    function updateSortIndicators() {
        const table = document.querySelector('[data-testid="caps-table"]');
        if (!table) return;

        const headers = table.querySelectorAll('th');

        headers.forEach((th) => {
            th.classList.remove('is-sorted');
            th.removeAttribute('aria-sort');
            
            // Supprimer les anciens indicateurs
            const oldIndicator = th.querySelector('[data-testid="caps-sort-indicator"]');
            if (oldIndicator) {
                oldIndicator.remove();
            }

            // Lire la clé de tri depuis data-sort-key (source de vérité unique)
            const thSortKey = th.dataset.sortKey;
            
            // Ajouter le nouvel indicateur si c'est la colonne active
            if (thSortKey === currentSortKey) {
                th.classList.add('is-sorted');
                th.setAttribute('aria-sort', currentSortDirection === 'asc' ? 'ascending' : 'descending');
                
                const button = th.querySelector('.data-table__sort-button');
                if (button) {
                    const indicator = document.createElement('span');
                    indicator.setAttribute('data-testid', 'caps-sort-indicator');
                    indicator.className = 'data-table__sort-icon';
                    indicator.textContent = currentSortDirection === 'asc' ? '▲' : '▼';
                    button.appendChild(indicator);
                }
            }
        });
    }

    /**
     * Navigue vers l'élément dans la page Songs ou Albums
     */
    function navigateToItem(item) {
        const targetPage = item.type === 'song' ? 'songs' : 'albums';
        
        // Activer l'onglet correspondant
        const navLink = document.querySelector(`[data-page="${targetPage}"]`);
        if (navLink) {
            navLink.click();
        }

        // Attendre que la page soit affichée
        setTimeout(() => {
            const targetTable = document.querySelector(`.data-table--${targetPage}`);
            if (!targetTable) return;

            // Trouver la ligne correspondante
            const targetRow = targetTable.querySelector(`[data-row-id="${item.id}"]`);
            if (!targetRow) return;

            // Scroll vers la ligne
            targetRow.scrollIntoView({ behavior: 'smooth', block: 'center' });

            // Ajouter un highlight temporaire
            targetRow.classList.add('row-highlighted');
            setTimeout(() => {
                targetRow.classList.remove('row-highlighted');
            }, 2000);

        }, 100);
    }

    /**
     * Gère l'événement de mise à jour des données
     */
    function handleDataSyncUpdated(event) {
        console.log('[Caps] Data sync updated, reloading...');
        loadAllData();
    }

    // Initialiser au chargement du DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
