"""Generate audio from podcast script using Google Cloud TTS."""
import json
import re
import base64
import time
import requests
import jwt
from src.config import GOOGLE_TTS_KEY_JSON, TTS_VOICE, TTS_API_URL


def _text_to_ssml(text: str) -> str:
    """Convert plain text to SSML with natural pauses at commas and sentences."""
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")

    paragraphs = text.split("\n\n")
    ssml_parts = []
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        sentences = re.split(r'(?<=[.!?])\s+', para)
        s_tags = []
        for s in sentences:
            s = s.strip()
            if not s:
                continue
            s = re.sub(r',\s*', ', <break time="200ms"/>', s)
            s_tags.append('<s>' + s + '</s><break time="300ms"/>')
        ssml_parts.append('<p>' + ''.join(s_tags) + '</p>')

    body = '<break time="600ms"/>'.join(ssml_parts)
    return '<speak>' + body + '</speak>'


def _get_access_token() -> str:
    """Generate self-signed JWT for Google Cloud TTS API."""
    key_data = json.loads(GOOGLE_TTS_KEY_JSON)
    now = int(time.time())
    payload = {
        "iss": key_data["client_email"],
        "sub": key_data["client_email"],
        "aud": "https://texttospeech.googleapis.com/",
        "iat": now,
        "exp": now + 3600,
    }
    token = jwt.encode(payload, key_data["private_key"], algorithm="RS256")
    return token


def _synthesize_chunk(text: str, token: str) -> bytes:
    """Synthesize a single text chunk to audio bytes."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    ssml_text = _text_to_ssml(text)
    payload = {
        "input": {"ssml": ssml_text},
        "voice": {
            "languageCode": "ko-KR",
            "name": TTS_VOICE,
        },
        "audioConfig": {
            "audioEncoding": "MP3",
            "speakingRate": 0.95,
        },
    }
    resp = requests.post(TTS_API_URL, headers=headers, json=payload, timeout=120)
    if resp.status_code != 200:
        raise RuntimeError(f"TTS API error {resp.status_code}: {resp.text[:200]}")
    audio_b64 = resp.json()["audioContent"]
    return base64.b64decode(audio_b64)


def generate_audio(script_text: str, output_path: str) -> str:
    """Generate MP3 audio from podcast script text.

    Splits text into chunks if needed (Chirp 3: HD has processing limits).
    Returns the output file path.
    """
    token = _get_access_token()

    # Split into chunks of ~800 chars (safe for Chirp 3: HD timeout)
    max_chars = 800
    chunks = []
    current = ""
    for line in script_text.split("\n"):
        if len(current) + len(line) + 1 > max_chars:
            if current:
                chunks.append(current)
            current = line
        else:
            current = current + "\n" + line if current else line
    if current:
        chunks.append(current)

    print(f"  TTS: {len(script_text)} chars, {len(chunks)} chunk(s)")

    audio_parts = []
    for i, chunk in enumerate(chunks):
        print(f"  Chunk {i + 1}/{len(chunks)} ({len(chunk)} chars)...")
        audio_bytes = _synthesize_chunk(chunk, token)
        audio_parts.append(audio_bytes)

    # Combine all chunks
    with open(output_path, "wb") as f:
        for part in audio_parts:
            f.write(part)

    size_kb = len(b"".join(audio_parts)) / 1024
    print(f"  Audio saved: {output_path} ({size_kb:.1f} KB)")
    return output_path


if __name__ == "__main__":
    test_text = "안녕하세요, 테스트 브리핑입니다."
    generate_audio(test_text, "/tmp/test_briefing.mp3")
