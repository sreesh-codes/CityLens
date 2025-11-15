from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from math import asin, cos, radians, sin, sqrt
from typing import Any, Dict, Optional

from loguru import logger

ISSUE_ENVIRONMENTAL_IMPACT = {
    "illegal_waste": 8,
    "flooding": 7,
    "tree_damage": 6,
}

MAX_DISTANCE_METERS = 50
DAYS_LOOKBACK = 30

def _haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000  # meters
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return R * c


def _recurrence_factor(
    issue_type: str,
    lat: float,
    lng: float,
    report_id: Optional[str],
) -> int:
    # Supabase analytics disabled in local dev. Placeholder recurrence value.
    lat, lng, report_id  # type: ignore[misc]
    logger.debug("Recurrence factor defaulted to 0 for issue_type=%s", issue_type)
    return 0


def _affected_population_factor(people: int) -> int:
    if people >= 1000:
        return 10
    if people >= 201:
        return 7
    if people >= 51:
        return 5
    if people >= 1:
        return 2
    return 0


def _environmental_factor(issue_type: str) -> int:
    return ISSUE_ENVIRONMENTAL_IMPACT.get(issue_type, 3)


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


@dataclass
class PriorityBreakdown:
    severity: float
    safety_risk_factor: float
    affected_population_factor: float
    environmental_impact_factor: float
    recurrence_factor: float
    score: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "severity": self.severity,
            "safety_risk_factor": self.safety_risk_factor,
            "affected_population_factor": self.affected_population_factor,
            "environmental_impact_factor": self.environmental_impact_factor,
            "recurrence_factor": self.recurrence_factor,
            "score": self.score,
        }


def calculate_priority_score(
    *,
    severity: float,
    safety_risk: bool,
    estimated_affected_people: int,
    issue_type: str,
    location_lat: float,
    location_lng: float,
    report_id: Optional[str] = None,
) -> PriorityBreakdown:
    base_severity = _clamp(severity, 1, 10)
    safety_factor = 10 if safety_risk else 0
    population_factor = _affected_population_factor(int(estimated_affected_people))
    environmental_factor = _environmental_factor(issue_type)
    recurrence = _recurrence_factor(issue_type, location_lat, location_lng, report_id)

    weighted_total = (
        base_severity * 0.35
        + safety_factor * 0.30
        + population_factor * 0.20
        + environmental_factor * 0.10
        + recurrence * 0.05
    )

    score = _clamp(weighted_total * 10, 0, 100)
    breakdown = PriorityBreakdown(
        severity=round(base_severity, 2),
        safety_risk_factor=safety_factor,
        affected_population_factor=population_factor,
        environmental_impact_factor=environmental_factor,
        recurrence_factor=recurrence,
        score=round(score, 2),
    )
    logger.info("Priority score calculated: {}", breakdown.to_dict())
    return breakdown


def explain_priority(report_id: str) -> Dict[str, Any]:
    logger.warning("explain_priority is not implemented in offline mode")
    return {
        "report_id": report_id,
        "priority_score": None,
        "factors": {},
        "reasoning": ["Detailed explanations require Supabase access."],
    }

