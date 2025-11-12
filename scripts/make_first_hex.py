# scripts/make_first_hex.py
# Crée un hexagone centré exactement sur Paris (48.8566, 2.3522)
# de taille ≈ 1 km de diamètre (résolution H3 = 8)

import os, uuid, json, h3
from geojson import Feature, FeatureCollection, Polygon

def main():
    os.makedirs("docs", exist_ok=True)

    # --- Centre géographique de Paris ---
    center_lat, center_lng = 48.866667, 2.333333

    # --- Taille de l’hexagone (≈ 1 km de diamètre) ---
    RES = 8  # chaque côté ≈ 0.46 km, donc largeur totale ≈ 1 km

    # --- Calcul H3 (v4) ---
    h = h3.latlng_to_cell(center_lat, center_lng, RES)
    lat, lng = h3.cell_to_latlng(h)
    boundary = h3.cell_to_boundary(h)  # [[lat, lng], ...]

    # --- Objet "zone" ---
    zone = {
        "uuid": str(uuid.uuid4()),
        "id": "PAR-CENTER",
        "h3_index": h,
        "city_code": "PAR",
        "latitude": lat,
        "longitude": lng,
        "available": True,
        "manual_surge": 0,
        "status": "active"
    }

    # --- Sauvegarde JSON (data) ---
    with open("docs/paris_center_hex.json", "w", encoding="utf-8") as f:
        json.dump(zone, f, ensure_ascii=False, indent=2)

    # --- Sauvegarde GeoJSON (affichage) ---
    ring = [[(lng_, lat_) for (lat_, lng_) in boundary] + [(boundary[0][1], boundary[0][0])]]
    poly = Feature(geometry=Polygon(ring), properties=zone)
    fc = FeatureCollection([poly])

    with open("docs/paris_center_hex.geojson", "w", encoding="utf-8") as f:
        json.dump(fc, f, ensure_ascii=False, indent=2)

    print("✅ OK - Hexagone centré sur Paris généré !")
    print("H3 Index :", h)
    print("Fichiers : docs/paris_center_hex.json & docs/paris_center_hex.geojson")

if __name__ == "__main__":
    main()

