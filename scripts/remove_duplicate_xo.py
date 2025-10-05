"""
Script pour supprimer le doublon "XO / The Host" avec 0 streams quotidiens (rang 310)
"""

import json
from pathlib import Path

def main():
    data_dir = Path(__file__).parent.parent / "data"
    songs_file = data_dir / "songs.json"
    
    # Charger les données
    print("Chargement de songs.json...")
    with open(songs_file, 'r', encoding='utf-8') as f:
        songs = json.load(f)
    
    print(f"Nombre total de chansons AVANT: {len(songs)}")
    
    # Trouver et afficher les deux versions de XO / The Host
    xo_songs = [s for s in songs if s['title'] == 'XO / The Host']
    print(f"\nTrouvé {len(xo_songs)} versions de 'XO / The Host':\n")
    
    for song in xo_songs:
        print(f"  Rang {song['rank']}:")
        print(f"    ID: {song['id']}")
        print(f"    Streams totaux: {song['streams_total']:,}")
        print(f"    Streams quotidiens: {song['streams_daily']}")
        print()
    
    # Supprimer la version avec 0 streams quotidiens (rang 310)
    song_to_remove = None
    for song in songs:
        if song['id'] == 'kworb:xo / the host@unknown-2':
            song_to_remove = song
            break
    
    if song_to_remove:
        print(f"Suppression de: {song_to_remove['title']} (rang {song_to_remove['rank']}, 0 streams quotidiens)")
        songs.remove(song_to_remove)
    else:
        print("ERREUR: Chanson à supprimer non trouvée!")
        return
    
    print(f"\nNombre total de chansons APRÈS: {len(songs)}")
    
    # Calculer les nouveaux totaux
    total_streams = sum(s['streams_total'] for s in songs)
    total_daily = sum(s['streams_daily'] for s in songs)
    
    print(f"\nNouvelles statistiques:")
    print(f"  Streams totaux: {total_streams:,}")
    print(f"  Streams quotidiens: {total_daily:,}")
    
    # Sauvegarder
    print("\nSauvegarde de songs.json...")
    with open(songs_file, 'w', encoding='utf-8') as f:
        json.dump(songs, f, indent=2, ensure_ascii=False)
    
    print("✅ Suppression terminée!")
    print(f"✅ Le fichier contient maintenant {len(songs)} chansons")

if __name__ == "__main__":
    main()
