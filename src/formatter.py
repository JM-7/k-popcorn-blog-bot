"""
카카오톡 발송용 메시지를 구성합니다.

요약 + GitHub blob 링크 방식 (전체 본문 X) — 사용자 결정에 따름.
"""

from . import config


def build_github_link(relative_path: str) -> str:
    """posts/2026-06-30-제목.md 같은 상대 경로를 GitHub blob URL로 변환합니다."""
    return (
        f"https://github.com/{config.GITHUB_OWNER}/{config.GITHUB_REPO}"
        f"/blob/{config.GITHUB_BRANCH}/{relative_path}"
    )


def build_kakao_text(category: str, post: dict) -> str:
    """
    카카오톡 텍스트 템플릿 본문을 만듭니다.
    링크는 send_text()의 link_url 인자로 별도 전달하므로 본문에는 텍스트만 포함합니다.
    """
    title = post["title"]
    summary = post["summary"]

    return f"[{category}] 새 글 초안 생성됨\n\n{title}\n\n{summary}"
