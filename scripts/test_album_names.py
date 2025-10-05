"""
Script de test pour vérifier les album_name ajoutés
"""

import json
from pathlib import Path

def main():
    """Vérifie les album_name pour les cas de test"""
    data_dir = Path(__file__).parent.parent / "data"
    songs_file = data_dir / "songs.json"
    
    with open(songs_file, 'r', encoding='utf-8') as f:
        songs = json.load(f)
    
    # Cas de test du prompt
    test_cases = [
        "Save Your Tears",
        "Save Your Tears (Remix) (with Ariana Grande) - Bonus Track",
        "*Moth To A Flame (with The Weeknd)",
        "*Love Me Harder (with The Weeknd)",
        "Lonely Star",
        "Live For",
        "*Elastic Heart - From \"The Hunger Games: Catching Fire\" Soundtrack",
        "Where You Belong - From \"Fifty Shades Of Grey\" Soundtrack",
        "Devil May Cry - From \"The Hunger Games: Catching Fire\" Soundtrack",
        "Nothing Is Lost (You Give Me Strength)",
        "Dancing In The Flames",
        "*Love Me Harder - Gregor Salto Amsterdam Mix",  # Cas qui échoue
    ]
    
    print("=" * 80)
    print("TEST DES ALBUM_NAME")
    print("=" * 80)
    print()
    
    for test_title in test_cases:
        found = False
        for song in songs:
            if song['title'] == test_title:
                album_name = song.get('album_name', 'MISSING')
                album_type = song.get('album_type', 'N/A')
                
                # Emoji pour le statut
                if album_name == 'MISSING':
                    status = "❌"
                elif album_name is None:
                    status = "⚠️"
                    album_name = "None (devrait afficher Inconnu)"
                else:
                    status = "✅"
                
                print(f"{status} {test_title}")
                print(f"   Album: {album_name}")
                print(f"   Type:  {album_type}")
                print()
                found = True
                break
        
        if not found:
            print(f"❓ {test_title}")
            print(f"   TITRE NON TROUVE DANS songs.json")
            print()
    
    print("=" * 80)
    print("Légende:")
    print("  ✅ = album_name présent")
    print("  ⚠️ = album_name null (fallback 'Inconnu' s'affichera)")
    print("  ❌ = album_name manquant (BUG)")
    print("  ❓ = titre non trouvé")
    print("=" * 80)

if __name__ == "__main__":
    main()
