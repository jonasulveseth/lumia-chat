"""
Utilities for parsing Swedish date expressions from free-form text.

This module provides a lightweight, dependency-free parser that aims to
identify a concrete calendar date (YYYY-MM-DD) from common Swedish
expressions such as "idag", "igår", "i förrgår", and weekday phrases like
"i måndags". It also supports explicit dates like "2025-08-14" and
"13 augusti" (optionally with a year).

The goal is to extract a single date suitable for use as a metadata filter
in Brain queries. If the text is ambiguous or no clear date can be found,
the function returns None, and the caller should proceed without a date
filter.
"""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from typing import Optional, List
import unicodedata


# Map Swedish weekday names (past tense) to Python weekday numbers
_WEEKDAY_NAME_TO_NUM = {
    "måndag": 0,
    "tisdag": 1,
    "onsdag": 2,
    "torsdag": 3,
    "fredag": 4,
    "lördag": 5,
    "söndag": 6,
}


# Map Swedish month names to month numbers (1-12)
_MONTH_NAME_TO_NUM = {
    "januari": 1,
    "februari": 2,
    "mars": 3,
    "april": 4,
    "maj": 5,
    "juni": 6,
    "juli": 7,
    "augusti": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "december": 12,
}


def _format_iso(d: date) -> str:
    return d.strftime("%Y-%m-%d")


def _match_explicit_iso(text: str) -> Optional[str]:
    """Match explicit ISO date YYYY-MM-DD anywhere in the text."""
    m = re.search(r"\b(20\d{2})-(\d{1,2})-(\d{1,2})\b", text)
    if not m:
        return None
    year, month, day = map(int, m.groups())
    try:
        return _format_iso(date(year, month, day))
    except ValueError:
        return None


def _match_day_month_name(text: str, today: date) -> Optional[str]:
    """
    Match expressions like "13 augusti", "13 augusti 2025", "14e augusti", "den 14e augusti".
    If year is missing, assume current year.
    """
    # Handle various Swedish date formats including ordinal numbers and common typos
    patterns = [
        r"\b(\d{1,2})(?:e|:e)?\s+(januari|februari|mars|april|maj|juni|juli|augusti|augiusti|september|oktober|november|december)(?:\s+(20\d{2}))?\b",
        r"\bden\s+(\d{1,2})(?:e|:e)?\s+(januari|februari|mars|april|maj|juni|juli|augusti|augiusti|september|oktober|november|december)(?:\s+(20\d{2}))?\b"
    ]
    
    for pattern in patterns:
        m = re.search(pattern, text)
        if m:
            day = int(m.group(1))
            month_name = m.group(2)
            # Handle common typos
            if month_name == "augiusti":
                month_name = "augusti"
            year = int(m.group(3)) if m.group(3) else today.year
            month = _MONTH_NAME_TO_NUM.get(month_name)
            try:
                return _format_iso(date(year, month, day))
            except ValueError:
                continue
    return None


def _match_relative_basics(text: str, today: date) -> Optional[str]:
    """Handle common relative terms: idag, igår, i förrgår."""
    t = text
    # Normalize some diacritics/variants to improve matching
    normalized = unicodedata.normalize("NFKD", t)
    ascii_text = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    
    # Check both original and normalized text
    for txt in [t, ascii_text]:
        if re.search(r"\bidag\b|\bi dag\b", txt):
            return _format_iso(today)
        if re.search(r"\bigår\b|\bigar\b", txt):
            return _format_iso(today - timedelta(days=1))
        if re.search(r"\bi\s+forrgår\b|\bforrgår\b|\bi\s+förrgår\b", txt):
            return _format_iso(today - timedelta(days=2))
    return None


def _match_last_weekday(text: str, today: date) -> Optional[str]:
    """
    Match phrases like "i måndags", "i tisdags", ... and return the most
    recent occurrence in the past (never a future date). If today is the same
    weekday, we consider a week ago.
    """
    m = re.search(
        r"\bi\s+(måndags|tisdags|onsdags|torsdags|fredags|lördags|söndags)\b",
        text,
    )
    if not m:
        return None
    base = m.group(1)
    # Remove the trailing 's' to get the weekday base form
    weekday_name = base[:-1] if base.endswith("s") else base
    weekday_num = _WEEKDAY_NAME_TO_NUM.get(weekday_name)
    if weekday_num is None:
        return None
    today_num = today.weekday()
    days_ago = (today_num - weekday_num) % 7
    if days_ago == 0:
        days_ago = 7
    return _format_iso(today - timedelta(days=days_ago))


def detect_swedish_date_filter(message: str) -> Optional[str]:
    """
    Try to detect a single calendar date (YYYY-MM-DD) from a Swedish message.

    Returns an ISO date string or None if no unambiguous date was found.
    """
    if not message:
        return None

    text = message.strip().lower()
    today = date.today()

    # 1) Explicit ISO date
    iso = _match_explicit_iso(text)
    if iso:
        return iso

    # 2) Common relative forms
    rel = _match_relative_basics(text, today)
    if rel:
        return rel

    # 3) "i måndags" style
    wday = _match_last_weekday(text, today)
    if wday:
        return wday

    # 4) "13 augusti" style (optional year)
    dm = _match_day_month_name(text, today)
    if dm:
        return dm

    return None


def detect_swedish_date_filters(message: str) -> List[str]:
    """
    Detect multiple dates when the message clearly references several relative days
    (e.g., "idag och igår"). Returns a list of unique ISO dates in priority order.
    Falls back to a single detected date (same logic as detect_swedish_date_filter)
    if only one can be inferred.
    """
    if not message:
        return []

    text = message.strip().lower()
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    today = date.today()

    candidates: List[str] = []

    # Explicit mentions: idag / igår / i förrgår — collect in order of mention
    # Use simple scans to preserve left-to-right order
    order = []
    tokens = [
        ("idag", "today"),
        ("i dag", "today"),
        ("igår", "yesterday"),
        ("igar", "yesterday"),
        ("i förrgår", "day_before_yesterday"),
        ("i forrgar", "day_before_yesterday"),
    ]
    for token, key in tokens:
        for hay in [text, ascii_text]:
            for m in re.finditer(re.escape(token), hay):
                order.append((m.start(), key))
    order.sort(key=lambda x: x[0])

    for _, key in order:
        if key == "today":
            candidates.append(_format_iso(today))
        elif key == "yesterday":
            candidates.append(_format_iso(today - timedelta(days=1)))
        elif key == "day_before_yesterday":
            candidates.append(_format_iso(today - timedelta(days=2)))

    # Weekday form (i måndags, ...)
    m = re.search(r"\bi\s+(måndags|tisdags|onsdags|torsdags|fredags|lördags|söndags)\b", text)
    if m:
        weekday_name = m.group(1)[:-1]
        weekday_num = _WEEKDAY_NAME_TO_NUM.get(weekday_name)
        if weekday_num is not None:
            today_num = today.weekday()
            days_ago = (today_num - weekday_num) % 7
            if days_ago == 0:
                days_ago = 7
            candidates.append(_format_iso(today - timedelta(days=days_ago)))

    # Explicit ISO
    iso = _match_explicit_iso(text)
    if iso:
        candidates.append(iso)

    # Day + month name
    dm = _match_day_month_name(text, today)
    if dm:
        candidates.append(dm)

    # Deduplicate while preserving order
    seen = set()
    unique_list: List[str] = []
    for d in candidates:
        if d not in seen:
            seen.add(d)
            unique_list.append(d)

    # If nothing clearly found, fall back to single detection logic
    if not unique_list:
        one = detect_swedish_date_filter(message)
        return [one] if one else []

    return unique_list



