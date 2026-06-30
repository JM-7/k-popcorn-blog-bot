# 강냉이 블로그 초안 자동 생성 봇

매일 1회, "알고 먹자"(식품/영양) 또는 "전쟁이야기"(역사) 카테고리 중
하나를 랜덤으로 골라 Gemini AI로 블로그 글 초안을 생성하고, 결과를 이
리포지토리의 `posts/` 폴더에 저장한 뒤 카카오톡 "나에게 보내기"로
요약과 링크를 알려줍니다.

## ⚠️ 중요: 완전 자동 발행이 아닙니다

티스토리 Open API는 2024년 서비스 종료되었고, 현재는 신규 발급도
막혀 있습니다. 또한 2026년부터 로그인 시 캡차가 강화되어 브라우저
자동화(Selenium 등)로 직접 글을 발행하는 방식도 신뢰하기 어렵습니다.

그래서 이 봇은 **반자동** 방식으로 동작합니다.

1. 봇이 글 초안을 생성해서 GitHub에 저장
2. 카카오톡으로 "이런 글 초안이 생성됐어요" 알림 + 요약 + 링크 전송
3. 사용자가 GitHub에서 전체 글을 확인하고, 마음에 들면 직접 티스토리
   글쓰기 페이지에 복사+붙여넣기로 발행

## 동작 흐름

```
GitHub Actions (매일 KST 09:00)
  ↓
1. 카테고리 랜덤 선택 (알고 먹자 / 전쟁이야기)
2. 카테고리 내 주제 랜덤 선택
3. Gemini API로 글 생성 (제목/본문/태그/요약, JSON 응답)
4. Picsum에서 대표 이미지 URL 구성 (키 불필요)
5. posts/YYYY-MM-DD-제목.md 로 저장
6. git commit & push
7. (push 성공 시에만) 카카오톡 발송 — 요약 + GitHub 링크
```

## ⚠️ 카카오 토큰 공유 관련 주의사항

이 리포지토리는 `k-popcorn-bot`(주식 브리핑 봇)과 **같은 카카오 앱 /
같은 Refresh Token**을 사용합니다. 두 리포지토리가 각자 별도로 토큰을
갱신하기 때문에, 만약 Kakao 서버가 새 Refresh Token을 발급하면 한쪽
GitHub Secret만 최신값으로 업데이트되고 다른 쪽은 구버전을 들고 있게
되어 다음 실행이 실패할 수 있습니다.

**워크플로 로그에 `[WARNING] 새 Refresh Token이 발급되었습니다`가
보이면, 이 리포지토리와 `k-popcorn-bot` 양쪽의 `KAKAO_REFRESH_TOKEN`
Secret을 모두 같은 새 값으로 갱신하세요.**

## 셋업 가이드

### 1. GitHub Secrets 등록

리포지토리 > Settings > Secrets and variables > Actions > New repository secret

| Name | Value |
|---|---|
| `GEMINI_API_KEY` | Google AI Studio에서 발급 (k-popcorn-bot과 같은 키 재사용 가능) |
| `KAKAO_REST_API_KEY` | k-popcorn-bot과 동일한 값 |
| `KAKAO_REFRESH_TOKEN` | k-popcorn-bot과 동일한 값 |

이미 `k-popcorn-bot`에 등록된 값을 그대로 복사해서 쓰면 됩니다. 처음부터
새로 발급받고 싶다면 `scripts/get_kakao_token.py`를 참고하세요 (단, 이
경우 두 리포지토리의 토큰이 어긋나니 양쪽 다 새 값으로 갱신해야 합니다).

### 2. 로컬 테스트 (선택)

```bash
pip install -r requirements.txt
export GEMINI_API_KEY=...

# 글 생성 + posts/ 저장만 (카카오 발송 X)
python -m src.main generate --dry-run
```

### 3. 자동 실행

GitHub에 push하면 매일 KST 09:00에 자동 실행됩니다.

수동 실행: 리포지토리 > Actions 탭 > "Generate Blog Post Draft" > "Run workflow"

## 주제 추가/수정

`src/topics.py`의 `FOOD_TOPICS`, `WAR_TOPICS` 리스트에 항목을
추가/삭제하면 됩니다. 기존 강냉이 블로그(k-popcorn.tistory.com)의
89개 글과 주제가 겹쳐도 무방합니다 (의도된 정책).

## 이미지 관련 한계

현재 [Picsum Photos](https://picsum.photos)를 사용해 키 없이 이미지
URL을 구성합니다. 다만 이 서비스는 주제와 무관한 랜덤 풍경/사물
사진을 제공하므로, "글 주제에 맞는" 이미지는 아닙니다.

더 정확한 주제 맞춤 이미지가 필요하면:
- Unsplash API 키를 발급받아 `src/image.py`를 검색 기반으로 교체
- 또는 AI 이미지 생성 API 연동

## 디렉토리 구조

```
k-popcorn-blog-bot/
├── .github/workflows/
│   └── generate_post.yml   # GitHub Actions 스케줄
├── scripts/
│   └── get_kakao_token.py  # (참고용) OAuth 헬퍼, k-popcorn-bot에서 복사
├── src/
│   ├── __init__.py
│   ├── config.py           # 카테고리, 모델, repo 정보
│   ├── topics.py           # 카테고리별 주제 풀 + 랜덤 선택
│   ├── writer.py           # Gemini 글 생성 (모델 폴백 포함)
│   ├── image.py            # Picsum 이미지 URL 구성
│   ├── storage.py          # posts/ 폴더에 마크다운 저장
│   ├── formatter.py        # 카카오 메시지 포맷
│   ├── kakao.py            # 카카오 API (토큰 갱신 + 발송)
│   └── main.py             # 파이프라인 진입점 (generate / notify)
├── posts/                  # 생성된 글이 쌓이는 폴더
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## 비용

- GitHub Actions: 퍼블릭 레포 무제한 / 프라이빗 월 2,000분 (사용량 ≈ 월 5분 미만)
- Gemini API: 무료 티어 (gemini-2.5-flash-lite, 1,000 RPD) — 하루 1회 호출로 충분
- Kakao Open API: 무료

## 트러블슈팅

**"refresh token is invalid" 에러** → Refresh Token이 만료됐거나
다른 리포지토리에서 먼저 갱신되어 구버전을 들고 있는 상태일 수
있습니다. `k-popcorn-bot`의 최신 워크플로 로그에서 새 토큰이 출력된
적이 있는지 확인하고, 있다면 그 값으로 양쪽 Secret을 갱신하세요.
없다면 `scripts/get_kakao_token.py`를 재실행해 새로 발급받으세요.

**Gemini 응답이 JSON 파싱 실패** → 드물게 모델이 코드블록(` ```json `)을
섞어 응답할 수 있습니다. `src/writer.py`의 `_parse_response`가 이를
방어적으로 처리하지만, 계속 실패하면 워크플로 로그의 원본 응답을
확인하세요.

**카카오 메시지가 도착하지 않음** → Kakao 앱의 [동의항목]에 '카카오톡
메시지 전송'이 켜져 있는지 확인하세요.
