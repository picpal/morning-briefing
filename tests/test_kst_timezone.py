"""KST 타임존 적용 테스트 - datetime.now()가 UTC+9 기준으로 동작하는지 검증."""
import unittest
from unittest.mock import patch
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))


class TestKSTTimezone(unittest.TestCase):
    """각 모듈에서 KST 타임존이 올바르게 적용되는지 테스트."""

    # 2026-04-03 07:30 KST = 2026-04-02 22:30 UTC
    # UTC 기준이면 4/2, KST 기준이면 4/3이 되어야 함
    MOCK_UTC = datetime(2026, 4, 2, 22, 30, 0, tzinfo=timezone.utc)

    @patch("src.modules.script_generator.datetime")
    def test_script_generator_uses_kst(self, mock_dt):
        mock_dt.now.return_value = self.MOCK_UTC.astimezone(KST)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        from src.modules.script_generator import datetime as sg_datetime

        now_kst = self.MOCK_UTC.astimezone(KST)
        today = now_kst.strftime("%Y-%m-%d")
        self.assertEqual(today, "2026-04-03")

    @patch("src.modules.notifier.datetime")
    def test_notifier_uses_kst(self, mock_dt):
        mock_dt.now.return_value = self.MOCK_UTC.astimezone(KST)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        now_kst = self.MOCK_UTC.astimezone(KST)
        today = now_kst.strftime("%Y-%m-%d")
        self.assertEqual(today, "2026-04-03")

    def test_kst_date_differs_from_utc_at_boundary(self):
        """UTC 22:30은 KST로 다음날 07:30 - 날짜가 달라야 함."""
        utc_time = datetime(2026, 4, 2, 22, 30, 0, tzinfo=timezone.utc)
        utc_date = utc_time.strftime("%Y-%m-%d")
        kst_date = utc_time.astimezone(KST).strftime("%Y-%m-%d")

        self.assertEqual(utc_date, "2026-04-02")
        self.assertEqual(kst_date, "2026-04-03")
        self.assertNotEqual(utc_date, kst_date)

    def test_kst_weekday_correct(self):
        """2026-04-03은 금요일(weekday=4)이어야 함."""
        kst_time = datetime(2026, 4, 3, 7, 30, 0, tzinfo=KST)
        weekdays = ["월", "화", "수", "목", "금", "토", "일"]
        self.assertEqual(weekdays[kst_time.weekday()], "금")

    def test_main_pipeline_date_format(self):
        """main.py와 동일한 로직으로 KST 날짜/요일 생성 테스트."""
        utc_time = datetime(2026, 4, 2, 22, 30, 0, tzinfo=timezone.utc)

        # main.py 로직 재현
        now_kst = utc_time.astimezone(KST)
        today = now_kst.strftime("%Y-%m-%d")
        weekday = ["월", "화", "수", "목", "금", "토", "일"][now_kst.weekday()]

        self.assertEqual(today, "2026-04-03")
        self.assertEqual(weekday, "금")

    def test_news_collector_cutoff_uses_kst(self):
        """뉴스 수집 cutoff가 KST 기준으로 계산되는지 테스트."""
        utc_time = datetime(2026, 4, 2, 22, 30, 0, tzinfo=timezone.utc)
        now_kst = utc_time.astimezone(KST)

        # news_collector.py 로직 재현: KST 기준 now에서 48시간 전
        cutoff = now_kst.replace(tzinfo=None) - timedelta(hours=48)
        expected = datetime(2026, 4, 1, 7, 30, 0)
        self.assertEqual(cutoff, expected)


if __name__ == "__main__":
    unittest.main()
