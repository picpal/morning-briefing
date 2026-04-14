"""Tests for fetch_anthropic_blog_posts() and collect_all_news() integration.

TDD order: Tests written first (RED), then implementation (GREEN).
All tests use unittest.mock — NO live network calls.
"""
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))


def _make_html(published_on: str, slug: str, title: str, summary: str) -> str:
    """Build minimal Next.js SSR HTML fixture containing one article's metadata."""
    pub = f'\\"publishedOn\\":\\"{published_on}\\"' if published_on != "null" else '\\"publishedOn\\":null'
    return (
        f'<html><script id="__NEXT_DATA__">'
        f'{pub},\\"slug\\":{{\\"current\\":\\"{slug}\\"}}'
        f',\\"summary\\":\\"{summary}\\"'
        f',\\"title\\":\\"{title}\\"'
        f'</script></html>'
    )


def _kst_now() -> datetime:
    return datetime.now(KST)


class TestFetchAnthropicBlogPosts(unittest.TestCase):
    """Unit tests for fetch_anthropic_blog_posts()."""

    # ------------------------------------------------------------------
    # T1: Happy path — parses embedded JSON, returns Claude Code entries
    #     within 3 days
    # ------------------------------------------------------------------
    @patch("src.modules.news_collector.requests.get")
    def test_T1_happy_path_returns_matching_entry(self, mock_get):
        """Should return entries with Claude Code keywords published within 3 days."""
        recent_date = (_kst_now() - timedelta(days=1)).strftime("%Y-%m-%d")
        html = _make_html(
            published_on=recent_date,
            slug="claude-code-auto-mode",
            title="Claude Code Auto Mode Released",
            summary="New agentic coding feature for Claude Code.",
        )
        mock_resp = MagicMock()
        mock_resp.text = html
        mock_get.return_value = mock_resp

        from src.modules.news_collector import fetch_anthropic_blog_posts
        results = fetch_anthropic_blog_posts(days=3)

        self.assertGreaterEqual(len(results), 1)
        entry = results[0]
        self.assertIn("title", entry)
        self.assertIn("link", entry)
        self.assertIn("summary", entry)
        self.assertIn("published", entry)
        self.assertEqual(entry["source"], "Anthropic Blog")
        self.assertIn("claude-code-auto-mode", entry["link"])

    # ------------------------------------------------------------------
    # T2: Skips entries with null publishedOn
    # ------------------------------------------------------------------
    @patch("src.modules.news_collector.requests.get")
    def test_T2_skips_null_published_on(self, mock_get):
        """Should skip entries whose publishedOn value is null."""
        html = _make_html(
            published_on="null",
            slug="some-article",
            title="Claude Code new feature",
            summary="agentic coding agent",
        )
        mock_resp = MagicMock()
        mock_resp.text = html
        mock_get.return_value = mock_resp

        from src.modules.news_collector import fetch_anthropic_blog_posts
        results = fetch_anthropic_blog_posts(days=3)

        # Should skip null-dated entries; result must NOT include this article
        links = [e["link"] for e in results]
        self.assertFalse(any("some-article" in l for l in links))

    # ------------------------------------------------------------------
    # T3: Skips entries older than 3 days
    # ------------------------------------------------------------------
    @patch("src.modules.news_collector.requests.get")
    def test_T3_skips_entries_older_than_days(self, mock_get):
        """Should skip entries published more than 3 days ago."""
        old_date = (_kst_now() - timedelta(days=5)).strftime("%Y-%m-%d")
        html = _make_html(
            published_on=old_date,
            slug="old-claude-code-post",
            title="Claude Code old update",
            summary="agentic coding agent old",
        )
        mock_resp = MagicMock()
        mock_resp.text = html
        mock_get.return_value = mock_resp

        from src.modules.news_collector import fetch_anthropic_blog_posts
        results = fetch_anthropic_blog_posts(days=3)

        links = [e["link"] for e in results]
        self.assertFalse(any("old-claude-code-post" in l for l in links))

    # ------------------------------------------------------------------
    # T4: Skips entries without Claude Code keywords
    # ------------------------------------------------------------------
    @patch("src.modules.news_collector.requests.get")
    def test_T4_skips_entries_without_keywords(self, mock_get):
        """Should skip entries that don't match any Claude Code keyword."""
        recent_date = (_kst_now() - timedelta(days=1)).strftime("%Y-%m-%d")
        html = _make_html(
            published_on=recent_date,
            slug="unrelated-ai-blog",
            title="General AI Research Update",
            summary="New findings in neural networks.",
        )
        mock_resp = MagicMock()
        mock_resp.text = html
        mock_get.return_value = mock_resp

        from src.modules.news_collector import fetch_anthropic_blog_posts
        results = fetch_anthropic_blog_posts(days=3)

        links = [e["link"] for e in results]
        self.assertFalse(any("unrelated-ai-blog" in l for l in links))

    # ------------------------------------------------------------------
    # T5: Network exception → returns [] (doesn't raise)
    # ------------------------------------------------------------------
    @patch("src.modules.news_collector.requests.get")
    def test_T5_network_exception_returns_empty_list(self, mock_get):
        """Should return [] gracefully when requests.get raises an exception."""
        mock_get.side_effect = Exception("Connection timeout")

        from src.modules.news_collector import fetch_anthropic_blog_posts
        try:
            results = fetch_anthropic_blog_posts(days=3)
        except Exception:
            self.fail("fetch_anthropic_blog_posts() raised an exception instead of returning []")

        self.assertEqual(results, [])

    # ------------------------------------------------------------------
    # T7: Dedup by title similarity
    # ------------------------------------------------------------------
    @patch("src.modules.news_collector.requests.get")
    def test_T7_dedup_by_title_similarity(self, mock_get):
        """Should deduplicate entries with identical titles from multiple sources."""
        recent_date = (_kst_now() - timedelta(days=1)).strftime("%Y-%m-%d")
        # Same article appears twice (two sources return it)
        html = _make_html(
            published_on=recent_date,
            slug="claude-code-harness",
            title="Claude Code Harness Feature",
            summary="New subagent harness for agentic coding.",
        )
        # Both sources return the same HTML (simulating duplicate)
        mock_resp = MagicMock()
        mock_resp.text = html
        mock_get.return_value = mock_resp

        from src.modules.news_collector import fetch_anthropic_blog_posts, ANTHROPIC_BLOG_SOURCES
        # If there are 2 sources and both return same article, should deduplicate
        results = fetch_anthropic_blog_posts(days=3)

        titles = [e["title"] for e in results]
        # Each unique title should appear only once
        self.assertEqual(len(titles), len(set(titles)))

    # ------------------------------------------------------------------
    # T8: Cap at 10 entries
    # ------------------------------------------------------------------
    @patch("src.modules.news_collector.requests.get")
    def test_T8_cap_at_10_entries(self, mock_get):
        """Should return at most 10 entries even if more match."""
        recent_date = (_kst_now() - timedelta(days=1)).strftime("%Y-%m-%d")

        # Build HTML with 12 distinct matching entries
        entries_html = ""
        for i in range(12):
            entries_html += (
                f'\\"publishedOn\\":\\"{recent_date}\\",'
                f'\\"slug\\":{{\\"current\\":\\"claude-code-item-{i}\\"}}'
                f',\\"summary\\":\\"agentic coding agent feature {i}\\"'
                f',\\"title\\":\\"Claude Code Feature {i}\\"'
                f'|SEPARATOR|'
            )
        html = f"<html>{entries_html}</html>"

        # We need a fixture that the regex actually matches 12 times.
        # Build proper fixture with full separator between articles.
        def build_multi_html(n: int) -> str:
            parts = []
            for i in range(n):
                parts.append(
                    f'\\"publishedOn\\":\\"{recent_date}\\",'
                    f'\\"slug\\":{{\\"current\\":\\"claude-code-item-{i}\\"}}'
                    f',\\"summary\\":\\"agentic coding agent feature number {i}\\"'
                    f',\\"title\\":\\"Claude Code Feature Number {i}\\"'
                )
            return "<html>" + " ".join(parts) + "</html>"

        mock_resp = MagicMock()
        mock_resp.text = build_multi_html(12)
        mock_get.return_value = mock_resp

        from src.modules.news_collector import fetch_anthropic_blog_posts
        results = fetch_anthropic_blog_posts(days=3)

        self.assertLessEqual(len(results), 10)


