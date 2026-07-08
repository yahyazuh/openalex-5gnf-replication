import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = ROOT / "data_sample" / "northwind"
RAW_DIR = ROOT / "northwind_results" / "raw"
SUMMARY_DIR = ROOT / "northwind_results" / "summary"

RAW_DIR.mkdir(parents=True, exist_ok=True)
SUMMARY_DIR.mkdir(parents=True, exist_ok=True)

# Conservative metadata scope for the Northwind supplementary validation.
# We use only repeated geographic/shipping descriptors that occur across
# several entity types. Domain entities such as Product, Category, Supplier,
# Customer, and Order are not treated as metadata values here.
METADATA_SCOPE = [
    {
        "file": "customers.csv",
        "entity_type": "Customer",
        "id_column": "customerID",
        "columns": {
            "country": "country",
            "region": "region",
            "city": "city",
            "postalCode": "postal_code",
        },
    },
    {
        "file": "suppliers.csv",
        "entity_type": "Supplier",
        "id_column": "supplierID",
        "columns": {
            "country": "country",
            "region": "region",
            "city": "city",
            "postalCode": "postal_code",
        },
    },
    {
        "file": "employees.csv",
        "entity_type": "Employee",
        "id_column": "employeeID",
        "columns": {
            "country": "country",
            "region": "region",
            "city": "city",
            "postalCode": "postal_code",
        },
    },
    {
        "file": "orders.csv",
        "entity_type": "Order",
        "id_column": "orderID",
        "columns": {
            "shipCountry": "country",
            "shipRegion": "region",
            "shipCity": "city",
            "shipPostalCode": "postal_code",
        },
    },
]

NULL_VALUES = {"", "NULL", "null", "None", "none", "N/A", "n/a"}


def is_valid(value: str) -> bool:
    return value is not None and value.strip() not in NULL_VALUES


def read_rows(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main():
    assignments = []

    for spec in METADATA_SCOPE:
        path = DATA_DIR / spec["file"]
        rows = read_rows(path)

        for row in rows:
            entity_id = row.get(spec["id_column"], "").strip()

            for source_column, category in spec["columns"].items():
                value = row.get(source_column, "").strip()

                if not is_valid(value):
                    continue

                assignments.append(
                    {
                        "source_file": spec["file"],
                        "entity_type": spec["entity_type"],
                        "entity_id": entity_id,
                        "source_column": source_column,
                        "metadata_category": category,
                        "metadata_value": value,
                    }
                )

    # 5GNF-style canonical MetadataValue nodes:
    # one node for each unique (metadata_category, metadata_value) pair.
    metadata_values = sorted(
        {
            (a["metadata_category"], a["metadata_value"])
            for a in assignments
        }
    )

    # Reconstruction check:
    # each original assignment can be reconstructed by joining its
    # entity-to-metadata association with the canonical metadata value.
    reconstructed_assignments = []
    metadata_value_set = set(metadata_values)

    for a in assignments:
        key = (a["metadata_category"], a["metadata_value"])
        if key in metadata_value_set:
            reconstructed_assignments.append(a)

    metadata_assignments_before_5gnf = len(assignments)
    metadata_values_after_5gnf = len(metadata_values)
    metadata_reuse_ratio = (
        metadata_assignments_before_5gnf / metadata_values_after_5gnf
        if metadata_values_after_5gnf
        else 0
    )
    reconstructed_assignments_count = len(reconstructed_assignments)
    lossless_reconstruction_accuracy = (
        reconstructed_assignments_count / metadata_assignments_before_5gnf
        if metadata_assignments_before_5gnf
        else 0
    )

    raw_assignments_path = RAW_DIR / "northwind_metadata_assignments_raw.csv"
    with raw_assignments_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "source_file",
                "entity_type",
                "entity_id",
                "source_column",
                "metadata_category",
                "metadata_value",
            ],
        )
        writer.writeheader()
        writer.writerows(assignments)

    metadata_values_path = RAW_DIR / "northwind_metadata_values_5gnf.csv"
    with metadata_values_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["metadata_value_id", "metadata_category", "metadata_value"],
        )
        writer.writeheader()
        for i, (category, value) in enumerate(metadata_values, start=1):
            writer.writerow(
                {
                    "metadata_value_id": f"NW_MV_{i}",
                    "metadata_category": category,
                    "metadata_value": value,
                }
            )

    summary_path = SUMMARY_DIR / "northwind_metadata_reuse_summary.csv"
    with summary_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "dataset",
                "metadata_assignments_before_5gnf",
                "metadata_values_after_5gnf",
                "metadata_reuse_ratio",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "dataset": "Northwind",
                "metadata_assignments_before_5gnf": metadata_assignments_before_5gnf,
                "metadata_values_after_5gnf": metadata_values_after_5gnf,
                "metadata_reuse_ratio": round(metadata_reuse_ratio, 4),
            }
        )

    lossless_path = SUMMARY_DIR / "northwind_lossless_reconstruction_summary.csv"
    with lossless_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "dataset",
                "original_metadata_assignments",
                "reconstructed_metadata_assignments",
                "lossless_reconstruction_accuracy",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "dataset": "Northwind",
                "original_metadata_assignments": metadata_assignments_before_5gnf,
                "reconstructed_metadata_assignments": reconstructed_assignments_count,
                "lossless_reconstruction_accuracy": round(
                    lossless_reconstruction_accuracy, 4
                ),
            }
        )

    print("Northwind structural metrics generated.")
    print(f"Raw assignments: {raw_assignments_path}")
    print(f"Metadata values: {metadata_values_path}")
    print(f"Reuse summary: {summary_path}")
    print(f"Lossless reconstruction summary: {lossless_path}")
    print()
    print(f"Metadata assignments before 5GNF: {metadata_assignments_before_5gnf}")
    print(f"Metadata values after 5GNF: {metadata_values_after_5gnf}")
    print(f"Metadata reuse ratio: {metadata_reuse_ratio:.4f}x")
    print(f"Lossless reconstruction accuracy: {lossless_reconstruction_accuracy:.4f}")


if __name__ == "__main__":
    main()