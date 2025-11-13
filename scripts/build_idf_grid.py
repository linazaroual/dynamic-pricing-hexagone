# scripts/build_idf_grid.py
# Génère une grille H3 (res=7 ≈ 1.2 km par côté) pour l'Île-de-France.
# Sorties :
#  - docs/idf_hex_grid_res7.json     (données "zones")
#  - docs/idf_hex_grid_res7.geojson  (pour Leaflet)

import os
import uuid
import json
import h3  # v4

# --- Paramètres généraux ---
RES = 7  # ≈ 1.2 km par côté (le plus proche de 1 km côté en H3)
SEED = (48.8566, 2.3522)  # centre de Paris, point de départ

# BBox simple de l'Île-de-France (approx) : à affiner plus tard si besoin
BBOX = {
    "minLat": 48.0,
    "minLng": 1.3,
    "maxLat": 49.3,
    "maxLng": 3.6,
}

# Nombre d'anneaux autour du centre (ajuste si besoin)
MAX_K = 110  # ça va largement couvrir l'IDF


def inside_bbox(lat: float, lng: float) -> bool:
    """Retourne True si le point (lat,lng) est dans la BBOX IDF."""
    return (
        BBOX["minLat"] <= lat <= BBOX["maxLat"]
        and BBOX["minLng"] <= lng <= BBOX["maxLng"]
    )


def cell_to_ring_lnglat(h: str):
    """
    h3.cell_to_boundary -> renvoie [[lat,lng], ...]
    Pour GeoJSON, on veut [ [ [lng,lat], ... , [lng0,lat0] ] ] (anneau fermé)
    """
    boundary = h3.cell_to_boundary(h)
    ring = [(lng, lat) for (lat, lng) in boundary]
    # fermer l'anneau :
    ring.append((boundary[0][1], boundary[0][0]))
    return [ring]


def main():
    os.makedirs("docs", exist_ok=True)

    # 1) On part d'une cellule H3 au centre de Paris
    seed_h = h3.latlng_to_cell(SEED[0], SEED[1], RES)

    # 2) On génère des anneaux autour du seed
    cells = set([seed_h])
    for k in range(1, MAX_K + 1):
        cells |= set(h3.grid_disk(seed_h, k))

    # 3) Filtrage par BBOX IDF
    filtered = []
    for c in cells:
        lat, lng = h3.cell_to_latlng(c)
        if inside_bbox(lat, lng):
            filtered.append(c)

    filtered = sorted(filtered)

    zones = []
    features = []

    # 4) Construction des "zones" + Features GeoJSON
    for i, c in enumerate(filtered, start=1):
        lat, lng = h3.cell_to_latlng(c)
        zone = {
            "uuid": str(uuid.uuid4()),
            "id": f"PAR-{i:04d}",
            "h3_index": c,
            "city_code": "PAR",  # pour l'instant on met PAR = région IDF
            "latitude": lat,
            "longitude": lng,
            "available": True,
            "manual_surge": 0,
            "status": "active",
        }
        zones.append(zone)

        ring = cell_to_ring_lnglat(c)
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Polygon", "coordinates": ring},
                "properties": zone,
            }
        )

    # 5) Sauvegarde JSON "données"
    with open("docs/idf_hex_grid_res7.json", "w", encoding="utf-8") as f:
        json.dump(zones, f, ensure_ascii=False, indent=2)

    # 6) Sauvegarde GeoJSON "affichage"
    geojson = {"type": "FeatureCollection", "features": features}
    with open("docs/idf_hex_grid_res7.geojson", "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)

    print(f"✅ Zones générées : {len(zones)}")
    print("→ docs/idf_hex_grid_res7.json")
    print("→ docs/idf_hex_grid_res7.geojson")


if __name__ == "__main__":
    main()