"""Refresh ipl-trades.json from official IPL trade advisories on iplt20.com."""

from __future__ import annotations

import datetime
import json
import os
import re
import sys
import urllib.error
import urllib.request
from html import unescape
from typing import Any

sys.path.insert(0, os.path.dirname(__file__))
from ipl_security import validate_snapshot, validate_trade_source_url

IPL_BASE = "https://www.iplt20.com"
NEWS_URL = f"{IPL_BASE}/news"
OUTPUT_FILE = "ipl-trades.json"

# IPL 2027 calendar (IST). Second trade window end is ~30 days before season start.
MILESTONES: list[dict[str, str]] = [
    {
        "id": "trade-window-1-end",
        "label": "Trade Window 1 Closes",
        "at": "2026-12-09T23:59:59+05:30",
        "detail": "7 days before mini-auction",
    },
    {
        "id": "mini-auction-2027",
        "label": "IPL 2027 Mini-Auction",
        "at": "2026-12-16T11:00:00+05:30",
        "detail": "Goa · 11:00 AM IST",
    },
    {
        "id": "trade-window-2-start",
        "label": "Trade Window 2 Opens",
        "at": "2026-12-17T00:00:00+05:30",
        "detail": "Post-auction trades resume",
    },
    {
        "id": "trade-window-2-end",
        "label": "Trade Window 2 Closes",
        "at": "2027-02-12T23:59:59+05:30",
        "detail": "~30 days before season",
    },
    {
        "id": "ipl-2027-kickoff",
        "label": "IPL 2027 Season",
        "at": "2027-03-14T00:00:00+05:30",
        "detail": "Mar 14 – May 30 window",
    },
]

FRANCHISES: dict[str, dict[str, str]] = {
    "CSK": {
        "name": "Chennai Super Kings",
        "color": "#F5C518",
        "tint": "linear-gradient(145deg, rgba(245, 197, 24, 0.22) 0%, rgba(16, 19, 28, 0.95) 85%)",
    },
    "DC": {
        "name": "Delhi Capitals",
        "color": "#3B82F6",
        "tint": "linear-gradient(145deg, rgba(59, 130, 246, 0.22) 0%, rgba(16, 19, 28, 0.95) 85%)",
    },
    "GT": {
        "name": "Gujarat Titans",
        "color": "#38BDF8",
        "tint": "linear-gradient(145deg, rgba(56, 189, 248, 0.22) 0%, rgba(16, 19, 28, 0.95) 85%)",
    },
    "KKR": {
        "name": "Kolkata Knight Riders",
        "color": "#A855F7",
        "tint": "linear-gradient(145deg, rgba(168, 85, 247, 0.24) 0%, rgba(16, 19, 28, 0.95) 85%)",
    },
    "LSG": {
        "name": "Lucknow Super Giants",
        "color": "#34D399",
        "tint": "linear-gradient(145deg, rgba(52, 211, 153, 0.22) 0%, rgba(16, 19, 28, 0.95) 85%)",
    },
    "MI": {
        "name": "Mumbai Indians",
        "color": "#00F0FF",
        "tint": "linear-gradient(145deg, rgba(0, 240, 255, 0.22) 0%, rgba(16, 19, 28, 0.95) 85%)",
    },
    "PBKS": {
        "name": "Punjab Kings",
        "color": "#EF4444",
        "tint": "linear-gradient(145deg, rgba(239, 68, 68, 0.22) 0%, rgba(16, 19, 28, 0.95) 85%)",
    },
    "RR": {
        "name": "Rajasthan Royals",
        "color": "#F472B6",
        "tint": "linear-gradient(145deg, rgba(244, 114, 182, 0.22) 0%, rgba(16, 19, 28, 0.95) 85%)",
    },
    "RCB": {
        "name": "Royal Challengers Bengaluru",
        "color": "#FF2A6D",
        "tint": "linear-gradient(145deg, rgba(255, 42, 109, 0.24) 0%, rgba(16, 19, 28, 0.95) 85%)",
    },
    "SRH": {
        "name": "Sunrisers Hyderabad",
        "color": "#FB923C",
        "tint": "linear-gradient(145deg, rgba(251, 146, 60, 0.22) 0%, rgba(16, 19, 28, 0.95) 85%)",
    },
}

