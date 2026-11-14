
import csv
from pathlib import Path
from collections import defaultdict, Counter

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data_sample" / "northwind" / "customers.csv"

with DATA.open(encoding="utf-8-sig", newline="") as f:
    customers = list(csv.DictReader(f))

groups = defaultdict(set)
counts = Counter()
complete = 0

for row in customers:
    city = row["city"].strip()
    country = row["country"].strip()

    if not city or not country:
        continue

    complete += 1
    groups[city].add(country)
    counts[city] += 1

violations = {
    city: countries
    for city, countries in groups.items()
    if len(countries) > 1
}

print("CUSTOMER FUNCTIONAL DEPENDENCY TEST")
print("-----------------------------------")
print("Dependency: city -> country")
print("Complete records:", complete)
print("Distinct cities:", len(groups))
print("Distinct countries:", len(set().union(*groups.values())))
print("Repeated cities:", sum(n > 1 for n in counts.values()))
print("FD violations:", len(violations))
print("FD satisfied:", len(violations) == 0)



# 5GNF multi-property trait transformation
# Trait key: city
# Trait properties: city, country

if violations:
    raise ValueError("Cannot normalize: FD violations exist")

traits = {}
assignments = {}

for row in customers:
    customer_id = row["customerID"].strip()
    city = row["city"].strip()
    country = row["country"].strip()

    if not city or not country:
        continue

    # One shared trait instance per city
    if city in traits:
        assert traits[city]["country"] == country
    else:
        traits[city] = {
            "city": city,
            "country": country
        }

    # Each customer links to one trait
    assert customer_id not in assignments
    assignments[customer_id] = city

# Reconstruct original property assignments
mismatches = 0

for row in customers:
    customer_id = row["customerID"].strip()
    city = row["city"].strip()
    country = row["country"].strip()

    if not city or not country:
        continue

    trait = traits[assignments[customer_id]]

    if trait["city"] != city or trait["country"] != country:
        mismatches += 1

# Check dependency preservation after normalization
normalized_fd_violations = sum(
    1 for city, trait in traits.items()
    if trait["city"] != city
)

print()
print("5GNF MULTI-PROPERTY VALIDATION")
print("-----------------------------------")
print("Original complete records:", complete)
print("Shared LocationTrait instances:", len(traits))
print("Customer-to-trait assignments:", len(assignments))
print("Reconstruction mismatches:", mismatches)
print("Normalized FD violations:", normalized_fd_violations)
print("Validation passed:",
      len(assignments) == complete
      and mismatches == 0
      and normalized_fd_violations == 0)

