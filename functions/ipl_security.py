"""Validation helpers for IPL trade snapshot data."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

ALLOWED_SOURCE_HOSTS = frozenset({"www.iplt20.com", "iplt20.com"})

TINT_RE = re.compile(
    r"^linear-gradient\(\s*\d+deg\s*,\s*rgba\(\d{1,3},\s*\d{1,3},\s*\d{1,3},\s*[\d.]+\)\s*0%\s*,\s*"
    r"rgba\(\d{1,3},\s*\d{1,3},\s*\d{1,3},\s*[\d.]+\)\s*\d{1,3}%\s*\)$",
    re.IGNORECASE,
)


def is_https_url(url: str, allowed_hosts: frozenset[str] | None = None) -> bool:
    if not url or not isinstance(url, str):
        return False
    try:
        parsed = urlparse(url.strip())
    except ValueError:
        return False
    if parsed.scheme != "https":
        return False
    if not parsed.netloc:
        return False
    if allowed_hosts is not None and parsed.hostname not in allowed_hosts:
        return False
    return True


def validate_tint(tint: str) -> bool:
    if not tint or len(tint) > 256:
        return False
    if any(char in tint for char in ";<>\"'\\"):
        return False
    return TINT_RE.match(tint) is not None


def validate_trade_source_url(url: str) -> str:
    if not is_https_url(url, ALLOWED_SOURCE_HOSTS):
        raise ValueError(f"Invalid trade sourceUrl (https://www.iplt20.com only): {url!r}")
    return url


def validate_franchises(franchises: dict[str, Any]) -> None:
    for code, row in franchises.items():
        tint = row.get("tint", "")
        if not validate_tint(tint):
            raise ValueError(f"Invalid tint for franchise {code!r}")


def validate_trades(trades: list[dict[str, Any]]) -> None:
    for trade in trades:
        source = trade.get("sourceUrl")
        if source:
            validate_trade_source_url(source)


def validate_snapshot(snapshot: dict[str, Any]) -> None:
    validate_franchises(snapshot.get("franchises", {}))
    validate_trades(snapshot.get("trades", []))