# Structured trade records keyed by official news slug (iplt20.com/news/article/<slug>).
TRADE_BY_SLUG: dict[str, dict[str, Any]] = {
    "rishabh-pant-and-kuldeep-yadav-complete-high-profile-trade-between-dc-and-lsg": {
        "type": "SWAP",
        "label": "Superstar Player Swap",
        "headline": "Pant ⇄ Kuldeep High-Profile Exchange",
        "amountCr": 14.25,
        "purseNote": "Pant rejoins DC at ₹15 Cr • Kuldeep to LSG at ₹13.5 Cr",
        "summary": (
            "Rishabh Pant returns to Delhi Capitals from Lucknow Super Giants, while "
            "Kuldeep Yadav joins LSG — one of the most significant IPL trades in recent years."
        ),
        "left": {
            "name": "Rishabh Pant",
            "from": "LSG",
            "to": "DC",
            "role": "WK-Batter",
            "rating": 96,
            "pose": "batter",
        },
        "right": {
            "name": "Kuldeep Yadav",
            "from": "DC",
            "to": "LSG",
            "role": "Bowler",
            "rating": 94,
            "pose": "bowler",
        },
        "players": [
            {
                "name": "Rishabh Pant",
                "from": "LSG",
                "to": "DC",
                "role": "WK-Batter",
                "feeCr": 15.0,
                "pose": "batter",
            },
            {
                "name": "Kuldeep Yadav",
                "from": "DC",
                "to": "LSG",
                "role": "Bowler",
                "feeCr": 13.5,
                "pose": "bowler",
            },
        ],
    },
    "t-natarajan-returns-to-sunrisers-hyderabad-zeeshan-ansari-moves-to-delhi-capitals": {
        "type": "SWAP",
        "label": "Direct Player Swap",
        "headline": "Natarajan Returns to SRH; Ansari to DC",
        "amountCr": 5.0,
        "purseNote": "Natarajan to SRH at ₹5 Cr • Ansari to DC at ₹0.40 Cr",
        "summary": (
            "T. Natarajan returns to Sunrisers Hyderabad from Delhi Capitals; "
            "leg-spinner Zeeshan Ansari moves to Delhi Capitals."
        ),
        "left": {
            "name": "T. Natarajan",
            "from": "DC",
            "to": "SRH",
            "role": "Bowler",
            "rating": 88,
            "pose": "bowler",
        },
        "right": {
            "name": "Zeeshan Ansari",
            "from": "SRH",
            "to": "DC",
            "role": "Bowler",
            "rating": 82,
            "pose": "bowler",
        },
        "players": [
            {
                "name": "T. Natarajan",
                "from": "DC",
                "to": "SRH",
                "role": "Bowler",
                "feeCr": 5.0,
                "pose": "bowler",
            },
            {
                "name": "Zeeshan Ansari",
                "from": "SRH",
                "to": "DC",
                "role": "Bowler",
                "feeCr": 0.4,
                "pose": "bowler",
            },
        ],
    },
    "csk-and-srh-agree-to-four-player-trade": {
        "type": "SWAP",
        "label": "Four-Player Blockbuster",
        "headline": "CSK ⇄ SRH Four-Player Trade",
        "amountCr": 9.0,
        "purseNote": "Livingstone (₹6 Cr) + Edwards (₹3 Cr) • Khaleel (₹4.8 Cr) + Ellis (₹2 Cr)",
        "summary": (
            "Chennai Super Kings acquire Liam Livingstone and Jack Edwards from Sunrisers Hyderabad; "
            "Khaleel Ahmed and Nathan Ellis move to SRH."
        ),
        "left": {
            "name": "Liam Livingstone (+ Jack Edwards)",
            "from": "SRH",
            "to": "CSK",
            "role": "All-Rounder",
            "rating": 93,
            "pose": "allrounder",
        },
        "right": {
            "name": "Khaleel Ahmed (+ Nathan Ellis)",
            "from": "CSK",
            "to": "SRH",
            "role": "Bowler",
            "rating": 88,
            "pose": "bowler",
        },
        "players": [
            {
                "name": "Liam Livingstone",
                "from": "SRH",
                "to": "CSK",
                "role": "All-Rounder",
                "feeCr": 6.0,
                "pose": "allrounder",
            },
            {
                "name": "Jack Edwards",
                "from": "SRH",
                "to": "CSK",
                "role": "All-Rounder",
                "feeCr": 3.0,
                "pose": "allrounder",
            },
            {
                "name": "Khaleel Ahmed",
                "from": "CSK",
                "to": "SRH",
                "role": "Bowler",
                "feeCr": 4.8,
                "pose": "bowler",
            },
            {
                "name": "Nathan Ellis",
                "from": "CSK",
                "to": "SRH",
                "role": "Bowler",
                "feeCr": 2.0,
                "pose": "bowler",
            },
        ],
    },
    "hardik-pandya-and-arshdeep-singh-complete-major-trade-between-pbks-and-mi": {
        "type": "SWAP",
        "label": "Marquee Player Swap",
        "headline": "Hardik ⇄ Arshdeep Blockbuster",
        "amountCr": 18.0,
        "purseNote": "Pandya to PBKS at ₹18 Cr • Arshdeep to MI at ₹18 Cr",
        "summary": (
            "Mumbai Indians captain Hardik Pandya joins Punjab Kings; "
            "Arshdeep Singh, PBKS' leading wicket-taker, moves to MI."
        ),
        "left": {
            "name": "Hardik Pandya",
            "from": "MI",
            "to": "PBKS",
            "role": "All-Rounder",
            "rating": 94,
            "pose": "allrounder",
        },
        "right": {
            "name": "Arshdeep Singh",
            "from": "PBKS",
            "to": "MI",
            "role": "Bowler",
            "rating": 93,
            "pose": "bowler",
        },
        "players": [
            {
                "name": "Hardik Pandya",
                "from": "MI",
                "to": "PBKS",
                "role": "All-Rounder",
                "feeCr": 18.0,
                "pose": "allrounder",
            },
            {
                "name": "Arshdeep Singh",
                "from": "PBKS",
                "to": "MI",
                "role": "Bowler",
                "feeCr": 18.0,
                "pose": "bowler",
            },
        ],
    },
    "harshal-patel-traded-to-gujarat-titans-from-sunrisers-hyderabad": {
        "type": "CASH",
        "label": "All-Cash Transfer",
        "headline": "Harshal Patel to Gujarat Titans",
        "amountCr": 4.0,
        "purseNote": "GT acquire Patel at ₹4 Cr • SRH purse credit",
        "summary": (
            "Two-time Purple Cap winner Harshal Patel moves from Sunrisers Hyderabad "
            "to Gujarat Titans for a revised fee of ₹4 crore."
        ),
        "left": {
            "name": "Harshal Patel",
            "from": "SRH",
            "to": "GT",
            "role": "Bowler",
            "rating": 91,
            "pose": "bowler",
        },
        "right": {
            "name": "Purse Credit",
            "from": "GT",
            "to": "SRH",
            "role": "₹4.00 Cr Vault",
            "rating": 89,
            "pose": "vault",
        },
        "players": [
            {
                "name": "Harshal Patel",
                "from": "SRH",
                "to": "GT",
                "role": "Bowler",
                "feeCr": 4.0,
                "pose": "bowler",
            },
        ],
    },
    "mohd-shami-and-m-siddharth-traded-to-rajasthan-royals-sam-curran-traded-to-lucknow-super-giants": {
        "type": "SWAP",
        "label": "Multi-Player Trade",
        "headline": "Shami + Siddharth ⇄ Sam Curran",
        "amountCr": 8.75,
        "purseNote": "Shami (₹8 Cr) + Siddharth (₹0.75 Cr) to RR • Curran (₹2.4 Cr) to LSG",
        "summary": (
            "Mohammed Shami and M. Siddharth join Rajasthan Royals from LSG; "
            "Sam Curran moves to Lucknow Super Giants from RR."
        ),
        "left": {
            "name": "Mohammed Shami (+ M. Siddharth)",
            "from": "LSG",
            "to": "RR",
            "role": "Bowler",
            "rating": 92,
            "pose": "bowler",
        },
        "right": {
            "name": "Sam Curran",
            "from": "RR",
            "to": "LSG",
            "role": "All-Rounder",
            "rating": 90,
            "pose": "allrounder",
        },
        "players": [
            {
                "name": "Mohammed Shami",
                "from": "LSG",
                "to": "RR",
                "role": "Bowler",
                "feeCr": 8.0,
                "pose": "bowler",
            },
            {
                "name": "M. Siddharth",
                "from": "LSG",
                "to": "RR",
                "role": "Bowler",
                "feeCr": 0.75,
                "pose": "bowler",
            },
            {
                "name": "Sam Curran",
                "from": "RR",
                "to": "LSG",
                "role": "All-Rounder",
                "feeCr": 2.4,
                "pose": "allrounder",
            },
        ],
    },
}

