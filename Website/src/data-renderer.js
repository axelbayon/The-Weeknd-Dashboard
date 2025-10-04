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
    }

    /**
     * Calcule et rend les agrégats de la page Songs
     */
    async renderSongsAggregates() {
        try {
            // Charger meta.json ET songs.json pour garantir les dernières valeurs
            const [songs, meta] = await Promise.all([
                window.dataLoader.loadSongs(),
                window.dataLoader.loadMeta()
            ]);
            
            if (!songs || songs.length === 0) {
                console.warn('⚠️ Aucune chanson à afficher');
                return;
            }

            const stats = this.calculateSongsStats(songs, meta);
            this.updateSongsAggregatesUI(stats);
            
            console.log('✅ Agrégats Songs mis à jour:', stats);
        } catch (error) {
            console.error('❌ Erreur rendu agrégats Songs:', error);
            this.showError('songs-aggregates');
        }
    }

    /**
     * Calcule les statistiques des chansons depuis meta.json
     * Utilise songs_role_stats si disponible, sinon recalcule depuis songs
     */
    calculateSongsStats(songs, meta = null) {
        // Utiliser meta passé en paramètre, sinon fallback sur cache
        if (!meta) {
            meta = window.dataLoader?.cachedData?.meta || {};
        }
        
        const roleStats = meta.songs_role_stats;
        
        if (roleStats && roleStats.lead && roleStats.feat) {
            // Utiliser les stats exactes de Kworb
            const lead = {
                count: roleStats.lead.count,
                totalStreams: roleStats.lead.streams_total,
                dailyStreams: roleStats.lead.streams_daily
            };
            
            const feat = {
                count: roleStats.feat.count,
                totalStreams: roleStats.feat.streams_total,
                dailyStreams: roleStats.feat.streams_daily
            };
            
            const total = lead.count + feat.count;
            const totalStreams = lead.totalStreams + feat.totalStreams;
            const dailyStreams = lead.dailyStreams + feat.dailyStreams;
            
            console.log('[Stats] Utilisation des stats Kworb exactes depuis meta.json');
            console.log(`  Lead: ${lead.count} songs, ${lead.totalStreams} total, ${lead.dailyStreams} daily`);
            console.log(`  Feat: ${feat.count} songs, ${feat.totalStreams} total, ${feat.dailyStreams} daily`);
            
            return {
                total,
                totalStreams,
                dailyStreams,
                lead,
                feat
            };
        }
        
        // Fallback : recalculer depuis songs array (ancienne méthode)
        console.warn('[Stats] songs_role_stats non disponible dans meta.json, recalcul depuis songs[]');
        
        const total = songs.length;
        
        let totalStreams = 0;
        let dailyStreams = 0;
        
        let leadCount = 0;
        let leadTotalStreams = 0;
        let leadDailyStreams = 0;
        
        let featCount = 0;
        let featTotalStreams = 0;
        let featDailyStreams = 0;

        songs.forEach(song => {
            const streams_total = Number(song.streams_total) || 0;
            const streams_daily = Number(song.streams_daily) || 0;
            
            totalStreams += streams_total;
            dailyStreams += streams_daily;

            if (song.role === 'lead') {
                leadCount++;
                leadTotalStreams += streams_total;
                leadDailyStreams += streams_daily;
            } else if (song.role === 'feat') {
                featCount++;
                featTotalStreams += streams_total;
                featDailyStreams += streams_daily;
            }
        });

        return {
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
     * Calcule et rend les agrégats de la page Albums
     */
    async renderAlbumsAggregates() {
        try {
            const albums = await window.dataLoader.loadAlbums();
            
            if (!albums || albums.length === 0) {
                console.warn('⚠️ Aucun album à afficher');
                return;
            }

            const stats = this.calculateAlbumsStats(albums);
            this.updateAlbumsAggregatesUI(stats);
            
            console.log('✅ Agrégats Albums mis à jour:', stats);
        } catch (error) {
            console.error('❌ Erreur rendu agrégats Albums:', error);
            this.showError('albums-aggregates');
        }
    }

    /**
     * Calcule les statistiques des albums
     */
    calculateAlbumsStats(albums) {
        const total = albums.length;
        let totalStreams = 0;
        let dailyStreams = 0;

        albums.forEach(album => {
            totalStreams += Number(album.streams_total) || 0;
            dailyStreams += Number(album.streams_daily) || 0;
        });

        return {
            total,
            totalStreams,
            dailyStreams
        };
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

            // Vider le tbody
            tbody.innerHTML = '';

            // Générer les lignes
            sortedSongs.forEach((song, index) => {
                const row = this.createSongRow(song, index + 1);
                tbody.appendChild(row);
            });

            this.lastRenderedData.songs = songs;
            console.log(`✅ Table Songs rendue: ${sortedSongs.length} lignes`);

            // Réinitialiser le tri (table-sort.js)
            if (window.tableSort) {
                window.tableSort.reinitTable('songs');
            }
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
        
        tdTitle.innerHTML = `
            <div class="data-table__title-wrapper">
                <div class="data-table__title-cover">
                    ${coverHtml}
                </div>
                <div class="data-table__title-meta">
                    <div class="data-table__song-name">${this.escapeHtml(song.title)}</div>
                    <span class="data-table__album">${this.escapeHtml(song.album)}</span>
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
        const isValidNumber = variationValue !== null && variationValue !== undefined && !isNaN(variationValue);
        
        if (isValidNumber) {
            tdVariation.setAttribute('data-sort-raw', variationValue);
            const variationText = formatPercent(variationValue);
            const value = Number(variationValue);
            
            // Triple condition : >0 vert, <0 rouge, =0 gris (Prompt 7.10)
            if (value > 0) {
                tdVariation.innerHTML = `<span class="data-table__delta--positive">${variationText}</span>`;
            } else if (value < 0) {
                tdVariation.innerHTML = `<span class="data-table__delta--negative">${variationText}</span>`;
            } else {
                tdVariation.innerHTML = `<span class="data-table__delta--neutral">${variationText}</span>`;
            }
        } else {
            // N.D. : classe neutre, pas de data-sort-raw (ou valeur sentinelle)
            tdVariation.setAttribute('data-sort-raw', '');
            tdVariation.innerHTML = `<span class="data-table__delta--na">N.D.</span>`;
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

            // Vider le tbody
            tbody.innerHTML = '';

            // Générer les lignes
            sortedAlbums.forEach((album, index) => {
                const row = this.createAlbumRow(album, index + 1);
                tbody.appendChild(row);
            });

            this.lastRenderedData.albums = albums;
            console.log(`✅ Table Albums rendue: ${sortedAlbums.length} lignes`);

            // Réinitialiser le tri (table-sort.js)
            if (window.tableSort) {
                window.tableSort.reinitTable('albums');
            }
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
            
            // Triple condition : >0 vert, <0 rouge, =0 gris (Prompt 7.10)
            if (value > 0) {
                tdVariation.innerHTML = `<span class="data-table__delta--positive">${variationText}</span>`;
            } else if (value < 0) {
                tdVariation.innerHTML = `<span class="data-table__delta--negative">${variationText}</span>`;
            } else {
                tdVariation.innerHTML = `<span class="data-table__delta--neutral">${variationText}</span>`;
            }
        } else {
            // N.D. : classe neutre, pas de data-sort-raw (ou valeur sentinelle)
            tdVariation.setAttribute('data-sort-raw', '');
            tdVariation.innerHTML = `<span class="data-table__delta--na">N.D.</span>`;
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
     */
    async initCurrentPage(pageName) {
        this.currentPage = pageName;

        if (pageName === 'songs') {
            await Promise.all([
                this.renderSongsAggregates(),
                this.renderSongsTable()
            ]);
        } else if (pageName === 'albums') {
            await Promise.all([
                this.renderAlbumsAggregates(),
                this.renderAlbumsTable()
            ]);
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
