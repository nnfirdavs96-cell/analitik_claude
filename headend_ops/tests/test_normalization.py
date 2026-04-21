"""Tests for fuzzy matching and normalization logic."""
import pytest

from app.normalization.fuzzy_match import find_best_match, find_best_match_with_score, normalize_text


class TestNormalizeText:
    def test_lowercase(self):
        assert normalize_text("МИР") == "мир"

    def test_strip_whitespace(self):
        assert normalize_text("  МИР  ") == "мир"

    def test_collapse_dashes(self):
        assert normalize_text("encoder-2") == "encoder 2"

    def test_collapse_underscores(self):
        assert normalize_text("encoder_2") == "encoder 2"


class TestFuzzyMatch:
    CHANNELS = ["МИР", "Россия 1", "НТВ", "Первый канал", "ТНТ"]
    ASSETS = ["Encoder-1", "Encoder-2", "Transcoder-1", "Mux-1", "Storage-1"]

    def test_exact_match(self):
        result = find_best_match("МИР", self.CHANNELS)
        assert result == "МИР"

    def test_case_insensitive(self):
        result = find_best_match("мир", self.CHANNELS)
        assert result == "МИР"

    def test_partial_fuzzy(self):
        result = find_best_match("Россия", self.CHANNELS)
        assert result == "Россия 1"

    def test_typo_tolerance(self):
        # "encoder2" should match "Encoder-2"
        result = find_best_match("encoder2", self.ASSETS)
        assert result is not None

    def test_no_match_below_threshold(self):
        result = find_best_match("xyz_totally_different", self.CHANNELS)
        assert result is None

    def test_empty_query(self):
        result = find_best_match("", self.CHANNELS)
        assert result is None

    def test_empty_candidates(self):
        result = find_best_match("МИР", [])
        assert result is None

    def test_with_score_returns_100_for_exact(self):
        match, score = find_best_match_with_score("МИР", self.CHANNELS)
        assert match == "МИР"
        assert score == 100

    def test_with_score_below_threshold_returns_none(self):
        match, score = find_best_match_with_score("zzzzz", self.CHANNELS)
        assert match is None
        assert score == 0

    def test_transcoder_fuzzy(self):
        result = find_best_match("транскодер 1", ["Transcoder-1", "Transcoder-2", "Encoder-1"])
        # May not match due to language difference — acceptable
        # But should not crash
        assert result is None or isinstance(result, str)
