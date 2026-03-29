"""Collect news from RSS feeds and web sources."""
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re


# RSS feeds by category
RSS_FEEDS = {
    "claude_anthropic": [
        "https://news.google.com/rss/search?q=Anthropic+OR+Claude+AI&hl=ko&gl=KR&ceid=KR:ko",
        "https://news.google.com/rss/search?q=Anthropic+OR+Claude+AI&hl=en&gl=US&ceid=US:en",
    ],
    "llm_ai": [
        "https://news.google.com/rss/search?q=LLM+OR+%22large+language+model%22+OR+GPT+OR+Gemini+OR+Mistral&hl=en&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=AI+agent+OR+agentic+AI+OR+MCP+protocol&hl=en&gl=US&ceid=US:en",
    ],
    "it_tech": [
        "https://news.google.com/rss/search?q=technology+news&hl=en&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=%ED%85%8C%ED%81%AC+%EB%89%B4%EC%8A%A4+IT&hl=ko&gl=KR&ceid=KR:ko",
    ],
    "stock_finance": [
        "https://news.google.com/rss/search?q=NVIDIA+stock+OR+AI+stock+OR+S%26P500&hl=en&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=%EC%BD%94%EC%8A%A4%ED%94%BC+OR+%EC%A3%BC%EC%8B%9D+OR+%EC%A6%9D%EC%8B%9C&hl=ko&gl=KR&ceid=KR:ko",
    ],
    "owasp_security": [
        "https://news.google.com/rss/search?q=OWASP+OR+cybersecurity+OR+zero-day+vulnerability&hl=en&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=%EB%B3%B4%EC%95%88+%EC%B7%A8%EC%95%BD%EC%A0%90+OR+%EC%82%AC%EC%9D%B4%EB%B2%84%EB%B3%B4%EC%95%88&hl=ko&gl=KR&ceid=KR:ko",
    ],
    "claude_code_docs": [
        "https://news.google.com/rss/search?q=%22Claude+Code%22+OR+%22Anthropic+docs%22+OR+%22Claude+update%22&hl=en&gl=US&ceid=US:en",
    ],
}


def fetch_rss_entries(feed_url: str, hours: int = 48) -> list[dict]:
    """Fetch RSS entries from the last N hours."""
    try:
        feed = feedparser.parse(feed_url)
        cutoff = datetime.now() - timedelta(hours=hours)
        entries = []
        for entry in feed.entries[:15]:
            published = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6])
            if published and published < cutoff:
                continue
            entries.append({
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "summary": entry.get("summary", ""),
                "published": published.isoformat() if published else "",
                "source": entry.get("source", {}).get("title", ""),
            })
        return entries
    except Exception as e:
        print(f"  RSS error ({feed_url[:60]}...): {e}")
        return []


def collect_all_news() -> dict[str, list[dict]]:
    """Collect news from all RSS feeds grouped by category."""
    all_news = {}
    for category, feeds in RSS_FEEDS.items():
        entries = []
        for feed_url in feeds:
            entries.extend(fetch_rss_entries(feed_url))
        # Deduplicate by title similarity
        seen_titles = set()
        unique = []
        for e in entries:
            short_title = re.sub(r"[^a-zA-Z가-힣0-9]", "", e["title"].lower())[:40]
            if short_title not in seen_titles:
                seen_titles.add(short_title)
                unique.append(e)
        all_news[category] = unique[:10]  # Max 10 per category
        print(f"  [{category}] {len(unique)} articles collected")
    return all_news


if __name__ == "__main__":
    news = collect_all_news()
    for cat, items in news.items():
        print(f"\n=== {cat} ({len(items)}) ===")
        for item in items[:3]:
            print(f"  - {item['title']}")
