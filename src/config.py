"""
블로그 자동 생성 봇 설정.

- 카테고리/주제 풀: topics.py에서 사용
- Gemini 모델: insight 봇과 동일한 무료 티어 모델 사용
- GitHub repo 정보: 카카오 메시지에 넣을 글 링크 생성용
"""

# 카테고리 (티스토리 실제 카테고리명과 일치)
CATEGORIES = ["알고 먹자", "전쟁이야기"]

# 사용할 Gemini 모델 — 무료 티어 한도 기준 (k-popcorn-bot과 동일 정책)
# - gemini-2.5-flash-lite: RPD 1,000, RPM 15 (하루 1회 발송엔 충분)
GEMINI_MODEL = "gemini-2.5-flash-lite"

# GitHub 리포지토리 정보 (카카오 메시지에 들어갈 blob 링크 생성용)
GITHUB_OWNER = "JM-7"
GITHUB_REPO = "k-popcorn-blog-bot"
GITHUB_BRANCH = "main"

# 카카오 '나에게 보내기' 텍스트 템플릿 글자수 제한
KAKAO_TEXT_MAX_LEN = 200

# posts/ 디렉토리 (리포지토리 루트 기준 상대 경로)
POSTS_DIR = "posts"
