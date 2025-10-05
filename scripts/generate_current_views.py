#!/usr/bin/env python3
"""
Générateur de vues courantes avec règles de calcul (variation, paliers, jours restants).
Lit les snapshots historiques et produit data/songs.json et data/albums.json.
"""

import hashlib
import json
import math
from pathlib import Path
from typing import Dict, List, Optional, Union


def normalize_key(title: str, album: str) -> str:
    """
    Normalise une clé d'alignement inter-jours.
    
    Règles :
    - lowercasing
    - trim
    - suppression ponctuation
    - "feat./with/x/& (...)" retirés
    """
    def clean(text: str) -> str:
        # Lowercase et trim
        text = text.lower().strip()
        
        # Retirer les patterns de featuring
        patterns = [
            " feat.", " feat ", " featuring ", " ft.", " ft ",
            " with ", " x ", " & ", " and "
        ]
        for pattern in patterns:
            if pattern in text:
                text = text.split(pattern)[0]
        
        # Retirer parenthèses et leur contenu
        if "(" in text:
            text = text.split("(")[0].strip()
        
        # Retirer ponctuation
        punctuation = ".,;:!?'\"-"
        for char in punctuation:
            text = text.replace(char, "")
        
        return text.strip()
    
    norm_title = clean(title)
    norm_album = clean(album)
    
    return f"kworb:{norm_title}@{norm_album}"


def calculate_variation_pct(
    streams_daily: float, 
    streams_daily_prev: Optional[float],
    streams_total: float,
    streams_total_prev: Optional[float]
) -> Union[float, str]:
    """
    Calcule la variation % entre J et J-1.
    Retourne un nombre arrondi à 2 décimales ou "N.D." si non calculable.
    
    Règle importante : Si streams_total == streams_total_prev, 
    alors les données ne sont PAS à jour (Spotify pas encore rafraîchi).
    Dans ce cas, retourner "N.D." même si streams_daily existe.
    """
    # Si streams_total n'a pas changé, les données ne sont pas à jour
    if streams_total_prev is not None and streams_total == streams_total_prev:
        return "N.D."
    
    # Si pas de données J-1 ou invalides
    if streams_daily_prev is None or streams_daily_prev <= 0:
        return "N.D."
    
    # Calcul normal de la variation
    variation = ((streams_daily - streams_daily_prev) / streams_daily_prev) * 100
    return round(variation, 2)


def calculate_next_cap(streams_total: float, step: int) -> int:
    """
    Calcule le prochain palier (multiple de step supérieur strict).
    """
    return math.ceil(streams_total / step) * step


def calculate_days_to_cap(next_cap_value: int, streams_total: float, streams_daily: float) -> Union[float, str]:
    """
    Calcule le nombre de jours estimés pour atteindre le palier.
    Retourne un nombre arrondi à 2 décimales ou "N.D." si non calculable.
    """
    if streams_daily <= 0:
        return "N.D."
    
    days = (next_cap_value - streams_total) / streams_daily
    return round(days, 2)


