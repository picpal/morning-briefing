# Morning Briefing Project

## 프로젝트 개요
매일 아침 IT/LLM 뉴스를 자동으로 수집하여 팟캐스트 스타일 오디오 브리핑을 생성하는 파이프라인.

## 파이프라인 흐름
```
[1] RSS 뉴스 수집 → [2] Claude API 마크다운 브리핑 생성 → [3] Claude API 팟캐스트 스크립트 변환 → [4] Google TTS 오디오 생성 → [5] Notion 등록 + Slack 알림
```

## 프로젝트 구조
```
morning-briefing/
├── .github/workflows/
│   └── morning-briefing.yml    # GitHub Actions (매일 08:00 KST)
├── src/
│   ├── config.py               # 환경변수, API 키, 설정값
│   ├── modules/
│   │   ├── news_collector.py   # Google News RSS 피드 수집 (6개 카테고리)
│   │   ├── script_generator.py # Claude API 호출 (브리핑 + 스크립트)
│   │   ├── tts_generator.py    # Google Cloud TTS (Chirp 3: HD)
│   │   └── notifier.py         # Notion 페이지 생성 + Slack 알림
│   └── prompts/
│       └── briefing_prompt.py  # 4개 프롬프트 (브리핑 system/user, 팟캐스트 system/user)
├── output/                     # 생성 결과물 (briefing-날짜.md, script-날짜.txt, briefing-날짜.mp3)
├── main.py                     # 엔트리포인트 - run_pipeline()
├── .env                        # 로컬 환경변수 (git 미포함)
├── .env.example                # 환경변수 템플릿
└── requirements.txt
```

## 브리핑 카테고리 (7개)
1. 🤖 Claude / Anthropic
2. 🧠 LLM / AI 일반
3. 💻 IT / 테크
4. 📈 주식 / 금융
5. 🔒 OWASP / 보안
6. 🛠️ Claude Code / Docs 업데이트
7. 💡 오늘의 Pick (가장 임팩트 있는 뉴스 1개 심층 분석)

## 환경변수 (GitHub Secrets)
| 변수명 | 용도 |
|--------|------|
| `ANTHROPIC_API_KEY` | Claude API 호출 |
| `GOOGLE_TTS_KEY_JSON` | Google Cloud 서비스 계정 JSON (전체 내용) |
| `NOTION_API_KEY` | Notion Integration 토큰 |
| `NOTION_DATABASE_ID` | `32e9789c-7eb1-8015-ac54-000bb7954c05` |
| `SLACK_WEBHOOK_URL` | Slack Incoming Webhook |

## TTS 설정
- **엔진**: Google Cloud TTS v1beta1 API
- **음성**: `ko-KR-Chirp3-HD-Achernar` (Chirp 3: HD, 최고 품질)
- **인증**: 서비스 계정 JSON → self-signed JWT → Bearer token
- **청킹**: 800자 단위로 분할 후 MP3 결합 (Chirp 3: HD 타임아웃 방지)

## 팟캐스트 스크립트 규칙
- 친근한 ~이에요/~했어요 체
- 불필요한 추임새 사용 금지 (자, 이제, 먼저, 다음은, 넘어갈게요 등)
- 영문 기사 제목/URL 포함 금지, 한국어 요약만
- 각 뉴스에 맥락 코멘트 추가
- 오프닝: 인사 + 날짜 + 키워드 3개
- 마무리: 핵심 3가지 리캡 + 인사

## TTS 발음 변환 규칙
스크립트 생성 시 Claude 프롬프트에 포함된 규칙:
- 영문 고유명사 → 한글 발음 (Anthropic→앤쓰로픽, NVIDIA→엔비디아)
- 영문 약어 → 한글 (AI→에이아이, LLM→엘엘엠, API→에이피아이)
- 숫자 콤마 → 한글 읽기 (5,349→오천삼백사십구)
- 달러 표기 → 한글 ($171→백칠십일 달러)
- 특수 표현 (Top 10→탑 텐, S&P 500→에스앤피 파이브헌드레드)

## 비용
- **Claude API**: 브리핑 생성 + 스크립트 변환 (sonnet 기준 약 $0.01/일)
- **Google TTS**: 일 약 1,700자 × 30일 = 약 51,000자/월 (무료 한도 100만자의 5%)
- **총 월 비용**: 사실상 무료 (Claude API 최소 비용만 발생)

## 실행 방법
```bash
# 로컬 테스트
cp .env.example .env  # 환경변수 설정
pip install -r requirements.txt
python main.py

# GitHub Actions 수동 실행
# repo → Actions → Morning Briefing → Run workflow
```

## 주의사항
- `.env` 파일은 절대 커밋하지 말 것 (.gitignore에 포함됨)
- `GOOGLE_TTS_KEY_JSON`은 JSON 전체를 한 줄로 넣어야 함
- Chirp 3: HD는 긴 텍스트 처리 시 타임아웃 가능 → 800자 청킹 적용됨
- RSS 피드가 비어있으면 파이프라인이 종료됨 (exit 1)
