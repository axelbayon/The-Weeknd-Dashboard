"""
Vérification des chansons après pipeline
"""

import json
from pathlib import Path

data_dir = Path(__file__).parent.parent / "data"
songs_file = data_dir / "songs.json"

with open(songs_file, 'r', encoding='utf-8') as f:
    songs = json.load(f)

print(f"Nombre total de chansons: {len(songs)}")

xo_songs = [s for s in songs if 'XO / The Host' in s['title']]
print(f"\nVersions 'XO / The Host' trouvées: {len(xo_songs)}\n")

for song in xo_songs:
    print(f"Rang {song['rank']}:")
    print(f"  ID: {song['id']}")
    print(f"  Streams quotidiens: {song['streams_daily']}")
    print(f"  Streams totaux: {song['streams_total']:,}")
    print()

# Totaux
total_streams = sum(s['streams_total'] for s in songs)
total_daily = sum(s['streams_daily'] for s in songs)

print(f"Statistiques globales:")
print(f"  Streams totaux: {total_streams:,}")
print(f"  Streams quotidiens: {total_daily:,}")