def load_snapshot(filepath: Path) -> List[Dict]:
    """Charge un snapshot JSON."""
    if not filepath.exists():
        return []
    
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_current_view(
    current_snapshot: List[Dict],
    previous_snapshot: List[Dict],
    cap_step: int,
    date_j: str,
    date_j1: Optional[str],
    covers_cache: Optional[Dict[str, Dict]] = None
) -> List[Dict]:
    """
    Génère la vue courante avec calculs à partir de J et J-1.
    Prompt 8.9: Injecte cover_url et album_name depuis covers_cache (dataset unifié).
    
    Args:
        current_snapshot: Données du jour J
        previous_snapshot: Données du jour J-1
        cap_step: Pas du palier (100M pour songs, 1B pour albums)
        date_j: Date du snapshot J (YYYY-MM-DD) - pour delta_for_date
        date_j1: Date du snapshot J-1 (YYYY-MM-DD) - pour delta_base_date
        covers_cache: Dict {id: {cover_url, album_name, ...}} pour injection
    """
    # Index par id pour lookup rapide
    prev_by_id = {item["id"]: item for item in previous_snapshot}
    covers_cache = covers_cache or {}
    
    result = []
    
    for current in current_snapshot:
        item_id = current["id"]
        
        # Récupérer streams_daily_prev, rank_prev ET streams_total_prev depuis J-1
        prev_item = prev_by_id.get(item_id)
        streams_daily_prev = prev_item["streams_daily"] if prev_item else None
        streams_total_prev = prev_item["streams_total"] if prev_item else None
        rank_prev = prev_item["rank"] if prev_item else None
        
        # Calcul du delta de rang (positif = gain de places, négatif = perte)
        # Prompt 8.8 : Toujours recalculé à neuf chaque jour, strictement J vs J-1
        rank_delta = None
        if rank_prev is not None:
            rank_delta = rank_prev - current["rank"]
        
        # Calculs (avec détection "Non mis-à-jour" si streams_total inchangé)
        variation_pct = calculate_variation_pct(
            current["streams_daily"], 
            streams_daily_prev,
            current["streams_total"],
            streams_total_prev
        )
        next_cap_value = calculate_next_cap(current["streams_total"], cap_step)
        days_to_next_cap = calculate_days_to_cap(
            next_cap_value,
            current["streams_total"],
            current["streams_daily"]
        )
        
        # Prompt 8.9: Enrichir avec cover_url et album_name depuis covers_cache
        cover_data = covers_cache.get(item_id, {})
        cover_url = cover_data.get("cover_url")
        album_name = cover_data.get("album_name")
        
        # Construire l'objet enrichi
        # Prompt 8.8 : Ajouter delta_base_date et delta_for_date pour traçabilité
        enriched = {
            **current,
            "streams_daily_prev": streams_daily_prev,
            "rank_prev": rank_prev,
            "rank_delta": rank_delta,
            "delta_base_date": date_j1,  # Date utilisée pour rank_prev (J-1)
            "delta_for_date": date_j,     # Date courante (J)
            "variation_pct": variation_pct,
            "next_cap_value": next_cap_value,
            "days_to_next_cap": days_to_next_cap,
            "spotify_track_id": current.get("spotify_track_id"),
            "spotify_album_id": current.get("spotify_album_id"),
            # Prompt 8.9: Dataset unifié
            "cover_url": cover_url,
            "album_name": album_name
        }
        
        result.append(enriched)
    
    return result


def load_covers_cache(filepath: Path) -> Dict[str, Dict]:
    """
    Charge le cache de covers depuis songs.json/albums.json existants.
    Prompt 8.9: Extrait cover_url et album_name pour réinjection dans dataset unifié.
    Retourne un dict indexé par id avec {cover_url, album_name}.
    """
    if not filepath.exists():
        return {}
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            items_list = json.load(f)
        
        # Extraire uniquement id, cover_url, album_name
        covers_dict = {}
        for item in items_list:
            item_id = item.get("id")
            if item_id:
                covers_dict[item_id] = {
                    "cover_url": item.get("cover_url"),
                    "album_name": item.get("album_name")
                }
        
        return covers_dict
    except Exception as e:
        print(f"WARNING Impossible de charger covers depuis {filepath}: {e}")
        return {}


def calculate_covers_revision(songs_data: List[Dict], albums_data: List[Dict]) -> str:
    """
    Prompt 8.9: Calcule un hash des covers pour tracking des changements.
    
    Combine tous les cover_url et album_name pour détecter les modifications
    de covers ou d'albums, permettant au frontend de savoir si un refresh
    des images est nécessaire.
    
    Returns:
        Hash SHA-256 (premiers 12 caractères) représentant l'état actuel des covers
    """
    # Extraire toutes les covers (songs + albums)
    all_covers = []
    
    for song in songs_data:
        cover = song.get("cover_url", "")
        album = song.get("album_name", "")
        if cover or album:
            all_covers.append(f"{song.get('id')}:{cover}:{album}")
    
    for album in albums_data:
        cover = album.get("cover_url", "")
        album_name = album.get("album_name", "")
        if cover or album_name:
            all_covers.append(f"{album.get('id')}:{cover}:{album_name}")
    
    # Trier pour consistance
    all_covers.sort()
    
    # Calculer hash
    covers_string = "|".join(all_covers)
    hash_full = hashlib.sha256(covers_string.encode("utf-8")).hexdigest()
    
    # Retourner premiers 12 caractères (suffisant pour tracking)
    return hash_full[:12]


def extract_kworb_day(meta_path: Path) -> Optional[str]:
    """
    Prompt 8.9: Extrait la date YYYY-MM-DD depuis kworb_last_update_utc.
    
    Utilisé pour afficher "Date des données actuelles : ... (Kworb : YYYY-MM-DD)"
    dans le frontend.
    
    Returns:
        Date au format YYYY-MM-DD ou None si non disponible
    """
    if not meta_path.exists():
        return None
    
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    
    kworb_utc = meta.get("kworb_last_update_utc")
    if not kworb_utc:
        return None
    
    # Extraire la date (format ISO 8601: 2025-10-05T00:00:00+00:00)
    try:
        date_part = kworb_utc.split("T")[0]  # "2025-10-05"
        return date_part
    except Exception:
        return None


