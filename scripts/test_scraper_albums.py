#!/usr/bin/env python3
"""
Script de validation des Albums après scraping Prompt 4.
Tests : comptage, schémas, unicité, variations, paliers 1B, dates.
"""

import json
import re
from pathlib import Path
from collections import Counter

def main():
    base_path = Path(__file__).parent.parent
    albums_path = base_path / "data" / "albums.json"
    snapshot_path = base_path / "data" / "history" / "albums" / "2025-10-01.json"
    meta_path = base_path / "data" / "meta.json"
    
    print("=" * 60)
    print("Test Albums — Validation Prompt 4")
    print("=" * 60)
    
    # Charger les données
    with open(albums_path, "r", encoding="utf-8") as f:
        albums = json.load(f)
    
    with open(snapshot_path, "r", encoding="utf-8") as f:
        snapshot = json.load(f)
    
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    
    # Test 1: Comptage minimum
    print(f"\n📊 Test 1: Comptage")
    print(f"   Albums dans data/albums.json: {len(albums)}")
    print(f"   Albums dans snapshot J: {len(snapshot)}")
    
    if len(albums) >= 20:
        print(f"   ✅ Minimum 20 albums atteint ({len(albums)})")
    else:
        print(f"   ❌ Moins de 20 albums ({len(albums)})")
    
    # Test 2: Pattern ID Albums
    print(f"\n🔑 Test 2: Pattern des IDs Albums")
    pattern = re.compile(r'^kworb:album:[a-z0-9\s]+(-\d+)?$')
    valid_ids = [album for album in albums if pattern.match(album['id'])]
    print(f"   IDs valides: {len(valid_ids)}/{len(albums)}")
    
    if len(valid_ids) == len(albums):
        print("   ✅ Tous les IDs respectent le pattern kworb:album:<norm_album>")
    else:
        print("   ❌ Certains IDs ne respectent pas le pattern")
        invalid = [a for a in albums if not pattern.match(a['id'])]
        for album in invalid[:3]:
            print(f"      - {album['id']}")
    
    # Test 3: Unicité des IDs
    print(f"\n🎯 Test 3: Unicité des IDs")
    ids = [album['id'] for album in albums]
    unique_ids = set(ids)
    duplicates = len(ids) - len(unique_ids)
    
    print(f"   Total: {len(ids)}")
    print(f"   Uniques: {len(unique_ids)}")
    print(f"   Doublons: {duplicates}")
    
    if duplicates == 0:
        print("   ✅ Tous les IDs sont uniques")
    else:
        print("   ❌ Doublons détectés:")
        id_counts = Counter(ids)
        for id_val, count in id_counts.most_common(5):
            if count > 1:
                print(f"      - {id_val}: {count} occurrences")
    
    # Test 4: Variations et paliers
    print(f"\n📈 Test 4: Variations et paliers")
    
    # Trouver cas avec variation numérique
    numeric_variations = [a for a in albums if isinstance(a.get('variation_pct'), (int, float))]
    nd_variations = [a for a in albums if a.get('variation_pct') == "N.D."]
    
    print(f"   Variations numériques: {len(numeric_variations)}")
    print(f"   Variations 'N.D.': {len(nd_variations)}")
    
    if numeric_variations:
        sample = numeric_variations[0]
        print(f"\n   Exemple variation numérique:")
        print(f"      Album: {sample['title']}")
        print(f"      variation_pct: {sample['variation_pct']}%")
        
        # Vérifier arrondi 2 décimales
        if isinstance(sample['variation_pct'], float):
            decimals = len(str(sample['variation_pct']).split('.')[-1]) if '.' in str(sample['variation_pct']) else 0
            if decimals <= 2:
                print(f"      ✅ Arrondi correct (≤2 décimales)")
            else:
                print(f"      ❌ Trop de décimales ({decimals})")
    
    if nd_variations:
        sample = nd_variations[0]
        print(f"\n   Exemple variation 'N.D.':")
        print(f"      Album: {sample['title']}")
        print(f"      variation_pct: {sample['variation_pct']}")
        print(f"      ✅ Format correct pour donnée manquante")
    
    # Test 5: Paliers 1B (1 000 000 000)
    print(f"\n💰 Test 5: Paliers 1 milliard")
    
    paliers_valides = []
    paliers_invalides = []
    
    for album in albums:
        next_cap = album.get('next_cap_value')
        if next_cap and next_cap % 1_000_000_000 == 0:
            paliers_valides.append(album)
        else:
            paliers_invalides.append(album)
    
    print(f"   Paliers valides (multiples 1B): {len(paliers_valides)}/{len(albums)}")
    
    if paliers_valides:
        sample = paliers_valides[0]
        print(f"\n   Exemple palier 1B:")
        print(f"      Album: {sample['title']}")
        print(f"      streams_total: {sample['streams_total']:,}")
        print(f"      next_cap_value: {sample['next_cap_value']:,}")
        print(f"      ✅ Multiple de 1 000 000 000")
    
    if paliers_invalides:
        print(f"\n   ❌ {len(paliers_invalides)} paliers invalides détectés")
        sample = paliers_invalides[0]
        print(f"      Exemple: {sample['title']}")
        print(f"      next_cap_value: {sample.get('next_cap_value')}")
    
    # Test 6: Days to next cap
    print(f"\n⏱️  Test 6: Jours restants (days_to_next_cap)")
    
    numeric_days = [a for a in albums if isinstance(a.get('days_to_next_cap'), (int, float))]
    nd_days = [a for a in albums if a.get('days_to_next_cap') == "N.D."]
    
    print(f"   Jours numériques: {len(numeric_days)}")
    print(f"   Jours 'N.D.': {len(nd_days)}")
    
    if numeric_days:
        sample = numeric_days[0]
        print(f"\n   Exemple jours calculés:")
        print(f"      Album: {sample['title']}")
        print(f"      days_to_next_cap: {sample['days_to_next_cap']}")
        
        # Vérifier arrondi 2 décimales
        if isinstance(sample['days_to_next_cap'], float):
            decimals = len(str(sample['days_to_next_cap']).split('.')[-1]) if '.' in str(sample['days_to_next_cap']) else 0
            if decimals <= 2:
                print(f"      ✅ Arrondi correct (≤2 décimales)")
            else:
                print(f"      ❌ Trop de décimales ({decimals})")
    
    # Test 7: Cohérence des dates
    print(f"\n📅 Test 7: Cohérence des dates")
    
    spotify_data_date = meta.get('spotify_data_date')
    latest_date = meta.get('history', {}).get('latest_date')
    available_dates_albums = meta.get('history', {}).get('available_dates_albums', [])
    
    print(f"   spotify_data_date: {spotify_data_date}")
    print(f"   history.latest_date: {latest_date}")
    print(f"   available_dates_albums: {available_dates_albums}")
    
    if spotify_data_date == latest_date:
        print(f"   ✅ spotify_data_date == latest_date")
    else:
        print(f"   ⚠️  Dates différentes")
    
    if spotify_data_date in available_dates_albums:
        print(f"   ✅ spotify_data_date présent dans available_dates_albums")
    else:
        print(f"   ❌ spotify_data_date absent de available_dates_albums")
    
    # Vérifier que tous les albums ont la même spotify_data_date
    dates_in_albums = set(album.get('spotify_data_date') for album in albums)
    if len(dates_in_albums) == 1:
        print(f"   ✅ Tous les albums ont la même spotify_data_date")
    else:
        print(f"   ❌ Dates incohérentes dans albums: {dates_in_albums}")
    
    # Résultat final
    print("\n" + "=" * 60)
    
    success = (
        len(albums) >= 20 and
        len(valid_ids) == len(albums) and
        duplicates == 0 and
        len(paliers_invalides) == 0 and
        spotify_data_date in available_dates_albums
    )
    
    if success:
        print("✅ TOUS LES TESTS ALBUMS PASSENT")
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
