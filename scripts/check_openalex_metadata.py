import json
from collections import Counter

input_file = "openalex_works_partial_20k.jsonl"

stats = Counter()
languages = Counter()
types = Counter()
oa_statuses = Counter()
licenses = Counter()
sources = Counter()
publishers = Counter()
countries = Counter()

total = 0

with open(input_file, "r", encoding="utf-8") as f:
    for line in f:
        total += 1
        work = json.loads(line)

        if work.get("id"):
            stats["has_id"] += 1

        if work.get("doi"):
            stats["has_doi"] += 1

        if work.get("title"):
            stats["has_title"] += 1

        if work.get("publication_year"):
            stats["has_publication_year"] += 1

        work_type = work.get("type")
        if work_type:
            stats["has_type"] += 1
            types[work_type] += 1

        language = work.get("language")
        if language:
            stats["has_language"] += 1
            languages[language] += 1

        open_access = work.get("open_access") or {}
        oa_status = open_access.get("oa_status")
        if oa_status:
            stats["has_oa_status"] += 1
            oa_statuses[oa_status] += 1

        primary_location = work.get("primary_location") or {}

        license_value = primary_location.get("license")
        if license_value:
            stats["has_license"] += 1
            licenses[license_value] += 1

        source = primary_location.get("source") or {}
        source_name = source.get("display_name")
        if source_name:
            stats["has_source"] += 1
            sources[source_name] += 1

        publisher = source.get("publisher")
        if publisher:
            stats["has_publisher"] += 1
            publishers[publisher] += 1

        authorships = work.get("authorships") or []
        if authorships:
            stats["has_authorships"] += 1

        for authorship in authorships:
            institutions = authorship.get("institutions") or []
            for institution in institutions:
                country_code = institution.get("country_code")
                if country_code:
                    countries[country_code] += 1

        if countries:
            stats["has_institution_country"] += 1

        topics = work.get("topics") or []
        if topics:
            stats["has_topics"] += 1

        concepts = work.get("concepts") or []
        if concepts:
            stats["has_concepts"] += 1


print("\n=== BASIC COUNTS ===")
print(f"Total works: {total}")

print("\n=== FIELD COMPLETENESS ===")
for key, value in stats.most_common():
    percentage = (value / total) * 100 if total else 0
    print(f"{key}: {value} ({percentage:.2f}%)")

print("\n=== TOP LANGUAGES ===")
for key, value in languages.most_common(10):
    print(key, value)

print("\n=== TOP TYPES ===")
for key, value in types.most_common(10):
    print(key, value)

print("\n=== TOP OPEN ACCESS STATUSES ===")
for key, value in oa_statuses.most_common(10):
    print(key, value)

print("\n=== TOP LICENSES ===")
for key, value in licenses.most_common(10):
    print(key, value)

print("\n=== TOP SOURCES ===")
for key, value in sources.most_common(10):
    print(key, value)

print("\n=== TOP PUBLISHERS ===")
for key, value in publishers.most_common(10):
    print(key, value)

print("\n=== TOP COUNTRIES ===")
for key, value in countries.most_common(10):
    print(key, value)