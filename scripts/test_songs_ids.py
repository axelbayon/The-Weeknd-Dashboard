#!/usr/bin/env python3
"""
Script de validation des IDs Songs après correction Prompt 4.
"""

import json
import re
from pathlib import Path

def main():
    base_path = Path(__file__).parent.parent
    songs_path = base_path / "data" / "songs.json"
    
    print("=" * 60)
    print("Test 1: Validation des IDs Songs (Prompt 4)")
    print("=" * 60)
    
    # Charger les données
    with open(songs_path, "r", encoding="utf-8") as f:
        songs = json.load(f)
    
    # Pattern attendu: ^kworb:[^:]+@[^:]+$
    pattern = re.compile(r'^kworb:[^:]+@[^:]+$')
    
    # Vérifications
    total = len(songs)
    valid_ids = [song for song in songs if pattern.match(song['id'])]
    unknown_count = sum(1 for song in songs if song['id'].endswith('@unknown'))
    invalid_ids = [song for song in songs if not pattern.match(song['id'])]
    
    print(f"\nTotal chansons: {total}")
    print(f"IDs valides (pattern correct): {len(valid_ids)}/{total}")
    print(f"IDs avec @unknown: {unknown_count}")
    
    # Vérifier qu'il n'y a pas de rank dans les IDs
    ids_with_rank = [song for song in songs if 'rank' in song['id']]
    print(f"IDs contenant 'rank': {len(ids_with_rank)} (devrait être 0)")
    
    if invalid_ids:
        print(f"\n❌ ÉCHEC: {len(invalid_ids)} IDs invalides trouvés:")
        for song in invalid_ids[:5]:
            print(f"   - {song['id']} (titre: {song['title']})")
    else:
        print(f"\n✅ SUCCÈS: Tous les IDs respectent le pattern ^kworb:[^:]+@[^:]+$")
    
    # Exemples d'IDs
    print(f"\nExemples d'IDs (5 premiers):")
    for song in songs[:5]:
        print(f"   {song['id']} <- {song['title']}")
    
    # Vérifier l'unicité
    ids = [song['id'] for song in songs]
    unique_ids = set(ids)
    duplicates = len(ids) - len(unique_ids)
    
    print(f"\nUnicité des IDs:")
    print(f"   Total: {len(ids)}")
    print(f"   Uniques: {len(unique_ids)}")
    print(f"   Doublons: {duplicates}")
    
    if duplicates > 0:
        print("\n⚠️  ATTENTION: Des IDs doublons ont été détectés!")
        from collections import Counter
        id_counts = Counter(ids)
        for id_val, count in id_counts.most_common(10):
            if count > 1:
                print(f"   - {id_val}: {count} occurrences")
    else:
        print("   ✅ Tous les IDs sont uniques")
    
    # Résultat final
    print("\n" + "=" * 60)
    if len(valid_ids) == total and duplicates == 0 and len(ids_with_rank) == 0:
        print("✅ TOUS LES TESTS PASSENT")
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
    print("=" * 60)

if __name__ == "__main__":
    main()
