"""Tests for KPI formula calculations."""
import pytest

from app.kpi.formulas import (
    calc_ai_quality_score,
    calc_department_kpi,
    calc_incident_score,
    calc_repeat_issue_score,
    calc_resolution_score,
    calc_work_completion_score,
)


class TestIncidentScore:
    def test_zero_incidents_gives_100(self):
        assert calc_incident_score(0, 0) == 100.0

    def test_many_critical_lowers_score(self):
        score = calc_incident_score(10, 8)
        assert score < 50

    def test_no_critical_better_than_all_critical(self):
        score_no_critical = calc_incident_score(5, 0)
        score_all_critical = calc_incident_score(5, 5)
        assert score_no_critical > score_all_critical

    def test_score_within_bounds(self):
        for total in range(0, 30, 5):
            for critical in range(0, total + 1, 2):
                score = calc_incident_score(total, critical)
                assert 0.0 <= score <= 100.0


class TestResolutionScore:
    def test_zero_incidents_gives_100(self):
        assert calc_resolution_score(0, 0, 0) == 100.0

    def test_fast_resolution_better_than_slow(self):
        fast = calc_resolution_score(10, 2, 20.0)
        slow = calc_resolution_score(10, 2, 300.0)
        assert fast > slow

    def test_all_resolved_better_than_none(self):
        all_resolved = calc_resolution_score(10, 0, 60.0)
        none_resolved = calc_resolution_score(0, 10, 60.0)
        assert all_resolved > none_resolved

    def test_score_within_bounds(self):
        score = calc_resolution_score(5, 3, 45.0)
        assert 0.0 <= score <= 100.0


class TestWorkScore:
    def test_no_works_gives_neutral(self):
        score = calc_work_completion_score(0, 0)
        assert score == 75.0  # neutral when no works

    def test_all_documented_gives_high_score(self):
        score = calc_work_completion_score(10, 10)
        assert score >= 90.0

    def test_none_documented_gives_low_score(self):
        score = calc_work_completion_score(10, 0)
        assert score < 60.0


class TestRepeatScore:
    def test_no_incidents_gives_100(self):
        assert calc_repeat_issue_score(0, 0) == 100.0

    def test_no_repeats_gives_100(self):
        assert calc_repeat_issue_score(10, 0) == 100.0

    def test_all_repeats_gives_zero(self):
        score = calc_repeat_issue_score(10, 10)
        assert score <= 0.0

    def test_partial_repeats(self):
        score = calc_repeat_issue_score(10, 3)
        assert 0.0 <= score <= 100.0


class TestAIQualityScore:
    def test_zero_score(self):
        score = calc_ai_quality_score(0)
        assert score == 50.0

    def test_high_score(self):
        score = calc_ai_quality_score(90.0)
        assert score == 90.0

    def test_clamped_to_100(self):
        score = calc_ai_quality_score(150.0)
        assert score == 100.0


class TestDepartmentKPI:
    def test_perfect_scores_give_100(self):
        score = calc_department_kpi(100, 100, 100, 100, 100)
        assert score == 100.0

    def test_zero_scores_give_zero(self):
        score = calc_department_kpi(0, 0, 0, 0, 0)
        assert score == 0.0

    def test_weighted_average(self):
        # 0.40*80 + 0.20*60 + 0.20*70 + 0.10*90 + 0.10*50 = 32+12+14+9+5 = 72
        score = calc_department_kpi(80, 60, 70, 90, 50)
        assert abs(score - 72.0) < 0.1

    def test_score_within_bounds(self):
        score = calc_department_kpi(75, 80, 65, 90, 70)
        assert 0.0 <= score <= 100.0
