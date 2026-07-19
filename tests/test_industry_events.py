from datetime import date

from scripts.update_industry_events import build_payload, reminder_band


def test_reminder_bands_are_deterministic():
    assert reminder_band(91) is None
    assert reminder_band(90) == "ninety_days"
    assert reminder_band(30) == "thirty_days"
    assert reminder_band(14) == "fourteen_days"
    assert reminder_band(7) == "seven_days"
    assert reminder_band(1) == "one_day"
    assert reminder_band(0) == "today"
    assert reminder_band(-1) is None


def test_build_payload_marks_upcoming_completed_and_changes():
    config = {
        "timezone": "Asia/Shanghai",
        "lookahead_days": 180,
        "events": [
            {"id": "soon", "cycle": 2026, "name": "Soon", "status": "confirmed", "start_date": "2026-07-25", "end_date": "2026-07-26", "location": "New"},
            {"id": "past", "cycle": 2026, "name": "Past", "status": "confirmed", "start_date": "2026-07-01", "end_date": "2026-07-02"},
            {"id": "unknown", "cycle": 2026, "name": "Unknown", "status": "unannounced", "start_date": None, "end_date": None},
        ],
    }
    previous = {"events": [{"id": "soon", "cycle": 2026, "location": "Old", "status": "confirmed", "start_date": "2026-07-25", "end_date": "2026-07-26"}]}
    payload = build_payload(config, previous, as_of=date(2026, 7, 19), generated_at="2026-07-19T09:00:00+08:00")
    by_id = {item["id"]: item for item in payload["events"]}
    assert by_id["soon"]["days_remaining"] == 6
    assert by_id["soon"]["reminder_band"] == "seven_days"
    assert by_id["soon"]["has_material_change"] is True
    assert by_id["past"]["status"] == "completed"
    assert by_id["unknown"]["days_remaining"] is None
    assert [item["id"] for item in payload["alerts"]] == ["soon"]
