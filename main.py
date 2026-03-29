#!/usr/bin/env python3
"""Morning Briefing Pipeline - Main entry point.

Collects IT/LLM news, generates a podcast-style briefing,
converts to audio, and delivers via Notion + Slack.
"""
import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# .env 파일이 있으면 로드 (로컬 테스트용)
load_dotenv()

from src.modules.news_collector import collect_all_news
from src.modules.script_generator import generate_briefing_markdown, generate_podcast_script
from src.modules.tts_generator import generate_audio
from src.modules.notifier import create_notion_page, send_slack_notification, upload_slack_audio


def run_pipeline():
    """Execute the full morning briefing pipeline."""
    today = datetime.now().strftime("%Y-%m-%d")
    weekday = ["월", "화", "수", "목", "금", "토", "일"][datetime.now().weekday()]
    title = f"IT/LLM 데일리 브리핑 - {today} ({weekday})"
    
    print(f"{'='*50}")
    print(f"  Morning Briefing Pipeline")
    print(f"  {title}")
    print(f"{'='*50}")

    # Step 1: Collect news
    print("\n[1/5] Collecting news from RSS feeds...")
    news_data = collect_all_news()
    total = sum(len(v) for v in news_data.values())
    print(f"  Total: {total} articles collected")

    if total == 0:
        print("  No news found. Exiting.")
        sys.exit(1)

    # Step 2: Generate markdown briefing via Claude
    print("\n[2/5] Generating briefing markdown...")
    briefing_md = generate_briefing_markdown(news_data)

    # Save markdown
    os.makedirs("output", exist_ok=True)
    md_path = f"output/briefing-{today}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(briefing_md)
    print(f"  Saved: {md_path}")

    # Step 3: Generate podcast script via Claude
    print("\n[3/5] Generating podcast script...")
    podcast_script = generate_podcast_script(briefing_md)

    script_path = f"output/script-{today}.txt"
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(podcast_script)
    print(f"  Saved: {script_path}")

    # Step 4: Generate audio via Google TTS
    print("\n[4/5] Generating audio...")
    audio_path = f"output/briefing-{today}.mp3"
    generate_audio(podcast_script, audio_path)

    # Upload audio to GitHub Release or get URL
    audio_url = os.environ.get("AUDIO_PUBLIC_URL", "")

    # Step 5: Deliver via Notion + Slack
    print("\n[5/5] Delivering to Notion and Slack...")
    notion_url = create_notion_page(title, briefing_md, audio_url)

    if notion_url:
        send_slack_notification(title, notion_url, audio_url)
        upload_slack_audio(audio_path, title)

    print(f"\n{'='*50}")
    print(f"  Pipeline completed successfully!")
    print(f"  Markdown: {md_path}")
    print(f"  Script:   {script_path}")
    print(f"  Audio:    {audio_path}")
    if notion_url:
        print(f"  Notion:   {notion_url}")
    print(f"{'='*50}")

    # Set GitHub Actions output
    gh_output = os.environ.get("GITHUB_OUTPUT", "")
    if gh_output:
        with open(gh_output, "a") as f:
            f.write(f"briefing_date={today}\n")
            f.write(f"audio_path={audio_path}\n")
            f.write(f"notion_url={notion_url}\n")


if __name__ == "__main__":
    run_pipeline()
