
from .domains import TURNAROUND_TIME


def is_pairwise_compatible(a, b):
    """
    Check whether two requests can use their
    selected tanker assignments together.
    """

    # Different tankers do not conflict under
    # the current simplified scheduling model.
    if a.tanker_id != b.tanker_id:
        return True

    # Check combined available water.
    if a.quantity + b.quantity > a.available_water:
        return False

    # Check delivery overlap and turnaround time.
    gap = max(
        a.start_minute - b.end_minute,
        b.start_minute - a.end_minute
    )

    return gap >= TURNAROUND_TIME


def is_consistent(assignment, assigned_values):
    """Check an assignment against existing decisions."""

    for existing in assigned_values.values():

        if not is_pairwise_compatible(assignment, existing):
            return False

    return True


def check_total_water(assignment, assigned_values):
    """
    Check cumulative water usage for each tanker.
    """

    usage = {}

    all_assignments = list(assigned_values.values()) + [assignment]

    for item in all_assignments:

        tanker_id = item.tanker_id

        usage[tanker_id] = usage.get(tanker_id, 0) + item.quantity

        if usage[tanker_id] > item.available_water:
            return False

    return True
