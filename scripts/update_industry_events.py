#!/usr/bin/env python3
"""Build the public industry-event calendar from verified official metadata."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

MATERIAL_FIELDS = ("status", "start_date", "end_date", "location", "format", "source_url")
USER_AGENT = "AIIndustryNewsRadar/1.0 (+https://github.com/LearnPrompt/ai-news-radar)"
MONTHS = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
}
MONTH_PATTERN = r"Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?"
TEXT_DATE_PATTERNS = (
    re.compile(rf"\b(?P<month>{MONTH_PATTERN})\.?\s+(?P<day1>\d{{1,2}})(?:st|nd|rd|th)?\s*[-–—]\s*(?P<day2>\d{{1,2}})(?:st|nd|rd|th)?\s*,?\s*(?P<year>20\d{{2}})\b", re.I),
    re.compile(rf"\b(?P<day1>\d{{1,2}})(?:st|nd|rd|th)?\s*[-–—]\s*(?P<day2>\d{{1,2}})(?:st|nd|rd|th)?\s+(?P<month>{MONTH_PATTERN})\.?\s+(?P<year>20\d{{2}})\b", re.I),
)


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


def _walk_json(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_json(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_json(child)


def _iso_date(value: Any) -> str | None:
    if not value:
        return None
    try:
        return date_parser.parse(str(value)).date().isoformat()
    except (TypeError, ValueError, OverflowError):
        return None


def _normalized_name(value: Any) -> str:
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", str(value or "").lower())


def _event_type(value: Any) -> bool:
    values = value if isinstance(value, list) else [value]
    return any(str(item).lower().rsplit("/", 1)[-1] == "event" for item in values)


def _candidate_matches(candidate: dict[str, Any], event: dict[str, Any]) -> bool:
    candidate_name = _normalized_name(candidate.get("name") or candidate.get("headline"))
    if not candidate_name:
        return False
    names = [event.get("name"), *(event.get("aliases") or [])]
    return any(
        len(alias) >= 4 and (alias in candidate_name or candidate_name in alias)
        for alias in (_normalized_name(name) for name in names)
        if alias
    )


def _location_text(value: Any) -> str | None:
    if isinstance(value, str):
        return value.strip() or None
    if not isinstance(value, dict):
        return None
    address = value.get("address")
    if isinstance(address, dict):
        parts = [address.get(key) for key in ("addressLocality", "addressRegion", "addressCountry")]
        text = ", ".join(str(part).strip() for part in parts if part)
        if text:
            return text
    return str(value.get("name") or "").strip() or None


def extract_structured_event(html: str, event: dict[str, Any]) -> dict[str, Any] | None:
    soup = BeautifulSoup(html, "html.parser")
    candidates: list[dict[str, Any]] = []
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            payload = json.loads(script.string or script.get_text() or "null")
        except (TypeError, json.JSONDecodeError):
            continue
        for node in _walk_json(payload):
            if _event_type(node.get("@type")) and _candidate_matches(node, event):
                start_date = _iso_date(node.get("startDate"))
                end_date = _iso_date(node.get("endDate"))
                if start_date:
                    candidates.append({
                        "name": str(node.get("name") or "").strip(),
                        "start_date": start_date,
                        "end_date": end_date,
                        "location": _location_text(node.get("location")),
                        "attendance_mode": str(node.get("eventAttendanceMode") or ""),
                    })
    cycle = int(event.get("cycle") or 0)
    matching_cycle = [item for item in candidates if int(item["start_date"][:4]) == cycle]
    if not matching_cycle:
        return None
    matching_cycle.sort(key=lambda item: (not bool(item.get("end_date")), item["start_date"]))
    return matching_cycle[0]


def extract_text_event_dates(html: str, event: dict[str, Any]) -> dict[str, Any] | None:
    text = re.sub(r"\s+", " ", BeautifulSoup(html, "html.parser").get_text(" ", strip=True))
    aliases = [_normalized_name(event.get("name")), *(_normalized_name(value) for value in event.get("aliases") or [])]
    aliases = [value for value in aliases if len(value) >= 3]
    cycle = int(event.get("cycle") or 0)
    candidates: list[tuple[int, dict[str, Any]]] = []
    for pattern in TEXT_DATE_PATTERNS:
        for match in pattern.finditer(text):
            if int(match.group("year")) != cycle:
                continue
            month = MONTHS.get(match.group("month").lower().rstrip("."))
            if not month:
                continue
            try:
                start = date(cycle, month, int(match.group("day1")))
                end = date(cycle, month, int(match.group("day2")))
            except ValueError:
                continue
            if end < start:
                continue
            # Official event headings normally precede their date. Restricting
            # the evidence window to preceding text avoids borrowing a nearby
            # date from an unrelated event listed earlier on an index page.
            window = _normalized_name(text[max(0, match.start() - 240):match.start()])
            proximity = max((len(alias) for alias in aliases if alias in window), default=0)
            if not proximity:
                continue
            candidates.append((proximity, {
                "name": str(event.get("name") or ""),
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "location": None,
                "attendance_mode": "",
            }))
    if not candidates:
        return None
    candidates.sort(key=lambda row: (-row[0], row[1]["start_date"]))
    return candidates[0][1]


def _format_from_attendance_mode(value: str) -> str | None:
    lowered = value.lower()
    if "mixed" in lowered or "hybrid" in lowered:
        return "hybrid"
    if "online" in lowered:
        return "online"
    if "offline" in lowered:
        return "in-person"
    return None


def verify_official_sources(
    config: dict[str, Any],
    *,
    session: requests.Session,
    observed_at: str,
) -> tuple[dict[str, Any], dict[str, int]]:
    checked = 0
    successful = 0
    structured = 0
    review_required = 0
    events: list[dict[str, Any]] = []
    for source in config.get("events", []):
        if not isinstance(source, dict):
            continue
        item = dict(source)
        url = str(item.get("source_url") or "").strip()
        verification: dict[str, Any] = {"checked_at": observed_at, "ok": False, "method": None}
        if not url:
            verification["error"] = "missing_official_source_url"
            item["verification"] = verification
            events.append(item)
            continue
        checked += 1
        try:
            response = session.get(url, timeout=12, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"})
            response.raise_for_status()
            successful += 1
            candidate = extract_structured_event(response.text, item)
            candidate_method = "official_jsonld" if candidate else None
            if not candidate:
                candidate = extract_text_event_dates(response.text, item)
                candidate_method = "official_text" if candidate else None
            verification.update({
                "ok": True,
                "http_status": response.status_code,
                "method": "official_page",
                "registration_open": bool(re.search(r"\bregister(?: now| today)?\b|registration (?:is )?open|立即注册|开放注册", response.text, re.I)),
                "agenda_published": bool(re.search(r"\bagenda\b|full schedule|advance program|完整议程|日程发布", response.text, re.I)),
            })
            if candidate:
                verification["method"] = candidate_method
                verification["structured_candidate"] = candidate
                signature = json.dumps(candidate, ensure_ascii=False, sort_keys=True)
                verification["candidate_hash"] = hashlib.sha256(signature.encode("utf-8")).hexdigest()[:16]
                if candidate_method == "official_jsonld":
                    structured += 1
                if candidate_method == "official_text":
                    verification["text_date_match"] = True
                if candidate.get("start_date") and candidate.get("end_date"):
                    item["start_date"] = candidate["start_date"]
                    item["end_date"] = candidate["end_date"]
                    item["status"] = "confirmed"
                    if candidate.get("location"):
                        item["location"] = candidate["location"]
                    detected_format = _format_from_attendance_mode(str(candidate.get("attendance_mode") or ""))
                    if detected_format:
                        item["format"] = detected_format
                else:
                    verification["review_required"] = True
                    review_required += 1
            item["verification"] = verification
        except requests.RequestException as exc:
            verification["error"] = f"{type(exc).__name__}: {exc}"[:240]
            item["verification"] = verification
        events.append(item)
    verified_config = dict(config)
    verified_config["events"] = events
    return verified_config, {
        "configured": len(events),
        "checked": checked,
        "successful": successful,
        "structured_matches": structured,
        "date_matches": sum(1 for item in events if isinstance(item.get("verification"), dict) and item["verification"].get("structured_candidate")),
        "review_required": review_required,
    }


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


def build_payload(config: dict[str, Any], previous: dict[str, Any], *, as_of: date, generated_at: str, source_check: dict[str, int] | None = None) -> dict[str, Any]:
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
            current_verification = item.get("verification") if isinstance(item.get("verification"), dict) else None
            previous_verification = old.get("verification") if isinstance(old.get("verification"), dict) else {}
            if current_verification:
                for field in ("registration_open", "agenda_published", "candidate_hash"):
                    if previous_verification.get(field) != current_verification.get(field):
                        item_changes.append({
                            "field": f"verification.{field}",
                            "old": previous_verification.get(field),
                            "new": current_verification.get(field),
                        })
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
        "source_check": source_check or {"configured": len(output), "checked": 0, "successful": 0, "structured_matches": 0, "date_matches": 0, "review_required": 0},
        "events": output,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the industry event warning calendar")
    parser.add_argument("--config", default="config/industry-events.json")
    parser.add_argument("--output", default="data/industry-events.json")
    parser.add_argument("--previous")
    parser.add_argument("--as-of")
    parser.add_argument("--offline", action="store_true", help="skip official-page verification")
    args = parser.parse_args()

    config = load_json(Path(args.config))
    timezone = ZoneInfo(str(config.get("timezone") or "Asia/Shanghai"))
    now = datetime.now(timezone)
    as_of = date.fromisoformat(args.as_of) if args.as_of else now.date()
    previous_path = Path(args.previous) if args.previous else Path(args.output)
    previous = load_json(previous_path, {"events": []})
    source_check = None
    if not args.offline:
        session = requests.Session()
        config, source_check = verify_official_sources(config, session=session, observed_at=now.isoformat(timespec="seconds"))
    payload = build_payload(config, previous, as_of=as_of, generated_at=now.isoformat(timespec="seconds"), source_check=source_check)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    checks = payload["source_check"]
    print(f"industry-events: {payload['confirmed_upcoming_count']} upcoming, {len(payload['alerts'])} alerts, official {checks['successful']}/{checks['checked']}")


if __name__ == "__main__":
    main()
