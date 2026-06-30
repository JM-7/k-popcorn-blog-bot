"""
파이프라인 진입점.

두 단계로 분리되어 있습니다 (커밋 실패 시 잘못된 카카오 알림이 가지 않도록):
  generate 단계: 글 생성 + posts/ 저장 (git commit은 워크플로 yml이 담당)
  notify 단계:   commit/push 성공 후에만 호출, 카카오 발송

generate 단계는 다음 정보를 GITHUB_OUTPUT 파일에 기록해 notify 단계로 전달합니다:
  category, title, summary, relative_path

실행:
  python -m src.main generate              # 글 생성 + 저장만
  python -m src.main generate --dry-run    # 저장은 하되 GITHUB_OUTPUT 기록 생략, 콘솔 출력만
  python -m src.main notify                # GITHUB_OUTPUT에 저장된 정보로 카카오 발송
"""

import os
import sys

from . import formatter
from . import image
from . import storage
from . import topics
from . import writer
from .kakao import KakaoClient


def _write_github_output(values: dict) -> None:
    """GitHub Actions의 GITHUB_OUTPUT 파일에 key=value 형태로 기록합니다."""
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        return
    with open(output_path, "a", encoding="utf-8") as f:
        for key, value in values.items():
            # 멀티라인 값을 안전하게 기록하기 위해 구분자(delimiter) 방식 사용
            f.write(f"{key}<<__EOF__\n{value}\n__EOF__\n")


def generate(dry_run: bool = False, repo_root: str = ".") -> int:
    print("[1/4] 카테고리/주제 선택 중...")
    category, topic = topics.pick_category_and_topic()
    print(f"      카테고리: {category} / 주제: {topic}")

    print("[2/4] Gemini로 글 생성 중...")
    post = writer.generate_post(category, topic)
    print(f"      제목: {post['title']}")
    print(f"      본문 길이: {len(post['body_markdown'])}자")

    print("[3/4] 이미지 URL 구성 중...")
    image_url = image.get_image_url(topic)
    print(f"      {image_url}")

    print("[4/4] posts/ 폴더에 저장 중...")
    relative_path = storage.save_post(category, topic, post, image_url, repo_root)
    print(f"      저장 완료: {relative_path}")

    print()
    print("--- 카카오 발송 예정 메시지 미리보기 ---")
    print(formatter.build_kakao_text(category, post))
    print(f"링크: {formatter.build_github_link(relative_path)}")

    if not dry_run:
        _write_github_output(
            {
                "category": category,
                "title": post["title"],
                "summary": post["summary"],
                "relative_path": relative_path,
            }
        )

    return 0


def notify() -> int:
    """generate 단계에서 GITHUB_OUTPUT에 기록한 정보로 카카오 발송."""
    category = os.environ["POST_CATEGORY"]
    title = os.environ["POST_TITLE"]
    summary = os.environ["POST_SUMMARY"]
    relative_path = os.environ["POST_RELATIVE_PATH"]

    post = {"title": title, "summary": summary}
    text = formatter.build_kakao_text(category, post)
    link = formatter.build_github_link(relative_path)

    print("카카오톡 발송 중...")
    client = KakaoClient()
    client.refresh()
    client.send_text(text, link_url=link)
    print("완료.")
    return 0


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--dry-run"]
    command = args[0] if args else "generate"

    if command == "generate":
        return generate(dry_run=dry_run)
    elif command == "notify":
        return notify()
    else:
        print(f"알 수 없는 명령: {command} (generate 또는 notify)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
