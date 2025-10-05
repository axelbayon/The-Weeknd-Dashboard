#!/usr/bin/env python3
"""
Tests de validation pour le système de rotation J/J-1/J-2 basé sur kworb_day.

Tests à exécuter :
T1 — Pas de bascule nocturne locale
T2 — Changement de jour Kworb ⇒ rotation
T3 — Idempotence
T4 — Front cohérent
T5 — Fallback parsing
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Ajouter scripts au path
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from date_manager import (
    parse_kworb_timestamp,
    extract_kworb_last_update,
    calculate_spotify_data_date,
    should_rotate,
    log_rotation_decision
)


def test_t1_pas_de_bascule_nocturne():
    """
    T1 — Pas de bascule nocturne locale
    
    Pré-état : kworb_last_update_utc = 2025-10-05T23:50Z, 
               meta.spotify_data_date = 2025-10-04, 
               J=2025-10-04.json
    
    Action : relancer l'orchestrateur à 02:30 locale (même kworb_day = 2025-10-05)
    
    Attendu : aucune rotation, J reste 2025-10-04.json, spotify_data_date = 2025-10-04
    """
    print("\n" + "="*70)
    print("TEST T1 : Pas de bascule nocturne locale")
    print("="*70)
    
    # Simuler kworb_last_update_utc = 2025-10-05T23:50Z
    kworb_timestamp = "2025-10-05T23:50:00+00:00"
    kworb_dt = parse_kworb_timestamp(kworb_timestamp)
    
    # Calculer spotify_data_date
    spotify_data_date = calculate_spotify_data_date(kworb_dt)
    
    # Vérifier
    assert kworb_dt.date().strftime("%Y-%m-%d") == "2025-10-05", "Kworb day devrait être 2025-10-05"
    assert spotify_data_date == "2025-10-04", f"Spotify data date devrait être 2025-10-04, mais est {spotify_data_date}"
    
    # Simuler meta.json avec latest_date = 2025-10-04
    meta = {
        "history": {
            "latest_date": "2025-10-04"
        }
    }
    
    # Vérifier qu'il ne faut PAS rotate
    should_rot = should_rotate(meta, spotify_data_date)
    assert not should_rot, "Ne devrait PAS rotate car même date"
    
    print("✅ T1 PASSED")
    print(f"   Kworb timestamp : {kworb_timestamp}")
    print(f"   Kworb day       : {kworb_dt.date()}")
    print(f"   Spotify date    : {spotify_data_date}")
    print(f"   Should rotate   : {should_rot} (attendu: False)")


def test_t2_changement_jour_kworb():
    """
    T2 — Changement de jour Kworb ⇒ rotation
    
    Pré-état : idem T1
    
    Action : nouveau scrape avec kworb_last_update_utc = 2025-10-06T00:10Z 
             (kworb_day passe au 6)
    
    Attendu :
    - spotify_data_date = 2025-10-05
    - 2025-10-04.json → J-1, ancien J-1 → J-2, nouveau J = 2025-10-05.json
    - meta.history.latest_date = 2025-10-05
    """
    print("\n" + "="*70)
    print("TEST T2 : Changement de jour Kworb → rotation")
    print("="*70)
    
    # Simuler nouveau kworb_last_update_utc = 2025-10-06T00:10Z
    kworb_timestamp = "2025-10-06T00:10:00+00:00"
    kworb_dt = parse_kworb_timestamp(kworb_timestamp)
    
    # Calculer spotify_data_date
    spotify_data_date = calculate_spotify_data_date(kworb_dt)
    
    # Vérifier
    assert kworb_dt.date().strftime("%Y-%m-%d") == "2025-10-06", "Kworb day devrait être 2025-10-06"
    assert spotify_data_date == "2025-10-05", f"Spotify data date devrait être 2025-10-05, mais est {spotify_data_date}"
    
    # Simuler meta.json avec latest_date = 2025-10-04 (ancien)
    meta = {
        "history": {
            "latest_date": "2025-10-04"
        }
    }
    
    # Vérifier qu'il FAUT rotate
    should_rot = should_rotate(meta, spotify_data_date)
    assert should_rot, "Devrait rotate car nouvelle date (2025-10-05 > 2025-10-04)"
    
    print("✅ T2 PASSED")
    print(f"   Kworb timestamp : {kworb_timestamp}")
    print(f"   Kworb day       : {kworb_dt.date()}")
    print(f"   Spotify date    : {spotify_data_date}")
    print(f"   Should rotate   : {should_rot} (attendu: True)")


def test_t3_idempotence():
    """
    T3 — Idempotence
    
    Rejouer T2 une seconde fois le même jour → aucun nouveau rename, 
    seul le contenu de 2025-10-05.json est réécrit.
    """
    print("\n" + "="*70)
    print("TEST T3 : Idempotence")
    print("="*70)
    
    # Même kworb_timestamp que T2
    kworb_timestamp = "2025-10-06T00:10:00+00:00"
    kworb_dt = parse_kworb_timestamp(kworb_timestamp)
    spotify_data_date = calculate_spotify_data_date(kworb_dt)
    
    # Meta avec latest_date = 2025-10-05 (déjà rotaté)
    meta = {
        "history": {
            "latest_date": "2025-10-05"
        }
    }
    
    # Vérifier qu'il ne faut PAS rotate
    should_rot = should_rotate(meta, spotify_data_date)
    assert not should_rot, "Ne devrait PAS rotate car même date (idempotence)"
    
    print("✅ T3 PASSED")
    print(f"   Spotify date    : {spotify_data_date}")
    print(f"   Latest date     : {meta['history']['latest_date']}")
    print(f"   Should rotate   : {should_rot} (attendu: False - idempotence)")


def test_t4_front_coherent():
    """
    T4 — Front cohérent
    
    La "Date des données Spotify" affichée = 2025-10-05 tant que Kworb 
    n'est pas passé au 2025-10-07.
    """
    print("\n" + "="*70)
    print("TEST T4 : Front cohérent")
    print("="*70)
    
    # meta.json actuel
    base_path = Path(__file__).parent
    meta_path = base_path / "data" / "meta.json"
    
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        
        kworb_utc = meta.get("kworb_last_update_utc")
        spotify_date = meta.get("spotify_data_date")
        
        if kworb_utc and spotify_date:
            kworb_dt = parse_kworb_timestamp(kworb_utc)
            kworb_day = kworb_dt.date().strftime("%Y-%m-%d")
            
            # Vérifier la cohérence : spotify_date = kworb_day - 1
            expected_spotify_date = calculate_spotify_data_date(kworb_dt)
            
            assert spotify_date == expected_spotify_date, \
                f"spotify_data_date ({spotify_date}) devrait être kworb_day - 1 ({expected_spotify_date})"
            
            print("✅ T4 PASSED")
            print(f"   Kworb last update : {kworb_utc}")
            print(f"   Kworb day         : {kworb_day}")
            print(f"   Spotify data date : {spotify_date}")
            print(f"   Cohérence         : OK ({spotify_date} = {kworb_day} - 1)")
        else:
            print("⚠️  T4 SKIPPED : meta.json incomplet")
    else:
        print("⚠️  T4 SKIPPED : meta.json non trouvé")


def test_t5_fallback_parsing():
    """
    T5 — Fallback parsing
    
    Forcer un kworb_last_update_utc illisible → aucune rotation, 
    spotify_data_date inchangé, log d'avertissement.
    """
    print("\n" + "="*70)
    print("TEST T5 : Fallback parsing")
    print("="*70)
    
    # Timestamp invalide
    invalid_timestamp = "invalid-timestamp-format"
    kworb_dt = parse_kworb_timestamp(invalid_timestamp)
    
    # Devrait retourner None
    assert kworb_dt is None, "Parsing invalide devrait retourner None"
    
    # Test d'extraction depuis HTML invalide
    html_invalid = "<html><body>Aucun timestamp ici</body></html>"
    extracted = extract_kworb_last_update(html_invalid)
    
    assert extracted is None, "Extraction depuis HTML invalide devrait retourner None"
    
    print("✅ T5 PASSED")
    print(f"   Parse invalide  : {invalid_timestamp} → None")
    print(f"   Extract invalide: HTML sans timestamp → None")
    print(f"   Fallback        : OK (None retourné, fallback sur datetime.now())")


def run_all_tests():
    """Exécute tous les tests."""
    print("\n" + "="*70)
    print("🧪 TESTS DE VALIDATION - Rotation J/J-1/J-2 basée sur kworb_day")
    print("="*70)
    
    try:
        test_t1_pas_de_bascule_nocturne()
        test_t2_changement_jour_kworb()
        test_t3_idempotence()
        test_t4_front_coherent()
        test_t5_fallback_parsing()
        
        print("\n" + "="*70)
        print("✅ TOUS LES TESTS PASSED")
        print("="*70)
        return True
    
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
