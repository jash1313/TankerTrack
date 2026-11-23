
from csp.scheduler import solve_schedule


# Sample tanker data
tankers = [
    ("T1", 2000, 2000, "Depot A", 1, "Available"),
    ("T2", 7000, 6000, "Depot A", 1, "Available"),
    ("T3", 5000, 5000, "Depot B", 1, "Available")
]

requests = [
    ("R1", "Area A", 3000, "High", "09:00", "Location A", "Pending", ""),
    ("R2", "Area B", 4000, "Medium", "09:00", "Location B", "Pending", "")
]


print("=" * 55)
print("          TANKERTRACK AI SCHEDULER")
print("=" * 55)


result = solve_schedule(tankers, requests)


print("\nSTATUS:", result["message"])

print("\nDOMAINS BEFORE AC-3:",
      result.get("domains_before", 0))

print("DOMAINS AFTER AC-3:",
      result.get("domains_after", 0))

print("VALUES ELIMINATED:",
      result.get("removed_values", 0))


if result["success"]:

    print("\nGENERATED SCHEDULE")
    print("-" * 55)

    for request_id, assignment in result["assignments"].items():

        print(
            f"{request_id} -> "
            f"Tanker {assignment.tanker_id} | "
            f"Time: {assignment.display_time()} | "
            f"Water: {assignment.quantity} L"
        )

    print("\nALL REQUESTS SUCCESSFULLY SCHEDULED!")

else:

    print("\nSCHEDULING FAILED.")
    print(result["message"])


print("\n" + "=" * 55)
