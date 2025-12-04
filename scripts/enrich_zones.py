
import json
import uuid

INPUT = "docs/idf_hex_grid_res8.json"
OUTPUT = "docs/idf_hex_grid_par_ready.json"
CITY_CODE = "PAR"


def generate_id(i):
    return f"{CITY_CODE}-{i:04d}"


def main():
    with open(INPUT, "r", encoding="utf-8") as f:
        zones = json.load(f)


    for i, z in enumerate(zones, start=1):
        z["id"] = generate_id(i)
        z["city_code"] = CITY_CODE
   
        z.setdefault("manual_surge", 0)
        z.setdefault("available", True)
        z.setdefault("status", "active")


    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(zones, f, indent=2)




if __name__ == "__main__":
    main()