TRADE_SLUG_RE = re.compile(
    r"(trade|traded|moves-to|returns-to.*moves-to)",
    re.IGNORECASE,
)

META_CONTENT_RE = re.compile(
    r'<meta\s+(?:property|name)=["\'](?P<key>[^"\']+)["\']\s+content=["\'](?P<val>[^"\']*)["\']',
    re.IGNORECASE,
)
TITLE_RE = re.compile(r"<title>([^<]+)</title>", re.IGNORECASE)


def fetch_text(url: str, timeout: int = 30) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "that-hitl-ipl-etl/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def parse_meta_tags(html: str) -> dict[str, str]:
    tags: dict[str, str] = {}
    for match in META_CONTENT_RE.finditer(html):
        tags[match.group("key")] = unescape(match.group("val"))
    return tags


def discover_trade_slugs(html: str) -> list[str]:
    slugs = set(re.findall(r'href="/news/article/([^"]+)"', html))
    trade_slugs = sorted(s for s in slugs if TRADE_SLUG_RE.search(s))
    return trade_slugs


def fetch_article_meta(slug: str) -> dict[str, str]:
    url = f"{IPL_BASE}/news/article/{slug}"
    html = fetch_text(url)
    tags = parse_meta_tags(html)
    title_match = TITLE_RE.search(html)
    title = unescape(title_match.group(1).strip()) if title_match else tags.get("og:title", slug)
    return {
        "slug": slug,
        "url": tags.get("og:url", url),
        "title": title,
        "publishedAt": tags.get("article:published_time", ""),
        "description": tags.get("og:description", tags.get("description", "")),
    }


