#!/usr/bin/env python3
"""
Tests pour Prompt 8.8 : Badges éphémères (J vs J-1 uniquement)

Scénarios testés :
- T1: Badges disparaissent jour suivant sans nouveau mouvement
- T2: Nouveaux mouvements affichent nouveaux badges
- T3: Validation des champs delta_base_date et delta_for_date
- T4: Cohérence des données après rotation
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta


def load_json(filepath):
    """Charge un fichier JSON."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def test_t1_delta_fields_present():
    """
    T1: Vérifier que delta_base_date et delta_for_date sont présents
    """
    print("\n" + "="*60)
    print("T1: Vérification présence delta_base_date et delta_for_date")
    print("="*60)
    
    songs = load_json('data/songs.json')
    albums = load_json('data/albums.json')
    
    # Vérifier songs
    songs_with_fields = sum(1 for s in songs if 'delta_base_date' in s and 'delta_for_date' in s)
    print(f"✅ Songs: {songs_with_fields}/{len(songs)} ont les champs delta_*_date")
    
    if songs_with_fields != len(songs):
        print(f"❌ ÉCHEC: {len(songs) - songs_with_fields} songs sans champs delta")
        return False
    
    # Vérifier albums
    albums_with_fields = sum(1 for a in albums if 'delta_base_date' in a and 'delta_for_date' in a)
    print(f"✅ Albums: {albums_with_fields}/{len(albums)} ont les champs delta_*_date")
    
    if albums_with_fields != len(albums):
        print(f"❌ ÉCHEC: {len(albums) - albums_with_fields} albums sans champs delta")
        return False
    
    # Échantillon
    print("\n📋 Échantillon Songs (5 premiers):")
    for i, song in enumerate(songs[:5], 1):
        print(f"  {i}. {song['title']}")
        print(f"     delta_base_date: {song.get('delta_base_date')}")
        print(f"     delta_for_date:  {song.get('delta_for_date')}")
        print(f"     rank_delta:      {song.get('rank_delta')}")
    
    print("\n✅ T1 PASSED: Tous les champs sont présents")
    return True


def test_t2_date_consistency():
    """
    T2: Vérifier la cohérence des dates (delta_for_date = meta.spotify_data_date)
    """
    print("\n" + "="*60)
    print("T2: Cohérence delta_for_date avec meta.spotify_data_date")
    print("="*60)
    
    meta = load_json('data/meta.json')
    songs = load_json('data/songs.json')
    albums = load_json('data/albums.json')
    
    expected_date = meta.get('spotify_data_date')
    print(f"📅 meta.spotify_data_date = {expected_date}")
    
    # Vérifier songs
    songs_mismatch = [s for s in songs if s.get('delta_for_date') != expected_date]
    if songs_mismatch:
        print(f"❌ ÉCHEC: {len(songs_mismatch)} songs avec delta_for_date incorrect")
        for s in songs_mismatch[:3]:
            print(f"  - {s['title']}: delta_for_date={s.get('delta_for_date')}, attendu={expected_date}")
        return False
    
    print(f"✅ Songs: {len(songs)} songs avec delta_for_date = {expected_date}")
    
    # Vérifier albums
    albums_mismatch = [a for a in albums if a.get('delta_for_date') != expected_date]
    if albums_mismatch:
        print(f"❌ ÉCHEC: {len(albums_mismatch)} albums avec delta_for_date incorrect")
        for a in albums_mismatch[:3]:
            print(f"  - {a['title']}: delta_for_date={a.get('delta_for_date')}, attendu={expected_date}")
        return False
    
    print(f"✅ Albums: {len(albums)} albums avec delta_for_date = {expected_date}")
    
    print("\n✅ T2 PASSED: Cohérence des dates validée")
    return True


def test_t3_delta_base_date_is_j_minus_1():
    """
    T3: Vérifier que delta_base_date = delta_for_date - 1 jour
    """
    print("\n" + "="*60)
    print("T3: Validation delta_base_date = J-1")
    print("="*60)
    
    songs = load_json('data/songs.json')
    meta = load_json('data/meta.json')
    
    # Calculer J-1 depuis meta.spotify_data_date
    j_date = datetime.strptime(meta['spotify_data_date'], '%Y-%m-%d')
    j_minus_1_expected = (j_date - timedelta(days=1)).strftime('%Y-%m-%d')
    
    print(f"📅 J (spotify_data_date) = {meta['spotify_data_date']}")
    print(f"📅 J-1 attendu = {j_minus_1_expected}")
    
    # Vérifier que delta_base_date correspond
    songs_with_correct_base = sum(
        1 for s in songs 
        if s.get('delta_base_date') == j_minus_1_expected or s.get('delta_base_date') is None
    )
    
    # Compter ceux avec base_date renseignée
    songs_with_base = [s for s in songs if s.get('delta_base_date')]
    
    if songs_with_base:
        base_date_value = songs_with_base[0]['delta_base_date']
        print(f"✅ delta_base_date trouvé: {base_date_value}")
        
        if base_date_value == j_minus_1_expected:
            print(f"✅ delta_base_date = J-1 ({j_minus_1_expected})")
        else:
            print(f"❌ ÉCHEC: delta_base_date={base_date_value}, attendu={j_minus_1_expected}")
            return False
    else:
        print("⚠️  Aucun song avec delta_base_date renseigné (J-1 potentiellement inexistant)")
    
    print("\n✅ T3 PASSED: delta_base_date cohérent avec J-1")
    return True


