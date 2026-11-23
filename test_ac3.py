from csp.domains import Assignment
from csp.ac3 import ac3

# Both requests have a delivery time of 09:00.

domains = {
    "R1": [
        Assignment(
            "T2", 540, 4000, 6000, "Area A"
        )
    ],

    "R2": [
        Assignment(
            "T2", 540, 3000, 6000, "Area B"
        ),

        Assignment(
            "T3", 540, 3000, 3500, "Area B"
        )
    ]
}

print("BEFORE AC-3")

for request, values in domains.items():
    print(request, ":", len(values), "assignments")

before = sum(len(v) for v in domains.values())

consistent, reduced_domains, removed = ac3(domains)

print("\nAFTER AC-3")

for request, values in reduced_domains.items():
    print(request, ":", len(values), "assignments")

after = sum(len(v) for v in reduced_domains.values())

print("\nRESULTS")
print("Before:", before)
print("After:", after)
print("Eliminated:", removed)
print("Consistent:", consistent)