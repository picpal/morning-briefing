"""Tests for BRIEFING_USER_TEMPLATE structure in briefing_prompt.py."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.prompts.briefing_prompt import BRIEFING_USER_TEMPLATE


class TestBriefingUserTemplate:
    """Verify the structure of BRIEFING_USER_TEMPLATE."""

    def test_claude_code_blog_section_present(self):
        """'📝 Anthropic 공식 블로그' section must exist in BRIEFING_USER_TEMPLATE."""
        assert "📝 Anthropic 공식 블로그" in BRIEFING_USER_TEMPLATE

    def test_claude_code_blog_after_docs_update_section(self):
        """'📝 Anthropic 공식 블로그' must appear after '🛠️ Claude Code / Docs 업데이트'."""
        docs_pos = BRIEFING_USER_TEMPLATE.find("🛠️ Claude Code / Docs 업데이트")
        blog_pos = BRIEFING_USER_TEMPLATE.find("📝 Anthropic 공식 블로그")
        assert docs_pos != -1, "'🛠️ Claude Code / Docs 업데이트' section not found"
        assert blog_pos != -1, "'📝 Anthropic 공식 블로그' section not found"
        assert blog_pos > docs_pos, (
            "'📝 Anthropic 공식 블로그' should appear after '🛠️ Claude Code / Docs 업데이트'"
        )

    def test_claude_code_blog_before_todays_pick_section(self):
        """'📝 Anthropic 공식 블로그' must appear before '💡 오늘의 Pick'."""
        blog_pos = BRIEFING_USER_TEMPLATE.find("📝 Anthropic 공식 블로그")
        pick_pos = BRIEFING_USER_TEMPLATE.find("💡 오늘의 Pick")
        assert blog_pos != -1, "'📝 Anthropic 공식 블로그' section not found"
        assert pick_pos != -1, "'💡 오늘의 Pick' section not found"
        assert blog_pos < pick_pos, (
            "'📝 Anthropic 공식 블로그' should appear before '💡 오늘의 Pick'"
        )
