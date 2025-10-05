/**
 * Module de rendu des données dans l'UI
 * Gère les agrégats et les tables Songs/Albums
 */

class DataRenderer {
    constructor() {
        this.currentPage = 'songs';
        this.lastRenderedData = {
            songs: null,
            albums: null
        };
        
        // Écouter l'événement de synchronisation pour rafraîchir les badges
        // Prompt 8.8: Invalider cache + rebuild rail si spotify_data_date change
        window.addEventListener('data-sync-updated', async (event) => {
            console.log('[DataRenderer] 🔄 Event data-sync-updated reçu');
            
            // Invalider cache songs/albums pour forcer refetch avec nouveaux deltas
            if (window.dataLoader) {
                window.dataLoader.invalidateCache('songs');
                window.dataLoader.invalidateCache('albums');
                console.log('[DataRenderer] 🗑️ Cache songs/albums invalidé');
            }
            
            // Attendre un court instant pour que les rails se rebuilds avec nouvelles données
            setTimeout(() => {
                if (window.rankRailSongs) window.rankRailSongs.debouncedRebuild();
                if (window.rankRailAlbums) window.rankRailAlbums.debouncedRebuild();
                console.log('[DataRenderer] ✅ Rails rebuilds déclenchés');
            }, 200);
        });
        
        // Écouter le resize de la fenêtre avec debounce
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                console.log('[DataRenderer] 🔄 Rafraîchissement badges après resize');
                if (window.rankRailSongs) window.rankRailSongs.debouncedRebuild();
                if (window.rankRailAlbums) window.rankRailAlbums.debouncedRebuild();
            }, 100);
        });
    }

    /**
     * Calcule et rend les agrégats de la page Songs
     */
    /**
     * Met à jour les agrégats Songs depuis le DOM (lignes visibles)
     * Prompt 8.7 : ne plus utiliser meta.json, calculer depuis les tr affichées
     */
    async renderSongsAggregates() {
        try {
            // Attendre que le tableau soit rendu (si appelé trop tôt)
            const tbody = document.querySelector('#page-songs tbody');
            if (!tbody || tbody.querySelectorAll('tr[data-row-id]').length === 0) {
                console.warn('⚠️ Tableau Songs pas encore rendu, attente...');
                return;
            }

            const stats = this.calculateSongsStatsFromDOM();
            
            if (!stats) {
                console.error('❌ Impossible de calculer les stats Songs depuis le DOM');
                return;
            }

            this.updateSongsAggregatesUI(stats);
            
            console.log('✅ Agrégats Songs mis à jour depuis DOM:', stats);
        } catch (error) {
            console.error('❌ Erreur rendu agrégats Songs:', error);
            this.showError('songs-aggregates');
        }
    }

    /**
     * Calcule les statistiques des chansons depuis les lignes visibles du tableau DOM
     * Prompt 8.7 : agrégats = somme des lignes affichées, pas depuis Kworb
     * Split Feat (astérisque) vs Solo/Lead
     */
    calculateSongsStatsFromDOM() {
        const tbody = document.querySelector('#page-songs tbody');
        if (!tbody) {
            console.warn('[Stats] Tbody Songs introuvable, impossible de calculer les stats');
            return null;
        }

        // Récupérer uniquement les lignes visibles (pas hidden, pas display:none)
        const rows = Array.from(tbody.querySelectorAll('tr[data-row-id]')).filter(row => {
            return row.offsetParent !== null; // vérifie si la ligne est visible
        });

        let total = 0;
        let totalStreams = 0;
        let dailyStreams = 0;

        let leadCount = 0;
        let leadTotalStreams = 0;
        let leadDailyStreams = 0;

        let featCount = 0;
        let featTotalStreams = 0;
        let featDailyStreams = 0;

        rows.forEach(row => {
            total++;

            // Extraire les données des cellules
            const titleCell = row.querySelector('td:nth-child(2)');
            const streamsCell = row.querySelector('td:nth-child(3)');
            const dailyCell = row.querySelector('td:nth-child(4)');

            const title = titleCell?.textContent?.trim() || '';
            const streams = this.parseStreamValue(streamsCell?.textContent?.trim() || '0');
            const daily = this.parseStreamValue(dailyCell?.textContent?.trim() || '0');

            totalStreams += streams;
            dailyStreams += daily;

            // Détecter Feat par astérisque au début du titre
            const isFeat = title.startsWith('*');

            if (isFeat) {
                featCount++;
                featTotalStreams += streams;
                featDailyStreams += daily;
            } else {
                leadCount++;
                leadTotalStreams += streams;
                leadDailyStreams += daily;
            }
        });

        const stats = {
            total,
            totalStreams,
            dailyStreams,
            lead: {
                count: leadCount,
                totalStreams: leadTotalStreams,
                dailyStreams: leadDailyStreams
            },
            feat: {
                count: featCount,
                totalStreams: featTotalStreams,
                dailyStreams: featDailyStreams
            }
        };

        console.log('[Stats] Calcul depuis DOM - Titres visibles:', stats);
        return stats;
    }

    /**
     * Parse une valeur de stream formatée (ex: "1 234 567") en nombre
     */
    parseStreamValue(text) {
        if (!text || text === '—' || text === '-') return 0;
        // Retirer tous les espaces et parser
        const cleaned = text.replace(/\s/g, '');
        const num = parseInt(cleaned, 10);
        return isNaN(num) ? 0 : num;
    }

    /**
     * Met à jour l'UI des agrégats Songs
     */
    updateSongsAggregatesUI(stats) {
        const { formatIntFr, formatNumber } = window.formatters;

        // Agrégats généraux (dans page-header--aggregate)
        const aggregateCards = document.querySelector('#page-songs .page-header--aggregate .page-header__cards');
        if (aggregateCards) {
            const cards = aggregateCards.querySelectorAll('.stat-card');
            if (cards[0]) cards[0].querySelector('.stat-card__value').textContent = formatNumber(stats.total);
            if (cards[1]) cards[1].querySelector('.stat-card__value').textContent = formatIntFr(stats.totalStreams);
            if (cards[2]) cards[2].querySelector('.stat-card__value').textContent = formatIntFr(stats.dailyStreams);

            // Ajouter data-testid
            if (cards[0]) cards[0].setAttribute('data-testid', 'songs-total-count');
            if (cards[1]) cards[1].setAttribute('data-testid', 'songs-streams-total');
            if (cards[2]) cards[2].setAttribute('data-testid', 'songs-streams-daily');
        }

        // Agrégats Lead/Feat (dans page-header--split)
        const splitCards = document.querySelector('#page-songs .page-header--split .page-header__cards');
        if (splitCards) {
            const leadCard = splitCards.querySelectorAll('.stat-card')[0];
            const featCard = splitCards.querySelectorAll('.stat-card')[1];

            if (leadCard) {
                const leadValues = leadCard.querySelectorAll('.stat-card__row-value');
                if (leadValues[0]) leadValues[0].textContent = formatNumber(stats.lead.count);
                if (leadValues[1]) leadValues[1].textContent = formatIntFr(stats.lead.totalStreams);
                if (leadValues[2]) leadValues[2].textContent = formatIntFr(stats.lead.dailyStreams);

                // Ajouter data-testid
                if (leadValues[0]) leadValues[0].setAttribute('data-testid', 'songs-lead-count');
                if (leadValues[1]) leadValues[1].setAttribute('data-testid', 'songs-lead-streams-total');
                if (leadValues[2]) leadValues[2].setAttribute('data-testid', 'songs-lead-streams-daily');
            }

            if (featCard) {
                const featValues = featCard.querySelectorAll('.stat-card__row-value');
                if (featValues[0]) featValues[0].textContent = formatNumber(stats.feat.count);
                if (featValues[1]) featValues[1].textContent = formatIntFr(stats.feat.totalStreams);
                if (featValues[2]) featValues[2].textContent = formatIntFr(stats.feat.dailyStreams);

                // Ajouter data-testid
                if (featValues[0]) featValues[0].setAttribute('data-testid', 'songs-feat-count');
                if (featValues[1]) featValues[1].setAttribute('data-testid', 'songs-feat-streams-total');
                if (featValues[2]) featValues[2].setAttribute('data-testid', 'songs-feat-streams-daily');
            }
        }
    }

    /**
     * Met à jour les agrégats Albums depuis le DOM (lignes visibles)
     * Prompt 8.7 : ne plus utiliser albums.json, calculer depuis les tr affichées
     */
    async renderAlbumsAggregates() {
        try {
            // Attendre que le tableau soit rendu
            const tbody = document.querySelector('#page-albums tbody');
            if (!tbody || tbody.querySelectorAll('tr[data-row-id]').length === 0) {
                console.warn('⚠️ Tableau Albums pas encore rendu, attente...');
                return;
            }

            const stats = this.calculateAlbumsStatsFromDOM();
            
            if (!stats) {
                console.error('❌ Impossible de calculer les stats Albums depuis le DOM');
                return;
            }

            this.updateAlbumsAggregatesUI(stats);
            
            console.log('✅ Agrégats Albums mis à jour depuis DOM:', stats);
        } catch (error) {
            console.error('❌ Erreur rendu agrégats Albums:', error);
            this.showError('albums-aggregates');
        }
    }

    /**
     * Calcule les statistiques des albums depuis les lignes visibles du tableau DOM
     * Prompt 8.7 : agrégats = somme des lignes affichées, pas depuis data.json
     */
    calculateAlbumsStatsFromDOM() {
        const tbody = document.querySelector('#page-albums tbody');
        if (!tbody) {
            console.warn('[Stats] Tbody Albums introuvable, impossible de calculer les stats');
            return null;
        }

        // Récupérer uniquement les lignes visibles
        const rows = Array.from(tbody.querySelectorAll('tr[data-row-id]')).filter(row => {
            return row.offsetParent !== null;
        });

        let total = 0;
        let totalStreams = 0;
        let dailyStreams = 0;

        rows.forEach(row => {
            total++;

            // Extraire les données des cellules (même structure que Songs)
            const streamsCell = row.querySelector('td:nth-child(3)');
            const dailyCell = row.querySelector('td:nth-child(4)');

            const streams = this.parseStreamValue(streamsCell?.textContent?.trim() || '0');
            const daily = this.parseStreamValue(dailyCell?.textContent?.trim() || '0');

            totalStreams += streams;
            dailyStreams += daily;
        });

        const stats = {
            total,
            totalStreams,
            dailyStreams
        };

        console.log('[Stats] Calcul depuis DOM - Albums visibles:', stats);
        return stats;
    }

    /**
     * Met à jour l'UI des agrégats Albums
     */
    updateAlbumsAggregatesUI(stats) {
        const { formatIntFr, formatNumber } = window.formatters;

        const aggregateCards = document.querySelector('#page-albums .page-header--aggregate .page-header__cards');
        if (aggregateCards) {
            const cards = aggregateCards.querySelectorAll('.stat-card');
            if (cards[0]) cards[0].querySelector('.stat-card__value').textContent = formatNumber(stats.total);
            if (cards[1]) cards[1].querySelector('.stat-card__value').textContent = formatIntFr(stats.totalStreams);
            if (cards[2]) cards[2].querySelector('.stat-card__value').textContent = formatIntFr(stats.dailyStreams);

            // Ajouter data-testid
            if (cards[0]) cards[0].setAttribute('data-testid', 'albums-total-count');
            if (cards[1]) cards[1].setAttribute('data-testid', 'albums-streams-total');
            if (cards[2]) cards[2].setAttribute('data-testid', 'albums-streams-daily');
        }
    }

    /**
     * Prompt 8.9: Mise à jour progressive de la table Songs (SWR - no flicker)
     * Compare les lignes existantes avec les nouvelles données et met à jour uniquement ce qui change
     * Précharge les images avant swap pour éviter le flash blanc
     */
    updateSongsTableProgressive(tbody, sortedSongs) {
        const { formatIntFr, formatPercent, formatDays, formatCap } = window.formatters;
        
        // Créer un map des lignes existantes par data-row-id
        const existingRows = new Map();
        tbody.querySelectorAll('tr[data-row-id]').forEach(row => {
            existingRows.set(row.getAttribute('data-row-id'), row);
        });
        
        // Parcourir les nouvelles données et mettre à jour/ajouter
        sortedSongs.forEach((song, index) => {
            const existingRow = existingRows.get(song.id);
            
            if (existingRow) {
                // Ligne existe: mise à jour sélective des cellules modifiées
                this.updateSongRowProgressive(existingRow, song, index + 1);
                existingRows.delete(song.id); // Marquer comme traitée
            } else {
                // Nouvelle ligne: créer et ajouter
                const newRow = this.createSongRow(song, index + 1);
                tbody.appendChild(newRow);
            }
        });
        
        // Supprimer les lignes qui n'existent plus dans les nouvelles données
        existingRows.forEach(row => row.remove());
    }

    /**
     * Prompt 8.9: Met à jour une ligne existante avec préchargement d'image
     */
    updateSongRowProgressive(row, song, displayRank) {
        const { formatIntFr, formatPercent, formatDays, formatCap } = window.formatters;
        
        // Mettre à jour le rank (colonne 1)
        const tdRank = row.querySelector('.data-table__cell--rank');
        if (tdRank) {
            tdRank.setAttribute('data-sort-raw', displayRank);
            const rankSpan = tdRank.querySelector('.num');
            if (rankSpan) rankSpan.textContent = formatIntFr(displayRank);
        }
        
        // Mettre à jour le cover (colonne 2) avec préchargement
        const tdCover = row.querySelector('td:nth-child(2)');
        if (tdCover && song.cover_url) {
            const img = tdCover.querySelector('img');
            const currentSrc = img ? img.src : null;
            const newSrc = song.cover_url;
            
            // Précharger nouvelle image avant swap (évite flash blanc)
            if (img && currentSrc !== newSrc) {
                const preloadImg = new Image();
                preloadImg.onload = () => {
                    img.src = newSrc;
                    img.alt = `Cover ${song.title}`;
                };
                preloadImg.onerror = () => {
                    img.src = '/Website/img/album-placeholder.svg';
                    img.alt = 'Cover indisponible';
                };
                preloadImg.src = newSrc;
            }
        }
        
        // Mettre à jour titre + album (colonne 3)
        const tdTitle = row.querySelector('.data-table__cell--title');
        if (tdTitle) {
            const titleText = tdTitle.querySelector('.song-title__text');
            const albumText = tdTitle.querySelector('.song-title__album');
            if (titleText) titleText.textContent = song.title;
            if (albumText) albumText.textContent = song.album_name || 'Album inconnu';
        }
        
        // Mettre à jour streams totaux (colonne 4)
        const tdStreamsTotal = row.querySelector('td:nth-child(4)');
        if (tdStreamsTotal) {
            tdStreamsTotal.setAttribute('data-sort-raw', song.streams_total);
            const numSpan = tdStreamsTotal.querySelector('.num');
            if (numSpan) numSpan.textContent = formatIntFr(song.streams_total);
        }
        
        // Mettre à jour streams quotidiens (colonne 5)
        const tdStreamsDaily = row.querySelector('td:nth-child(5)');
        if (tdStreamsDaily) {
            tdStreamsDaily.setAttribute('data-sort-raw', song.streams_daily);
            const numSpan = tdStreamsDaily.querySelector('.num');
            if (numSpan) numSpan.textContent = formatIntFr(song.streams_daily);
        }
        
        // Mettre à jour variation (colonne 6)
        const tdVariation = row.querySelector('td:nth-child(6)');
        if (tdVariation) {
            tdVariation.setAttribute('data-sort-raw', song.streams_delta);
            const numSpan = tdVariation.querySelector('.num');
            if (numSpan) numSpan.textContent = formatIntFr(song.streams_delta);
        }
        
        // Mettre à jour % variation (colonne 7)
        const tdVariationPercent = row.querySelector('td:nth-child(7)');
        if (tdVariationPercent) {
            tdVariationPercent.setAttribute('data-sort-raw', song.streams_delta_percent);
            const numSpan = tdVariationPercent.querySelector('.num');
            if (numSpan) numSpan.textContent = formatPercent(song.streams_delta_percent);
        }
        
        // Mettre à jour palier (colonne 8)
        const tdMilestone = row.querySelector('td:nth-child(8)');
        if (tdMilestone) {
            const cap = formatCap(song.next_milestone);
            tdMilestone.setAttribute('data-sort-raw', song.next_milestone);
            const numSpan = tdMilestone.querySelector('.num');
            if (numSpan) numSpan.textContent = cap;
        }
        
        // Mettre à jour jours restants (colonne 9)
        const tdDaysLeft = row.querySelector('td:nth-child(9)');
        if (tdDaysLeft) {
            const formatted = formatDays(song.days_to_next_milestone);
            tdDaysLeft.setAttribute('data-sort-raw', song.days_to_next_milestone);
            const numSpan = tdDaysLeft.querySelector('.num');
            if (numSpan) numSpan.textContent = formatted;
        }
    }

    /**
     * Rend la table Songs
     */
    async renderSongsTable() {
        try {
            const songs = await window.dataLoader.loadSongs();
            
            if (!songs || songs.length === 0) {
                console.warn('⚠️ Aucune chanson à afficher');
                return;
            }

            // Trier par streams_total décroissant
            const sortedSongs = [...songs].sort((a, b) => b.streams_total - a.streams_total);

            const tbody = document.querySelector('#page-songs .data-table--songs tbody');
            if (!tbody) {
                console.error('❌ Tbody Songs introuvable');
                return;
            }

            // Prompt 8.9: SWR (Stale-While-Revalidate) - Mise à jour progressive sans clear
            // Premier render: créer toutes les lignes
            if (!this.lastRenderedData.songs || tbody.children.length === 0) {
                tbody.innerHTML = '';
                sortedSongs.forEach((song, index) => {
                    const row = this.createSongRow(song, index + 1);
                    tbody.appendChild(row);
                });
                console.log(`✅ Table Songs rendue (initial): ${sortedSongs.length} lignes`);
            } else {
                // Refresh: mise à jour progressive par diff (no clear, no flicker)
                this.updateSongsTableProgressive(tbody, sortedSongs);
                console.log(`✅ Table Songs mise à jour (progressive): ${sortedSongs.length} lignes`);
            }

            this.lastRenderedData.songs = songs;

            // Réinitialiser le tri (table-sort.js)
            if (window.tableSort) {
                window.tableSort.reinitTable('songs');
            }

            // Monter et binder le rail de badges (nouveau système robuste)
            if (window.rankRailSongs) {
                window.rankRailSongs.mount('#page-songs .table-section');
                window.rankRailSongs.bind();
                window.rankRailSongs.rebuild(sortedSongs);
            }

            // Dispatcher événement après double RAF (garantir repaint)
            requestAnimationFrame(() => {
                requestAnimationFrame(() => {
                    const wrapper = document.querySelector('#page-songs .table-wrapper');
                    if (wrapper) {
                        wrapper.dispatchEvent(new CustomEvent('table:rows-updated'));
                    }

                    // Prompt 8.7 : Recalculer les agrégats depuis les lignes visibles
                    this.renderSongsAggregates();
                });
            });
        } catch (error) {
            console.error('❌ Erreur rendu table Songs:', error);
            this.showError('songs-table');
        }
    }

    /**
     * Crée une ligne de la table Songs
     */
    createSongRow(song, displayRank) {
        const { formatIntFr, formatPercent, formatDays, formatCap } = window.formatters;

        const tr = document.createElement('tr');
        tr.setAttribute('data-row-id', song.id);
        tr.setAttribute('data-testid', 'songs-row');

        // Colonne #
        const tdRank = document.createElement('td');
        tdRank.className = 'data-table__cell--rank cell-num';
        tdRank.setAttribute('data-sort-value', 'rank');
        tdRank.setAttribute('data-sort-raw', displayRank);
        
        // Ajouter texte accessible (screen reader only) pour mouvement
        if (song.rank_delta && song.rank_delta !== 0) {
            const srText = document.createElement('span');
            srText.className = 'sr-only';
            const deltaAbs = Math.abs(song.rank_delta);
            const places = deltaAbs > 1 ? 'places' : 'place';
            srText.textContent = song.rank_delta > 0 
                ? `+${deltaAbs} ${places}` 
                : `${song.rank_delta} ${places}`;
            tdRank.appendChild(srText);
        }
        
        // Ajouter le numéro de rang
        tdRank.textContent = displayRank;
        
        tr.appendChild(tdRank);

        // Colonne Titre
        const tdTitle = document.createElement('td');
        tdTitle.className = 'data-table__cell--title col-title';
        tdTitle.setAttribute('data-sort-value', 'title');
        tdTitle.setAttribute('data-sort-raw', song.title); // Garde * pour tri intelligent
        
        // Cover : utiliser cover_url si disponible, sinon placeholder
        const coverHtml = song.cover_url
            ? `<img src="${this.escapeHtml(song.cover_url)}" alt="Cover ${this.escapeHtml(song.title)}" class="data-table__cover-image">`
            : `<div class="cover-placeholder">🎵</div>`;
        
        // Album name : utiliser album_name si disponible, sinon "Inconnu"
        const albumName = song.album_name || 'Inconnu';
        
        tdTitle.innerHTML = `
            <div class="data-table__title-wrapper">
                <div class="data-table__title-cover">
                    ${coverHtml}
                </div>
                <div class="data-table__title-meta">
                    <div class="data-table__song-name">${this.escapeHtml(song.title)}</div>
                    <span class="data-table__album" title="${this.escapeHtml(albumName)}">${this.escapeHtml(albumName)}</span>
                </div>
            </div>
        `;
        tr.appendChild(tdTitle);

        // Colonne Streams totaux (format entier FR)
        const tdStreamsTotal = document.createElement('td');
        tdStreamsTotal.className = 'data-table__cell--numeric cell-num';
        tdStreamsTotal.setAttribute('data-sort-value', 'streams_total');
        tdStreamsTotal.setAttribute('data-sort-raw', song.streams_total);
        tdStreamsTotal.textContent = formatIntFr(song.streams_total);
        tr.appendChild(tdStreamsTotal);

        // Colonne Streams quotidiens (format entier FR)
        const tdStreamsDaily = document.createElement('td');
        tdStreamsDaily.className = 'data-table__cell--numeric cell-num';
        tdStreamsDaily.setAttribute('data-sort-value', 'streams_daily');
        tdStreamsDaily.setAttribute('data-sort-raw', song.streams_daily);
        tdStreamsDaily.textContent = formatIntFr(song.streams_daily);
        tr.appendChild(tdStreamsDaily);

        // Colonne Variation (%) - Pipeline Caps, condition triple pour 0 neutre (Prompt 7.10)
        const tdVariation = document.createElement('td');
        tdVariation.className = 'data-table__cell--numeric cell-num';
        tdVariation.setAttribute('data-sort-value', 'variation');
        
        // Gérer les valeurs manquantes correctement
        const variationValue = song.variation_pct;
        const isValidNumber = variationValue !== null 
            && variationValue !== undefined 
            && variationValue !== 'N.D.' 
            && !isNaN(variationValue);
        
        if (isValidNumber) {
            tdVariation.setAttribute('data-sort-raw', variationValue);
            const variationText = formatPercent(variationValue);
            const value = Number(variationValue);
            
            // Triple condition : >0 vert, <0 rouge, =0 gris
            if (value > 0) {
                tdVariation.innerHTML = `<span class="data-table__delta--positive">${variationText}</span>`;
            } else if (value < 0) {
                tdVariation.innerHTML = `<span class="data-table__delta--negative">${variationText}</span>`;
            } else {
                tdVariation.innerHTML = `<span class="data-table__delta--neutral">${variationText}</span>`;
            }
        } else {
            // "Non mis-à-jour" : classe muted, valeur sentinelle pour tri (nulls last)
            // Utiliser une valeur sentinelle spéciale détectée par compareValues()
            tdVariation.setAttribute('data-sort-raw', 'NA_SENTINEL');
            tdVariation.innerHTML = `<span class="data-table__delta--na">${formatPercent(variationValue)}</span>`;
        }
        tr.appendChild(tdVariation);

        // Colonne Prochain cap (j)
        const tdDaysToCap = document.createElement('td');
        tdDaysToCap.className = 'data-table__cell--numeric cell-num';
        tdDaysToCap.setAttribute('data-sort-value', 'days_to_next_cap');
        tdDaysToCap.setAttribute('data-sort-raw', song.days_to_next_cap || 999999);
        tdDaysToCap.textContent = formatDays(song.days_to_next_cap);
        tr.appendChild(tdDaysToCap);

        // Colonne Prochain palier
        const tdNextCap = document.createElement('td');
        tdNextCap.className = 'data-table__cell--numeric cell-num';
        tdNextCap.setAttribute('data-sort-value', 'next_cap');
        tdNextCap.setAttribute('data-sort-raw', song.next_cap_value); // Valeur numérique pour tri correct
        tdNextCap.textContent = formatCap(song.next_cap_value);
        tr.appendChild(tdNextCap);

        return tr;
    }

    /**
     * Prompt 8.9: Mise à jour progressive de la table Albums (SWR - no flicker)
     */
    updateAlbumsTableProgressive(tbody, sortedAlbums) {
        const { formatIntFr, formatPercent, formatDays, formatCap } = window.formatters;
        
        // Créer un map des lignes existantes par data-row-id
        const existingRows = new Map();
        tbody.querySelectorAll('tr[data-row-id]').forEach(row => {
            existingRows.set(row.getAttribute('data-row-id'), row);
        });
        
        // Parcourir les nouvelles données et mettre à jour/ajouter
        sortedAlbums.forEach((album, index) => {
            const existingRow = existingRows.get(album.id);
            
            if (existingRow) {
                // Ligne existe: mise à jour sélective des cellules modifiées
                this.updateAlbumRowProgressive(existingRow, album, index + 1);
                existingRows.delete(album.id); // Marquer comme traitée
            } else {
                // Nouvelle ligne: créer et ajouter
                const newRow = this.createAlbumRow(album, index + 1);
                tbody.appendChild(newRow);
            }
        });
        
        // Supprimer les lignes qui n'existent plus dans les nouvelles données
        existingRows.forEach(row => row.remove());
    }

    /**
     * Prompt 8.9: Met à jour une ligne Album existante avec préchargement d'image
     */
    updateAlbumRowProgressive(row, album, displayRank) {
        const { formatIntFr, formatPercent, formatDays, formatCap } = window.formatters;
        
        // Mettre à jour le rank (colonne 1)
        const tdRank = row.querySelector('.data-table__cell--rank');
        if (tdRank) {
            tdRank.setAttribute('data-sort-raw', displayRank);
            const rankSpan = tdRank.querySelector('.num');
            if (rankSpan) rankSpan.textContent = formatIntFr(displayRank);
        }
        
        // Mettre à jour le cover (colonne 2) avec préchargement
        const tdCover = row.querySelector('td:nth-child(2)');
        if (tdCover && album.cover_url) {
            const img = tdCover.querySelector('img');
            const currentSrc = img ? img.src : null;
            const newSrc = album.cover_url;
            
            // Précharger nouvelle image avant swap (évite flash blanc)
            if (img && currentSrc !== newSrc) {
                const preloadImg = new Image();
                preloadImg.onload = () => {
                    img.src = newSrc;
                    img.alt = `Cover ${album.album_name}`;
                };
                preloadImg.onerror = () => {
                    img.src = '/Website/img/album-placeholder.svg';
                    img.alt = 'Cover indisponible';
                };
                preloadImg.src = newSrc;
            }
        }
        
        // Mettre à jour titre album (colonne 3)
        const tdTitle = row.querySelector('.data-table__cell--title');
        if (tdTitle) {
            const titleText = tdTitle.querySelector('.album-title__text');
            if (titleText) titleText.textContent = album.album_name || 'Album inconnu';
        }
        
        // Mettre à jour streams totaux (colonne 4)
        const tdStreamsTotal = row.querySelector('td:nth-child(4)');
        if (tdStreamsTotal) {
            tdStreamsTotal.setAttribute('data-sort-raw', album.streams_total);
            const numSpan = tdStreamsTotal.querySelector('.num');
            if (numSpan) numSpan.textContent = formatIntFr(album.streams_total);
        }
        
        // Mettre à jour streams quotidiens (colonne 5)
        const tdStreamsDaily = row.querySelector('td:nth-child(5)');
        if (tdStreamsDaily) {
            tdStreamsDaily.setAttribute('data-sort-raw', album.streams_daily);
            const numSpan = tdStreamsDaily.querySelector('.num');
            if (numSpan) numSpan.textContent = formatIntFr(album.streams_daily);
        }
        
        // Mettre à jour variation (colonne 6)
        const tdVariation = row.querySelector('td:nth-child(6)');
        if (tdVariation) {
            tdVariation.setAttribute('data-sort-raw', album.streams_delta);
            const numSpan = tdVariation.querySelector('.num');
            if (numSpan) numSpan.textContent = formatIntFr(album.streams_delta);
        }
        
        // Mettre à jour % variation (colonne 7)
        const tdVariationPercent = row.querySelector('td:nth-child(7)');
        if (tdVariationPercent) {
            tdVariationPercent.setAttribute('data-sort-raw', album.streams_delta_percent);
            const numSpan = tdVariationPercent.querySelector('.num');
            if (numSpan) numSpan.textContent = formatPercent(album.streams_delta_percent);
        }
        
        // Mettre à jour palier (colonne 8)
        const tdMilestone = row.querySelector('td:nth-child(8)');
        if (tdMilestone) {
            const cap = formatCap(album.next_milestone);
            tdMilestone.setAttribute('data-sort-raw', album.next_milestone);
            const numSpan = tdMilestone.querySelector('.num');
            if (numSpan) numSpan.textContent = cap;
        }
        
        // Mettre à jour jours restants (colonne 9)
        const tdDaysLeft = row.querySelector('td:nth-child(9)');
        if (tdDaysLeft) {
            const formatted = formatDays(album.days_to_next_milestone);
            tdDaysLeft.setAttribute('data-sort-raw', album.days_to_next_milestone);
            const numSpan = tdDaysLeft.querySelector('.num');
            if (numSpan) numSpan.textContent = formatted;
        }
    }

    /**
     * Rend la table Albums
     */
    async renderAlbumsTable() {
        try {
            const albums = await window.dataLoader.loadAlbums();
            
            if (!albums || albums.length === 0) {
                console.warn('⚠️ Aucun album à afficher');
                return;
            }

            // Trier par streams_total décroissant
            const sortedAlbums = [...albums].sort((a, b) => b.streams_total - a.streams_total);

            const tbody = document.querySelector('#page-albums .data-table--albums tbody');
            if (!tbody) {
                console.error('❌ Tbody Albums introuvable');
                return;
            }

            // Prompt 8.9: SWR (Stale-While-Revalidate) - Mise à jour progressive sans clear
            // Premier render: créer toutes les lignes
            if (!this.lastRenderedData.albums || tbody.children.length === 0) {
                tbody.innerHTML = '';
                sortedAlbums.forEach((album, index) => {
                    const row = this.createAlbumRow(album, index + 1);
                    tbody.appendChild(row);
                });
                console.log(`✅ Table Albums rendue (initial): ${sortedAlbums.length} lignes`);
            } else {
                // Refresh: mise à jour progressive par diff (no clear, no flicker)
                this.updateAlbumsTableProgressive(tbody, sortedAlbums);
                console.log(`✅ Table Albums mise à jour (progressive): ${sortedAlbums.length} lignes`);
            }

            this.lastRenderedData.albums = albums;

            // Réinitialiser le tri (table-sort.js)
            if (window.tableSort) {
                window.tableSort.reinitTable('albums');
            }

            // Monter et binder le rail de badges (nouveau système robuste)
            if (window.rankRailAlbums) {
                window.rankRailAlbums.mount('#page-albums .table-section');
                window.rankRailAlbums.bind();
                window.rankRailAlbums.rebuild(sortedAlbums);
            }

            // Dispatcher événement après double RAF (garantir repaint)
            requestAnimationFrame(() => {
                requestAnimationFrame(() => {
                    const wrapper = document.querySelector('#page-albums .table-wrapper');
                    if (wrapper) {
                        wrapper.dispatchEvent(new CustomEvent('table:rows-updated'));
                    }

                    // Prompt 8.7 : Recalculer les agrégats depuis les lignes visibles
                    this.renderAlbumsAggregates();
                });
            });
        } catch (error) {
            console.error('❌ Erreur rendu table Albums:', error);
            this.showError('albums-table');
        }
    }

    /**
     * Crée une ligne de la table Albums
     */
    createAlbumRow(album, displayRank) {
        const { formatIntFr, formatPercent, formatDays, formatCap } = window.formatters;

        const tr = document.createElement('tr');
        tr.setAttribute('data-row-id', album.id);
        tr.setAttribute('data-testid', 'albums-row');

        // Colonne #
        const tdRank = document.createElement('td');
        tdRank.className = 'data-table__cell--rank cell-num';
        tdRank.setAttribute('data-sort-value', 'rank');
        tdRank.setAttribute('data-sort-raw', displayRank);
        
        // Ajouter texte accessible (screen reader only) pour mouvement
        if (album.rank_delta && album.rank_delta !== 0) {
            const srText = document.createElement('span');
            srText.className = 'sr-only';
            const deltaAbs = Math.abs(album.rank_delta);
            const places = deltaAbs > 1 ? 'places' : 'place';
            srText.textContent = album.rank_delta > 0 
                ? `+${deltaAbs} ${places}` 
                : `${album.rank_delta} ${places}`;
            tdRank.appendChild(srText);
        }
        
        // Ajouter le numéro de rang
        tdRank.textContent = displayRank;
        
        tr.appendChild(tdRank);

        // Colonne Titre
        const tdTitle = document.createElement('td');
        tdTitle.className = 'data-table__cell--title col-title';
        tdTitle.setAttribute('data-sort-value', 'title');
        tdTitle.setAttribute('data-sort-raw', album.title);
        
        // Cover : utiliser cover_url si disponible, sinon placeholder
        const coverHtml = album.cover_url
            ? `<img src="${this.escapeHtml(album.cover_url)}" alt="Cover ${this.escapeHtml(album.title)}" class="data-table__cover-image">`
            : `<div class="cover-placeholder">💿</div>`;
        
        tdTitle.innerHTML = `
            <div class="data-table__title-wrapper">
                <div class="data-table__title-cover">
                    ${coverHtml}
                </div>
                <div class="data-table__title-meta">
                    <div class="data-table__song-name">${this.escapeHtml(album.title)}</div>
                </div>
            </div>
        `;
        tr.appendChild(tdTitle);

        // Colonne Streams totaux (format entier FR)
        const tdStreamsTotal = document.createElement('td');
        tdStreamsTotal.className = 'data-table__cell--numeric cell-num';
        tdStreamsTotal.setAttribute('data-sort-value', 'streams_total');
        tdStreamsTotal.setAttribute('data-sort-raw', album.streams_total);
        tdStreamsTotal.textContent = formatIntFr(album.streams_total);
        tr.appendChild(tdStreamsTotal);

        // Colonne Streams quotidiens (format entier FR)
        const tdStreamsDaily = document.createElement('td');
        tdStreamsDaily.className = 'data-table__cell--numeric cell-num';
        tdStreamsDaily.setAttribute('data-sort-value', 'streams_daily');
        tdStreamsDaily.setAttribute('data-sort-raw', album.streams_daily);
        tdStreamsDaily.textContent = formatIntFr(album.streams_daily);
        tr.appendChild(tdStreamsDaily);

        // Colonne Variation (%) - Pipeline Caps, condition triple pour 0 neutre (Prompt 7.10)
        const tdVariation = document.createElement('td');
        tdVariation.className = 'data-table__cell--numeric cell-num';
        tdVariation.setAttribute('data-sort-value', 'variation');
        
        // Gérer les valeurs manquantes correctement
        const variationValue = album.variation_pct;
        const isValidNumber = variationValue !== null && variationValue !== undefined && !isNaN(variationValue);
        
        if (isValidNumber) {
            tdVariation.setAttribute('data-sort-raw', variationValue);
            const variationText = formatPercent(variationValue);
            const value = Number(variationValue);
            
            // Triple condition : >0 vert, <0 rouge, =0 gris
            if (value > 0) {
                tdVariation.innerHTML = `<span class="data-table__delta--positive">${variationText}</span>`;
            } else if (value < 0) {
                tdVariation.innerHTML = `<span class="data-table__delta--negative">${variationText}</span>`;
            } else {
                tdVariation.innerHTML = `<span class="data-table__delta--neutral">${variationText}</span>`;
            }
        } else {
            // "Non mis-à-jour" : classe muted, valeur sentinelle pour tri (nulls last)
            tdVariation.setAttribute('data-sort-raw', 'null'); // Valeur sentinelle
            tdVariation.innerHTML = `<span class="data-table__delta--na">${formatPercent(null)}</span>`;
        }
        tr.appendChild(tdVariation);

        // Colonne Prochain cap (j)
        const tdDaysToCap = document.createElement('td');
        tdDaysToCap.className = 'data-table__cell--numeric cell-num';
        tdDaysToCap.setAttribute('data-sort-value', 'days_to_next_cap');
        tdDaysToCap.setAttribute('data-sort-raw', album.days_to_next_cap || 999999);
        tdDaysToCap.textContent = formatDays(album.days_to_next_cap);
        tr.appendChild(tdDaysToCap);

        // Colonne Prochain palier
        const tdNextCap = document.createElement('td');
        tdNextCap.className = 'data-table__cell--numeric cell-num';
        tdNextCap.setAttribute('data-sort-value', 'next_cap');
        tdNextCap.setAttribute('data-sort-raw', album.next_cap_value); // Valeur numérique pour tri correct
        tdNextCap.textContent = formatCap(album.next_cap_value);
        tr.appendChild(tdNextCap);

        return tr;
    }

    /**
     * Génère et positionne les badges de mouvement de rang dans le rail overlay
     * @param {string} tableSelector - Sélecteur CSS de la table (ex: '#page-songs .data-table--songs')
     * @param {Array} items - Tableau des chansons/albums avec rank_delta
     */
    /**
     * Affiche un message d'erreur léger
     */
    showError(context) {
        // TODO: Implémenter une notification légère
        console.error(`Erreur de chargement: ${context}`);
    }

    /**
     * Échappe les caractères HTML
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Initialise le rendu pour la page courante
     * Prompt 8.7 : renderAggregates() appelé APRÈS renderTable() car les cartes
     * calculent depuis les lignes DOM maintenant, pas depuis meta.json
     */
    async initCurrentPage(pageName) {
        this.currentPage = pageName;

        if (pageName === 'songs') {
            await this.renderSongsTable();
            // Les agrégats seront calculés après le render via RAF dans renderSongsTable
        } else if (pageName === 'albums') {
            await this.renderAlbumsTable();
            // Les agrégats seront calculés après le render via RAF dans renderAlbumsTable
        }
    }

    /**
     * Rafraîchit les données de la page courante
     */
    async refreshCurrentPage() {
        console.log(`🔄 Rafraîchissement page: ${this.currentPage}`);
        await this.initCurrentPage(this.currentPage);
    }
}

// Instance singleton
const dataRenderer = new DataRenderer();
window.dataRenderer = dataRenderer;
