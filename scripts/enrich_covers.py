"""
Script d'enrichissement des covers Spotify
Lit songs.json et albums.json, enrichit avec cover_url via API Spotify
"""

import os
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ajouter le dossier scripts au path
sys.path.insert(0, str(Path(__file__).parent))

from spotify_client import SpotifyClient
from cover_resolver import CoverResolver


def load_env():
    """Charge les variables d'environnement depuis .env.local"""
    env_path = Path(__file__).parent.parent / ".env.local"
    if not env_path.exists():
        print("❌ Fichier .env.local non trouvé")
        sys.exit(1)
    
    load_dotenv(env_path)
    
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    market = os.getenv("SPOTIFY_MARKET", "US")
    
    if not client_id or not client_secret:
        print("❌ SPOTIFY_CLIENT_ID et SPOTIFY_CLIENT_SECRET requis dans .env.local")
        sys.exit(1)
    
    return client_id, client_secret, market


def load_json_data(file_path: Path):
    """Charge un fichier JSON"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Erreur lecture {file_path.name}: {e}")
        return None


def save_json_data(file_path: Path, data):
    """Sauvegarde un fichier JSON"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"OK {file_path.name} sauvegarde")
    except Exception as e:
        print(f"ERREUR sauvegarde {file_path.name}: {e}")


def enrich_songs(songs_data, resolver: CoverResolver):
    """Enrichit songs.json avec les covers"""
    enriched_count = 0
    failed_count = 0
    
    print(f"\nEnrichissement de {len(songs_data)} titres...")
    
    for song in songs_data:
        title = song.get("title", "")
        
        # Déterminer si lead ou feat (basé sur la présence de * au début)
        is_lead = not title.startswith("*")
        
        # Résoudre la cover
        cover_info = resolver.get_best_cover_for_track(title, is_lead=is_lead)
        
        if cover_info and cover_info.get("cover_url"):
            song["spotify_album_id"] = cover_info.get("album_id")
            song["cover_url"] = cover_info.get("cover_url")
            song["album_name"] = cover_info.get("album_name")
            song["album_type"] = cover_info.get("album_type")
            enriched_count += 1
            print(f"  OK {title} -> {cover_info.get('album_name')}")
        else:
            failed_count += 1
            print(f"  WARNING {title} -> Aucune cover trouvee")
    
    print(f"\nTitres enrichis: {enriched_count}/{len(songs_data)}")
    print(f"Echecs: {failed_count}")
    
    return songs_data


def enrich_albums(albums_data, resolver: CoverResolver):
    """Enrichit albums.json avec les covers (filtre Avatar/Music)"""
    enriched_count = 0
    failed_count = 0
    removed_count = 0
    
    print(f"\nEnrichissement de {len(albums_data)} albums...")
    
    # Filtrer les albums à supprimer AVANT l'enrichissement
    filtered_albums = []
    for album in albums_data:
        album_name = album.get("title", "")
        
        # Retirer ^ au début pour le test de suppression
        clean_name = album_name.lstrip("^").strip()
        
        # Tester si le nom commence par un des patterns à supprimer (insensible à la casse)
        should_remove = False
        for pattern in resolver.ALBUMS_TO_REMOVE:
            # Vérifier si le nom nettoyé commence par le pattern (ou contient uniquement le pattern)
            if clean_name.lower().startswith(pattern.lower()):
                should_remove = True
                removed_count += 1
                print(f"  SUPPRIME {album_name}")
                break
        
        if not should_remove:
            filtered_albums.append(album)
    
    # Enrichir les albums restants
    for album in filtered_albums:
        album_name = album.get("title", "")
        
        # Résoudre la cover
        cover_info = resolver.get_cover_for_album(album_name)
        
        if cover_info and cover_info.get("cover_url"):
            album["spotify_album_id"] = cover_info.get("album_id")
            album["cover_url"] = cover_info.get("cover_url")
            album["album_name"] = cover_info.get("album_name")
            album["album_type"] = cover_info.get("album_type")
            enriched_count += 1
            print(f"  OK {album_name}")
        else:
            failed_count += 1
            print(f"  WARNING {album_name} -> Aucune cover trouvee")
    
    print(f"\nAlbums enrichis: {enriched_count}/{len(filtered_albums)}")
    print(f"Albums supprimes: {removed_count}")
    print(f"Echecs: {failed_count}")
    print(f"Total final: {len(filtered_albums)} albums")
    
    return filtered_albums


def main():
    """Point d'entrée principal"""
    print("=" * 60)
    print("Enrichissement covers Spotify")
    print("=" * 60)
    
    # Charger les credentials
    client_id, client_secret, market = load_env()
    print(f"OK Credentials charges (market: {market})")
    
    # Initialiser le client et le resolver
    client = SpotifyClient(client_id, client_secret, market)
    resolver = CoverResolver(client)
    
    # Chemins des fichiers
    data_dir = Path(__file__).parent.parent / "data"
    songs_file = data_dir / "songs.json"
    albums_file = data_dir / "albums.json"
    
    # Charger les données
    songs_data = load_json_data(songs_file)
    albums_data = load_json_data(albums_file)
    
    if not songs_data or not albums_data:
        print("ERREUR: Impossible de charger les donnees")
        return
    
    # Enrichir songs
    enriched_songs = enrich_songs(songs_data, resolver)
    save_json_data(songs_file, enriched_songs)
    
    # Enrichir albums
    enriched_albums = enrich_albums(albums_data, resolver)
    save_json_data(albums_file, enriched_albums)
    
    print("\n" + "=" * 60)
    print("OK Enrichissement termine !")
    print("=" * 60)


if __name__ == "__main__":
    main()
