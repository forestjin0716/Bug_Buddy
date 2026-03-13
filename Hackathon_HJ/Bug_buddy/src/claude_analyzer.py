"""Claude API를 이용한 이슈 분석 모듈."""

from __future__ import annotations

import json
from typing import Any

import anthropic

REQUIRED_KEYS = ["missing_fields", "questions_to_ask", "redmine_subject", "redmine_description", "confidence", "risk_flags"]

SYSTEM_PROMPT = """당신은 소프트웨어 버그 이슈를 분석하는 전문가입니다.
주어진 이슈 정보를 분석하여 다음 JSON 형식으로만 응답하세요. 다른 텍스트는 포함하지 마세요.

{
  "missing_fields": ["누락된 필드명 목록"],
  "questions_to_ask": ["추가로 필요한 질문 목록"],
  "redmine_subject": "Redmine 이슈 제목 (예: [BUG] 현상 요약)",
  "redmine_description": "Redmine 이슈 본문 (마크다운 형식)",
  "confidence": 0.85,
  "risk_flags": ["PII_POSSIBLE", "SECURITY_RELATED 등 위험 플래그"]
}"""


def validate_response(data: dict) -> tuple[bool, str | None]:
    """Claude 응답 JSON의 필수 키와 타입을 검증한다."""
    for key in REQUIRED_KEYS:
        if key not in data:
            return False, f"필수 키 누락: {key}"

    if not isinstance(data["missing_fields"], list):
        return False, "missing_fields는 list여야 합니다"
    if not isinstance(data["questions_to_ask"], list):
        return False, "questions_to_ask는 list여야 합니다"
    if not isinstance(data["risk_flags"], list):
        return False, "risk_flags는 list여야 합니다"
    if not isinstance(data["redmine_subject"], str):
        return False, "redmine_subject는 str이어야 합니다"
    if not isinstance(data["redmine_description"], str):
        return False, "redmine_description은 str이어야 합니다"
    if not isinstance(data["confidence"], (int, float)):
        return False, "confidence는 float이어야 합니다"
    if not (0.0 <= data["confidence"] <= 1.0):
        return False, f"confidence는 0.0~1.0 범위여야 합니다: {data['confidence']}"

    return True, None


def parse_json_response(raw: str) -> tuple[dict | None, str | None]:
    """Claude 응답 문자열에서 JSON을 파싱한다."""
    try:
        text = raw.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
        data = json.loads(text)
        return data, None
    except json.JSONDecodeError as e:
        return None, f"JSON 파싱 실패: {e}"


def analyze_issue(
    issue_data: dict,
    api_key: str,
    model: str = "claude-3-5-sonnet-latest",
    max_tokens: int = 2048,
) -> tuple[dict | None, str | None]:
    """이슈 데이터를 Claude API로 분석하여 (결과 dict, 에러 메시지) 튜플을 반환한다."""
    client = anthropic.Anthropic(api_key=api_key)

    user_message = f"다음 이슈를 분석해주세요:\n\n{json.dumps(issue_data, ensure_ascii=False, indent=2)}"

    def _call_api() -> tuple[dict | None, str | None]:
        try:
            message = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message}],
            )
            raw = message.content[0].text
            data, err = parse_json_response(raw)
            if err:
                return None, err
            valid, verr = validate_response(data)
            if not valid:
                return None, f"응답 검증 실패: {verr}"
            return data, None
        except anthropic.APIError as e:
            return None, f"Claude API 오류: {e}"
        except Exception as e:
            return None, f"예상치 못한 오류: {e}"

    result, err = _call_api()

    # 재시도: confidence==0.0 AND redmine_subject=="" 인 경우
    if result is not None and result.get("confidence") == 0.0 and result.get("redmine_subject") == "":
        result, err = _call_api()

    return result, err
