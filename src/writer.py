"""
Google Gemini API로 블로그 글 초안을 생성합니다.

- k-popcorn-bot의 insight.py와 동일한 모델 폴백/재시도 전략을 사용합니다.
- 카테고리(알고 먹자 / 전쟁이야기)에 맞는 시스템 프롬프트로 분기합니다.
- 응답은 JSON 형식(제목/본문/태그/요약)으로 강제합니다.

503/429 등 일시적 오류에 대비한 폴백:
  1) gemini-2.5-flash-lite 최대 3회 (5/15/30초 대기)
  2) gemini-2.0-flash 최대 2회
  3) gemini-2.0-flash-lite 최대 2회
"""

import json
import os
import time

from google import genai
from google.genai import types

from . import config

SYSTEM_INSTRUCTIONS = {
    "알고 먹자": """당신은 식품/영양 정보 블로그 '강냉이'의 필자입니다.
주어진 식재료에 대해 성분, 효능, 부작용을 다루는 블로그 글을 작성합니다.
사실에 기반해 작성하되, 과장된 효능 주장이나 의학적 단정("반드시 낫는다" 등)은 피하세요.
글은 친근하면서도 정보 전달에 충실한 톤으로 작성하세요.""",
    "전쟁이야기": """당신은 역사/전쟁 블로그 '강냉이'의 필자입니다.
주어진 전쟁/전투에 대해 배경, 원인, 전개, 결과를 다루는 블로그 글을 작성합니다.
역사적 사실에 기반해 작성하고, 확인되지 않은 추측은 추측이라고 명시하세요.
글은 흥미롭게 읽히면서도 사실 전달에 충실한 톤으로 작성하세요.""",
}

OUTPUT_SCHEMA_INSTRUCTION = """
반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트나 마크다운 코드블록 없이 순수 JSON만 출력하세요.

{
  "title": "글 제목 (한국어, 25자 이내)",
  "body_markdown": "본문 전체 (마크다운 형식, 소제목은 ## 사용, 800~1500자 분량)",
  "summary": "카카오톡 알림용 한 줄 요약 (한국어, 60자 이내)",
  "tags": ["태그1", "태그2", "태그3"]
}
"""

MODEL_FALLBACK = [
    (config.GEMINI_MODEL, 3),
    ("gemini-2.0-flash", 2),
    ("gemini-2.0-flash-lite", 2),
]

RETRY_DELAYS = [5, 15, 30]
RETRYABLE_KEYWORDS = ("503", "429", "UNAVAILABLE", "RESOURCE_EXHAUSTED", "DEADLINE_EXCEEDED")


def _build_prompt(category: str, topic: str) -> str:
    return f"""카테고리: {category}
주제: {topic}

위 주제로 블로그 글을 작성하세요.

조건:
- 본문은 소제목(##)을 활용해 2~4개 섹션으로 구성
- 마크다운 문법 사용 가능 (제목, 목록, 강조 등)
- 본문 내에 구체적인 성분명/사건명/연도 등 구체적 정보 포함
- 확실하지 않은 정보는 만들어내지 말 것
{OUTPUT_SCHEMA_INSTRUCTION}"""


def _call_gemini(client, model: str, system_instruction: str, prompt: str) -> str:
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.7,
            max_output_tokens=4000,
            thinking_config=types.ThinkingConfig(thinking_budget=0),
            response_mime_type="application/json",
        ),
    )
    return (response.text or "").strip()


def _is_retryable(error: Exception) -> bool:
    msg = str(error)
    return any(kw in msg for kw in RETRYABLE_KEYWORDS)


def _parse_response(raw: str) -> dict:
    """Gemini 응답을 JSON으로 파싱. 코드블록이 섞여 와도 방어적으로 처리."""
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    data = json.loads(text)

    required = ("title", "body_markdown", "summary", "tags")
    missing = [k for k in required if k not in data]
    if missing:
        raise ValueError(f"응답에 필수 필드 누락: {missing}")

    return data


def generate_post(category: str, topic: str) -> dict:
    """
    주어진 카테고리/주제로 블로그 글을 생성합니다.

    Returns:
        {"title": str, "body_markdown": str, "summary": str, "tags": list[str]}
    """
    system_instruction = SYSTEM_INSTRUCTIONS.get(category)
    if system_instruction is None:
        raise ValueError(f"알 수 없는 카테고리: {category}")

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    prompt = _build_prompt(category, topic)

    last_error: Exception = RuntimeError("호출 시도 없음")

    for model, max_attempts in MODEL_FALLBACK:
        for attempt in range(1, max_attempts + 1):
            try:
                raw = _call_gemini(client, model, system_instruction, prompt)
                if not raw:
                    raise RuntimeError("Gemini가 빈 응답을 반환")

                result = _parse_response(raw)

                if attempt > 1 or model != config.GEMINI_MODEL:
                    print(f"[writer] {model} (시도 {attempt}) 성공")
                return result

            except Exception as e:
                last_error = e
                error_msg = str(e)[:150]
                retryable = _is_retryable(e)
                is_last_attempt = attempt == max_attempts

                if retryable and not is_last_attempt:
                    delay = RETRY_DELAYS[min(attempt - 1, len(RETRY_DELAYS) - 1)]
                    print(
                        f"[writer] {model} 시도 {attempt} 실패 "
                        f"({error_msg}) → {delay}초 후 재시도"
                    )
                    time.sleep(delay)
                else:
                    print(f"[writer] {model} 시도 {attempt} 실패 ({error_msg})")
                    break

    raise RuntimeError(f"Gemini API 모든 재시도 실패: {last_error}")
