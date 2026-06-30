"""
카카오 Open API: 토큰 갱신 + '나에게 보내기' 메시지 발송.

k-popcorn-bot(주식 브리핑)의 kakao.py와 로직은 동일합니다.
단, 이 리포지토리는 사용자 결정에 따라 같은 카카오 앱/Refresh Token을
공유합니다 — 두 리포지토리가 동시에 토큰을 갱신하면 한쪽 GitHub Secret이
구버전 Refresh Token을 들고 있게 될 수 있습니다.

대응: Kakao가 새 Refresh Token을 발급하면 워크플로 로그에 경고를 출력합니다.
이 경고가 뜨면 *양쪽* 리포지토리의 KAKAO_REFRESH_TOKEN을 모두 새 값으로
갱신해야 합니다 (둘 중 하나만 갱신하면 다른 한쪽이 다음 실행에서 실패합니다).
"""

import json
import os
from typing import Optional

import requests

from . import config

TOKEN_URL = "https://kauth.kakao.com/oauth/token"
MEMO_URL = "https://kapi.kakao.com/v2/api/talk/memo/default/send"


class KakaoClient:
    def __init__(
        self,
        rest_api_key: Optional[str] = None,
        refresh_token: Optional[str] = None,
    ):
        self.rest_api_key = rest_api_key or os.environ["KAKAO_REST_API_KEY"]
        self.refresh_token = refresh_token or os.environ["KAKAO_REFRESH_TOKEN"]
        self.access_token: Optional[str] = None

    def refresh(self) -> None:
        """Refresh Token으로 새 Access Token을 발급받습니다."""
        response = requests.post(
            TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "client_id": self.rest_api_key,
                "refresh_token": self.refresh_token,
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        self.access_token = data["access_token"]

        if "refresh_token" in data:
            new_refresh = data["refresh_token"]
            print("=" * 60)
            print("[WARNING] 새 Refresh Token이 발급되었습니다.")
            print("이 토큰은 k-popcorn-bot과 공유 중입니다.")
            print("아래 두 리포지토리의 KAKAO_REFRESH_TOKEN을 *모두* 갱신하세요:")
            print("  1. k-popcorn-bot (주식 브리핑)")
            print("  2. k-popcorn-blog-bot (블로그 초안, 이 리포지토리)")
            print("새 값:")
            print(new_refresh)
            print("=" * 60)

    def send_text(self, text: str, link_url: str) -> dict:
        """
        '나에게 보내기'로 텍스트 메시지를 발송합니다.
        200자를 초과하면 자동으로 잘립니다.
        """
        if self.access_token is None:
            raise RuntimeError("먼저 refresh()를 호출하세요.")

        if len(text) > config.KAKAO_TEXT_MAX_LEN:
            text = text[: config.KAKAO_TEXT_MAX_LEN - 1] + "…"

        template = {
            "object_type": "text",
            "text": text,
            "link": {
                "web_url": link_url,
                "mobile_web_url": link_url,
            },
            "button_title": "전체 글 보기",
        }

        response = requests.post(
            MEMO_URL,
            headers={"Authorization": f"Bearer {self.access_token}"},
            data={"template_object": json.dumps(template, ensure_ascii=False)},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
