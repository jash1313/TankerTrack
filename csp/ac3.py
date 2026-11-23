
from collections import deque

from .constraints import is_pairwise_compatible


def revise(domains, xi, xj):
    """
    Remove values from Xi that have no compatible
    value in the domain of Xj.
    """

    revised = False

    valid_values = []

    for value_i in domains[xi]:

        supported = any(
            is_pairwise_compatible(value_i, value_j)
            for value_j in domains[xj]
        )

        if supported:
            valid_values.append(value_i)
        else:
            revised = True

    if revised:
        domains[xi] = valid_values

    return revised


def ac3(domains):
    """
    Arc Consistency Algorithm 3.

    Returns:
        success: Whether all domains remain non-empty.
        domains: Reduced domains.
        removed_count: Number of eliminated values.
    """

    original_count = sum(
        len(domain) for domain in domains.values()
    )

    queue = deque(
        (xi, xj)
        for xi in domains
        for xj in domains
        if xi != xj
    )

    while queue:

        xi, xj = queue.popleft()

        if revise(domains, xi, xj):

            if not domains[xi]:
                removed_count = (
                    original_count -
                    sum(len(d) for d in domains.values())
                )

                return False, domains, removed_count

            for xk in domains:

                if xk != xi and xk != xj:
                    queue.append((xk, xi))

    final_count = sum(
        len(domain) for domain in domains.values()
    )

    removed_count = original_count - final_count

    return True, domains, removed_count
