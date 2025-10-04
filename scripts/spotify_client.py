"""
Client Spotify API avec Client C            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"WARNING Erreur chargement cache: {e}")tials Flow
Cache des réponses + gestion rate limiting (429)
"""

import os
import time
import json
import hashlib
import requests
from pathlib import Path
from typing import Optional, Dict, List, Any


class SpotifyClient:
    """Client Spotify API avec cache et rate limiting"""
    
    BASE_URL = "https://api.spotify.com/v1"
    AUTH_URL = "https://accounts.spotify.com/api/token"
    
    def __init__(self, client_id: str, client_secret: str, market: str = "US"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.market = market
        self.access_token: Optional[str] = None
        self.token_expires_at: float = 0
        
        # Cache directory
        self.cache_dir = Path(__file__).parent.parent / "data" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "spotify_api_cache.json"
        self.cache: Dict[str, Any] = self._load_cache()
    
    def _load_cache(self) -> Dict[str, Any]:
        """Charge le cache depuis le fichier JSON"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"WARNING Erreur chargement cache: {e}")
        return {}
    
    def _save_cache(self):
        """Sauvegarde le cache dans le fichier JSON"""
        cache_path = Path("data/cache/spotify_api_cache.json")
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, indent=2)
        except Exception as e:
            print(f"WARNING Erreur sauvegarde cache: {e}")
    
    def _cache_key(self, endpoint: str, params: Dict) -> str:
        """Génère une clé de cache MD5 unique"""
        key_str = f"{endpoint}:{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _get_access_token(self) -> str:
        """Obtient un access token via Client Credentials Flow"""
        # Réutiliser le token si encore valide
        if self.access_token and time.time() < self.token_expires_at:
            return self.access_token
        
        # Requête nouveau token
        response = requests.post(
            self.AUTH_URL,
            data={"grant_type": "client_credentials"},
            auth=(self.client_id, self.client_secret),
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        self.access_token = data["access_token"]
        # Expiration avec marge de sécurité (5 min avant)
        self.token_expires_at = time.time() + data["expires_in"] - 300
        
        return self.access_token
    
    def _request(self, endpoint: str, params: Optional[Dict] = None, use_cache: bool = True) -> Dict:
        """Effectue une requête à l'API Spotify avec retry sur 429"""
        params = params or {}
        params["market"] = self.market
        
        # Vérifier le cache
        cache_key = self._cache_key(endpoint, params)
        if use_cache and cache_key in self.cache:
            return self.cache[cache_key]
        
        # Requête API avec retry
        max_retries = 3
        for attempt in range(max_retries):
            try:
                token = self._get_access_token()
                headers = {"Authorization": f"Bearer {token}"}
                
                response = requests.get(
                    f"{self.BASE_URL}/{endpoint}",
                    headers=headers,
                    params=params,
                    timeout=10
                )
                
                # Gestion rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 2))
                    print(f"⏳ Rate limit atteint, attente {retry_after}s...")
                    time.sleep(retry_after)
                    continue
                
                response.raise_for_status()
                data = response.json()
                
                # Mettre en cache
                self.cache[cache_key] = data
                self._save_cache()
                
                return data
                
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise
                print(f"WARNING Tentative {attempt + 1}/{max_retries} echouee: {e}")
                time.sleep(2 ** attempt)  # Backoff exponentiel
        
        return {}
    
    def search_track(self, query: str, artist: str = "The Weeknd", limit: int = 10) -> List[Dict]:
        """
        Recherche une piste sur Spotify
        
        Args:
            query: Nom de la piste (sera normalisé)
            artist: Nom de l'artiste (défaut: The Weeknd)
            limit: Nombre de résultats max
        
        Returns:
            Liste de tracks avec leurs albums
        """
        # Construction de la query avec guillemets pour exactitude
        search_query = f'track:"{query}" artist:"{artist}"'
        
        params = {
            "q": search_query,
            "type": "track",
            "limit": limit
        }
        
        try:
            response = self._request("search", params)
            return response.get("tracks", {}).get("items", [])
        except Exception as e:
            print(f"ERREUR recherche track '{query}': {e}")
            return []
    
    def get_album(self, album_id: str) -> Optional[Dict]:
        """
        Récupère les détails d'un album par son ID
        
        Args:
            album_id: ID Spotify de l'album
        
        Returns:
            Détails de l'album avec images HD
        """
        try:
            return self._request(f"albums/{album_id}")
        except Exception as e:
            print(f"ERREUR recuperation album '{album_id}': {e}")
            return None
    
    def search_album(self, query: str, artist: str = "The Weeknd", limit: int = 10) -> List[Dict]:
        """
        Recherche un album sur Spotify
        
        Args:
            query: Nom de l'album
            artist: Nom de l'artiste (défaut: The Weeknd)
            limit: Nombre de résultats max
        
        Returns:
            Liste d'albums
        """
        search_query = f'album:"{query}" artist:"{artist}"'
        
        params = {
            "q": search_query,
            "type": "album",
            "limit": limit
        }
        
        try:
            response = self._request("search", params)
            return response.get("albums", {}).get("items", [])
        except Exception as e:
            print(f"ERREUR recherche album '{query}': {e}")
            return []
