
from copy import deepcopy

from .domains import generate_domains
from .ac3 import ac3
from .backtracking import backtracking_search


PRIORITY_VALUES = {
    "Low": 1,
    "Medium": 2,
    "High": 3,
    "Emergency": 4
}


def solve_schedule(tankers, requests):
    """
    Complete TankerTrack CSP scheduling pipeline.

    1. Select pending requests.
    2. Generate domains.
    3. Apply AC-3.
    4. Apply Backtracking Search.
    5. Return the schedule.
    """

    pending_requests = [
        request
        for request in requests
        if request[6] == "Pending"
    ]

    if not pending_requests:
        return {
            "success": False,
            "message": "No pending requests available.",
            "assignments": {},
            "removed_values": 0
        }

    priorities = {
        request[0]: PRIORITY_VALUES.get(request[3], 1)
        for request in pending_requests
    }

    # STEP 1: Generate domains
    domains = generate_domains(
        tankers,
        pending_requests
    )

    domains_before = sum(
        len(domain) for domain in domains.values()
    )

    # STEP 2: Check for empty domains
    if any(not domain for domain in domains.values()):
        return {
            "success": False,
            "message": (
                "At least one request has no feasible tanker assignment."
            ),
            "assignments": {},
            "domains_before": domains_before,
            "domains_after": 0,
            "removed_values": 0
        }

    # STEP 3: Apply AC-3
    reduced_domains = deepcopy(domains)

    consistent, reduced_domains, removed_values = ac3(
        reduced_domains
    )

    if not consistent:
        return {
            "success": False,
            "message": "AC-3 detected an inconsistent CSP.",
            "assignments": {},
            "domains_before": domains_before,
            "domains_after": sum(
                len(d) for d in reduced_domains.values()
            ),
            "removed_values": removed_values
        }

    # STEP 4: Apply Backtracking Search
    assignments = backtracking_search(
        reduced_domains,
        priorities
    )

    if assignments is None:
        return {
            "success": False,
            "message": (
                "No complete valid schedule could be found "
                "for all pending requests."
            ),
            "assignments": {},
            "domains_before": domains_before,
            "domains_after": sum(
                len(d) for d in reduced_domains.values()
            ),
            "removed_values": removed_values
        }

    # STEP 5: Return result
    return {
        "success": True,
        "message": "Valid schedule generated successfully.",
        "assignments": assignments,
        "domains_before": domains_before,
        "domains_after": sum(
            len(d) for d in reduced_domains.values()
        ),
        "removed_values": removed_values
    }


def generate_schedule_from_database():
    """Run the scheduler using the SQLite database."""

    from database import get_all_tankers, get_all_requests

    tankers = get_all_tankers()
    requests = get_all_requests()

    return solve_schedule(tankers, requests)
