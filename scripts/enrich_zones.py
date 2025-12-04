import json
import uuid
import h3

INPUT = "docs/idf_hex_grid_res8.geojson"
OUTPUT = "docs/idf_hex_grid_ready.json"

def main():
    with open(INPUT, "r", encoding="utf-8") as f:
        data = json.load(f)

    zones = data["features"]


    for i, feature in enumerate(zones):
        props = feature.get("properties", {})
        h3_index = props.get("h3_index") or props.get("id")

        if not h3_index:
            continue

        lat, lng = h3.cell_to_latlng(h3_index)

        feature["properties"].update({
            "uuid": str(uuid.uuid4()),
            "id": f"IDF-{str(i+1).zfill(5)}",
            "latitude": lat,
            "longitude": lng,
            "city_code": "IDF",
            "manual_surge": 0,
            "available": True,
            "status": "active"
        })

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump({
            "type": "FeatureCollection",
            "features": zones
        }, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()