import json
import time
import requests
from tqdm import tqdm

MAILTO = "manarfraihat85@gmail.com"
TARGET_RECORDS = 100000
PER_PAGE = 200

BASE_URL = "https://api.openalex.org/works"

params = {
    "filter": (
        "from_publication_date:2020-01-01,"
        "to_publication_date:2025-12-31,"
        "has_doi:true"
    ),
    "search": "graph database knowledge graph information systems",
    "per-page": PER_PAGE,
    "cursor": "*",
    "mailto": MAILTO,
    "select": (
        "id,doi,title,publication_year,publication_date,type,language,"
        "open_access,primary_location,authorships,topics,concepts"
    )
}

output_file = "openalex_works_100k.jsonl"

count = 0

with open(output_file, "w", encoding="utf-8") as f:
    pbar = tqdm(total=TARGET_RECORDS)

    while count < TARGET_RECORDS:
        try:
            response = requests.get(BASE_URL, params=params, timeout=60)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            print("Waiting 10 seconds and trying again...")
            time.sleep(10)
            continue

        data = response.json()
        results = data.get("results", [])

        if not results:
            print("No more results returned.")
            break

        for work in results:
            f.write(json.dumps(work, ensure_ascii=False) + "\n")
            count += 1
            pbar.update(1)

            if count >= TARGET_RECORDS:
                break

        next_cursor = data.get("meta", {}).get("next_cursor")

        if not next_cursor:
            print("No next cursor returned.")
            break

        params["cursor"] = next_cursor
        time.sleep(2.0)

    pbar.close()

print(f"Downloaded {count} records to {output_file}")