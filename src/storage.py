"""
생성된 블로그 글을 posts/ 폴더에 마크다운 파일로 저장합니다.

파일명 규칙: posts/YYYY-MM-DD-제목슬러그.md
"""

import os
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from . import config

KST = ZoneInfo("Asia/Seoul")


def _slugify(title: str) -> str:
    """파일명으로 쓸 수 있게 제목을 정리합니다. 한글은 유지하고 특수문자만 제거."""
    cleaned = re.sub(r"[^\w가-힣]+", "-", title).strip("-")
    return cleaned[:40] if cleaned else "untitled"


def build_markdown(category: str, topic: str, post: dict, image_url: str) -> str:
    """프론트매터 + 본문으로 구성된 마크다운 문자열을 생성합니다."""
    now = datetime.now(KST)
    tags_line = ", ".join(post["tags"])

    frontmatter = (
        "---\n"
        f"title: {post['title']}\n"
        f"category: {category}\n"
        f"topic: {topic}\n"
        f"tags: [{tags_line}]\n"
        f"date: {now.strftime('%Y-%m-%d %H:%M')} KST\n"
        f"status: draft\n"
        "---\n\n"
    )

    image_block = f"![대표 이미지]({image_url})\n\n"

    return frontmatter + f"# {post['title']}\n\n" + image_block + post["body_markdown"] + "\n"


def save_post(category: str, topic: str, post: dict, image_url: str, repo_root: str) -> str:
    """
    마크다운 파일을 posts/ 폴더에 저장하고, 저장된 파일의 상대 경로를 반환합니다.

    Args:
        repo_root: 리포지토리 루트의 절대 경로 (이 경로 기준으로 posts/ 하위에 저장)

    Returns:
        리포지토리 루트 기준 상대 경로 (예: "posts/2026-06-30-아보카도.md")
    """
    now = datetime.now(KST)
    date_str = now.strftime("%Y-%m-%d")
    slug = _slugify(post["title"])
    filename = f"{date_str}-{slug}.md"

    posts_dir = os.path.join(repo_root, config.POSTS_DIR)
    os.makedirs(posts_dir, exist_ok=True)

    full_path = os.path.join(posts_dir, filename)
    markdown = build_markdown(category, topic, post, image_url)

    with open(full_path, "w", encoding="utf-8") as f:
        f.write(markdown)

    return f"{config.POSTS_DIR}/{filename}"
