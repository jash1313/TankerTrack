from time import perf_counter

from database import get_all_tankers, get_all_requests
from csp.scheduler import solve_schedule
from evaluation.baseline import run_baseline_scheduler


def run_scheduler_comparison():

    tankers = get_all_tankers()
    requests = get_all_requests()

    pending_count = sum(
        1 for request in requests
        if request[6] == "Pending"
    )

    # Run greedy baseline
    start = perf_counter()

    baseline = run_baseline_scheduler(
        tankers,
        requests
    )

    baseline_time = perf_counter() - start

    # Run CSP scheduler
    start = perf_counter()

    csp_result = solve_schedule(
        tankers,
        requests
    )

    csp_time = perf_counter() - start

    csp_assignments = (
        csp_result["assignments"]
        if csp_result["success"] else {}
    )

    baseline_count = baseline["scheduled_count"]
    csp_count = len(csp_assignments)

    return {
        "success": True,
        "pending_requests": pending_count,

        "baseline": {
            "scheduled": baseline_count,
            "unscheduled": baseline["unscheduled"],
            "execution_time": baseline_time,
            "completion_rate": (
                baseline_count / pending_count * 100
                if pending_count else 0
            )
        },

        "csp": {
            "scheduled": csp_count,
            "unscheduled": (
                []
                if csp_result["success"]
                else [
                    request[0]
                    for request in requests
                    if request[6] == "Pending"
                ]
            ),
            "execution_time": csp_time,
            "completion_rate": (
                csp_count / pending_count * 100
                if pending_count else 0
            ),
            "message": csp_result["message"]
        }
    }