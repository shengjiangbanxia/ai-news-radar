"""Tests for the DeepSeek-first title translation path: provider priority,
Google fallback, and the ds1| versioned cache-key compatibility strategy."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from scripts.update_news import (
    ZH_CACHE_DS_PREFIX,
    add_bilingual_fields,
    translate_to_zh_deepseek,
)


EN_TITLE = "OpenAI launches new Codex agent for developers"
DS_ZH = "OpenAI 为开发者推出全新 Codex 智能体"
GOOGLE_ZH = "OpenAI 为开发人员推出新的 Codex 代理"

DS_ENV = {"DEEPSEEK_API_KEY": "sk-test"}


def make_item(title: str = EN_TITLE) -> dict:
    return {"title": title, "url": "https://example.com/news/1"}


def deepseek_ok_response(content: str = DS_ZH) -> MagicMock:
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"choices": [{"message": {"content": content}}]}
    return resp


def deepseek_error_response(status: int = 500) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status
    return resp


def google_session(translated: str = GOOGLE_ZH) -> MagicMock:
    session = MagicMock()
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = [[[translated, EN_TITLE]]]
    resp.raise_for_status.return_value = None
    session.get.return_value = resp
    return session


def run_enrich(session: MagicMock, cache: dict) -> tuple[list[dict], dict]:
    items_ai, _, cache_out = add_bilingual_fields(
        [make_item()], [], session, cache, max_new_translations=10
    )
    return items_ai, cache_out


class TestDeepSeekPriority(unittest.TestCase):
    def test_deepseek_success_skips_google(self):
        session = google_session()
        with patch.dict("os.environ", DS_ENV, clear=True), patch(
            "scripts.update_news.requests.post", return_value=deepseek_ok_response()
        ) as mock_post:
            items, cache = run_enrich(session, {})
        mock_post.assert_called_once()
        session.get.assert_not_called()
        self.assertEqual(items[0]["title_zh"], DS_ZH)

    def test_deepseek_failure_falls_back_to_google(self):
        session = google_session()
        with patch.dict("os.environ", DS_ENV, clear=True), patch(
            "scripts.update_news.requests.post", return_value=deepseek_error_response()
        ) as mock_post:
            items, cache = run_enrich(session, {})
        mock_post.assert_called_once()
        session.get.assert_called_once()
        self.assertEqual(items[0]["title_zh"], GOOGLE_ZH)
        # Google translations keep the bare cache key.
        self.assertEqual(cache.get(EN_TITLE), GOOGLE_ZH)
        self.assertNotIn(ZH_CACHE_DS_PREFIX + EN_TITLE, cache)

    def test_no_key_goes_straight_to_google(self):
        session = google_session()
        with patch.dict("os.environ", {}, clear=True), patch(
            "scripts.update_news.requests.post"
        ) as mock_post:
            items, cache = run_enrich(session, {})
        mock_post.assert_not_called()
        session.get.assert_called_once()
        self.assertEqual(items[0]["title_zh"], GOOGLE_ZH)


class TestTranslateToZhDeepseek(unittest.TestCase):
    def test_returns_none_without_key(self):
        with patch.dict("os.environ", {}, clear=True), patch(
            "scripts.update_news.requests.post"
        ) as mock_post:
            self.assertIsNone(translate_to_zh_deepseek(EN_TITLE))
        mock_post.assert_not_called()

    def test_returns_none_on_exception(self):
        with patch.dict("os.environ", DS_ENV, clear=True), patch(
            "scripts.update_news.requests.post", side_effect=Exception("boom")
        ):
            self.assertIsNone(translate_to_zh_deepseek(EN_TITLE))

    def test_returns_none_on_empty_choices(self):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"choices": []}
        with patch.dict("os.environ", DS_ENV, clear=True), patch(
            "scripts.update_news.requests.post", return_value=resp
        ):
            self.assertIsNone(translate_to_zh_deepseek(EN_TITLE))


class TestCacheKeyVersioning(unittest.TestCase):
    def test_deepseek_translation_cached_with_prefix(self):
        session = google_session()
        with patch.dict("os.environ", DS_ENV, clear=True), patch(
            "scripts.update_news.requests.post", return_value=deepseek_ok_response()
        ):
            _, cache = run_enrich(session, {})
        self.assertEqual(cache.get(ZH_CACHE_DS_PREFIX + EN_TITLE), DS_ZH)
        self.assertNotIn(EN_TITLE, cache)

    def test_prefixed_cache_hit_skips_all_network(self):
        session = google_session()
        cache = {ZH_CACHE_DS_PREFIX + EN_TITLE: DS_ZH}
        with patch.dict("os.environ", DS_ENV, clear=True), patch(
            "scripts.update_news.requests.post"
        ) as mock_post:
            items, _ = run_enrich(session, cache)
        mock_post.assert_not_called()
        session.get.assert_not_called()
        self.assertEqual(items[0]["title_zh"], DS_ZH)

    def test_bare_key_cache_is_miss_when_deepseek_key_present(self):
        session = google_session()
        cache = {EN_TITLE: GOOGLE_ZH}
        with patch.dict("os.environ", DS_ENV, clear=True), patch(
            "scripts.update_news.requests.post", return_value=deepseek_ok_response()
        ) as mock_post:
            items, cache_out = run_enrich(session, cache)
        mock_post.assert_called_once()
        self.assertEqual(items[0]["title_zh"], DS_ZH)
        # Old bare-key entry stays untouched; new entry lands under ds1| prefix.
        self.assertEqual(cache_out.get(EN_TITLE), GOOGLE_ZH)
        self.assertEqual(cache_out.get(ZH_CACHE_DS_PREFIX + EN_TITLE), DS_ZH)

    def test_bare_key_cache_hits_when_no_deepseek_key(self):
        session = google_session()
        cache = {EN_TITLE: GOOGLE_ZH}
        with patch.dict("os.environ", {}, clear=True), patch(
            "scripts.update_news.requests.post"
        ) as mock_post:
            items, _ = run_enrich(session, cache)
        mock_post.assert_not_called()
        session.get.assert_not_called()
        self.assertEqual(items[0]["title_zh"], GOOGLE_ZH)


class TestRepairTermTable(unittest.TestCase):
    def test_hugging_face_repair(self):
        from scripts.update_news import repair_zh_title_translation

        self.assertEqual(
            repair_zh_title_translation("Hugging Face releases new dataset", "拥抱脸发布新数据集"),
            "Hugging Face发布新数据集",
        )

    def test_transformer_not_repaired_for_movie_context(self):
        from scripts.update_news import repair_zh_title_translation

        self.assertEqual(
            repair_zh_title_translation("New Transformers movie trailer released", "新变形金刚电影预告发布"),
            "新变形金刚电影预告发布",
        )

    def test_openai_and_anthropic_repair(self):
        from scripts.update_news import repair_zh_title_translation

        self.assertEqual(
            repair_zh_title_translation("OpenAI and Anthropic partner up", "开放人工智能与人择合作"),
            "OpenAI与Anthropic合作",
        )


if __name__ == "__main__":
    unittest.main()
