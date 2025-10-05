#!/usr/bin/env python3
"""Test rapide pour vérifier rank_prev et rank_delta."""

import json

# Charger songs.json
with open("data/songs.json", "r", encoding="utf-8") as f:
    songs = json.load(f)

# Filtrer ceux qui ont un rank_delta non nul
with_delta = [s for s in songs if s.get("rank_delta") is not None and s.get("rank_delta") != 0]

print(f"Nombre de chansons avec mouvement de rang: {len(with_delta)}\n")

# Afficher les 10 premiers mouvements (gains et pertes)
gains = sorted([s for s in with_delta if s["rank_delta"] > 0], key=lambda x: x["rank_delta"], reverse=True)[:5]
losses = sorted([s for s in with_delta if s["rank_delta"] < 0], key=lambda x: x["rank_delta"])[:5]

print("🔼 TOP 5 GAINS (↑):")
for s in gains:
    print(f"  #{s['rank']:3} {s['title']:45} (était #{s['rank_prev']:3}) → +{s['rank_delta']} places")

print("\n🔽 TOP 5 PERTES (↓):")
for s in losses:
    print(f"  #{s['rank']:3} {s['title']:45} (était #{s['rank_prev']:3}) → {s['rank_delta']} places")

# Cas spécifiques à vérifier
print("\n📊 CAS SPÉCIFIQUES:")
test_titles = ["Take My Breath", "Double Fantasy"]
for title in test_titles:
    song = next((s for s in songs if s["title"] == title), None)
    if song:
        delta_str = f"+{song['rank_delta']}" if song.get('rank_delta', 0) > 0 else str(song.get('rank_delta', 'N/A'))
        print(f"  {title:20} : #{song['rank']:3} (J-1: #{song.get('rank_prev', 'N/A'):3}) → delta: {delta_str}")
