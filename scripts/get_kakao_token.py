"""
최초 1회만 실행: 카카오 OAuth Refresh Token 발급.

사전 준비:
  1. https://developers.kakao.com 에서 앱 생성
  2. [내 애플리케이션] > [앱 설정] > [플랫폼] > Web 플랫폼 추가
     - 사이트 도메인: https://example.com (임의 값 가능)
  3. [카카오 로그인] 활성화 + Redirect URI 등록
     - https://example.com/oauth (임의 값 가능)
  4. [동의항목] > '카카오톡 메시지 전송' 동의 항목 활성화
  5. [앱 키]에서 REST API 키 확인

실행:
  python scripts/get_kakao_token.py
"""

import os
import sys
from urllib.parse import urlencode

import requests

REDIRECT_URI = "https://example.com/oauth"  # 콘솔에 등록한 값과 동일해야 함


def main() -> int:
    rest_api_key = os.environ.get("KAKAO_REST_API_KEY") or input(
        "REST API 키를 입력하세요: "
    ).strip()

    if not rest_api_key:
        print("REST API 키가 필요합니다.")
        return 1

    # Step 1: 인증 코드 받기
    params = {
        "client_id": rest_api_key,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "talk_message",
    }
    auth_url = f"https://kauth.kakao.com/oauth/authorize?{urlencode(params)}"

    print()
    print("=" * 70)
    print("1단계: 아래 URL을 브라우저에서 여세요.")
    print()
    print(auth_url)
    print()
    print("2단계: 카카오 로그인 후 동의하면 example.com/oauth?code=XXXX 로")
    print("       리디렉트됩니다. 페이지가 안 열려도 OK입니다.")
    print("       주소창의 'code=' 다음 값(긴 문자열)을 복사하세요.")
    print("=" * 70)
    print()

    auth_code = input("인증 코드를 붙여넣으세요: ").strip()
    if not auth_code:
        print("코드가 입력되지 않았습니다.")
        return 1

    # Step 2: 코드를 토큰으로 교환
    response = requests.post(
        "https://kauth.kakao.com/oauth/token",
        data={
            "grant_type": "authorization_code",
            "client_id": rest_api_key,
            "redirect_uri": REDIRECT_URI,
            "code": auth_code,
        },
        timeout=10,
    )

    if response.status_code != 200:
        print(f"\n토큰 발급 실패: {response.status_code}")
        print(response.text)
        return 1

    tokens = response.json()

    print()
    print("=" * 70)
    print("발급 성공! 아래 값을 GitHub Secrets에 등록하세요.")
    print()
    print(f"KAKAO_REST_API_KEY  = {rest_api_key}")
    print(f"KAKAO_REFRESH_TOKEN = {tokens['refresh_token']}")
    print()
    print(f"(참고: Access Token = {tokens['access_token'][:20]}... "
          f"유효기간 {tokens.get('expires_in')}초)")
    print(f"(참고: Refresh Token 유효기간 {tokens.get('refresh_token_expires_in')}초"
          f" ≈ {tokens.get('refresh_token_expires_in', 0) // 86400}일)")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
