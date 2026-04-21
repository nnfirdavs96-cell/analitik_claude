"""Fuzzy matching utilities for dictionary normalization."""
import re
from typing import Optional

from thefuzz import fuzz, process

FUZZY_THRESHOLD = 75  # minimum score to accept a fuzzy match


def normalize_text(text: str) -> str:
    """Lowercase, strip, collapse whitespace, remove punctuation."""
    text = text.lower().strip()
    text = re.sub(r'[\-_\s]+', ' ', text)
    text = re.sub(r'[^\w\s]', '', text)
    return text.strip()


def find_best_match(
    query: str,
    candidates: list[str],
    threshold: int = FUZZY_THRESHOLD,
) -> Optional[str]:
    """
    Return the best fuzzy match from candidates above the threshold.
    Returns None if no match is good enough.
    """
    if not query or not candidates:
        return None

    query_norm = normalize_text(query)
    norm_map = {normalize_text(c): c for c in candidates}
    norm_candidates = list(norm_map.keys())

    # Exact match first
    if query_norm in norm_map:
        return norm_map[query_norm]

    # Fuzzy match
    result = process.extractOne(
        query_norm,
        norm_candidates,
        scorer=fuzz.token_sort_ratio,
    )
    if result and result[1] >= threshold:
        return norm_map[result[0]]

    return None


def find_best_match_with_score(
    query: str,
    candidates: list[str],
    threshold: int = FUZZY_THRESHOLD,
) -> tuple[Optional[str], int]:
    """Returns (best_match, score) or (None, 0)."""
    if not query or not candidates:
        return None, 0

    query_norm = normalize_text(query)
    norm_map = {normalize_text(c): c for c in candidates}
    norm_candidates = list(norm_map.keys())

    if query_norm in norm_map:
        return norm_map[query_norm], 100

    result = process.extractOne(
        query_norm,
        norm_candidates,
        scorer=fuzz.token_sort_ratio,
    )
    if result and result[1] >= threshold:
        return norm_map[result[0]], result[1]

    return None, 0
