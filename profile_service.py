from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable, List, Sequence

GAMIFICATION_RULES = {
    'report_submitted': 10,
    'report_verified': 25,
    'report_resolved': 50,
    'first_in_area': 100,
    'streak_bonus': 150,
}


@dataclass
class ReportEvent:
    report_id: str
    event_type: str
    occurred_at: datetime
    location_hash: str | None = None


@dataclass
class ReportSummary:
    report_id: str
    status: str
    verified: bool
    resolved: bool
    submitted_at: datetime
    location_hash: str | None = None


@dataclass
class ProfileSnapshot:
    reputation: int
    total_reports: int
    resolved_reports: int
    streak: int
    badges: List[str]


def calculate_reputation(events: Sequence[ReportEvent]) -> int:
    points = 0
    streak_tracker: list[datetime] = []

    for event in events:
        points += GAMIFICATION_RULES.get(event.event_type, 0)
        if event.event_type == 'report_submitted':
            streak_tracker.append(event.occurred_at)

    if _has_streak(streak_tracker, required_reports=5, window_days=7):
        points += GAMIFICATION_RULES['streak_bonus']

    return points


def summarize_profile(reports: Iterable[ReportSummary], events: Iterable[ReportEvent]) -> ProfileSnapshot:
    reports_list = list(reports)
    events_list = list(events)
    reputation = calculate_reputation(events_list)
    total_reports = len(reports_list)
    resolved_reports = sum(1 for report in reports_list if report.resolved)
    badges = assign_badges(reports_list, events_list, reputation)
    streak = _current_streak(events_list)
    return ProfileSnapshot(
        reputation=reputation,
        total_reports=total_reports,
        resolved_reports=resolved_reports,
        streak=streak,
        badges=badges,
    )


def assign_badges(reports: Sequence[ReportSummary], events: Sequence[ReportEvent], reputation: int) -> List[str]:
    badges: list[str] = []
    reports_with_verification = sum(1 for report in reports if report.verified)
    reports_with_fast_resolution = sum(
        1
        for report in reports
        if report.resolved and (datetime.utcnow() - report.submitted_at) <= timedelta(hours=2)
    )

    if len(reports) >= 1:
        badges.append('First Reporter')
    if reports_with_verification >= 10:
        badges.append('Eagle Eye')
    if reputation >= 1000:
        badges.append('Eco Warrior')
    if reports_with_fast_resolution >= 1:
        badges.append('Lightning Strike')
    if _has_streak([event.occurred_at for event in events if event.event_type == 'report_submitted'], 5, 7):
        badges.append('Streak Master')

    return badges


def _has_streak(timestamps: Sequence[datetime], required_reports: int, window_days: int) -> bool:
    ordered = sorted(timestamps)
    for start_index in range(len(ordered)):
        window_start = ordered[start_index]
        count = 1
        for next_stamp in ordered[start_index + 1 :]:
            if next_stamp - window_start <= timedelta(days=window_days):
                count += 1
                if count >= required_reports:
                    return True
            else:
                break
    return False


def _current_streak(events: Sequence[ReportEvent]) -> int:
    submissions = sorted(
        (event.occurred_at.date() for event in events if event.event_type == 'report_submitted'), reverse=True
    )
    if not submissions:
        return 0
    streak = 1
    last_date = submissions[0]
    for submitted_date in submissions[1:]:
        if (last_date - submitted_date).days == 1:
            streak += 1
            last_date = submitted_date
        elif last_date == submitted_date:
            continue
        else:
            break
    return streak
