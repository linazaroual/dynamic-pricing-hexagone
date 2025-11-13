# scripts/build_idf_grid.py
# Génère une grille H3 (res=7 ≈ 1.2 km côté) pour une forme approchée de l'Île-de-France.
# Sorties :
#  - docs/idf_hex_grid_res7.json     (données zones)
#  - docs/idf_hex_grid_res7.geojson  (affichage Leaflet)

import os
import uuid
import json
import h3  # H3 v4


# --- Paramètres généraux ---
RES = 7  # ≈ 1.2 km par côté
SEED = (48.8566, 2.3522)  # centre Paris

# BBOX pour limiter les calculs (grosse boîte autour de l'IDF)
BBOX = {
    "minLat": 48.0,
    "minLng": 1.3,
    "maxLat": 49.3,
    "maxLng": 3.6,
}

# Polygone approché de l'Île-de-France (ordre autour de la région)
# (lat, lng)
IDF_POLY = [
    (48.05, 1.40),  # sud-ouest (proche Chartres)
    (48.25, 1.65),
    (48.40, 1.80),
    (48.55, 1.85),
    (48.70, 1.80),
    (48.90, 1.70),  # nord-ouest
    (49.10, 1.90),
    (49.20, 2.20),
    (49.25, 2.55),
    (49.20, 2.90),
    (49.05, 3.25),  # nord-est
    (48.80, 3.40),
    (48.55, 3.45),
    (48.35, 3.30),
    (48.20, 3.05),
    (48.05, 2.70),
    (48.00, 2.30),
    (48.02, 1.90),
    (48.05, 1.40),  # retour au début
]


def inside_bbox(lat: float, lng: float) -> bool:
    """Retourne True si le point (lat,lng) est dans la BBOX large IDF."""
    return (
        BBOX["minLat"] <= lat <= BBOX["maxLat"]
        and BBOX["minLng"] <= lng <= BBOX["maxLng"]
    )


def point_in_poly(lat: float, lng: float, poly) -> bool:
    """
    Test point-in-polygon (algorithme du rayon).
    poly = liste de (lat, lng).
    """
    x = lng
    y = lat
    inside = False
    n = len(poly)
    for i in range(n - 1):
        x1 = poly[i][1]
        y1 = poly[i][0]
        x2 = poly[i + 1][1]
        y2 = poly[i + 1][0]

        # Check intersection entre le segment [i,i+1] et le rayon horizontal
        if ((y1 > y) != (y2 > y)) and x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1:
            inside = not inside
    return inside


def cell_to_ring_lnglat(h: str):
    """
    h3.cell_to_boundary -> [[lat,lng], ...]
    Pour GeoJSON, on veut [ [ [lng,lat], ... , [lng0,lat0] ] ]
    """
    boundary = h3.cell_to_boundary(h)
    ring = [(lng, lat) for (lat, lng) in boundary]
    ring.append((boundary[0][1], boundary[0][0]))  # fermer l'anneau
    return [ring]


def main():
    os.makedirs("docs", exist_ok=True)

    # 1) cellule seed au centre de Paris
    seed_h = h3.latlng_to_cell(SEED[0], SEED[1], RES)

    # 2) on génère des anneaux autour du seed
    # k max : assez grand pour couvrir la région
    MAX_K = 110
    cells = set([seed_h])
    for k in range(1, MAX_K + 1):
        cells |= set(h3.grid_disk(seed_h, k))

    # 3) filtrage BBOX + polygone IDF
    filtered = []
    for c in cells:
        lat, lng = h3.cell_to_latlng(c)
        if not inside_bbox(lat, lng):
            continue
        if not point_in_poly(lat, lng, IDF_POLY):
            continue
        filtered.append(c)

    filtered = sorted(filtered)

    zones = []
    features = []

    # 4) construction des zones + GeoJSON
    for i, c in enumerate(filtered, start=1):
        lat, lng = h3.cell_to_latlng(c)
        zone = {
            "uuid": str(uuid.uuid4()),
            "id": f"PAR-{i:04d}",
            "h3_index": c,
            "city_code": "PAR",  # Paris Region
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

    # 5) JSON "données"
    with open("docs/idf_hex_grid_res7.json", "w", encoding="utf-8") as f:
        json.dump(zones, f, ensure_ascii=False, indent=2)

    # 6) GeoJSON "affichage"
    geojson = {"type": "FeatureCollection", "features": features}
    with open("docs/idf_hex_grid_res7.geojson", "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)

    print(f"✅ Zones générées (IDF shape) : {len(zones)}")
    print("→ docs/idf_hex_grid_res7.json")
    print("→ docs/idf_hex_grid_res7.geojson")


if __name__ == "__main__":
    main()