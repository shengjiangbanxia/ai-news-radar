#!/usr/bin/env python3
"""Build the public industry-event calendar from verified official metadata."""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

MATERIAL_FIELDS = ("status", "start_date", "end_date", "location", "format", "source_url")


def load_json(path: Path, default: dict[str, Any] | None = None) -> dict[str, Any]:
    if not path.exists() and default is not None:
        return default
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: root must be an object")
    return payload


def event_key(event: dict[str, Any]) -> str:
    return f"{event.get('id', '')}:{event.get('cycle', '')}"


def reminder_band(days: int | None) -> str | None:
    if days is None or days < 0:
        return None
    if days == 0:
        return "today"
    if days <= 1:
        return "one_day"
    if days <= 7:
        return "seven_days"
    if days <= 14:
        return "fourteen_days"
    if days <= 30:
        return "thirty_days"
    if days <= 90:
        return "ninety_days"
    return None


def build_payload(config: dict[str, Any], previous: dict[str, Any], *, as_of: date, generated_at: str) -> dict[str, Any]:
    prior = {event_key(item): item for item in previous.get("events", []) if isinstance(item, dict)}
    lookahead = int(config.get("lookahead_days") or 180)
    output: list[dict[str, Any]] = []
    changes: list[dict[str, Any]] = []

    for source in config.get("events", []):
        if not isinstance(source, dict):
            continue
        item = dict(source)
        start = date.fromisoformat(item["start_date"]) if item.get("start_date") else None
        end = date.fromisoformat(item["end_date"]) if item.get("end_date") else start
        days = (start - as_of).days if start else None
        if end and end < as_of and item.get("status") == "confirmed":
            item["status"] = "completed"
        item["days_remaining"] = days
        item["reminder_band"] = reminder_band(days)
        item["within_lookahead"] = bool(days is not None and 0 <= days <= lookahead)
        old = prior.get(event_key(item))
        item_changes = []
        if old:
            for field in MATERIAL_FIELDS:
                if old.get(field) != item.get(field):
                    item_changes.append({"field": field, "old": old.get(field), "new": item.get(field)})
        if item_changes:
            changes.append({"id": item.get("id"), "cycle": item.get("cycle"), "changes": item_changes})
        item["has_material_change"] = bool(item_changes)
        output.append(item)

    status_order = {"confirmed": 0, "partial": 1, "unannounced": 2, "rumored": 3, "cancelled": 4, "completed": 5}
    output.sort(key=lambda item: (
        0 if item.get("days_remaining") is not None and item["days_remaining"] >= 0 else 1,
        item.get("days_remaining") if item.get("days_remaining") is not None and item["days_remaining"] >= 0 else 99999,
        status_order.get(str(item.get("status")), 9),
        str(item.get("name")),
    ))
    upcoming = [item for item in output if item.get("status") == "confirmed" and item.get("days_remaining") is not None and item["days_remaining"] >= 0]
    alerts = [item for item in upcoming if item.get("reminder_band") or item.get("has_material_change")]
    return {
        "generated_at": generated_at,
        "as_of": as_of.isoformat(),
        "timezone": config.get("timezone") or "Asia/Shanghai",
        "lookahead_days": lookahead,
        "milestones": config.get("milestones") or [90, 30, 14, 7, 1, 0],
        "event_count": len(output),
        "confirmed_upcoming_count": len(upcoming),
        "alerts": alerts,
        "changes": changes,
        "events": output,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the industry event warning calendar")
    parser.add_argument("--config", default="config/industry-events.json")
    parser.add_argument("--output", default="data/industry-events.json")
    parser.add_argument("--previous")
    parser.add_argument("--as-of")
    args = parser.parse_args()

    config = load_json(Path(args.config))
    timezone = ZoneInfo(str(config.get("timezone") or "Asia/Shanghai"))
    now = datetime.now(timezone)
    as_of = date.fromisoformat(args.as_of) if args.as_of else now.date()
    previous_path = Path(args.previous) if args.previous else Path(args.output)
    previous = load_json(previous_path, {"events": []})
    payload = build_payload(config, previous, as_of=as_of, generated_at=now.isoformat(timespec="seconds"))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"industry-events: {payload['confirmed_upcoming_count']} upcoming, {len(payload['alerts'])} alerts")


if __name__ == "__main__":
    main()
