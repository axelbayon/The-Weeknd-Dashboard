/**
 * Module de recherche sticky pour les chansons
 * Permet de rechercher et naviguer vers une chanson depuis n'importe quelle page
 */

class StickySearch {
    constructor() {
        this.input = null;
        this.suggestionsContainer = null;
        this.songs = null;
        this.MIN_CHARS = 2;
        this.MAX_RESULTS = 10;
        this.HIGHLIGHT_DURATION = 3000; // 3 secondes
        this.selectedIndex = -1;
    }

    /**
     * Initialise la recherche sticky
     */
    init() {
        this.input = document.querySelector('#search-input');
        
        if (!this.input) {
            console.error('❌ Input de recherche introuvable');
            return;
        }

        // Créer le conteneur de suggestions
        this.createSuggestionsContainer();

        // Écouter les événements
        this.input.addEventListener('input', (e) => this.handleInput(e));
        this.input.addEventListener('keydown', (e) => this.handleKeyDown(e));
        this.input.addEventListener('focus', () => this.showSuggestions());
        
        // Fermer les suggestions en cliquant ailleurs
        document.addEventListener('click', (e) => {
            if (!this.input.contains(e.target) && !this.suggestionsContainer.contains(e.target)) {
                this.hideSuggestions();
            }
        });

        console.log('✅ Recherche sticky initialisée');
    }

    /**
     * Crée le conteneur de suggestions
     */
    createSuggestionsContainer() {
        this.suggestionsContainer = document.createElement('div');
        this.suggestionsContainer.className = 'search-suggestions';
        this.suggestionsContainer.setAttribute('data-testid', 'search-suggestions');
        this.suggestionsContainer.style.cssText = `
            position: absolute;
            bottom: 100%;
            left: 0;
            right: 0;
            max-height: 400px;
            overflow-y: auto;
            background: var(--color-surface-dark, #1a1a1a);
            border: 1px solid var(--color-border, #333);
            border-radius: 8px 8px 0 0;
            box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.3);
            display: none;
            z-index: 1000;
        `;

        // Insérer après la bottombar__inner
        const bottombarInner = this.input.closest('.bottombar__inner');
        if (bottombarInner) {
            bottombarInner.style.position = 'relative';
            bottombarInner.appendChild(this.suggestionsContainer);
        }
    }

    /**
     * Gère la saisie dans l'input
     */
    async handleInput(e) {
        const query = e.target.value.trim();

        if (query.length < this.MIN_CHARS) {
            this.hideSuggestions();
            return;
        }

        await this.search(query);
    }

