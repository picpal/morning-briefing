"""Collect news from RSS feeds and web sources."""
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
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


ANTHROPIC_BLOG_SOURCES = [
    "https://www.anthropic.com/engineering",
    "https://www.anthropic.com/news",
]

ANTHROPIC_BLOG_KEYWORDS = [
    # Claude Code
    "claude code", "claude-code",
    # Agent infrastructure
    "agentic coding", "claude agent sdk", "agent sdk",
    "managed agents", "managed agent",
    "coding agent", "harness", "subagent",
    # Protocol / integration
    "mcp", "model context protocol",
    "skill", "prompt caching", "prompt cache",
    "computer use", "tool use",
    # Official SDKs / APIs
    "claude api", "anthropic api",
]

# Regex to extract article metadata from Next.js SSR HTML.
# Groups: (1) publishedOn value or null, (2) slug string,
#         (3) summary string, (4) title string.
_BLOG_PATTERN = re.compile(
    r'\\"publishedOn\\":(\\"[^"]+\\"|null)[^{}]*?'
    r'\\"slug\\":\{[^}]*?\\"current\\":\\"([^"]+)\\"'
    r'[\s\S]{0,3000}?'
    r'\\"summary\\":\\"((?:[^"\\\\]|\\\\.)*)\\"'
    r'[^{}]*?'
    r'\\"title\\":\\"((?:[^"\\\\]|\\\\.)*)\\"'
)


def _unescape(s: str) -> str:
    """Unescape simple backslash sequences extracted from Next.js SSR JSON."""
    return s.replace('\\"', '"').replace("\\\\", "\\").replace("\\n", " ")


def _dedup_by_title(entries: list[dict]) -> list[dict]:
    """Deduplicate entries by normalised title (alphanumeric chars, first 40)."""
    seen: set[str] = set()
    unique: list[dict] = []
    for e in entries:
        short_title = re.sub(r"[^a-zA-Z가-힣0-9]", "", e["title"].lower())[:40]
        if short_title not in seen:
            seen.add(short_title)
            unique.append(e)
    return unique


def fetch_anthropic_blog_posts(days: int = 3) -> list[dict]:
    """Fetch Anthropic blog posts mentioning Claude Code published within *days* days.

    Uses Next.js SSR JSON embedded in the page HTML — no external HTML parser
    dependency beyond what is already imported.  Returns a list of dicts with
    the same shape as fetch_rss_entries entries.
    """
    KST = timezone(timedelta(hours=9))
    cutoff = datetime.now(KST) - timedelta(days=days)
    entries: list[dict] = []

    for url in ANTHROPIC_BLOG_SOURCES:
        try:
            resp = requests.get(
                url,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10,
            )
            html = resp.text

            for match in _BLOG_PATTERN.finditer(html):
                published_raw, slug, summary, title = match.groups()

                # T2: skip null publishedOn
                if published_raw == "null":
                    continue

                # Strip surrounding escaped quotes from publishedOn value
                date_str = published_raw.strip('\\"')

                # Parse date — handle YYYY-MM-DD and ISO-8601 variants
                try:
                    if "T" in date_str or "t" in date_str:
                        # ISO-8601 with time component
                        parsed_date = datetime.fromisoformat(
                            date_str.replace("Z", "+00:00")
                        )
                        # Convert to KST for comparison
                        parsed_date = parsed_date.astimezone(KST)
                    else:
                        # Short form YYYY-MM-DD — treat as KST midnight
                        parsed_date = datetime.strptime(date_str, "%Y-%m-%d").replace(
                            tzinfo=KST
                        )
                except ValueError:
                    continue

                # T3: skip entries older than cutoff
                if parsed_date < cutoff:
                    continue

                title_clean = _unescape(title)
                summary_clean = _unescape(summary)

                # T4: keyword filter (case-insensitive) on title + summary
                combined = (title_clean + " " + summary_clean).lower()
                if not any(kw in combined for kw in ANTHROPIC_BLOG_KEYWORDS):
                    continue

                # Construct full URL: base_url (without trailing slash) + "/" + slug
                base = url.rstrip("/")
                full_url = base + "/" + slug

                entries.append({
                    "title": title_clean,
                    "link": full_url,
                    "summary": summary_clean,
                    "published": parsed_date.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "source": "Anthropic Blog",
                })

        except Exception as e:
            print(f"  Anthropic blog error ({url}): {e}")

    # T7: dedup by title similarity (same algo as collect_all_news)
    unique = _dedup_by_title(entries)

    # T8: cap at 10
    return unique[:10]


def fetch_rss_entries(feed_url: str, hours: int = 48) -> list[dict]:
    """Fetch RSS entries from the last N hours."""
    try:
        feed = feedparser.parse(feed_url)
        KST = timezone(timedelta(hours=9))
        cutoff = datetime.now(KST).replace(tzinfo=None) - timedelta(hours=hours)
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
        unique = _dedup_by_title(entries)
        all_news[category] = unique[:10]  # Max 10 per category
        print(f"  [{category}] {len(unique)} articles collected")

    # T6: Integrate Anthropic blog posts under "claude_code_blog" key
    blog_entries = fetch_anthropic_blog_posts()
    unique_blog = _dedup_by_title(blog_entries)
    all_news["claude_code_blog"] = unique_blog[:10]
    print(f"  [claude_code_blog] {len(unique_blog)} articles collected")

    return all_news


if __name__ == "__main__":
    news = collect_all_news()
    for cat, items in news.items():
        print(f"\n=== {cat} ({len(items)}) ===")
        for item in items[:3]:
            print(f"  - {item['title']}")
