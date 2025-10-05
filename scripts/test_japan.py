import os
from dotenv import load_dotenv
from spotify_client import SpotifyClient

load_dotenv('.env.local')
client = SpotifyClient(
    os.getenv('SPOTIFY_CLIENT_ID'),
    os.getenv('SPOTIFY_CLIENT_SECRET'),
    os.getenv('SPOTIFY_MARKET', 'US')
)

# Test recherche
result = client.search_album('The Weeknd In Japan', 'The Weeknd')
print(f"Résultats trouvés: {len(result)}")

if result:
    for i, album in enumerate(result[:5]):
        print(f"{i+1}. '{album['name']}' - {album['id']}")
        print(f"   Artists: {', '.join([a['name'] for a in album['artists']])}")
        print()
else:
    print("AUCUN résultat")
