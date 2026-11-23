import pytest

from csp.domains import Assignment, generate_domains
from csp.ac3 import ac3
from csp.backtracking import backtracking_search


def test_ac3_removes_unsupported_assignment():

    domains = {
        "R1": [
            Assignment("T2", 540, 4000, 6000, "Area A")
        ],
        "R2": [
            Assignment("T2", 540, 3000, 6000, "Area B"),
            Assignment("T3", 540, 3000, 3500, "Area B")
        ]
    }

    consistent, result, removed = ac3(domains)

    assert consistent is True
    assert removed == 1
    assert len(result["R2"]) == 1
    assert result["R2"][0].tanker_id == "T3"


def test_ac3_detects_inconsistent_domains():

    domains = {
        "R1": [
            Assignment("T2", 540, 4000, 6000, "Area A")
        ],
        "R2": [
            Assignment("T2", 540, 3000, 6000, "Area B")
        ]
    }

    consistent, result, removed = ac3(domains)

    assert consistent is False
    assert removed >= 1


def test_domain_generation_rejects_small_tankers():

    tankers = [
        ("T1", 2000, 2000, "Depot A", 1, "Available"),
        ("T2", 5000, 5000, "Depot B", 1, "Available")
    ]

    requests = [
        ("R1", "Area A", 3000, "High",
         "09:00", "Location A", "Pending", "")
    ]

    domains = generate_domains(tankers, requests)

    assert len(domains["R1"]) == 4

    assert all(
        assignment.tanker_id == "T2"
        for assignment in domains["R1"]
    )


def test_backtracking_finds_valid_schedule():

    domains = {
        "R1": [
            Assignment("T2", 540, 3000, 6000, "Area A")
        ],
        "R2": [
            Assignment("T2", 540, 4000, 6000, "Area B"),
            Assignment("T3", 540, 4000, 5000, "Area B")
        ]
    }

    result = backtracking_search(domains)

    assert result is not None
    assert result["R1"].tanker_id == "T2"
    assert result["R2"].tanker_id == "T3"


def test_backtracking_rejects_impossible_schedule():

    domains = {
        "R1": [
            Assignment("T2", 540, 4000, 6000, "Area A")
        ],
        "R2": [
            Assignment("T2", 540, 3000, 6000, "Area B")
        ]
    }

    result = backtracking_search(domains)

    assert result is None