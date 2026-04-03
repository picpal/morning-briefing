"""Send briefing to Notion and Slack."""
import json
import re
import requests
from datetime import datetime, timezone, timedelta
from src.config import NOTION_API_KEY, NOTION_DATABASE_ID, SLACK_WEBHOOK_URL, SLACK_BOT_TOKEN, SLACK_CHANNEL_ID


def _parse_markdown_links(text: str) -> list:
    """Parse markdown links [title](url) into Notion rich_text segments."""
    segments = []
    pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    last_end = 0
    for match in re.finditer(pattern, text):
        # Text before the link
        before = text[last_end:match.start()]
        if before:
            segments.append({"type": "text", "text": {"content": before}})
        # The link itself
        link_title = match.group(1)
        link_url = match.group(2)
        segments.append({
            "type": "text",
            "text": {"content": link_title, "link": {"url": link_url}},
        })
        last_end = match.end()
    # Remaining text after last link
    remaining = text[last_end:]
    if remaining:
        segments.append({"type": "text", "text": {"content": remaining}})
    # If no links found, return simple text
    if not segments:
        segments.append({"type": "text", "text": {"content": text}})
    return segments


def create_notion_page(title: str, markdown_content: str, audio_url: str = None) -> str:
    """Create a Notion page in the Morning Briefing database.
    
    Returns the page URL.
    """
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }

    # Build page content blocks from markdown
    blocks = []
    for line in markdown_content.split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("## "):
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": _parse_markdown_links(line[3:])
                },
            })
        elif line.startswith("### "):
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": _parse_markdown_links(line[4:])
                },
            })
        elif line.startswith("- "):
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": _parse_markdown_links(line[2:])
                },
            })
        elif line.startswith("> "):
            blocks.append({
                "object": "block",
                "type": "quote",
                "quote": {
                    "rich_text": _parse_markdown_links(line[2:])
                },
            })
        elif line.startswith("---"):
            blocks.append({"object": "block", "type": "divider", "divider": {}})
        else:
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": _parse_markdown_links(line)
                },
            })

    # Add audio link block if available
    if audio_url:
        blocks.append({"object": "block", "type": "divider", "divider": {}})
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {"type": "text", "text": {"content": "🎧 오디오 브리핑: "}},
                    {"type": "text", "text": {"content": "듣기", "link": {"url": audio_url}}},
                ]
            },
        })

    KST = timezone(timedelta(hours=9))
    today = datetime.now(KST).strftime("%Y-%m-%d")

    # Count articles from markdown content
    article_count = markdown_content.count("###") if markdown_content else 0

    payload = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {
            "Title": {
                "title": [{"text": {"content": title}}]
            },
            "Date": {
                "date": {"start": today}
            },
            "Status": {
                "status": {"name": "완료"}
            },
            "ArticleCount": {
                "number": article_count
            },
        },
        "children": blocks[:100],  # Notion limit
    }

    resp = requests.post(
        "https://api.notion.com/v1/pages",
        headers=headers,
        json=payload,
        timeout=30,
    )
    if resp.status_code != 200:
        print(f"  Notion error {resp.status_code}: {resp.text[:200]}")
        return ""

    page_url = resp.json().get("url", "")
    print(f"  Notion page created: {page_url}")
    return page_url


def upload_slack_audio(audio_path: str, title: str) -> bool:
    """Upload audio file to Slack channel via Bot Token."""
    if not SLACK_BOT_TOKEN or not SLACK_CHANNEL_ID:
        print("  Slack bot token or channel ID not configured, skipping audio upload")
        return False

    headers = {"Authorization": f"Bearer {SLACK_BOT_TOKEN}"}

    # Step 1: Get upload URL
    import os
    file_size = os.path.getsize(audio_path)
    filename = os.path.basename(audio_path)

    resp = requests.get(
        "https://slack.com/api/files.getUploadURLExternal",
        headers=headers,
        params={"filename": filename, "length": file_size},
        timeout=10,
    )
    data = resp.json()
    if not data.get("ok"):
        print(f"  Slack upload URL error: {data.get('error', 'unknown')}")
        return False

    upload_url = data["upload_url"]
    file_id = data["file_id"]

    # Step 2: Upload file
    with open(audio_path, "rb") as f:
        resp = requests.post(upload_url, files={"file": f}, timeout=60)
    if resp.status_code != 200:
        print(f"  Slack file upload error: {resp.status_code}")
        return False

    # Step 3: Complete upload
    resp = requests.post(
        "https://slack.com/api/files.completeUploadExternal",
        headers={**headers, "Content-Type": "application/json"},
        json={
            "files": [{"id": file_id, "title": title}],
            "channel_id": SLACK_CHANNEL_ID,
            "initial_comment": f"🎧 *{title}* - 오디오 브리핑",
        },
        timeout=10,
    )
    data = resp.json()
    if data.get("ok"):
        print("  Slack audio uploaded")
        return True
    else:
        print(f"  Slack complete upload error: {data.get('error', 'unknown')}")
        return False


def send_slack_notification(briefing_title: str, notion_url: str, audio_url: str = None):
    """Send Slack notification with briefing link."""
    if not SLACK_WEBHOOK_URL:
        print("  Slack webhook not configured, skipping")
        return

    text = f"📋 *{briefing_title}*\n<{notion_url}|Notion에서 보기>"
    if audio_url:
        text += f"\n🎧 <{audio_url}|오디오 브리핑 듣기>"

    payload = {"text": text}
    resp = requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=10)
    if resp.status_code == 200:
        print("  Slack notification sent")
    else:
        print(f"  Slack error {resp.status_code}: {resp.text[:100]}")


if __name__ == "__main__":
    print("Notifier module loaded successfully")
