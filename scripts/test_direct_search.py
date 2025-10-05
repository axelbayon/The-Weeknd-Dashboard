import os
from dotenv import load_dotenv
from spotify_client import SpotifyClient

load_dotenv('.env.local')
client = SpotifyClient(
    os.getenv('SPOTIFY_CLIENT_ID'),
    os.getenv('SPOTIFY_CLIENT_SECRET'),
    os.getenv('SPOTIFY_MARKET', 'US')
)

# Chercher directement la chanson "Nothing Is Lost"
print("=== RECHERCHE: Nothing Is Lost ===")
tracks = client.search_track('Nothing Is Lost')

if tracks:
    for i, track in enumerate(tracks[:5]):
        print(f"\n{i+1}. Titre: '{track['name']}'")
        print(f"   Artistes: {', '.join([a['name'] for a in track['artists']])}")
        album = track.get('album', {})
        print(f"   Album: '{album.get('name')}'")
        print(f"   Album ID: {album.get('id')}")
        if 'avatar' in album.get('name', '').lower():
            print("   ✓✓✓ AVATAR OST TROUVÉ !")

# Chercher "Elastic Heart The Weeknd"
print("\n\n=== RECHERCHE: Elastic Heart ===")
tracks2 = client.search_track('Elastic Heart')

if tracks2:
    for i, track in enumerate(tracks2[:5]):
        artists = [a['name'] for a in track['artists']]
        if 'The Weeknd' in artists or 'the weeknd' in str(artists).lower():
            print(f"\n{i+1}. Titre: '{track['name']}'")
            print(f"   Artistes: {', '.join(artists)}")
            album = track.get('album', {})
            print(f"   Album: '{album.get('name')}'")
            print(f"   Album ID: {album.get('id')}")
