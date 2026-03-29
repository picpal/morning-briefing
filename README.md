# Morning Briefing

매일 아침 IT/LLM 뉴스를 자동으로 수집하여 팟캐스트 스타일 오디오 브리핑을 생성합니다.

## Pipeline

```
RSS 뉴스 수집 → Claude API 브리핑 생성 → 팟캐스트 스크립트 변환 → Google TTS 오디오 생성 → Notion 등록 + Slack 알림 + 오디오 업로드
```

## 카테고리

| 카테고리 | 내용 |
|---------|------|
| 🤖 Claude / Anthropic | Claude, Anthropic 관련 소식 |
| 🧠 LLM / AI 일반 | LLM, AI 에이전트, 프레임워크 |
| 💻 IT / 테크 | 주요 IT 뉴스 |
| 📈 주식 / 금융 | AI 관련 주식, 증시 동향 |
| 🔒 OWASP / 보안 | 사이버보안, 취약점 |
| 🛠️ Claude Code / Docs | Claude Code 업데이트 |
| 💡 오늘의 Pick | 가장 주목할 뉴스 심층 분석 |

## 설정

### GitHub Secrets 등록

| Secret 이름 | 설명 |
|------------|------|
| `ANTHROPIC_API_KEY` | Claude API 키 |
| `GOOGLE_TTS_KEY_JSON` | Google Cloud 서비스 계정 JSON (전체 내용, 한 줄) |
| `NOTION_API_KEY` | Notion Integration 토큰 |
| `NOTION_DATABASE_ID` | Notion 데이터베이스 ID |
| `SLACK_WEBHOOK_URL` | Slack Incoming Webhook URL |
| `SLACK_BOT_TOKEN` | Slack Bot User OAuth Token (`xoxb-...`) |
| `SLACK_CHANNEL_ID` | Slack 알림 채널 ID (`C0...`) |

### 스케줄

- 매일 오전 08:00 KST 자동 실행 (GitHub Actions cron)
- `workflow_dispatch`로 수동 실행 가능

## 로컬 실행

```bash
# 1. 가상환경 생성 및 의존성 설치
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. 환경변수 설정
cp .env.example .env
# .env 파일을 열어 각 값을 입력

# 3. 실행
python main.py
```

## 설정 가이드

### 1. Claude API 키

1. [Anthropic Console](https://console.anthropic.com/)에서 API 키 발급
2. `.env`에 `ANTHROPIC_API_KEY=sk-ant-...` 입력

### 2. Google Cloud TTS

1. [Google Cloud Console](https://console.cloud.google.com/)에서 프로젝트 생성
2. **Cloud Text-to-Speech API** 활성화
3. **서비스 계정** 생성 후 JSON 키 다운로드
4. `.env`에 JSON 전체를 **한 줄로** 입력:
   ```
   GOOGLE_TTS_KEY_JSON='{"type":"service_account","project_id":"...",...}'
   ```

### 3. Notion 연동

1. [Notion Integrations](https://www.notion.so/my-integrations)에서 Internal Integration 생성
2. Integration Secret(`ntn_...`) 복사 → `.env`에 `NOTION_API_KEY` 입력
3. Notion에서 데이터베이스 생성 (필수 속성: `Title`, `Date`, `Status`, `ArticleCount`)
4. 데이터베이스 페이지 → `...` → **연결 추가** → 생성한 Integration 선택
5. 데이터베이스 링크에서 ID 추출 → `.env`에 `NOTION_DATABASE_ID` 입력
   ```
   https://www.notion.so/workspace/[DATABASE_ID]?v=...
   ```

### 4. Slack 연동

**Webhook (텍스트 알림):**
1. [Slack API Apps](https://api.slack.com/apps)에서 앱 생성
2. **Incoming Webhooks** 활성화 후 Webhook URL 생성
3. `.env`에 `SLACK_WEBHOOK_URL` 입력

**Bot Token (오디오 파일 업로드):**
1. 같은 앱의 **OAuth & Permissions** 페이지에서 Bot Token Scopes 추가:
   - `files:write` — 파일 업로드
   - `chat:write` — 메시지 전송
2. 앱을 워크스페이스에 (재)설치
3. **Bot User OAuth Token** (`xoxb-...`) 복사 → `.env`에 `SLACK_BOT_TOKEN` 입력
4. Slack 채널에서 `/invite @앱이름`으로 Bot 초대
5. 채널 설정에서 **채널 ID** 복사 → `.env`에 `SLACK_CHANNEL_ID` 입력

## 프로젝트 구조

```
morning-briefing/
├── .github/workflows/
│   └── morning-briefing.yml    # GitHub Actions 워크플로우
├── src/
│   ├── config.py               # 환경변수 및 설정
│   ├── modules/
│   │   ├── news_collector.py   # RSS 뉴스 수집
│   │   ├── script_generator.py # Claude API 브리핑/스크립트 생성
│   │   ├── tts_generator.py    # Google Cloud TTS 오디오 생성
│   │   └── notifier.py         # Notion/Slack 전달
│   └── prompts/
│       └── briefing_prompt.py  # Claude API 프롬프트
├── output/                     # 생성된 브리핑 파일
├── main.py                     # 메인 파이프라인
├── requirements.txt
└── README.md
```

## 음성 설정

- **엔진**: Google Cloud TTS - Chirp 3: HD
- **음성**: ko-KR-Chirp3-HD-Achernar
- **스타일**: 친근한 팟캐스트 어투 (~이에요/~했어요)
- **발음 보정**: 영문 약어/숫자를 한글 발음으로 자동 변환
