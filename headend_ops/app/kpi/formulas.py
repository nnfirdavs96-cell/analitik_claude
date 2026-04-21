"""
KPI formula definitions.

department_kpi_score =
    0.40 * incident_score
  + 0.20 * resolution_score
  + 0.20 * work_completion_score
  + 0.10 * repeat_issue_score
  + 0.10 * ai_quality_score
"""
from app.core.config import settings


def calc_incident_score(total_incidents: int, critical_incidents: int) -> float:
    """
    Higher score when there are fewer and less severe incidents.
    100 = zero incidents, 0 = many critical incidents.
    """
    if total_incidents == 0:
        return 100.0

    severity_penalty = critical_incidents * 3 + (total_incidents - critical_incidents)
    score = max(0.0, 100.0 - severity_penalty * 2.5)
    return round(score, 2)


def calc_resolution_score(
    resolved: int,
    unresolved: int,
    avg_resolution_minutes: float,
) -> float:
    """
    Higher score when most incidents are resolved quickly.
    Target resolution: ≤ 60 minutes.
    """
    total = resolved + unresolved
    if total == 0:
        return 100.0

    resolution_rate = resolved / total if total > 0 else 0.0

    # Time penalty: >120 min is bad, <30 min is great
    if avg_resolution_minutes <= 0:
        time_score = 100.0
    elif avg_resolution_minutes <= 30:
        time_score = 100.0
    elif avg_resolution_minutes <= 60:
        time_score = 85.0
    elif avg_resolution_minutes <= 120:
        time_score = 65.0
    elif avg_resolution_minutes <= 240:
        time_score = 45.0
    else:
        time_score = 25.0

    score = (resolution_rate * 60.0) + (time_score * 0.4)
    return round(min(100.0, max(0.0, score)), 2)


def calc_work_completion_score(total_works: int, works_with_result: int) -> float:
    """Higher score when completed works are properly documented."""
    if total_works == 0:
        return 75.0  # neutral when no works
    rate = works_with_result / total_works
    score = 40.0 + (rate * 60.0)
    return round(min(100.0, score), 2)


def calc_repeat_issue_score(total_incidents: int, repeat_incidents: int) -> float:
    """Lower score when repeat incidents increase."""
    if total_incidents == 0:
        return 100.0
    repeat_rate = repeat_incidents / total_incidents
    score = max(0.0, 100.0 - repeat_rate * 120.0)
    return round(score, 2)


def calc_ai_quality_score(ai_avg_score: float) -> float:
    """Based on AI evaluation of documentation and action quality."""
    if ai_avg_score <= 0:
        return 50.0
    return round(min(100.0, max(0.0, float(ai_avg_score))), 2)


def calc_department_kpi(
    incident_score: float,
    resolution_score: float,
    work_completion_score: float,
    repeat_issue_score: float,
    ai_quality_score: float,
) -> float:
    """Weighted composite KPI score (0-100)."""
    score = (
        settings.KPI_WEIGHT_INCIDENT * incident_score
        + settings.KPI_WEIGHT_RESOLUTION * resolution_score
        + settings.KPI_WEIGHT_WORK * work_completion_score
        + settings.KPI_WEIGHT_REPEAT * repeat_issue_score
        + settings.KPI_WEIGHT_AI_QUALITY * ai_quality_score
    )
    return round(min(100.0, max(0.0, score)), 2)
