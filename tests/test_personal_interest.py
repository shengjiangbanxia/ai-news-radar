import pytest

from scripts.personal_interest import score_personal_interest


@pytest.mark.parametrize(
    "term",
    [
        "display", "audio", "tsmc", "cxmt", "samsung", "sumsung", "memory",
        "ai", "npu", "台积电", "apple", "高通", "智谱", "镁光", "大模型论文",
    ],
)
def test_requested_interest_terms_are_included(term):
    result = score_personal_interest({"title": f"Industry update: {term}"})
    assert result["is_interesting"] is True
    assert term.lower() in result["signals"]


def test_broad_autonomous_application_without_industry_context_is_excluded():
    title = (
        "Autonomous micro-drone achieves first air-to-air insect kill on the way "
        "towards completely eradicating mosquitoes"
    )
    result = score_personal_interest({"title": title})
    assert result["is_interesting"] is False
    assert result["reason"] == "no_interest_signal"
    assert result["excluded_topics"] == []


@pytest.mark.parametrize("title", ["Agent joins a travel agency", "Corporate training starts Monday"])
def test_context_only_ai_words_do_not_pass_alone(title):
    result = score_personal_interest({"title": title})
    assert result["is_interesting"] is False


def test_unrelated_general_news_is_excluded():
    result = score_personal_interest({"title": "Local tourism activity opens this weekend"})
    assert result["is_interesting"] is False
    assert result["reason"] == "no_interest_signal"


@pytest.mark.parametrize(
    ("title", "category"),
    [
        ("CXL memory pooling expands across next-generation racks", "server_industry"),
        ("Liquid cooling roadmap targets denser AI clusters", "server_industry"),
        ("Copilot+ PC adds a new on-device model runtime", "pc"),
        ("RAG and vector database research improves enterprise agents", "ai"),
        ("Thunderbolt dock gains smarter display and audio routing", "pc"),
    ],
)
def test_domain_taxonomy_covers_topics_beyond_the_example_terms(title, category):
    result = score_personal_interest({"title": title})
    assert result["is_interesting"] is True
    assert category in result["categories"]


def test_keyword_substrings_do_not_create_false_server_matches():
    result = score_personal_interest({
        "title": "Security engineer ports password cracker hashcat to Gameboy Advance"
    })
    assert result["is_interesting"] is False
    assert "rack" not in result["signals"]
