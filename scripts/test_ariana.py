import os
from dotenv import load_dotenv
from spotify_client import SpotifyClient

load_dotenv('.env.local')
client = SpotifyClient(
    os.getenv('SPOTIFY_CLIENT_ID'),
    os.getenv('SPOTIFY_CLIENT_SECRET'),
    os.getenv('SPOTIFY_MARKET', 'US')
)

# Test recherche album Ariana Grande
result = client.search_album('My Everything (Deluxe)', 'Ariana Grande')
print(f"Résultats trouvés: {len(result)}")

if result:
    for i, album in enumerate(result[:3]):
        print(f"{i+1}. {album['name']} - {album['id']}")
        print(f"   Type: {album['album_type']}")
        print(f"   Release: {album['release_date']}")
        print(f"   URL: {album['external_urls']['spotify']}")
        print()
else:
    print("AUCUN résultat")

# Test aussi sans (Deluxe)
print("\n--- Test sans (Deluxe) ---")
result2 = client.search_album('My Everything', 'Ariana Grande')
print(f"Résultats trouvés: {len(result2)}")

if result2:
    for i, album in enumerate(result2[:3]):
        print(f"{i+1}. {album['name']} - {album['id']}")
        print(f"   Type: {album['album_type']}")
