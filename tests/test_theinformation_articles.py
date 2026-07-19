from datetime import datetime, timezone

from scripts.update_news import parse_theinformation_articles_items, resolve_opml_bridge_source


def test_resolve_theinformation_articles_bridge():
    assert resolve_opml_bridge_source("https://www.theinformation.com/articles") == {
        "bridge_type": "theinformation_articles",
        "url": "https://www.theinformation.com/articles",
    }


def test_parse_theinformation_jina_markdown_keeps_public_summary_and_exact_time():
    markdown = """
### [Exclusive: Oracle Data Centers Face Cost Surprises](https://www.theinformation.com/newsletters/ai-infrastructure/oracle-cost-surprises)

By [Reporter](https://www.theinformation.com/u/reporter) · Jul 18, 2026 10:04am PDT

[Building an AI supercampus increasingly means paying more than expected.](https://www.theinformation.com/newsletters/ai-infrastructure/oracle-cost-surprises)

### [Unrelated next item](https://www.theinformation.com/articles/next-item)

By Reporter · Jul 18, 2026 8:00am PDT
"""
    items = parse_theinformation_articles_items(
        markdown,
        now=datetime(2026, 7, 19, tzinfo=timezone.utc),
        source_name="The Information",
        markdown=True,
    )

    assert len(items) == 2
    assert items[0].published_at == datetime(2026, 7, 18, 17, 4, tzinfo=timezone.utc)
    assert items[0].meta["summary"] == "Building an AI supercampus increasingly means paying more than expected."


def test_parse_theinformation_jina_markdown_accepts_title_only():
    markdown = """
### [AI Chip Startup Raises Funding](https://www.theinformation.com/articles/ai-chip-startup)

By Reporter · Jul 18, 2026 9:30am PDT
"""
    items = parse_theinformation_articles_items(
        markdown,
        now=datetime(2026, 7, 19, tzinfo=timezone.utc),
        source_name="The Information",
        markdown=True,
    )

    assert len(items) == 1
    assert items[0].meta["summary"] == ""
