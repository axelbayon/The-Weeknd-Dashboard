#!/usr/bin/env python3
"""
Générateur de vues courantes avec règles de calcul (variation, paliers, jours restants).
Lit les snapshots historiques et produit data/songs.json et data/albums.json.
"""

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
    cap_step: int
) -> List[Dict]:
    """
    Génère la vue courante avec calculs à partir de J et J-1.
    
    Args:
        current_snapshot: Données du jour J
        previous_snapshot: Données du jour J-1
        cap_step: Pas du palier (100M pour songs, 1B pour albums)
    """
    # Index par id pour lookup rapide
    prev_by_id = {item["id"]: item for item in previous_snapshot}
    
    result = []
    
    for current in current_snapshot:
        item_id = current["id"]
        
        # Récupérer streams_daily_prev, rank_prev ET streams_total_prev depuis J-1
        prev_item = prev_by_id.get(item_id)
        streams_daily_prev = prev_item["streams_daily"] if prev_item else None
        streams_total_prev = prev_item["streams_total"] if prev_item else None
        rank_prev = prev_item["rank"] if prev_item else None
        
        # Calcul du delta de rang (positif = gain de places, négatif = perte)
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
        
        # Construire l'objet enrichi
        enriched = {
            **current,
            "streams_daily_prev": streams_daily_prev,
            "rank_prev": rank_prev,
            "rank_delta": rank_delta,
            "variation_pct": variation_pct,
            "next_cap_value": next_cap_value,
            "days_to_next_cap": days_to_next_cap,
            "spotify_track_id": current.get("spotify_track_id"),
            "spotify_album_id": current.get("spotify_album_id")
        }
        
        result.append(enriched)
    
    return result


def main():
    """Point d'entrée principal."""
    # Chemins
    base_path = Path(__file__).parent.parent
    history_songs = base_path / "data" / "history" / "songs"
    history_albums = base_path / "data" / "history" / "albums"
    
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
    
    # Générer vues courantes
    songs_current = generate_current_view(songs_j, songs_j1, 100_000_000)
    albums_current = generate_current_view(albums_j, albums_j1, 1_000_000_000)
    
    # Sauvegarder
    with open(base_path / "data" / "songs.json", "w", encoding="utf-8") as f:
        json.dump(songs_current, f, indent=2, ensure_ascii=False)
    
    with open(base_path / "data" / "albums.json", "w", encoding="utf-8") as f:
        json.dump(albums_current, f, indent=2, ensure_ascii=False)
    
    print("OK Vues courantes generees avec succes")
    print(f"   - {len(songs_current)} chansons dans data/songs.json")
    print(f"   - {len(albums_current)} albums dans data/albums.json")


if __name__ == "__main__":
    main()
