import json
from shapely.geometry import Point, shape
import h3
from tqdm import tqdm

INPUT = "docs/idf_hex_grid_res8.geojson"
DEPT_FILE = "docs/departements_idf.geojson"
OUTPUT = "docs/idf_hex_grid_ready.json"

def find_dept(lat, lng, departments):
    point = Point(lng, lat)
    for d in departments:
        geom = shape(d["geometry"])
        if geom.contains(point):
            return d["properties"].get("code")
    return "00"  

def main():
    with open(INPUT, "r", encoding="utf-8") as f:
        data = json.load(f)
    features = data["features"]

    with open(DEPT_FILE, "r", encoding="utf-8") as f:
        dept_data = json.load(f)

    departments = dept_data["features"]

    for feature in tqdm(features, desc="Enrichissement IDF"):
        h3_index = feature["properties"]["h3_index"]
        lat, lng = h3.cell_to_latlng(h3_index)

        dept_code = find_dept(lat, lng, departments)

        feature["properties"].update({
            "latitude": lat,
            "longitude": lng,
            "city_code": dept_code,
            "manual_surge": 0,
            "available": True,
            "status": "active"
        })

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump({
            "type": "FeatureCollection",
            "features": features
        }, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()