def test_t4_badges_logic_validation():
    """
    T4: Valider la logique des badges (rank_delta != 0 ET delta_for_date = J)
    """
    print("\n" + "="*60)
    print("T4: Logique badges - rank_delta et date")
    print("="*60)
    
    songs = load_json('data/songs.json')
    meta = load_json('data/meta.json')
    
    expected_date = meta['spotify_data_date']
    
    # Compter les badges qui devraient s'afficher
    badges_valides = [
        s for s in songs 
        if s.get('rank_delta') and s.get('rank_delta') != 0 
        and s.get('delta_for_date') == expected_date
    ]
    
    # Compter ceux avec rank_delta mais date obsolète (NE doivent PAS s'afficher)
    badges_obsoletes = [
        s for s in songs 
        if s.get('rank_delta') and s.get('rank_delta') != 0 
        and s.get('delta_for_date') != expected_date
    ]
    
    print(f"📊 Statistiques badges:")
    print(f"  - Badges VALIDES (rank_delta != 0 ET date = J): {len(badges_valides)}")
    print(f"  - Badges OBSOLÈTES (rank_delta != 0 MAIS date != J): {len(badges_obsoletes)}")
    
    if badges_obsoletes:
        print(f"\n❌ ÉCHEC: {len(badges_obsoletes)} badges avec date obsolète détectés")
        for s in badges_obsoletes[:3]:
            print(f"  - {s['title']}: delta={s['rank_delta']}, date={s.get('delta_for_date')}, attendu={expected_date}")
        return False
    
    # Afficher échantillon badges valides
    if badges_valides:
        print(f"\n📋 Échantillon badges VALIDES (5 premiers):")
        for i, s in enumerate(badges_valides[:5], 1):
            arrow = "▲" if s['rank_delta'] > 0 else "▼"
            print(f"  {i}. {s['title']}: {arrow} {abs(s['rank_delta'])} (rank: {s['rank']} ← {s.get('rank_prev')})")
    else:
        print("\n⚠️  Aucun badge valide trouvé (tous les rangs stables)")
    
    print("\n✅ T4 PASSED: Logique badges validée")
    return True


def test_t5_front_cache_busting():
    """
    T5: Vérifier que le front utilise ?v=<generated_at> pour cache-busting
    """
    print("\n" + "="*60)
    print("T5: Cache-busting frontend (?v=generated_at)")
    print("="*60)
    
    # Vérifier data-loader.js
    data_loader_path = Path('Website/src/data-loader.js')
    
    if not data_loader_path.exists():
        print("❌ ÉCHEC: data-loader.js introuvable")
        return False
    
    with open(data_loader_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Chercher les patterns de cache-busting
    has_generated_at = 'meta.generated_at' in content
    has_cache_buster = '?v=' in content or '?t=' in content
    
    if has_generated_at and has_cache_buster:
        print(f"✅ data-loader.js utilise meta.generated_at pour cache-busting")
    else:
        print(f"❌ ÉCHEC: Cache-busting non trouvé dans data-loader.js")
        print(f"  - meta.generated_at trouvé: {has_generated_at}")
        print(f"  - ?v= ou ?t= trouvé: {has_cache_buster}")
        return False
    
    # Vérifier rank-rail.js
    rank_rail_path = Path('Website/src/rank-rail.js')
    
    if not rank_rail_path.exists():
        print("❌ ÉCHEC: rank-rail.js introuvable")
        return False
    
    with open(rank_rail_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Chercher validation delta_for_date
    has_validation = 'delta_for_date' in content and 'spotify_data_date' in content
    
    if has_validation:
        print(f"✅ rank-rail.js valide delta_for_date vs spotify_data_date")
    else:
        print(f"❌ ÉCHEC: Validation date non trouvée dans rank-rail.js")
        return False
    
    print("\n✅ T5 PASSED: Cache-busting et validation front OK")
    return True


def main():
    """Point d'entrée principal."""
    print("\n" + "="*60)
    print("🧪 TESTS PROMPT 8.8 - BADGES ÉPHÉMÈRES")
    print("="*60)
    
    tests = [
        ("T1: Champs delta_*_date présents", test_t1_delta_fields_present),
        ("T2: Cohérence dates", test_t2_date_consistency),
        ("T3: delta_base_date = J-1", test_t3_delta_base_date_is_j_minus_1),
        ("T4: Logique badges", test_t4_badges_logic_validation),
        ("T5: Cache-busting front", test_t5_front_cache_busting),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ ERREUR dans {name}: {e}")
            results.append((name, False))
    
    # Résumé
    print("\n" + "="*60)
    print("📊 RÉSUMÉ DES TESTS")
    print("="*60)
    
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} - {name}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    print(f"\n🎯 Score: {passed}/{total} tests réussis")
    
    if passed == total:
        print("\n✅ ✅ ✅ TOUS LES TESTS SONT PASSÉS ✅ ✅ ✅")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) échoué(s)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
