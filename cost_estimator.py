from __future__ import annotations

from typing import Dict, Tuple

DEFAULT_COST_RANGE = (500, 2000)

ISSUE_COST_RANGES: Dict[str, Tuple[int, int]] = {
    "pothole": (2500, 6000),
    "illegal_waste": (800, 3000),
    "broken_streetlight": (400, 1500),
    "graffiti": (300, 1200),
    "flooding": (5000, 12000),
    "traffic_congestion": (1500, 5000),
    "damaged_signage": (700, 2500),
    "tree_damage": (1000, 3000),
    "unclear_issue": (0, 0),
}


def estimate_cost(issue_type: str) -> Dict[str, int]:
    issue = issue_type or "unclear_issue"
    low, high = ISSUE_COST_RANGES.get(issue, DEFAULT_COST_RANGE)
    return {"issue_type": issue, "cost_estimate_min": low, "cost_estimate_max": high}

