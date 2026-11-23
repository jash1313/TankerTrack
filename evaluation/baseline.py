from csp.domains import generate_domains
from csp.constraints import is_consistent, check_total_water


def run_baseline_scheduler(tankers, requests):
    """
    Greedy first-fit baseline scheduler.
    """

    pending = [
        request for request in requests
        if request[6] == "Pending"
    ]

    domains = generate_domains(tankers, pending)

    assignments = {}
    unscheduled = []

    for request in pending:

        request_id = request[0]
        candidates = domains.get(request_id, [])

        selected = None

        for candidate in candidates:

            if not is_consistent(candidate, assignments):
                continue

            if not check_total_water(candidate, assignments):
                continue

            selected = candidate
            break

        if selected is not None:
            assignments[request_id] = selected
        else:
            unscheduled.append(request_id)

    return {
        "assignments": assignments,
        "unscheduled": unscheduled,
        "scheduled_count": len(assignments),
        "total_requests": len(pending)
    }