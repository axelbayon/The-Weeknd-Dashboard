"""
Script pour rechercher l'album Popular (The Idol HBO)
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))

from spotify_client import SpotifyClient

# Charger credentials
env_path = Path(__file__).parent.parent / ".env.local"
load_dotenv(env_path)

client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

client = SpotifyClient(client_id, client_secret)

# Recherche album
print("Recherche: 'Popular music from the HBO original series'")
results = client.search_album("Popular music from the HBO original series")

albums = results if isinstance(results, list) else results.get('albums', {}).get('items', [])
print(f"\nTrouvé {len(albums)} résultats:\n")

for i, album in enumerate(albums, 1):
    print(f"{i}. {album['name']}")
    print(f"   Artiste: {album['artists'][0]['name']}")
    print(f"   ID: {album['id']}")
    print(f"   Type: {album['album_type']}")
    print()

# Test recherche alternative
print("\n" + "="*60)
print("Recherche: 'The Idol HBO Popular'")
results2 = client.search_album("The Idol HBO Popular")

albums2 = results2 if isinstance(results2, list) else results2.get('albums', {}).get('items', [])
print(f"\nTrouvé {len(albums2)} résultats:\n")

for i, album in enumerate(albums2, 1):
    print(f"{i}. {album['name']}")
    print(f"   Artiste: {album['artists'][0]['name']}")
    print(f"   ID: {album['id']}")
    print()
