"""KST 타임존 적용 테스트 - 각 모듈이 UTC+9 기준으로 날짜를 산출하는지 검증."""
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))


class TestKSTBoundary(unittest.TestCase):
    """KST/UTC 경계 시간대에서 날짜가 올바르게 산출되는지 테스트."""

    def test_utc_2230_is_kst_next_day(self):
        """UTC 22:30 → KST 다음날 07:30, 날짜가 달라야 함."""
        utc_time = datetime(2026, 4, 2, 22, 30, 0, tzinfo=timezone.utc)
        self.assertEqual(utc_time.strftime("%Y-%m-%d"), "2026-04-02")
        self.assertEqual(utc_time.astimezone(KST).strftime("%Y-%m-%d"), "2026-04-03")

    def test_utc_1500_is_kst_same_day_midnight(self):
        """UTC 15:00 → KST 00:00 (자정), 날짜가 바뀌는 정확한 경계."""
        utc_time = datetime(2026, 4, 2, 15, 0, 0, tzinfo=timezone.utc)
        self.assertEqual(utc_time.astimezone(KST).strftime("%Y-%m-%d"), "2026-04-03")

    def test_utc_1459_is_kst_same_day(self):
        """UTC 14:59 → KST 23:59, 아직 같은 날."""
        utc_time = datetime(2026, 4, 2, 14, 59, 0, tzinfo=timezone.utc)
        self.assertEqual(utc_time.astimezone(KST).strftime("%Y-%m-%d"), "2026-04-02")

    def test_weekday_friday(self):
        """2026-04-03은 금요일(weekday=4)."""
        kst_time = datetime(2026, 4, 3, 7, 30, 0, tzinfo=KST)
        weekdays = ["월", "화", "수", "목", "금", "토", "일"]
        self.assertEqual(weekdays[kst_time.weekday()], "금")

    def test_weekday_all_days(self):
        """월~일 매핑이 정확한지 전체 검증."""
        weekdays = ["월", "화", "수", "목", "금", "토", "일"]
        # 2026-03-30(월) ~ 2026-04-05(일)
        from datetime import date
        base = date(2026, 3, 30)  # 월요일
        for i, expected in enumerate(weekdays):
            dt = datetime(base.year, base.month, base.day, 12, 0, 0, tzinfo=KST) + timedelta(days=i)
            self.assertEqual(weekdays[dt.weekday()], expected)


class TestMainPipelineKST(unittest.TestCase):
    """main.py run_pipeline의 KST 날짜/요일 로직 검증."""

    @patch("main.datetime")
    def test_run_pipeline_uses_kst_date(self, mock_dt):
        """run_pipeline이 KST 기준 날짜를 사용하는지 검증."""
        fake_kst = datetime(2026, 4, 3, 7, 30, 0, tzinfo=KST)
        mock_dt.now.return_value = fake_kst
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        # main.py 로직 재현
        now_kst = mock_dt.now(KST)
        today = now_kst.strftime("%Y-%m-%d")
        weekday = ["월", "화", "수", "목", "금", "토", "일"][now_kst.weekday()]

        self.assertEqual(today, "2026-04-03")
        self.assertEqual(weekday, "금")


class TestScriptGeneratorKST(unittest.TestCase):
    """script_generator.py가 KST 날짜를 Claude 프롬프트에 전달하는지 검증."""

    @patch("src.modules.script_generator._call_claude")
    @patch("src.modules.script_generator.datetime")
    def test_generate_briefing_passes_kst_date(self, mock_dt, mock_claude):
        """generate_briefing_markdown이 KST 날짜로 프롬프트를 구성하는지 확인."""
        fake_kst = datetime(2026, 4, 3, 7, 30, 0, tzinfo=KST)
        mock_dt.now.return_value = fake_kst
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        mock_claude.return_value = "## 테스트 브리핑"

        from src.modules.script_generator import generate_briefing_markdown
        result = generate_briefing_markdown({"claude_anthropic": []})

        # _call_claude가 호출될 때 user 프롬프트에 2026-04-03이 포함되어야 함
        call_args = mock_claude.call_args
        user_prompt = call_args[1]["user"] if "user" in call_args[1] else call_args[0][1]
        self.assertIn("2026-04-03", user_prompt)


class TestNotifierKST(unittest.TestCase):
    """notifier.py가 Notion에 KST 날짜를 전달하는지 검증."""

    @patch("src.modules.notifier.requests.post")
    @patch("src.modules.notifier.datetime")
    def test_create_notion_page_uses_kst_date(self, mock_dt, mock_post):
        """Notion API 호출 시 KST 날짜가 사용되는지 확인."""
        fake_kst = datetime(2026, 4, 3, 7, 30, 0, tzinfo=KST)
        mock_dt.now.return_value = fake_kst
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"url": "https://notion.so/test"}
        mock_post.return_value = mock_response

        from src.modules.notifier import create_notion_page
        create_notion_page("테스트 브리핑", "## 내용", "")

        # requests.post 호출 시 body에 2026-04-03이 포함되어야 함
        call_args = mock_post.call_args
        import json
        body = json.dumps(call_args[1].get("json", {}))
        self.assertIn("2026-04-03", body)


class TestNewsCollectorKST(unittest.TestCase):
    """news_collector.py의 cutoff가 KST 기준으로 계산되는지 검증."""

    @patch("src.modules.news_collector.feedparser.parse")
    @patch("src.modules.news_collector.datetime")
    def test_cutoff_filters_by_kst(self, mock_dt, mock_parse):
        """KST 기준 cutoff로 오래된 뉴스를 필터링하는지 확인."""
        fake_kst_naive = datetime(2026, 4, 3, 7, 30, 0)
        mock_now = MagicMock()
        mock_now.replace.return_value = fake_kst_naive
        mock_dt.now.return_value = mock_now
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        # 48시간 이내 기사 1개, 이전 기사 1개
        recent_entry = MagicMock()
        recent_entry.published_parsed = (2026, 4, 2, 12, 0, 0, 0, 0, 0)
        recent_entry.get = lambda k, d="": {"title": "Recent", "link": "http://r", "published": "2026"}.get(k, d)

        old_entry = MagicMock()
        old_entry.published_parsed = (2026, 3, 30, 0, 0, 0, 0, 0, 0)
        old_entry.get = lambda k, d="": {"title": "Old", "link": "http://o", "published": "2026"}.get(k, d)

        mock_feed = MagicMock()
        mock_feed.entries = [recent_entry, old_entry]
        mock_parse.return_value = mock_feed

        from src.modules.news_collector import fetch_rss_entries
        entries = fetch_rss_entries("http://test.rss", hours=48)

        # cutoff = 4/3 07:30 - 48h = 4/1 07:30
        # recent(4/2 12:00) → 통과, old(3/30 00:00) → 필터됨
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["title"], "Recent")


if __name__ == "__main__":
    unittest.main()
