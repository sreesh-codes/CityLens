from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from loguru import logger

DEPARTMENT_ROUTES: Dict[str, List[str]] = {
    "pothole": ["Roads & Transport Authority"],
    "damaged_signage": ["Roads & Transport Authority"],
    "illegal_waste": ["Waste Management Department"],
    "broken_streetlight": ["Dubai Electricity & Water Authority"],
    "graffiti": ["Community Development Authority"],
    "flooding": ["Drainage & Irrigation"],
    "traffic_congestion": ["Traffic Management Center"],
    "tree_damage": ["Parks & Recreation"],
}

DISTRICT_SPECIALISTS: Dict[str, List[str]] = {
    "palm jumeirah": ["Community Development Authority", "Parks & Recreation"],
    "jebel ali": ["Waste Management Department"],
    "dubai marina": ["Roads & Transport Authority"],
    "diera": ["Drainage & Irrigation"],
}

EMERGENCY_ESCALATION = {
    "name": "Emergency Response Taskforce",
    "contact_email": "emergency@dubai.gov.ae",
    "phone": "+971-4-000-0000",
    "threshold": 80,
}

_department_cache: Dict[str, Dict[str, str]] = {}

DEPARTMENT_DIRECTORY: Dict[str, Dict[str, str]] = {
    "roads & transport authority": {
        "id": "dept-rta",
        "name": "Roads & Transport Authority",
        "category": "Infrastructure",
        "contact_email": "rta@dubai.gov.ae",
        "average_resolution_time": "36h",
    },
    "waste management department": {
        "id": "dept-waste",
        "name": "Waste Management Department",
        "category": "Sanitation",
        "contact_email": "waste@dubai.gov.ae",
        "average_resolution_time": "16h",
    },
    "dubai electricity & water authority": {
        "id": "dept-dewa",
        "name": "Dubai Electricity & Water Authority",
        "category": "Utilities",
        "contact_email": "dewa@dubai.gov.ae",
        "average_resolution_time": "20h",
    },
    "community development authority": {
        "id": "dept-cda",
        "name": "Community Development Authority",
        "category": "Community",
        "contact_email": "community@dubai.gov.ae",
        "average_resolution_time": "24h",
    },
    "drainage & irrigation": {
        "id": "dept-drainage",
        "name": "Drainage & Irrigation",
        "category": "Water",
        "contact_email": "drainage@dubai.gov.ae",
        "average_resolution_time": "28h",
    },
    "traffic management center": {
        "id": "dept-traffic",
        "name": "Traffic Management Center",
        "category": "Mobility",
        "contact_email": "traffic@dubai.gov.ae",
        "average_resolution_time": "18h",
    },
    "parks & recreation": {
        "id": "dept-parks",
        "name": "Parks & Recreation",
        "category": "Environment",
        "contact_email": "parks@dubai.gov.ae",
        "average_resolution_time": "30h",
    },
}


def _normalize(name: str) -> str:
    return name.strip().lower()


def _fetch_department_by_name(name: str) -> Optional[Dict[str, str]]:
    normalized = _normalize(name)
    if normalized in _department_cache:
        return _department_cache[normalized]

    record = DEPARTMENT_DIRECTORY.get(normalized)
    if record:
        _department_cache[normalized] = record
        return record

    logger.warning("Department '{}' not found in static directory; skipping", name)
    return None


def _build_department_list(issue_type: str, district: Optional[str]) -> List[Dict[str, str]]:
    names = DEPARTMENT_ROUTES.get(issue_type, [])
    district_names = DISTRICT_SPECIALISTS.get(_normalize(district or ""), [])
    combined = names + [n for n in district_names if n not in names]

    resolved: List[Dict[str, str]] = []
    for name in combined:
        match = _fetch_department_by_name(name)
        if match:
            resolved.append(match)
        else:
            logger.warning("Department '{}' not found in database; skipping", name)
    return resolved


def assign_department(issue_type: str, location: Dict[str, Optional[str]]) -> Dict[str, Any]:  # type: ignore[name-defined]
    """
    Determine the municipal department responsible for the reported issue.
    location dict can include:
      - district: textual district/neighborhood name
      - priority_score: numeric value (0-100)
      - lat/lng: reserved for future proximity-based routing
    """
    issue_type = issue_type or "unclear_issue"
    district = (location or {}).get("district")
    priority_score = float((location or {}).get("priority_score") or 0)

    departments = _build_department_list(issue_type, district)
    if not departments:
        logger.warning("No department match for issue_type=%s district=%s", issue_type, district)
        return {
            "primary_department": None,
            "backup_departments": [],
            "escalation": None,
            "notes": f"No department match for {issue_type}. Manual review required.",
        }

    escalation = None
    if priority_score >= EMERGENCY_ESCALATION["threshold"]:
        escalation = {
            "name": EMERGENCY_ESCALATION["name"],
            "contact_email": EMERGENCY_ESCALATION["contact_email"],
            "phone": EMERGENCY_ESCALATION["phone"],
            "reason": f"Priority score {priority_score} exceeded threshold {EMERGENCY_ESCALATION['threshold']}",
        }

    return {
        "primary_department": departments[0],
        "backup_departments": departments[1:],
        "escalation": escalation,
        "notes": (
            f"District specialist added for {district}."
            if district and district.lower() in DISTRICT_SPECIALISTS
            else None
        ),
    }

