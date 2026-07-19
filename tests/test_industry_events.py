from datetime import date

from scripts.update_industry_events import (
    build_payload,
    extract_structured_event,
    extract_text_event_dates,
    reminder_band,
    verify_official_sources,
)


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


def test_extract_structured_event_requires_matching_name_and_cycle():
    html = """
    <script type="application/ld+json">
    {"@context":"https://schema.org","@type":"Event","name":"NVIDIA GTC 2027",
     "startDate":"2027-03-14T09:00:00-07:00","endDate":"2027-03-18T17:00:00-07:00",
     "eventAttendanceMode":"https://schema.org/MixedEventAttendanceMode",
     "location":{"name":"McEnery Convention Center","address":{"addressLocality":"San Jose","addressCountry":"USA"}}}
    </script>
    """
    event = {"name": "NVIDIA GTC", "aliases": ["GTC"], "cycle": 2027}
    candidate = extract_structured_event(html, event)
    assert candidate["start_date"] == "2027-03-14"
    assert candidate["end_date"] == "2027-03-18"
    assert candidate["location"] == "San Jose, USA"
    assert extract_structured_event(html, {**event, "cycle": 2028}) is None


def test_verify_official_sources_promotes_exact_structured_date():
    class Response:
        status_code = 200
        text = """<html><script type="application/ld+json">
        {"@type":"Event","name":"Example Summit 2027","startDate":"2027-02-03",
         "endDate":"2027-02-05","eventAttendanceMode":"https://schema.org/OnlineEventAttendanceMode"}
        </script><p>Registration is open. Full schedule.</p></html>"""

        def raise_for_status(self):
            return None

    class Session:
        def get(self, *args, **kwargs):
            return Response()

    config = {"events": [{
        "id": "example", "name": "Example Summit", "aliases": [], "cycle": 2027,
        "status": "unannounced", "start_date": None, "end_date": None,
        "source_url": "https://example.com/event",
    }]}
    verified, stats = verify_official_sources(config, session=Session(), observed_at="2026-07-19T10:00:00+08:00")
    item = verified["events"][0]
    assert item["status"] == "confirmed"
    assert item["start_date"] == "2027-02-03"
    assert item["end_date"] == "2027-02-05"
    assert item["format"] == "online"
    assert item["verification"]["registration_open"] is True
    assert item["verification"]["agenda_published"] is True
    assert stats["structured_matches"] == 1


def test_extract_text_event_dates_supports_both_official_date_orders():
    ces = extract_text_event_dates(
        "<main><h1>CES 2027</h1><p>CES 2027: Jan. 6-9, 2027 in Las Vegas.</p></main>",
        {"name": "CES", "aliases": ["Consumer Electronics Show"], "cycle": 2027},
    )
    assert ces["start_date"] == "2027-01-06"
    assert ces["end_date"] == "2027-01-09"

    mwc = extract_text_event_dates(
        "<main><h1>MWC Barcelona</h1><p>Date 1-4 March 2027</p></main>",
        {"name": "MWC Barcelona", "aliases": ["Mobile World Congress"], "cycle": 2027},
    )
    assert mwc["start_date"] == "2027-03-01"
    assert mwc["end_date"] == "2027-03-04"


def test_extract_text_event_dates_rejects_unrelated_or_wrong_cycle():
    html = "<p>Other Conference Jan 6-9, 2027</p><h1>Example Summit</h1>"
    assert extract_text_event_dates(html, {"name": "Example Summit", "aliases": [], "cycle": 2027}) is None
    assert extract_text_event_dates("<h1>Example Summit</h1><p>Jan 6-9, 2027</p>", {"name": "Example Summit", "aliases": [], "cycle": 2028}) is None
