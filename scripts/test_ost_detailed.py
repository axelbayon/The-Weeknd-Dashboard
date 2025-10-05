import os
from dotenv import load_dotenv
from spotify_client import SpotifyClient

load_dotenv('.env.local')
client = SpotifyClient(
    os.getenv('SPOTIFY_CLIENT_ID'),
    os.getenv('SPOTIFY_CLIENT_SECRET'),
    os.getenv('SPOTIFY_MARKET', 'US')
)

# Test Avatar OST avec différentes variantes
print("=== AVATAR OST - Variantes ===")
variants = [
    'Avatar: The Way of Water (Original Motion Picture Soundtrack)',
    'Avatar The Way of Water Original Motion Picture Soundtrack',
    'Avatar 2 Soundtrack',
]
for var in variants:
    result = client.search_album(var, 'Various Artists')
    if result:
        for i, album in enumerate(result[:3]):
            print(f"{i+1}. '{album['name']}'")
            if 'soundtrack' in album['name'].lower() or 'score' in album['name'].lower():
                print(f"   ✓ ID: {album['id']}")
        print()

# Test Paradise Again (album studio, pas live)
print("\n=== PARADISE AGAIN - Studio ===")
result = client.search_album('Paradise Again', 'Swedish House Mafia')
if result:
    for i, album in enumerate(result[:5]):
        album_type = album.get('album_type', '')
        release_date = album.get('release_date', '')
        print(f"{i+1}. '{album['name']}' - Type: {album_type}, Release: {release_date}")
        if 'live' not in album['name'].lower():
            print(f"   ✓ Studio: {album['id']}")
