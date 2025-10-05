#!/usr/bin/env python3
"""Vérifie pourquoi certains badges s'affichent encore."""

import json

# Charger les données
with open('data/songs.json', 'r', encoding='utf-8') as f:
    songs = json.load(f)

with open('data/meta.json', 'r', encoding='utf-8') as f:
    meta = json.load(f)

# Titres à vérifier
titles_to_check = ['Take My Breath', 'Double Fantasy', 'Opening Night', 'Phantom Regrets']

print(f"meta.spotify_data_date = {meta.get('spotify_data_date')}")
print("\n" + "="*80)

for title in titles_to_check:
    matching = [s for s in songs if title.lower() in s['title'].lower()]
    
    if matching:
        for song in matching:
            print(f"\n📋 {song['title']}")
            print(f"   rank: {song['rank']} (était {song.get('rank_prev')})")
            print(f"   rank_delta: {song.get('rank_delta')}")
            print(f"   delta_base_date: {song.get('delta_base_date')}")
            print(f"   delta_for_date: {song.get('delta_for_date')}")
            
            # Vérifier si le badge DEVRAIT s'afficher
            should_show = (
                song.get('rank_delta') and 
                song.get('rank_delta') != 0 and
                song.get('delta_for_date') == meta.get('spotify_data_date')
            )
            
            print(f"   ➡️  Badge devrait s'afficher: {'OUI ✅' if should_show else 'NON ❌'}")
            
            if should_show:
                arrow = "▲" if song['rank_delta'] > 0 else "▼"
                print(f"   🏷️  Badge: {arrow} {abs(song['rank_delta'])}")
