import json
import uuid
import h3
from shapely.geometry import Point, shape

INPUT = "docs/idf_hex_grid_res8.geojson"
OUTPUT = "docs/idf_hex_grid_ready.json"
DEPT_FILE = "docs/departements_idf.geojson"

def load_departments():
    with open(DEPT_FILE, "r", encoding="utf-8") as f:
        gj = json.load(f)
    return [(shape(feat["geometry"]), feat["properties"]["code_insee"]) for feat in gj["features"]]

def find_department(lat, lng, departments):
    pt = Point(lng, lat)
    for geom, code in departments:
        if geom.contains(pt):
            return code
    return "00"  

def main():
    with open(INPUT, "r", encoding="utf-8") as f:
        data = json.load(f)

    features = data["features"]

    departments = load_departments()

    counters = {}

    for feature in features:
        h3_index = feature.get("id") or feature["properties"].get("h3_index")

        lat, lng = h3.cell_to_latlng(h3_index)
        dept = find_department(lat, lng, departments)

        counters.setdefault(dept, 0)
        counters[dept] += 1
        zone_id = f"{dept}-{counters[dept]:05d}"

        feature["properties"].update({
            "uuid": str(uuid.uuid4()),
            "id": zone_id,
            "h3_index": h3_index,
            "latitude": lat,
            "longitude": lng,
            "city_code": dept,
            "manual_surge": 0,
            "available": True,
            "status": "active"
        })

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": features}, f, ensure_ascii=False, indent=2)



if __name__ == "__main__":
    main()