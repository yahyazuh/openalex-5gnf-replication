import json
import csv
from pathlib import Path
from tqdm import tqdm

INPUT_FILE = "openalex_works_100k.jsonl"
OUTPUT_DIR = Path("neo4j_csv")
OUTPUT_DIR.mkdir(exist_ok=True)

works_csv = OUTPUT_DIR / "works.csv"
metadata_csv = OUTPUT_DIR / "metadata_values.csv"
work_metadata_csv = OUTPUT_DIR / "work_metadata_edges.csv"
concepts_csv = OUTPUT_DIR / "concepts.csv"
work_concepts_csv = OUTPUT_DIR / "work_concepts_edges.csv"
sources_csv = OUTPUT_DIR / "sources.csv"
work_sources_csv = OUTPUT_DIR / "work_sources_edges.csv"

metadata_values = {}
concepts = {}
sources = {}

work_metadata_edges = set()
work_concepts_edges = set()
work_sources_edges = set()

def safe(value):
    if value is None:
        return ""
    return str(value).replace("\n", " ").replace("\r", " ").strip()


def openalex_short_id(openalex_id):
    if not openalex_id:
        return ""
    return str(openalex_id).rstrip("/").split("/")[-1]


def add_metadata(work_id, category, value):
    value = safe(value)
    if not value:
        return

    meta_id = f"{category}:{value}".lower().replace(" ", "_")

    metadata_values[meta_id] = {
        "metadata_id": meta_id,
        "category": category,
        "value": value
    }

    work_metadata_edges.add((work_id, meta_id, category))

def add_source(work_id, source_obj):
    if not isinstance(source_obj, dict):
        return

    source_id_raw = source_obj.get("id")
    source_id = openalex_short_id(source_id_raw)

    if not source_id:
        return

    sources[source_id] = {
        "source_id": source_id,
        "openalex_id": safe(source_id_raw),
        "display_name": safe(source_obj.get("display_name")),
        "type": safe(source_obj.get("type")),
        "issn_l": safe(source_obj.get("issn_l")),
        "is_oa": safe(source_obj.get("is_oa"))
    }

    work_sources_edges.add((work_id, source_id))
def add_concepts(work_id, work):
    concept_list = work.get("concepts") or []

    for c in concept_list:
        if not isinstance(c, dict):
            continue

        concept_id_raw = c.get("id")
        concept_id = openalex_short_id(concept_id_raw)

        if not concept_id:
            continue

        concepts[concept_id] = {
            "concept_id": concept_id,
            "openalex_id": safe(concept_id_raw),
            "display_name": safe(c.get("display_name")),
            "level": safe(c.get("level")),
            "score": safe(c.get("score")),
            "wikidata": safe(c.get("wikidata"))
        }

        work_concepts_edges.add((work_id, concept_id, safe(c.get("score"))))

def get_license(work):
    primary_location = work.get("primary_location") or {}
    best_oa_location = work.get("best_oa_location") or {}

    return (
        primary_location.get("license")
        or best_oa_location.get("license")
        or ""
    )


def get_source(work):
    primary_location = work.get("primary_location") or {}
    source = primary_location.get("source")

    if isinstance(source, dict):
        return source

    best_oa_location = work.get("best_oa_location") or {}
    source = best_oa_location.get("source")

    if isinstance(source, dict):
        return source

    return None
total = 0
skipped = 0

with open(INPUT_FILE, "r", encoding="utf-8") as f_in, \
     open(works_csv, "w", newline="", encoding="utf-8") as f_works:

    work_writer = csv.DictWriter(
        f_works,
        fieldnames=[
            "work_id",
            "openalex_id",
            "doi",
            "title",
            "publication_year",
            "cited_by_count"
        ]
    )
    work_writer.writeheader()
    for line in tqdm(f_in, desc="Converting OpenAlex JSONL"):
        total += 1

        try:
            work = json.loads(line)
        except json.JSONDecodeError:
            skipped += 1
            continue

        openalex_id = work.get("id")
        work_id = openalex_short_id(openalex_id)

        if not work_id:
            skipped += 1
            continue

        work_writer.writerow({
            "work_id": work_id,
            "openalex_id": safe(openalex_id),
            "doi": safe(work.get("doi")),
            "title": safe(work.get("display_name") or work.get("title")),
            "publication_year": safe(work.get("publication_year")),
            "cited_by_count": safe(work.get("cited_by_count"))
        })
        add_metadata(work_id, "work_type", work.get("type"))
        add_metadata(work_id, "language", work.get("language"))

        open_access = work.get("open_access") or {}
        add_metadata(work_id, "oa_status", open_access.get("oa_status"))
        add_metadata(work_id, "is_oa", open_access.get("is_oa"))

        license_value = get_license(work)
        add_metadata(work_id, "license", license_value)

        add_source(work_id, get_source(work))
        add_concepts(work_id, work)

with open(metadata_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["metadata_id", "category", "value"])
    writer.writeheader()
    writer.writerows(metadata_values.values())


with open(work_metadata_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["work_id", "metadata_id", "category"])
    for row in sorted(work_metadata_edges):
        writer.writerow(row)

with open(concepts_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "concept_id",
            "openalex_id",
            "display_name",
            "level",
            "score",
            "wikidata"
        ]
    )
    writer.writeheader()
    writer.writerows(concepts.values())


with open(work_concepts_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["work_id", "concept_id", "score"])
    for row in sorted(work_concepts_edges):
        writer.writerow(row)
with open(sources_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "source_id",
            "openalex_id",
            "display_name",
            "type",
            "issn_l",
            "is_oa"
        ]
    )
    writer.writeheader()
    writer.writerows(sources.values())


with open(work_sources_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["work_id", "source_id"])
    for row in sorted(work_sources_edges):
        writer.writerow(row)
print("\nDone.")
print(f"Total records read: {total}")
print(f"Skipped records: {skipped}")
print(f"Works written: {total - skipped}")
print(f"Reusable metadata values: {len(metadata_values)}")
print(f"Concepts: {len(concepts)}")
print(f"Sources: {len(sources)}")
print(f"Work-metadata edges: {len(work_metadata_edges)}")
print(f"Work-concept edges: {len(work_concepts_edges)}")
print(f"Work-source edges: {len(work_sources_edges)}")
print(f"\nCSV files saved in: {OUTPUT_DIR.resolve()}")