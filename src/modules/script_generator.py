"""Generate briefing markdown and podcast script using Claude API."""
import json
from datetime import datetime, timezone, timedelta
from anthropic import Anthropic
from src.config import ANTHROPIC_API_KEY, CLAUDE_MODEL
from src.prompts.briefing_prompt import (
    BRIEFING_SYSTEM_PROMPT,
    BRIEFING_USER_TEMPLATE,
    PODCAST_SYSTEM_PROMPT,
    PODCAST_USER_TEMPLATE,
)


def _call_claude(system: str, user: str, max_tokens: int = 8192) -> str:
    """Call Claude API and return the response text."""
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return message.content[0].text


def generate_briefing_markdown(news_data: dict[str, list[dict]]) -> str:
    """Generate markdown briefing from collected news data."""
    KST = timezone(timedelta(hours=9))
    today = datetime.now(KST).strftime("%Y-%m-%d")

    # Format news data for the prompt
    formatted = ""
    category_names = {
        "claude_anthropic": "Claude / Anthropic",
        "llm_ai": "LLM / AI 일반",
        "it_tech": "IT / 테크",
        "stock_finance": "주식 / 금융",
        "owasp_security": "OWASP / 보안",
        "claude_code_docs": "Claude Code / Docs 업데이트",
        "claude_code_blog": "Anthropic 공식 블로그",
    }
    for cat_key, items in news_data.items():
        cat_name = category_names.get(cat_key, cat_key)
        formatted += f"\n### {cat_name}\n"
        for item in items:
            formatted += f"- 제목: {item['title']}\n  링크: {item['link']}\n  요약: {item['summary'][:200]}\n  출처: {item['source']}\n\n"

    user_prompt = BRIEFING_USER_TEMPLATE.format(date=today, news_data=formatted)
    print("  Generating briefing markdown via Claude API...")
    return _call_claude(BRIEFING_SYSTEM_PROMPT, user_prompt)


def generate_podcast_script(briefing_markdown: str) -> str:
    """Convert markdown briefing to podcast-style speech script."""
    user_prompt = PODCAST_USER_TEMPLATE.format(briefing_markdown=briefing_markdown)
    print("  Generating podcast script via Claude API...")
    return _call_claude(PODCAST_SYSTEM_PROMPT, user_prompt, max_tokens=4096)


if __name__ == "__main__":
    # Test with sample data
    sample = {"claude_anthropic": [{"title": "Test", "link": "https://example.com", "summary": "Test summary", "source": "Test"}]}
    md = generate_briefing_markdown(sample)
    print(md[:500])
