"""
키 없이 사용 가능한 무료 이미지 URL을 구성합니다.

선택: Picsum Photos (https://picsum.photos)
- API 키 불필요, 안정적으로 운영 중
- 단점: 주제와 무관한 랜덤 사진 (실사/풍경 위주, "주제 맞춤" 이미지는 아님)

대안으로 검토했던 source.unsplash.com은 Unsplash 측에서 단계적 종료를 선언한
서비스라 제외했습니다. 추후 품질을 높이고 싶다면 Unsplash API 키를 발급받아
검색 기반으로 교체하는 것을 권장합니다 (이 모듈의 인터페이스만 유지하면 교체 쉬움).
"""

import hashlib

PICSUM_BASE = "https://picsum.photos/seed/{seed}/800/450"


def get_image_url(topic: str) -> str:
    """
    주제 문자열을 시드로 사용해 고정된(매번 같은 주제면 같은 이미지) URL을 생성합니다.
    완전 랜덤 대신 시드 기반으로 해서, 같은 글을 재생성해도 같은 이미지가 나오게 합니다.
    """
    seed = hashlib.md5(topic.encode("utf-8")).hexdigest()[:10]
    return PICSUM_BASE.format(seed=seed)