def update_meta_with_covers_info(meta_path: Path, covers_revision: str, kworb_day: Optional[str]) -> None:
    """
    Prompt 8.9: Met à jour meta.json avec covers_revision et kworb_day.
    
    Args:
        meta_path: Chemin vers meta.json
        covers_revision: Hash des covers actuelles
        kworb_day: Date Kworb au format YYYY-MM-DD
    """
    if not meta_path.exists():
        print("⚠️  meta.json introuvable, impossible d'ajouter covers_revision/kworb_day")
        return
    
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    
    # Ajouter les nouveaux champs
    meta["covers_revision"] = covers_revision
    if kworb_day:
        meta["kworb_day"] = kworb_day
    
    # Sauvegarder
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    
    print(f"✅ meta.json mis à jour : covers_revision={covers_revision}, kworb_day={kworb_day}")


def main():
    """Point d'entrée principal."""
    # Chemins
    base_path = Path(__file__).parent.parent
    history_songs = base_path / "data" / "history" / "songs"
    history_albums = base_path / "data" / "history" / "albums"
    
    # Prompt 8.9: Charger les covers depuis songs.json/albums.json EXISTANTS
    # (qui ont été enrichis par enrich_covers.py)
    songs_json_path = base_path / "data" / "songs.json"
    albums_json_path = base_path / "data" / "albums.json"
    covers_songs = load_covers_cache(songs_json_path)
    covers_albums = load_covers_cache(albums_json_path)
    
    print(f"[Covers] {len(covers_songs)} songs, {len(covers_albums)} albums chargés depuis cache")
    
    # Charger meta.json pour obtenir les dates disponibles
    meta_path = base_path / "data" / "meta.json"
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        available_dates = meta.get("history", {}).get("available_dates", [])
    else:
        # Fallback : scanner le dossier history/songs
        available_dates = []
        if history_songs.exists():
            for file in sorted(history_songs.glob("*.json"), reverse=True):
                available_dates.append(file.stem)
    
    if not available_dates:
        print("Aucun snapshot disponible. Génération impossible.")
        return
    
    # Utiliser les dates les plus récentes disponibles
    date_j = available_dates[0] if len(available_dates) > 0 else None
    date_j1 = available_dates[1] if len(available_dates) > 1 else None
    
    if not date_j:
        print("Aucune date J trouvée")
        return
    
    print(f"Utilisation des snapshots : J={date_j}, J-1={date_j1 or 'N/A'}")
    
    # Charger snapshots
    songs_j = load_snapshot(history_songs / f"{date_j}.json")
    songs_j1 = load_snapshot(history_songs / f"{date_j1}.json") if date_j1 else []
    albums_j = load_snapshot(history_albums / f"{date_j}.json")
    albums_j1 = load_snapshot(history_albums / f"{date_j1}.json") if date_j1 else []
    
    # Générer vues courantes avec covers injectées (Prompt 8.9: dataset unifié)
    songs_current = generate_current_view(songs_j, songs_j1, 100_000_000, date_j, date_j1, covers_songs)
    albums_current = generate_current_view(albums_j, albums_j1, 1_000_000_000, date_j, date_j1, covers_albums)
    
    # Compter combien ont des covers
    songs_with_covers = sum(1 for s in songs_current if s.get("cover_url"))
    albums_with_covers = sum(1 for a in albums_current if a.get("cover_url"))
    
    # Sauvegarder
    with open(base_path / "data" / "songs.json", "w", encoding="utf-8") as f:
        json.dump(songs_current, f, indent=2, ensure_ascii=False)
    
    with open(base_path / "data" / "albums.json", "w", encoding="utf-8") as f:
        json.dump(albums_current, f, indent=2, ensure_ascii=False)
    
    print("OK Vues courantes generees avec succes")
    print(f"   - {len(songs_current)} chansons dans data/songs.json ({songs_with_covers} avec cover)")
    print(f"   - {len(albums_current)} albums dans data/albums.json ({albums_with_covers} avec cover)")
    
    # Prompt 8.9: Calcul covers_revision (hash des covers pour tracking changements)
    covers_revision = calculate_covers_revision(songs_current, albums_current)
    
    # Prompt 8.9: Extraction kworb_day depuis kworb_last_update_utc
    kworb_day = extract_kworb_day(meta_path)
    
    # Mise à jour meta.json avec les nouveaux champs
    update_meta_with_covers_info(meta_path, covers_revision, kworb_day)


if __name__ == "__main__":
    main()
