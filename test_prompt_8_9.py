#!/usr/bin/env python3
"""
Tests automatisés pour le Prompt 8.9 : "Carte Date + SWR no-flicker + 5 min refresh"

Objectifs du Prompt 8.9 :
A) Carte "Date des données actuelles (Kworb: ...)" dans header
B) SWR (Stale-While-Revalidate) : dataset unifié + no flicker
C) Auto-refresh à 5 minutes

Tests :
- T1 : meta.json contient covers_revision et kworb_day
- T2 : songs.json et albums.json contiennent cover_url et album_name (dataset unifié)
- T3 : meta-refresh.js affiche date Kworb
- T4 : meta-refresh.js REFRESH_INTERVAL_S = 300 (5 minutes)
- T5 : data-renderer.js implémente updateSongsTableProgressive() et updateAlbumsTableProgressive()
- T6 : Image preloading présent (new Image().onload)
"""

import json
import sys
from pathlib import Path


def test_1_meta_json_fields():
    """T1 : Vérifier que meta.json contient covers_revision et kworb_day"""
    print("=" * 80)
    print("T1 : Vérification meta.json (covers_revision + kworb_day)")
    print("=" * 80)
    
    meta_path = Path("data/meta.json")
    if not meta_path.exists():
        print("❌ FAIL : data/meta.json introuvable")
        return False
    
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    
    # Vérifier covers_revision
    if "covers_revision" not in meta:
        print("❌ FAIL : covers_revision absent de meta.json")
        return False
    
    covers_revision = meta["covers_revision"]
    if not isinstance(covers_revision, str) or len(covers_revision) < 8:
        print(f"❌ FAIL : covers_revision invalide : {covers_revision}")
        return False
    
    print(f"✅ covers_revision présent : {covers_revision}")
    
    # Vérifier kworb_day
    if "kworb_day" not in meta:
        print("❌ FAIL : kworb_day absent de meta.json")
        return False
    
    kworb_day = meta["kworb_day"]
    if not isinstance(kworb_day, str) or len(kworb_day) != 10:
        print(f"❌ FAIL : kworb_day invalide : {kworb_day}")
        return False
    
    # Format YYYY-MM-DD
    try:
        year, month, day = kworb_day.split("-")
        if len(year) != 4 or len(month) != 2 or len(day) != 2:
            raise ValueError("Format incorrect")
    except Exception:
        print(f"❌ FAIL : kworb_day format incorrect : {kworb_day}")
        return False
    
    print(f"✅ kworb_day présent : {kworb_day}")
    print("✅ PASS : T1 validé\n")
    return True


def test_2_unified_dataset():
    """T2 : Vérifier que songs.json et albums.json contiennent cover_url et album_name"""
    print("=" * 80)
    print("T2 : Dataset unifié (cover_url + album_name dans songs.json/albums.json)")
    print("=" * 80)
    
    songs_path = Path("data/songs.json")
    albums_path = Path("data/albums.json")
    
    if not songs_path.exists():
        print("❌ FAIL : data/songs.json introuvable")
        return False
    
    if not albums_path.exists():
        print("❌ FAIL : data/albums.json introuvable")
        return False
    
    # Vérifier songs.json
    with open(songs_path, "r", encoding="utf-8") as f:
        songs = json.load(f)
    
    songs_with_covers = 0
    songs_with_album_names = 0
    
    for song in songs:
        if song.get("cover_url"):
            songs_with_covers += 1
        if song.get("album_name"):
            songs_with_album_names += 1
    
    print(f"Songs : {len(songs)} total")
    print(f"  - {songs_with_covers} avec cover_url ({songs_with_covers/len(songs)*100:.1f}%)")
    print(f"  - {songs_with_album_names} avec album_name ({songs_with_album_names/len(songs)*100:.1f}%)")
    
    if songs_with_covers < len(songs) * 0.95:
        print("❌ FAIL : Moins de 95% des songs ont un cover_url")
        return False
    
    if songs_with_album_names < len(songs) * 0.95:
        print("❌ FAIL : Moins de 95% des songs ont un album_name")
        return False
    
    # Vérifier albums.json
    with open(albums_path, "r", encoding="utf-8") as f:
        albums = json.load(f)
    
    albums_with_covers = 0
    albums_with_names = 0
    
    for album in albums:
        if album.get("cover_url"):
            albums_with_covers += 1
        if album.get("album_name"):
            albums_with_names += 1
    
    print(f"\nAlbums : {len(albums)} total")
    print(f"  - {albums_with_covers} avec cover_url ({albums_with_covers/len(albums)*100:.1f}%)")
    print(f"  - {albums_with_names} avec album_name ({albums_with_names/len(albums)*100:.1f}%)")
    
    if albums_with_covers < len(albums) * 0.85:
        print("❌ FAIL : Moins de 85% des albums ont un cover_url")
        return False
    
    if albums_with_names < len(albums) * 0.85:
        print("❌ FAIL : Moins de 85% des albums ont un album_name")
        return False
    
    print("✅ PASS : T2 validé\n")
    return True