class TestCollectAllNewsIntegration(unittest.TestCase):
    """Integration tests for collect_all_news() including claude_code_blog key."""

    # ------------------------------------------------------------------
    # T6: collect_all_news() includes "claude_code_blog" key
    # ------------------------------------------------------------------
    @patch("src.modules.news_collector.fetch_anthropic_blog_posts")
    @patch("src.modules.news_collector.fetch_rss_entries")
    def test_T6_collect_all_news_includes_claude_code_blog_key(
        self, mock_rss, mock_blog
    ):
        """collect_all_news() should include 'claude_code_blog' key in result."""
        mock_rss.return_value = []
        mock_blog.return_value = [
            {
                "title": "Claude Code Agent SDK",
                "link": "https://www.anthropic.com/engineering/claude-code-agent-sdk",
                "summary": "New agent SDK for claude code.",
                "published": "2026-04-12",
                "source": "Anthropic Blog",
            }
        ]

        from src.modules.news_collector import collect_all_news
        result = collect_all_news()

        self.assertIn("claude_code_blog", result)
        self.assertIsInstance(result["claude_code_blog"], list)

    @patch("src.modules.news_collector.fetch_anthropic_blog_posts")
    @patch("src.modules.news_collector.fetch_rss_entries")
    def test_T6b_claude_code_blog_contains_blog_entries(
        self, mock_rss, mock_blog
    ):
        """claude_code_blog value should contain entries returned by fetch_anthropic_blog_posts."""
        mock_rss.return_value = []
        sample_entry = {
            "title": "Claude Code Subagent Support",
            "link": "https://www.anthropic.com/news/claude-code-subagent",
            "summary": "Subagent support added to Claude Code.",
            "published": "2026-04-13",
            "source": "Anthropic Blog",
        }
        mock_blog.return_value = [sample_entry]

        from src.modules.news_collector import collect_all_news
        result = collect_all_news()

        blog_entries = result["claude_code_blog"]
        self.assertGreater(len(blog_entries), 0)
        self.assertEqual(blog_entries[0]["title"], "Claude Code Subagent Support")


if __name__ == "__main__":
    unittest.main(verbosity=2)
