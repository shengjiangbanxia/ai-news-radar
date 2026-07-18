from datetime import datetime, timezone

from scripts.update_news import parse_trendforce_news_items


def test_parse_trendforce_news_html_uses_date_from_canonical_url():
    html = """
    <article>
      <a href="/news/2026/07/17/news-example-chip-story/">[News] Example chip story</a>
    </article>
    """

    items = parse_trendforce_news_items(html, source_name="TrendForce News")

    assert len(items) == 1
    assert items[0].source == "TrendForce News"
    assert items[0].url == "https://www.trendforce.com/news/2026/07/17/news-example-chip-story/"
    assert items[0].published_at == datetime(2026, 7, 17, 15, 59, 59, tzinfo=timezone.utc)


def test_parse_trendforce_news_jina_markdown_deduplicates_urls():
    markdown = """
    [First headline](https://www.trendforce.com/news/2026/07/17/first-headline/)
    [First headline](https://www.trendforce.com/news/2026/07/17/first-headline/)
    """

    items = parse_trendforce_news_items(markdown, source_name="TrendForce News", markdown=True)

    assert [item.title for item in items] == ["First headline"]


def test_parse_trendforce_news_jina_markdown_keeps_summary():
    markdown = """
    ## [First headline](https://www.trendforce.com/news/2026/07/17/first-headline/)

    [Semiconductors](https://www.trendforce.com/research/semiconductor)

    This is the article summary shown on the listing page.

    [View More](https://www.trendforce.com/news/2026/07/17/first-headline/)
    """

    items = parse_trendforce_news_items(markdown, source_name="TrendForce News", markdown=True)

    assert len(items) == 1
    assert items[0].meta["summary"] == "Semiconductors This is the article summary shown on the listing page."
