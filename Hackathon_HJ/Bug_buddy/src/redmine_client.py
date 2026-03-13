"""Redmine REST API 클라이언트 모듈 (read-only)."""

from __future__ import annotations

import requests

TRACKER_FALLBACK = ["Common", "Feature", "Defect", "Request", "Patch", "Issue", "Review"]
STATUS_FALLBACK = ["New", "Confirm", "Assigned", "In progress", "Resolved", "Closed", "Need Feedback", "Rejected"]

DEFAULT_TIMEOUT = 5


def get_trackers(
    base_url: str,
    api_key: str,
) -> tuple[list | None, str | None]:
    """Redmine에서 Tracker 목록을 가져온다.

    Returns:
        ([{"id": int, "name": str}], None) 또는 (None, 에러 메시지)
    """
    if not base_url or not api_key:
        return None, "REDMINE_URL 또는 REDMINE_API_KEY가 설정되지 않았습니다"

    url = f"{base_url.rstrip('/')}/trackers.json"
    headers = {"X-Redmine-API-Key": api_key}

    try:
        response = requests.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
        if response.status_code == 401:
            return None, "Redmine 인증 실패: API 키를 확인해주세요"
        if response.status_code != 200:
            return None, f"Redmine API 오류: HTTP {response.status_code}"
        data = response.json()
        return data.get("trackers", []), None
    except requests.Timeout:
        return None, f"Redmine 연결 타임아웃 ({DEFAULT_TIMEOUT}초)"
    except requests.ConnectionError:
        return None, "Redmine 서버에 연결할 수 없습니다"
    except Exception as e:
        return None, f"예상치 못한 오류: {e}"


def get_issue_statuses(
    base_url: str,
    api_key: str,
) -> tuple[list | None, str | None]:
    """Redmine에서 이슈 상태 목록을 가져온다.

    Returns:
        ([{"id": int, "name": str}], None) 또는 (None, 에러 메시지)
    """
    if not base_url or not api_key:
        return None, "REDMINE_URL 또는 REDMINE_API_KEY가 설정되지 않았습니다"

    url = f"{base_url.rstrip('/')}/issue_statuses.json"
    headers = {"X-Redmine-API-Key": api_key}

    try:
        response = requests.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
        if response.status_code == 401:
            return None, "Redmine 인증 실패: API 키를 확인해주세요"
        if response.status_code != 200:
            return None, f"Redmine API 오류: HTTP {response.status_code}"
        data = response.json()
        return data.get("issue_statuses", []), None
    except requests.Timeout:
        return None, f"Redmine 연결 타임아웃 ({DEFAULT_TIMEOUT}초)"
    except requests.ConnectionError:
        return None, "Redmine 서버에 연결할 수 없습니다"
    except Exception as e:
        return None, f"예상치 못한 오류: {e}"


def load_trackers_with_fallback(base_url: str, api_key: str) -> list[str]:
    """Tracker 이름 목록을 반환한다. API 실패 시 TRACKER_FALLBACK을 사용한다."""
    result, err = get_trackers(base_url, api_key)
    if err or not result:
        return TRACKER_FALLBACK
    return [t["name"] for t in result]


def load_statuses_with_fallback(base_url: str, api_key: str) -> list[str]:
    """이슈 상태 이름 목록을 반환한다. API 실패 시 STATUS_FALLBACK을 사용한다."""
    result, err = get_issue_statuses(base_url, api_key)
    if err or not result:
        return STATUS_FALLBACK
    return [s["name"] for s in result]


def create_issue(*args, **kwargs):
    """이슈 생성 (v2에서 구현 예정)."""
    raise NotImplementedError("v2에서 구현 예정")
