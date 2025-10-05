import os
from dotenv import load_dotenv
from spotify_client import SpotifyClient

load_dotenv('.env.local')
client = SpotifyClient(
    os.getenv('SPOTIFY_CLIENT_ID'),
    os.getenv('SPOTIFY_CLIENT_SECRET'),
    os.getenv('SPOTIFY_MARKET', 'US')
)

# Test 1: Hunger Games OST
print("=== HUNGER GAMES OST ===")
result1 = client.search_album('The Hunger Games: Catching Fire', 'Various Artists')
if result1:
    print(f"✓ Trouvé: '{result1[0]['name']}' ({result1[0]['id']})")
else:
    print("✗ Non trouvé")

# Test 2: Fifty Shades OST
print("\n=== FIFTY SHADES OST ===")
result2 = client.search_album('Fifty Shades of Grey', 'Various Artists')
if result2:
    print(f"✓ Trouvé: '{result2[0]['name']}' ({result2[0]['id']})")
else:
    print("✗ Non trouvé")

# Test 3: Avatar OST
print("\n=== AVATAR OST ===")
result3 = client.search_album('Avatar: The Way of Water', 'Various Artists')
if result3:
    print(f"✓ Trouvé: '{result3[0]['name']}' ({result3[0]['id']})")
else:
    print("✗ Non trouvé")

# Test 4: Cashmere Cat - 9
print("\n=== CASHMERE CAT - 9 ===")
result4 = client.search_album('9', 'Cashmere Cat')
if result4:
    print(f"✓ Trouvé: '{result4[0]['name']}' ({result4[0]['id']})")
else:
    print("✗ Non trouvé")

# Test 5: Paradise Again
print("\n=== PARADISE AGAIN ===")
result5 = client.search_album('Paradise Again', 'Swedish House Mafia')
if result5:
    print(f"✓ Trouvé: '{result5[0]['name']}' ({result5[0]['id']})")
else:
    print("✗ Non trouvé")
