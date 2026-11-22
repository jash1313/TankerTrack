from database import (
    initialize_database,
    add_tanker,
    add_request,
    get_all_tankers,
    get_all_requests
)

initialize_database()

print("Database initialized!")

# Add sample tanker
add_tanker("T1", 5000, 5000, "Depot A")

# Add sample request
add_request(
    "R1",
    "Area A",
    3000,
    "High",
    "09:00",
    "Location A"
)

print("\nTANKERS:")
for tanker in get_all_tankers():
    print(tanker)

print("\nWATER REQUESTS:")
for request in get_all_requests():
    print(request)

print("\nDATABASE TEST COMPLETED!")