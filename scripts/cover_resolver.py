"""
Résolveur de covers Spotify avec règles métier strictes
Gère : Original vs Deluxe, Trilogy, Mixtapes, BO, Singles, Live, Feat
"""

import re
from typing import Optional, Dict, List, Tuple
from spotify_client import SpotifyClient


class CoverResolver:
    """Résout la cover appropriée selon les règles métier"""
    
    # Blacklist : ne jamais utiliser ces albums pour les chansons
    ALBUM_BLACKLIST = ["the highlights"]
    
    # Albums à supprimer complètement de l'affichage
    ALBUMS_TO_REMOVE = ["Avatar", "Music"]
    
    # Trilogy allowlist : seules ces 3 chansons prennent la cover Trilogy
    TRILOGY_SONGS = [
        "Twenty Eight",
        "Valerie", 
        "Till Dawn (Here Comes the Sun)"
    ]
    
    # Mapping explicite : titre → album exact
    EXPLICIT_MAPPINGS = {
        # Trilogy mixtapes originales
        "High For This": "House Of Balloons (Original)",
        "What You Need": "House Of Balloons (Original)",
        "House of Balloons / Glass Table Girls": "House Of Balloons (Original)",
        "The Morning": "House Of Balloons (Original)",
        "Wicked Games": "House Of Balloons (Original)",
        "The Party & The After Party": "House Of Balloons (Original)",
        "Coming Down": "House Of Balloons (Original)",
        "Loft Music": "House Of Balloons (Original)",
        "The Knowing": "House Of Balloons (Original)",
        
        "Lonely Star": "Thursday (Original)",
        "Life of the Party": "Thursday (Original)",
        "Thursday": "Thursday (Original)",
        "The Zone": "Thursday (Original)",
        "The Birds Part 1": "Thursday (Original)",
        "The Birds Part 2": "Thursday (Original)",
        "The Birds Pt. 2": "Thursday (Original)",
        "Gone": "Thursday (Original)",
        "Rolling Stone": "Thursday (Original)",
        "Heaven or Las Vegas": "Thursday (Original)",
        
        "D.D.": "Echoes Of Silence (Original)",
        "Montreal": "Echoes Of Silence (Original)",
        "Outside": "Echoes Of Silence (Original)",
        "XO / The Host": "Echoes Of Silence (Original)",
        "Initiation": "Echoes Of Silence (Original)",
        "Same Old Song": "Echoes Of Silence (Original)",
        "The Fall": "Echoes Of Silence (Original)",
        "Next": "Echoes Of Silence (Original)",
        "Echoes of Silence": "Echoes Of Silence (Original)",
        
        # Cas spéciaux
        "Save Your Tears": "After Hours",  # Original sur After Hours
        "Save Your Tears (Remix)": "After Hours (Deluxe)",
        "In Your Eyes (Remix)": "After Hours (Deluxe)",
        
        "Moth To A Flame": "Paradise Again",  # Swedish House Mafia
        "*Moth To A Flame (with The Weeknd)": "Paradise Again",  # Swedish House Mafia
        "*Love Me Harder (with The Weeknd)": "My Everything (Deluxe)",  # Ariana Grande
        "Love Me Harder": "My Everything (Deluxe)",  # Ariana Grande
        "*Love Me Harder - Alex Ghenea Remix": "My Everything (Deluxe)",  # Ariana Grande
        "Live For": "Kiss Land",
        "*Wild Love": "9",  # Cashmere Cat
        
        # Bandes originales (titres complets avec "from..." comme dans les données)
        "Elastic Heart": "The Hunger Games: Catching Fire (Original Motion Picture Soundtrack)",
        "*Elastic Heart": "The Hunger Games: Catching Fire (Original Motion Picture Soundtrack)",
        "*Elastic Heart - From \"The Hunger Games: Catching Fire\" Soundtrack": "The Hunger Games: Catching Fire (Original Motion Picture Soundtrack)",
        "Where You Belong": "Fifty Shades of Grey (Original Motion Picture Soundtrack)",
        "Where You Belong - From \"Fifty Shades Of Grey\" Soundtrack": "Fifty Shades of Grey (Original Motion Picture Soundtrack)",
        "Devil May Cry": "The Hunger Games: Catching Fire (Original Motion Picture Soundtrack)",
        "Devil May Cry - From \"The Hunger Games: Catching Fire\" Soundtrack": "The Hunger Games: Catching Fire (Original Motion Picture Soundtrack)",
        "Nothing Is Lost (You Give Me Strength)": "Avatar: The Way of Water (Original Motion Picture Soundtrack)",
        
        # Singles récents
        "Dancing In The Flames": "Dancing In The Flames",
        "Timeless": "Timeless",
    }
    
    # Mappings nécessitant un artiste spécifique (pas The Weeknd)
    ARTIST_OVERRIDES = {
        "My Everything (Deluxe)": "Ariana Grande",
        "Paradise Again": "Swedish House Mafia",
        "Moth To A Flame": "Swedish House Mafia",
        "9": "Cashmere Cat",
        "The Hunger Games: Catching Fire (Original Motion Picture Soundtrack)": "Various Artists",
        "Fifty Shades of Grey (Original Motion Picture Soundtrack)": "Various Artists",
        "Avatar: The Way of Water (Original Motion Picture Soundtrack)": "Various Artists",
    }
    
    # IDs Spotify directs pour albums difficiles à trouver (OST, etc.)
    DIRECT_ALBUM_IDS = {
        "Avatar: The Way of Water (Original Motion Picture Soundtrack)": "4M2Mf4pmARKGVT9MLCe3HA",
        "The Hunger Games: Catching Fire (Original Motion Picture Soundtrack)": "38qFiy7n8yWm2Qm91vyx0j",
        "Fifty Shades of Grey (Original Motion Picture Soundtrack)": "4gnEi23PFBwHXT9rMqTsN5",
    }
    
    def __init__(self, spotify_client: SpotifyClient):
        self.client = spotify_client
    
    def normalize_title(self, title: str) -> str:
        """
        Normalise le titre pour la recherche Spotify
        - Retire * (featuring) et ^ (compilation) au début
        - Retire " - from ..." et "(from ...)"
        - Conserve (Remix), (Live), Instrumental
        """
        # Retirer * et ^ au début
        title = re.sub(r'^[\*\^]\s*', '', title).strip()
        
        # Retirer segments "from"
        title = re.sub(r'\s*[-–]\s*from\s+["\'].*?["\']', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s*\(from\s+["\'].*?["\']\)', '', title, flags=re.IGNORECASE)
        
        return title.strip()
    
    def is_blacklisted_album(self, album_name: str) -> bool:
        """Vérifie si l'album est dans la blacklist"""
        album_lower = album_name.lower()
        return any(blacklisted in album_lower for blacklisted in self.ALBUM_BLACKLIST)
    
    def should_remove_album(self, album_name: str) -> bool:
        """Vérifie si l'album doit être supprimé de l'affichage"""
        return album_name in self.ALBUMS_TO_REMOVE
    
    def is_the_weeknd_lead(self, track: Dict) -> bool:
        """Vérifie si The Weeknd est l'artiste principal (premier dans la liste)"""
        artists = track.get("artists", [])
        if not artists:
            return False
        return "the weeknd" in artists[0].get("name", "").lower()
    
    def get_best_cover_for_track(self, title: str, is_lead: bool = True) -> Optional[Dict]:
        """
        Résout la meilleure cover pour une piste selon les règles métier
        
        Returns:
            Dict avec {cover_url, album_id, album_name} ou None
        """
        # Normaliser le titre
        normalized_title = self.normalize_title(title)
        
        # Vérifier les mappings explicites d'abord
        if title in self.EXPLICIT_MAPPINGS:
            target_album = self.EXPLICIT_MAPPINGS[title]
            return self._find_album_cover(target_album)
        
        # Cas spécial Trilogy : allowlist
        if title in self.TRILOGY_SONGS:
            return self._find_album_cover("Trilogy")
        
        # Rechercher la piste sur Spotify
        tracks = self.client.search_track(normalized_title)
        
        if not tracks:
            print(f"WARNING Aucun resultat pour '{title}'")
            return None
        
        # Filtrer et scorer les résultats
        candidates = []
        for track in tracks:
            # Vérifier correspondance titre
            track_name = track.get("name", "")
            if not self._titles_match(normalized_title, track_name):
                continue
            
            # Vérifier rôle lead/feat
            if is_lead and not self.is_the_weeknd_lead(track):
                continue
            if not is_lead and self.is_the_weeknd_lead(track):
                continue
            
            album = track.get("album", {})
            album_name = album.get("name", "")
            
            # Exclure albums blacklistés
            if self.is_blacklisted_album(album_name):
                continue
            
            # Scorer
            score = self._score_album(album, title)
            candidates.append((score, track, album))
        
        if not candidates:
            print(f"WARNING Aucun candidat valide pour '{title}'")
            return None
        
        # Trier par score décroissant
        candidates.sort(key=lambda x: x[0], reverse=True)
        best_track, best_album = candidates[0][1], candidates[0][2]
        
        return self._extract_cover(best_album)
    
    def _titles_match(self, title1: str, title2: str) -> bool:
        """Compare deux titres (case-insensitive, accents ignorés)"""
        def clean(s):
            s = s.lower()
            s = re.sub(r'[àáâãäå]', 'a', s)
            s = re.sub(r'[èéêë]', 'e', s)
            s = re.sub(r'[ìíîï]', 'i', s)
            s = re.sub(r'[òóôõö]', 'o', s)
            s = re.sub(r'[ùúûü]', 'u', s)
            return s
        
        return clean(title1) == clean(title2)
    
    def _score_album(self, album: Dict, original_title: str) -> float:
        """
        Score un album selon les règles de priorité
        Score plus élevé = meilleur choix
        """
        score = 0.0
        album_name = album.get("name", "").lower()
        album_type = album.get("album_type", "")
        
        # Bonus : album studio > single > compilation
        if album_type == "album":
            score += 100
        elif album_type == "single":
            score += 50
        elif album_type == "compilation":
            score += 10
        
        # Malus : Deluxe (sauf si explicitement demandé)
        if "deluxe" in album_name:
            if "remix" in original_title.lower():
                score += 20  # Bonus si c'est un remix
            else:
                score -= 30  # Malus sinon
        
        # Malus : Live (sauf si titre contient "live")
        if "live" in album_name:
            if "live" in original_title.lower():
                score += 50
            else:
                score -= 50
        
        # Malus : Remixes/Instrumental
        if "remix" in album_name and "remix" not in original_title.lower():
            score -= 40
        if "instrumental" in album_name and "instrumental" not in original_title.lower():
            score -= 40
        
        # Bonus : correspondance exacte nom album dans titre
        if album_name in original_title.lower():
            score += 30
        
        # Popularité (si disponible)
        popularity = album.get("popularity", 0)
        score += popularity * 0.1
        
        return score
    
    def _find_album_cover(self, album_name: str) -> Optional[Dict]:
        """Recherche un album spécifique par nom et retourne sa cover"""
        # Si un ID direct existe, l'utiliser directement
        if album_name in self.DIRECT_ALBUM_IDS:
            album_id = self.DIRECT_ALBUM_IDS[album_name]
            album_data = self.client.get_album(album_id)
            if album_data:
                return self._extract_cover(album_data)
        
        # Sinon, chercher par nom
        artist = self.ARTIST_OVERRIDES.get(album_name, "The Weeknd")
        albums = self.client.search_album(album_name, artist)
        
        # Si on cherche un album sans "Live" dans le nom, filtrer les lives
        exclude_live = 'live' not in album_name.lower()
        
        for album in albums:
            album_result_name = album.get("name", "")
            
            # Exclure les albums live si on cherche un album studio
            if exclude_live and 'live' in album_result_name.lower():
                continue
            
            # Match exact (insensible à la casse)
            if album_result_name.lower() == album_name.lower():
                return self._extract_cover(album)
        
        print(f"WARNING Album '{album_name}' non trouve")
        return None
    
    def _extract_cover(self, album: Dict) -> Dict:
        """Extrait les infos cover d'un album"""
        images = album.get("images", [])
        cover_url = images[0]["url"] if images else None
        
        return {
            "cover_url": cover_url,
            "album_id": album.get("id"),
            "album_name": album.get("name")
        }
    
    def get_cover_for_album(self, album_name: str) -> Optional[Dict]:
        """
        Résout la cover pour un album (page Albums)
        Différencie After Hours vs After Hours (Deluxe)
        """
        # Vérifier si l'album doit être supprimé
        if self.should_remove_album(album_name):
            return None
        
        # Normaliser le nom (retirer ^)
        normalized_name = self.normalize_title(album_name)
        
        # Rechercher l'album exact
        albums = self.client.search_album(normalized_name)
        
        # Chercher correspondance exacte
        for album in albums:
            if album.get("name", "").lower() == normalized_name.lower():
                return self._extract_cover(album)
        
        print(f"WARNING Album '{album_name}' non trouve")
        return None
