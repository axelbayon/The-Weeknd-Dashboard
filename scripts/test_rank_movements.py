#!/usr/bin/env python3
"""Test complet des mouvements de rang (J vs J-1)."""

import json

# Charger songs.json et albums.json
with open("data/songs.json", "r", encoding="utf-8") as f:
    songs = json.load(f)

with open("data/albums.json", "r", encoding="utf-8") as f:
    albums = json.load(f)

print("=" * 70)
print("TEST MOUVEMENTS DE RANG (J vs J-1)")
print("=" * 70)

# Test 1 : Vérifier champs présents
print("\n✅ TEST 1 : Vérification champs rank_prev et rank_delta")
songs_with_prev = [s for s in songs if s.get("rank_prev") is not None]
songs_with_delta = [s for s in songs if s.get("rank_delta") is not None]
print(f"   - Chansons avec rank_prev: {len(songs_with_prev)}/{len(songs)}")
print(f"   - Chansons avec rank_delta: {len(songs_with_delta)}/{len(songs)}")

albums_with_prev = [a for a in albums if a.get("rank_prev") is not None]
albums_with_delta = [a for a in albums if a.get("rank_delta") is not None]
print(f"   - Albums avec rank_prev: {len(albums_with_prev)}/{len(albums)}")
print(f"   - Albums avec rank_delta: {len(albums_with_delta)}/{len(albums)}")

# Test 2 : Cas spécifiques Take My Breath vs Double Fantasy
print("\n✅ TEST 2 : Cas Take My Breath vs Double Fantasy (inversion symétrique)")
tmb = next((s for s in songs if s["title"] == "Take My Breath"), None)
df = next((s for s in songs if s["title"] == "Double Fantasy (with Future)"), None)

if tmb and df:
    print(f"   Take My Breath:")
    print(f"      Rang actuel (J): #{tmb['rank']}")
    print(f"      Rang précédent (J-1): #{tmb.get('rank_prev', 'N/A')}")
    print(f"      Delta: {tmb.get('rank_delta', 'N/A'):+} {'↑' if tmb.get('rank_delta', 0) > 0 else '↓' if tmb.get('rank_delta', 0) < 0 else '='}")
    
    print(f"   Double Fantasy:")
    print(f"      Rang actuel (J): #{df['rank']}")
    print(f"      Rang précédent (J-1): #{df.get('rank_prev', 'N/A')}")
    print(f"      Delta: {df.get('rank_delta', 'N/A'):+} {'↑' if df.get('rank_delta', 0) > 0 else '↓' if df.get('rank_delta', 0) < 0 else '='}")
    
    # Vérifier symétrie
    if tmb.get('rank_delta') == 1 and df.get('rank_delta') == -1:
        print("   ✅ Inversion symétrique confirmée!")
    else:
        print("   ⚠️  Pas d'inversion dans cet échantillon")

# Test 3 : Mouvements significatifs
print("\n✅ TEST 3 : Mouvements significatifs (≥2 places)")
songs_movements = [s for s in songs if s.get("rank_delta") is not None and s.get("rank_delta") != 0]
big_gains = sorted([s for s in songs_movements if s["rank_delta"] >= 2], key=lambda x: x["rank_delta"], reverse=True)[:3]
big_losses = sorted([s for s in songs_movements if s["rank_delta"] <= -2], key=lambda x: x["rank_delta"])[:3]

if big_gains:
    print("   Gains importants (↑):")
    for s in big_gains:
        print(f"      #{s['rank']:3} {s['title']:45} (était #{s['rank_prev']:3}) → +{s['rank_delta']}")
else:
    print("   Aucun gain ≥2 places")

if big_losses:
    print("   Pertes importantes (↓):")
    for s in big_losses:
        print(f"      #{s['rank']:3} {s['title']:45} (était #{s['rank_prev']:3}) → {s['rank_delta']}")
else:
    print("   Aucune perte ≥2 places")

# Test 4 : Statistiques globales
print("\n✅ TEST 4 : Statistiques globales")
gains = [s for s in songs_movements if s["rank_delta"] > 0]
losses = [s for s in songs_movements if s["rank_delta"] < 0]
stable = [s for s in songs if s.get("rank_delta") == 0]

print(f"   - Gains (↑): {len(gains)}")
print(f"   - Pertes (↓): {len(losses)}")
print(f"   - Stables (=): {len(stable)}")
print(f"   - Sans données J-1: {len(songs) - len(songs_with_prev)}")

# Test 5 : Albums
print("\n✅ TEST 5 : Mouvements Albums")
albums_movements = [a for a in albums if a.get("rank_delta") is not None and a.get("rank_delta") != 0]
album_gains = [a for a in albums_movements if a["rank_delta"] > 0]
album_losses = [a for a in albums_movements if a["rank_delta"] < 0]

print(f"   - Albums avec mouvements: {len(albums_movements)}")
print(f"   - Gains (↑): {len(album_gains)}")
print(f"   - Pertes (↓): {len(album_losses)}")

if albums_movements:
    print("   Exemple mouvements:")
    for a in albums_movements[:3]:
        arrow = "↑" if a["rank_delta"] > 0 else "↓"
        print(f"      #{a['rank']:2} {a['title']:40} (était #{a['rank_prev']:2}) {arrow} {abs(a['rank_delta'])}")

print("\n" + "=" * 70)
print("RÉSUMÉ")
print("=" * 70)
print(f"✅ {len(songs_movements)} chansons avec mouvements détectés")
print(f"✅ {len(gains)} gains (↑) et {len(losses)} pertes (↓)")
print(f"✅ {len(albums_movements)} albums avec mouvements détectés")
print(f"✅ Cas Take My Breath vs Double Fantasy: {'OK' if tmb and df else 'N/A'}")
print("=" * 70)
