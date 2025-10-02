/**
 * Module de chargement des données JSON
 * Gère le cache, les retries, et les événements de mise à jour
 */

class DataLoader {
    constructor() {
        this.cache = {
            songs: null,
            albums: null,
            meta: null,
            lastFetch: {
                songs: null,
                albums: null,
                meta: null
            }
        };
        this.isLoading = {
            songs: false,
            albums: false,
            meta: false
        };
        this.CACHE_DURATION = 5000; // 5 secondes
        this.MAX_RETRIES = 3;
        this.RETRY_DELAY = 1000; // 1 seconde
    }

    /**
     * Charge les données songs.json avec cache et retry
     */
    async loadSongs(forceRefresh = false) {
        // Vérifier le cache
        if (!forceRefresh && this.cache.songs && this._isCacheValid('songs')) {
            return this.cache.songs;
        }

        // Éviter les requêtes simultanées
        if (this.isLoading.songs) {
            return this._waitForLoad('songs');
        }

        this.isLoading.songs = true;

        try {
            const data = await this._fetchWithRetry('/data/songs.json');
            this.cache.songs = data;
            this.cache.lastFetch.songs = Date.now();
            this._emitDataLoaded('songs', data);
            return data;
        } catch (error) {
            console.error('❌ Erreur chargement songs.json:', error);
            this._emitLoadError('songs', error);
            // Retourner le cache si disponible, sinon erreur
            if (this.cache.songs) {
                console.warn('⚠️ Utilisation du cache songs.json');
                return this.cache.songs;
            }
            throw error;
        } finally {
            this.isLoading.songs = false;
        }
    }

    /**
     * Charge les données albums.json avec cache et retry
     */
    async loadAlbums(forceRefresh = false) {
        // Vérifier le cache
        if (!forceRefresh && this.cache.albums && this._isCacheValid('albums')) {
            return this.cache.albums;
        }

        // Éviter les requêtes simultanées
        if (this.isLoading.albums) {
            return this._waitForLoad('albums');
        }

        this.isLoading.albums = true;

        try {
            const data = await this._fetchWithRetry('/data/albums.json');
            this.cache.albums = data;
            this.cache.lastFetch.albums = Date.now();
            this._emitDataLoaded('albums', data);
            return data;
        } catch (error) {
            console.error('❌ Erreur chargement albums.json:', error);
            this._emitLoadError('albums', error);
            // Retourner le cache si disponible, sinon erreur
            if (this.cache.albums) {
                console.warn('⚠️ Utilisation du cache albums.json');
                return this.cache.albums;
            }
            throw error;
        } finally {
            this.isLoading.albums = false;
        }
    }

    /**
     * Charge les données meta.json avec cache et retry
     */
    async loadMeta(forceRefresh = false) {
        // Vérifier le cache
        if (!forceRefresh && this.cache.meta && this._isCacheValid('meta')) {
            return this.cache.meta;
        }

        // Éviter les requêtes simultanées
        if (this.isLoading.meta) {
            return this._waitForLoad('meta');
        }

        this.isLoading.meta = true;

        try {
            const data = await this._fetchWithRetry('/data/meta.json');
            this.cache.meta = data;
            this.cache.lastFetch.meta = Date.now();
            this._emitDataLoaded('meta', data);
            return data;
        } catch (error) {
            console.error('❌ Erreur chargement meta.json:', error);
            this._emitLoadError('meta', error);
            // Retourner le cache si disponible, sinon erreur
            if (this.cache.meta) {
                console.warn('⚠️ Utilisation du cache meta.json');
                return this.cache.meta;
            }
            throw error;
        } finally {
            this.isLoading.meta = false;
        }
    }

    /**
     * Invalide le cache pour forcer un rechargement
     */
    invalidateCache(type = 'all') {
        if (type === 'all' || type === 'songs') {
            this.cache.songs = null;
            this.cache.lastFetch.songs = null;
        }
        if (type === 'all' || type === 'albums') {
            this.cache.albums = null;
            this.cache.lastFetch.albums = null;
        }
        if (type === 'all' || type === 'meta') {
            this.cache.meta = null;
            this.cache.lastFetch.meta = null;
        }
        console.log(`🔄 Cache invalidé: ${type}`);
    }

    /**
     * Fetch avec retry et backoff exponentiel
     */
    async _fetchWithRetry(url, retries = this.MAX_RETRIES) {
        for (let attempt = 1; attempt <= retries; attempt++) {
            try {
                // Cache-busting avec timestamp
                const cacheBuster = `?t=${Date.now()}`;
                const response = await fetch(url + cacheBuster);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                
                if (attempt > 1) {
                    console.log(`✅ Succès après ${attempt} tentatives: ${url}`);
                }
                
                return data;
            } catch (error) {
                const isLastAttempt = attempt === retries;
                
                if (isLastAttempt) {
                    throw error;
                }
                
                const delay = this.RETRY_DELAY * Math.pow(2, attempt - 1);
                console.warn(`⚠️ Tentative ${attempt}/${retries} échouée: ${url}. Retry dans ${delay}ms...`);
                await this._sleep(delay);
            }
        }
    }

    /**
     * Vérifie si le cache est encore valide
     */
    _isCacheValid(type) {
        const lastFetch = this.cache.lastFetch[type];
        if (!lastFetch) return false;
        return (Date.now() - lastFetch) < this.CACHE_DURATION;
    }

    /**
     * Attend qu'un chargement en cours se termine
     */
    async _waitForLoad(type) {
        let attempts = 0;
        const maxAttempts = 50; // 5 secondes max
        
        while (this.isLoading[type] && attempts < maxAttempts) {
            await this._sleep(100);
            attempts++;
        }
        
        return this.cache[type];
    }

    /**
     * Émet un événement de données chargées
     */
    _emitDataLoaded(type, data) {
        const event = new CustomEvent('data-loaded', {
            detail: { type, data, timestamp: Date.now() }
        });
        window.dispatchEvent(event);
    }

    /**
     * Émet un événement d'erreur de chargement
     */
    _emitLoadError(type, error) {
        const event = new CustomEvent('data-load-error', {
            detail: { type, error: error.message, timestamp: Date.now() }
        });
        window.dispatchEvent(event);
    }

    /**
     * Utilitaire sleep
     */
    _sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Obtenir les statistiques du cache
     */
    getCacheStats() {
        return {
            songs: {
                cached: !!this.cache.songs,
                count: this.cache.songs?.length || 0,
                lastFetch: this.cache.lastFetch.songs,
                valid: this._isCacheValid('songs')
            },
            albums: {
                cached: !!this.cache.albums,
                count: this.cache.albums?.length || 0,
                lastFetch: this.cache.lastFetch.albums,
                valid: this._isCacheValid('albums')
            },
            meta: {
                cached: !!this.cache.meta,
                lastFetch: this.cache.lastFetch.meta,
                valid: this._isCacheValid('meta')
            }
        };
    }

    /**
     * Getter pour accéder au cache (compatibilité avec code existant)
     */
    get cachedData() {
        return {
            songs: this.cache.songs,
            albums: this.cache.albums,
            meta: this.cache.meta
        };
    }
}

// Instance singleton
const dataLoader = new DataLoader();

// Export pour utilisation dans d'autres modules
window.dataLoader = dataLoader;