    /**
     * Gère les touches clavier
     */
    handleKeyDown(e) {
        const suggestions = this.suggestionsContainer.querySelectorAll('.search-suggestion-item');
        
        if (suggestions.length === 0) return;

        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                this.selectedIndex = Math.min(this.selectedIndex + 1, suggestions.length - 1);
                this.updateSelection(suggestions);
                break;
            case 'ArrowUp':
                e.preventDefault();
                this.selectedIndex = Math.max(this.selectedIndex - 1, 0);
                this.updateSelection(suggestions);
                break;
            case 'Enter':
                e.preventDefault();
                if (this.selectedIndex >= 0 && suggestions[this.selectedIndex]) {
                    suggestions[this.selectedIndex].click();
                }
                break;
            case 'Escape':
                this.hideSuggestions();
                this.input.blur();
                break;
        }
    }

    /**
     * Met à jour la sélection visuelle
     */
    updateSelection(suggestions) {
        suggestions.forEach((item, index) => {
            if (index === this.selectedIndex) {
                item.classList.add('search-suggestion-item--selected');
                item.scrollIntoView({ block: 'nearest' });
            } else {
                item.classList.remove('search-suggestion-item--selected');
            }
        });
    }

    /**
     * Recherche des chansons
     */
    async search(query) {
        try {
            // Charger les chansons (avec cache)
            if (!this.songs) {
                this.songs = await window.dataLoader.loadSongs();
            }

            // Normaliser la requête
            const normalizedQuery = this.normalizeString(query);

            // Filtrer les chansons
            const results = this.songs.filter(song => {
                const normalizedTitle = this.normalizeString(song.title);
                const normalizedAlbum = this.normalizeString(song.album);
                return normalizedTitle.includes(normalizedQuery) || normalizedAlbum.includes(normalizedQuery);
            }).slice(0, this.MAX_RESULTS);

            this.displayResults(results, query);
        } catch (error) {
            console.error('❌ Erreur recherche:', error);
        }
    }

    /**
     * Normalise une chaîne pour la recherche
     */
    normalizeString(str) {
        return str.toLowerCase()
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, ''); // Retirer les accents
    }

    /**
     * Affiche les résultats de recherche
     */
    displayResults(results, query) {
        this.suggestionsContainer.innerHTML = '';
        this.selectedIndex = -1;

        if (results.length === 0) {
            const noResult = document.createElement('div');
            noResult.className = 'search-no-result';
            noResult.textContent = 'Aucun résultat';
            noResult.style.cssText = `
                padding: 16px;
                text-align: center;
                color: var(--color-text-secondary, #999);
                font-size: 14px;
            `;
            this.suggestionsContainer.appendChild(noResult);
            this.showSuggestions();
            return;
        }

        // Créer les items de suggestion
        results.forEach(song => {
            const item = this.createSuggestionItem(song, query);
            this.suggestionsContainer.appendChild(item);
        });

        this.showSuggestions();
    }

    /**
     * Crée un item de suggestion
     */
    createSuggestionItem(song, query) {
        const item = document.createElement('div');
        item.className = 'search-suggestion-item';
        item.setAttribute('data-testid', 'search-suggestion-item');
        item.setAttribute('data-song-id', song.id);
        
        item.style.cssText = `
            padding: 12px 16px;
            cursor: pointer;
            border-bottom: 1px solid var(--color-border, #333);
            transition: background-color 0.2s;
        `;

        // Highlight du texte correspondant
        const titleHighlighted = this.highlightMatch(song.title, query);
        const albumHighlighted = this.highlightMatch(song.album, query);

        item.innerHTML = `
            <div style="font-weight: 500; margin-bottom: 4px; color: var(--color-text-primary, #fff);">
                ${titleHighlighted}
            </div>
            <div style="font-size: 13px; color: var(--color-text-secondary, #999);">
                ${albumHighlighted}
            </div>
        `;

        // Hover
        item.addEventListener('mouseenter', () => {
            item.style.backgroundColor = 'var(--color-surface-hover, #2a2a2a)';
        });
        item.addEventListener('mouseleave', () => {
            if (!item.classList.contains('search-suggestion-item--selected')) {
                item.style.backgroundColor = '';
            }
        });

        // Clic
        item.addEventListener('click', () => {
            this.navigateToSong(song.id);
            this.hideSuggestions();
            this.input.value = '';
        });

        return item;
    }

    /**
     * Met en surbrillance les correspondances dans le texte
     */
    highlightMatch(text, query) {
        const normalizedText = this.normalizeString(text);
        const normalizedQuery = this.normalizeString(query);
        const index = normalizedText.indexOf(normalizedQuery);

        if (index === -1) {
            return this.escapeHtml(text);
        }

        const before = text.substring(0, index);
        const match = text.substring(index, index + query.length);
        const after = text.substring(index + query.length);

        return `${this.escapeHtml(before)}<mark style="background-color: #ff9800; color: #000; padding: 2px 4px; border-radius: 2px;">${this.escapeHtml(match)}</mark>${this.escapeHtml(after)}`;
    }

    /**
     * Navigue vers une chanson
     */
    navigateToSong(songId) {
        console.log(`🎯 Navigation vers chanson: ${songId}`);

        // Activer l'onglet Songs
        const songsLink = document.querySelector('[data-page="songs"]');
        if (songsLink) {
            songsLink.click();
        }

        // Attendre que la page soit chargée
        setTimeout(() => {
            const row = document.querySelector(`[data-row-id="${songId}"]`);
            
            if (row) {
                // Scroll vers la ligne
                row.scrollIntoView({ behavior: 'smooth', block: 'center' });
                
                // Ajouter highlight temporaire
                row.classList.add('search-highlight');
                row.style.cssText = `
                    background-color: rgba(255, 152, 0, 0.2) !important;
                    transition: background-color 0.3s;
                `;

                // Retirer le highlight après quelques secondes
                setTimeout(() => {
                    row.style.backgroundColor = '';
                    setTimeout(() => {
                        row.classList.remove('search-highlight');
                        row.style.cssText = '';
                    }, 300);
                }, this.HIGHLIGHT_DURATION);
            } else {
                console.warn(`⚠️ Ligne non trouvée: ${songId}`);
            }
        }, 300);
    }

    /**
     * Affiche les suggestions
     */
    showSuggestions() {
        if (this.suggestionsContainer.children.length > 0) {
            this.suggestionsContainer.style.display = 'block';
        }
    }

    /**
     * Cache les suggestions
     */
    hideSuggestions() {
        this.suggestionsContainer.style.display = 'none';
        this.selectedIndex = -1;
    }

    /**
     * Invalide le cache des chansons
     */
    invalidateCache() {
        this.songs = null;
    }

    /**
     * Échappe les caractères HTML
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Instance singleton
const stickySearch = new StickySearch();
window.stickySearch = stickySearch;

// Initialiser quand le DOM est prêt
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => stickySearch.init());
} else {
    stickySearch.init();
}
