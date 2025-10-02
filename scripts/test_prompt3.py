#!/usr/bin/env python3
"""Tests de validation pour le Prompt 3."""

import json

# Charger les données
with open('data/songs.json', 'r', encoding='utf-8') as f:
    songs = json.load(f)

with open('data/meta.json', 'r', encoding='utf-8') as f:
    meta = json.load(f)

print("\n=== TESTS DE VALIDATION PROMPT 3 ===\n")

# Test 1: Comptage
print("Test 1: Comptage des chansons (>= 200)")
print(f"   Nombre de chansons: {len(songs)}")
print(f"   Resultat: {'PASS' if len(songs) >= 200 else 'FAIL'}\n")

# Test 2: Extraits avec variation numerique
print("Test 2: Extrait avec variation_pct numerique (2 dec.)")
numeric_var = [s for s in songs if isinstance(s.get('variation_pct'), (int, float))]
if numeric_var:
    s = numeric_var[0]
    print(f"   Chanson: {s['title']}")
    print(f"   Rank: {s['rank']} | Streams: {s['streams_total']:,}")
    print(f"   variation_pct: {s['variation_pct']}% (2 dec)")
    print(f"   next_cap_value: {s['next_cap_value']:,} (multiple de 100M)")
    print(f"   days_to_next_cap: {s['days_to_next_cap']} (2 dec)\n")

# Test 3: Extrait avec N.D.
print("Test 3: Extrait avec variation_pct = 'N.D.'")
nd_var = [s for s in songs if s.get('variation_pct') == 'N.D.']
if nd_var:
    s = nd_var[0]
    print(f"   Chanson: {s['title']}")
    print(f"   Rank: {s['rank']}")
    print(f"   variation_pct: {s['variation_pct']} (pas de J-1)")
    print(f"   next_cap_value: {s['next_cap_value']:,}")
    print(f"   days_to_next_cap: {s['days_to_next_cap']}\n")
else:
    print("   Aucun cas N.D. trouve (toutes les chansons ont un J-1)\n")

# Test 4: Presence lead/feat
print("Test 4: Presence de roles lead et feat")
leads = [s for s in songs if s.get('role') == 'lead']
feats = [s for s in songs if s.get('role') == 'feat']
print(f"   Lead: {len(leads)} chansons")
print(f"   Feat: {len(feats)} chansons")
if leads:
    print(f"   Exemple lead: {leads[0]['title']}")
if feats:
    print(f"   Exemple feat: {feats[0]['title']}")
print(f"   Resultat: {'PASS' if leads and feats else 'FAIL'}\n")

# Test 5: Coherence dates
print("Test 5: Coherence des dates")
spotify_data_date = meta.get('spotify_data_date')
latest_date = meta.get('history', {}).get('latest_date')
songs_dates = set(s['spotify_data_date'] for s in songs)
print(f"   meta.spotify_data_date: {spotify_data_date}")
print(f"   meta.history.latest_date: {latest_date}")
print(f"   Dates uniques dans songs.json: {songs_dates}")
print(f"   Resultat: {'PASS' if spotify_data_date == latest_date and songs_dates == {latest_date} else 'FAIL'}\n")

# Test 6: Unicite des id
print("Test 6: Unicite des id")
ids = [s['id'] for s in songs]
unique_ids = set(ids)
print(f"   Total id: {len(ids)}")
print(f"   Id uniques: {len(unique_ids)}")
print(f"   Resultat: {'PASS' if len(ids) == len(unique_ids) else 'FAIL'}\n")