def test_3_meta_refresh_kworb_display():
    """T3 : Vérifier que meta-refresh.js affiche la date Kworb"""
    print("=" * 80)
    print("T3 : meta-refresh.js affiche date Kworb")
    print("=" * 80)
    
    meta_refresh_path = Path("Website/src/meta-refresh.js")
    if not meta_refresh_path.exists():
        print("❌ FAIL : Website/src/meta-refresh.js introuvable")
        return False
    
    with open(meta_refresh_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Vérifier présence de meta.kworb_day
    if "meta.kworb_day" not in content:
        print("❌ FAIL : meta.kworb_day absent de meta-refresh.js")
        return False
    
    print("✅ meta.kworb_day utilisé")
    
    # Vérifier format d'affichage "(Kworb :"
    if "(Kworb :" not in content and "(Kworb:" not in content:
        print("⚠️ WARNING : Format '(Kworb :' non trouvé (peut être commenté)")
    else:
        print("✅ Format '(Kworb :' présent")
    
    print("✅ PASS : T3 validé\n")
    return True


def test_4_refresh_interval_5_min():
    """T4 : Vérifier que REFRESH_INTERVAL_S = 300 (5 minutes)"""
    print("=" * 80)
    print("T4 : meta-refresh.js REFRESH_INTERVAL_S = 300 (5 min)")
    print("=" * 80)
    
    meta_refresh_path = Path("Website/src/meta-refresh.js")
    if not meta_refresh_path.exists():
        print("❌ FAIL : Website/src/meta-refresh.js introuvable")
        return False
    
    with open(meta_refresh_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Vérifier REFRESH_INTERVAL_S = 300
    if "REFRESH_INTERVAL_S = 300" not in content:
        print("❌ FAIL : REFRESH_INTERVAL_S = 300 non trouvé")
        
        # Debug : chercher quelle valeur est définie
        for line in content.split("\n"):
            if "REFRESH_INTERVAL_S" in line and "const" in line:
                print(f"Trouvé : {line.strip()}")
        
        return False
    
    print("✅ REFRESH_INTERVAL_S = 300 confirmé")
    print("✅ PASS : T4 validé\n")
    return True


def test_5_swr_progressive_updates():
    """T5 : Vérifier que data-renderer.js implémente SWR (progressive updates)"""
    print("=" * 80)
    print("T5 : data-renderer.js SWR (updateSongsTableProgressive + updateAlbumsTableProgressive)")
    print("=" * 80)
    
    data_renderer_path = Path("Website/src/data-renderer.js")
    if not data_renderer_path.exists():
        print("❌ FAIL : Website/src/data-renderer.js introuvable")
        return False
    
    with open(data_renderer_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Vérifier updateSongsTableProgressive()
    if "updateSongsTableProgressive" not in content:
        print("❌ FAIL : updateSongsTableProgressive() absent")
        return False
    
    print("✅ updateSongsTableProgressive() présent")
    
    # Vérifier updateAlbumsTableProgressive()
    if "updateAlbumsTableProgressive" not in content:
        print("❌ FAIL : updateAlbumsTableProgressive() absent")
        return False
    
    print("✅ updateAlbumsTableProgressive() présent")
    
    # Vérifier qu'on ne vide plus le tbody (pas de tbody.innerHTML = '')
    # Doit être conditionnel : premier render = clear, refresh = progressive
    if "tbody.innerHTML = '';" in content and "if (!this.lastRenderedData.songs" in content:
        print("✅ Clear conditionnel présent (initial render only)")
    else:
        print("⚠️ WARNING : Clear conditionnel peut être modifié")
    
    print("✅ PASS : T5 validé\n")
    return True


def test_6_image_preloading():
    """T6 : Vérifier que le preloading d'images est implémenté"""
    print("=" * 80)
    print("T6 : Image preloading (new Image().onload)")
    print("=" * 80)
    
    data_renderer_path = Path("Website/src/data-renderer.js")
    if not data_renderer_path.exists():
        print("❌ FAIL : Website/src/data-renderer.js introuvable")
        return False
    
    with open(data_renderer_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Vérifier présence de new Image()
    if "new Image()" not in content:
        print("❌ FAIL : new Image() absent (pas de preloading)")
        return False
    
    print("✅ new Image() présent")
    
    # Vérifier preloadImg.onload
    if "preloadImg.onload" not in content and ".onload" not in content:
        print("❌ FAIL : preloadImg.onload absent")
        return False
    
    print("✅ preloadImg.onload présent")
    
    # Vérifier preloadImg.onerror
    if "preloadImg.onerror" not in content and ".onerror" not in content:
        print("⚠️ WARNING : preloadImg.onerror absent (pas de fallback)")
    else:
        print("✅ preloadImg.onerror présent")
    
    print("✅ PASS : T6 validé\n")
    return True


def main():
    print("\n" + "=" * 80)
    print("TESTS AUTOMATISÉS - PROMPT 8.9")
    print("Carte Date + SWR no-flicker + 5 min refresh")
    print("=" * 80 + "\n")
    
    tests = [
        ("T1 : meta.json (covers_revision + kworb_day)", test_1_meta_json_fields),
        ("T2 : Dataset unifié (cover_url + album_name)", test_2_unified_dataset),
        ("T3 : meta-refresh.js affiche Kworb", test_3_meta_refresh_kworb_display),
        ("T4 : REFRESH_INTERVAL_S = 300 (5 min)", test_4_refresh_interval_5_min),
        ("T5 : SWR progressive updates", test_5_swr_progressive_updates),
        ("T6 : Image preloading", test_6_image_preloading),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ ERREUR dans {name} : {e}\n")
            results.append((name, False))
    
    # Résumé
    print("\n" + "=" * 80)
    print("RÉSUMÉ DES TESTS")
    print("=" * 80)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} : {name}")
    
    print(f"\nRésultat : {passed}/{total} tests passés")
    
    if passed == total:
        print("🎉 TOUS LES TESTS SONT PASSÉS !")
        return 0
    else:
        print(f"⚠️ {total - passed} test(s) échoué(s)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
