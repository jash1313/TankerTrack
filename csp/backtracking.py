
from .constraints import (
    is_consistent,
    check_total_water,
    is_pairwise_compatible
)


def select_unassigned_variable(domains, assignment, priorities):
    """
    MRV heuristic:
    Select the variable with the fewest remaining values.

    High-priority requests break ties.
    """

    unassigned = [
        variable
        for variable in domains
        if variable not in assignment
    ]

    if not unassigned:
        return None

    return min(
        unassigned,
        key=lambda variable: (
            len(domains[variable]),
            -priorities.get(variable, 0)
        )
    )


def order_domain_values(variable, domains, assignment):
    """
    Least Constraining Value heuristic.

    Prefer values that eliminate fewer options
    from other unassigned variables.
    """

    def conflict_count(value):

        conflicts = 0

        for other_variable, other_domain in domains.items():

            if other_variable == variable:
                continue

            if other_variable in assignment:
                continue

            conflicts += sum(
                not is_pairwise_compatible(value, other_value)
                for other_value in other_domain
            )

        return conflicts

    return sorted(
        domains[variable],
        key=lambda value: (
            conflict_count(value),
            value.start_minute,
            value.tanker_id
        )
    )


def backtracking_search(domains, priorities=None):
    """
    Solve the CSP using recursive backtracking.
    """

    if priorities is None:
        priorities = {}

    assignment = {}

    def backtrack():

        if len(assignment) == len(domains):
            return dict(assignment)

        variable = select_unassigned_variable(
            domains,
            assignment,
            priorities
        )

        values = order_domain_values(
            variable,
            domains,
            assignment
        )

        for value in values:

            if not is_consistent(value, assignment):
                continue

            if not check_total_water(value, assignment):
                continue

            assignment[variable] = value

            result = backtrack()

            if result is not None:
                return result

            del assignment[variable]

        return None

    return backtrack()
