import json

with open('data/songs.json', 'r', encoding='utf-8') as f:
    songs = json.load(f)

print("=== Échantillon variations ===")
for i, song in enumerate(songs[:10]):
    var = song.get('variation_pct')
    print(f"{i+1}. {song['title']}: variation_pct = {repr(var)} (type: {type(var).__name__})")

# Compter les variations nulles vs 0 vs "N.D."
nulls = sum(1 for s in songs if s.get('variation_pct') is None)
zeros = sum(1 for s in songs if s.get('variation_pct') == 0)
nd = sum(1 for s in songs if s.get('variation_pct') == 'N.D.')
positives = sum(1 for s in songs if isinstance(s.get('variation_pct'), (int, float)) and s.get('variation_pct') > 0)
negatives = sum(1 for s in songs if isinstance(s.get('variation_pct'), (int, float)) and s.get('variation_pct') < 0)

print(f"\n=== Stats ===")
print(f"Total chansons: {len(songs)}")
print(f"Variations null: {nulls}")
print(f"Variations = 0: {zeros}")
print(f"Variations = 'N.D.' (string): {nd}")
print(f"Variations positives: {positives}")
print(f"Variations négatives: {negatives}")

if nd > 0:
    print(f"\n=== Exemples N.D. ===")
    nd_songs = [s for s in songs if s.get('variation_pct') == 'N.D.']
    for s in nd_songs[:5]:
        print(f"  - {s['title']}: variation_pct = {repr(s.get('variation_pct'))}")
