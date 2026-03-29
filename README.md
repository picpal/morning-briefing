# Morning Briefing

매일 아침 IT/LLM 뉴스를 자동으로 수집하여 팟캐스트 스타일 오디오 브리핑을 생성합니다.

## Pipeline

```
RSS 뉴스 수집 → Claude API 브리핑 생성 → 팟캐스트 스크립트 변환 → Google TTS 오디오 생성 → Notion 등록 → Slack 알림
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
| `GOOGLE_TTS_KEY_JSON` | Google Cloud 서비스 계정 JSON (전체 내용) |
| `NOTION_API_KEY` | Notion Integration 토큰 |
| `SLACK_WEBHOOK_URL` | Slack Incoming Webhook URL |
| `NOTION_DATABASE_ID` | Notion 데이터베이스 ID |

### 스케줄

- 매일 오전 08:00 KST 자동 실행 (GitHub Actions cron)
- `workflow_dispatch`로 수동 실행 가능

## 로컬 실행

```bash
pip install -r requirements.txt

export ANTHROPIC_API_KEY="your-key"
export GOOGLE_TTS_KEY_JSON='{"type":"service_account",...}'
export NOTION_API_KEY="your-key"
export SLACK_WEBHOOK_URL="https://hooks.slack.com/..."

python main.py
```

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
