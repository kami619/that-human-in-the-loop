"""Refresh the DeepSWE and Artificial Analysis dashboard snapshots."""

import datetime
import json
import os
import requests


DEEPSWE_URL = "https://deepswe.datacurve.ai/artifacts/v1.1/leaderboard-live.json"
ARTIFICIAL_ANALYSIS_URL = "https://artificialanalysis.ai/api/v2/language/models/free"
DEEPSWE_FILE = "deepswe-leaderboard.json"
ARTIFICIAL_ANALYSIS_FILE = "artificial-analysis-leaderboard.json"
TOP_N = 20


def fetch_json(url, headers=None, params=None):
    response = requests.get(url, headers=headers or {}, params=params or {}, timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_paginated_json(url, headers=None):
    """Fetch every page from an Artificial Analysis list endpoint."""
    page = 1
    combined = None
    rows = []
    while True:
        response = fetch_json(url, headers=headers, params={"page": page})
        if combined is None:
            combined = response
        rows.extend(response.get("data", []))
        pagination = response.get("pagination", {})
        if not pagination.get("has_more"):
            break
        page += 1
        if page > pagination.get("total_pages", page):
            raise RuntimeError("Artificial Analysis pagination metadata is inconsistent")
    combined["data"] = rows
    return combined


def provider_for_model(model):
    prefixes = {
        "claude-": "Anthropic",
        "gpt-": "OpenAI",
        "kimi-": "Kimi",
        "gemini-": "Google",
        "glm-": "Z AI",
        "grok-": "xAI",
        "muse-": "Meta",
        "qwen": "Alibaba",
    }
    lowered = model.lower()
    return next((provider for prefix, provider in prefixes.items() if lowered.startswith(prefix)), "Unknown")


def process_deepswe(data):
    """Select the best effort/configuration for each model and rank it."""
    best_by_model = {}
    for row in data.get("rows", []):
        if row.get("source") not in (None, "deep-swe"):
            continue
        model = row.get("model")
        pass_rate = row.get("pass_rate")
        if not model or not isinstance(pass_rate, (int, float)):
            continue
        current = best_by_model.get(model)
        if current is None or pass_rate > current.get("pass_rate", -1):
            best_by_model[model] = row

    ranked = sorted(best_by_model.values(), key=lambda row: row["pass_rate"], reverse=True)[:TOP_N]
    return [
        {
            "rank": index,
            "model": row["model"],
            "provider": provider_for_model(row["model"]),
            "reasoning_effort": row.get("reasoning_effort"),
            "pass_rate": round(row["pass_rate"] * 100, 2),
            "confidence_interval": round((row.get("ci_half") or 0) * 100, 2),
            "average_cost_usd": row.get("mean_cost_usd"),
            "output_tokens": row.get("mean_output_tokens"),
            "agent_steps": row.get("mean_agent_steps"),
        }
        for index, row in enumerate(ranked, start=1)
    ]


def _nested(model, *path):
    value = model
    for key in path:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def _first(model, paths):
    for path in paths:
        value = _nested(model, *path)
        if value is not None:
            return value
    return None


def process_artificial_analysis(data):
    """Normalize the documented language-model API response."""
    rows = []
    for model in data.get("data", []):
        intelligence_index = _first(model, [
            ("evaluations", "artificial_analysis_intelligence_index"),
            ("artificial_analysis_intelligence_index",),
        ])
        if not model.get("name") or intelligence_index is None:
            continue
        rows.append({
            "model": model["name"],
            "provider": _first(model, [("model_creator", "name"), ("creator", "name")]) or "Unknown",
            "intelligence_index": intelligence_index,
            "cost_per_task_usd": _first(model, [
                ("artificial_analysis_intelligence_index_cost", "cost_per_task", "total_cost"),
                ("pricing", "cost_per_task_usd"),
                ("pricing", "cost_per_task"),
            ]),
            "output_speed_tokens_per_second": _first(model, [
                ("performance", "median_output_tokens_per_second"),
                ("median_output_tokens_per_second",),
            ]),
            "latency_first_chunk_seconds": _first(model, [
                ("performance", "median_time_to_first_token_seconds"),
                ("median_time_to_first_token_seconds",),
            ]),
            "total_response_seconds": _first(model, [
                ("performance", "median_total_response_time_seconds"),
                ("performance", "median_end_to_end_response_time_seconds"),
            ]),
        })

    rows.sort(key=lambda row: row["intelligence_index"], reverse=True)
    for rank, row in enumerate(rows[:TOP_N], start=1):
        row["rank"] = rank
    return rows[:TOP_N]


def write_snapshot(path, meta, leaderboard):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump({"meta": meta, "leaderboard": leaderboard}, handle, indent=4)
        handle.write("\n")


def update_deepswe():
    data = fetch_json(DEEPSWE_URL)
    generated_at = data.get("generated_at", datetime.datetime.now(datetime.timezone.utc).isoformat())
    write_snapshot(
        DEEPSWE_FILE,
        {
            "source": "Datacurve DeepSWE",
            "url": "https://deepswe.datacurve.ai/",
            "artifact_url": DEEPSWE_URL,
            "version": "v1.1",
            "last_updated": generated_at[:10],
            "tasks": data.get("n_tasks_in_set"),
            "description": "Long-horizon coding-agent benchmark with program-based verification",
        },
        process_deepswe(data),
    )


def update_artificial_analysis():
    api_key = os.environ.get("ARTIFICIAL_ANALYSIS_API_KEY")
    if not api_key:
        raise RuntimeError("ARTIFICIAL_ANALYSIS_API_KEY is required")
    data = fetch_paginated_json(ARTIFICIAL_ANALYSIS_URL, {"x-api-key": api_key})
    write_snapshot(
        ARTIFICIAL_ANALYSIS_FILE,
        {
            "source": "Artificial Analysis Intelligence Index",
            "url": "https://artificialanalysis.ai/leaderboards/models",
            "api_url": ARTIFICIAL_ANALYSIS_URL,
            "version": str(data.get("intelligence_index_version", "unknown")),
            "last_updated": datetime.datetime.now(datetime.timezone.utc).date().isoformat(),
            "description": "Independent model intelligence, cost, and performance comparison",
        },
        process_artificial_analysis(data),
    )


def main():
    print("Updating DeepSWE snapshot...")
    update_deepswe()
    print("Updating Artificial Analysis snapshot...")
    update_artificial_analysis()
    print("Done.")


if __name__ == "__main__":
    main()
