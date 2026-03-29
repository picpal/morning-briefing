"""Configuration and environment variables."""
import os

# API Keys (from GitHub Secrets)
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GOOGLE_TTS_KEY_JSON = os.environ.get("GOOGLE_TTS_KEY_JSON", "")
NOTION_API_KEY = os.environ.get("NOTION_API_KEY", "")
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")

# Notion
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID", "32e9789c-7eb1-8015-ac54-000bb7954c05")

# Slack
SLACK_CHANNEL_ID = os.environ.get("SLACK_CHANNEL_ID", "C0APAH1HJ2W")

# TTS
TTS_VOICE = os.environ.get("TTS_VOICE", "ko-KR-Chirp3-HD-Achernar")
TTS_API_URL = "https://texttospeech.googleapis.com/v1beta1/text:synthesize"

# Claude
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-20250514")

# Briefing categories
CATEGORIES = [
    "🤖 Claude / Anthropic",
    "🧠 LLM / AI 일반",
    "💻 IT / 테크",
    "📈 주식 / 금융",
    "🔒 OWASP / 보안",
    "🛠️ Claude Code / Docs 업데이트",
    "💡 오늘의 Pick",
]