def normalize_title(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def build_trade_record(slug: str, meta: dict[str, str], ordinal: int) -> dict[str, Any]:
    template = TRADE_BY_SLUG.get(slug)
    if template is None:
        raise KeyError(f"No structured trade mapping for new official slug: {slug}")

    official_title = meta.get("title", "")
    headline = template.get("headline", official_title)
    source_url = meta.get("url", f"{IPL_BASE}/news/article/{slug}")
    record = {
        "id": f"IPL27-{ordinal:02d}",
        **template,
        "headline": headline,
        "sourceUrl": validate_trade_source_url(source_url),
        "officialTitle": official_title,
        "publishedAt": meta.get("publishedAt", ""),
    }
    return record


def build_snapshot(trade_slugs: list[str] | None = None) -> dict[str, Any]:
    news_html = fetch_text(NEWS_URL)
    discovered = discover_trade_slugs(news_html)
    if trade_slugs is not None:
        discovered = [s for s in discovered if s in trade_slugs]
        missing = set(trade_slugs) - set(discovered)
        if missing:
            raise RuntimeError(f"Expected trade slugs not listed on {NEWS_URL}: {sorted(missing)}")

    unmapped = [s for s in discovered if s not in TRADE_BY_SLUG]
    if unmapped:
        raise RuntimeError(
            "New trade articles on iplt20.com need mappings in TRADE_BY_SLUG: "
            + ", ".join(unmapped)
        )

    trades: list[dict[str, Any]] = []
    for slug in discovered:
        meta = fetch_article_meta(slug)
        trades.append(build_trade_record(slug, meta, ordinal=0))

    trades.sort(key=lambda row: row.get("publishedAt") or "")
    for index, trade in enumerate(trades, start=1):
        trade["id"] = f"IPL27-{index:02d}"

    now = datetime.datetime.now(datetime.timezone.utc).astimezone()
    snapshot = {
        "snapshotDate": now.date().isoformat(),
        "fetchedAt": now.isoformat(),
        "seasonLabel": "IPL 2027 Trade Window",
        "status": "LIVE",
        "source": IPL_BASE,
        "discoveredSlugs": discovered,
        "franchises": FRANCHISES,
        "milestones": MILESTONES,
        "trades": trades,
    }
    validate_snapshot(snapshot)
    return snapshot


def write_snapshot(path: str = OUTPUT_FILE, trade_slugs: list[str] | None = None) -> dict[str, Any]:
    snapshot = build_snapshot(trade_slugs=trade_slugs)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(snapshot, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    return snapshot


def main() -> None:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target = os.path.join(root, OUTPUT_FILE)
    snapshot = write_snapshot(target)
    print(f"Wrote {len(snapshot['trades'])} trades to {target}")


if __name__ == "__main__":
    import os

    main()