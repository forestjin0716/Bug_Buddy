"""고객사 코드 후보 파일 검색 모듈."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

ALLOWED_EXTENSIONS = {
    ".py", ".java", ".js", ".ts", ".jsx", ".tsx",
    ".cs", ".cpp", ".c", ".go", ".rb", ".php",
}

IGNORE_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv",
    "venv", ".idea", ".vscode", "dist",
}

MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB


def load_customers(
    path: str = "data/customers.json",
) -> tuple[list, str | None]:
    """customers.json을 로드하여 (고객사 목록, 에러 메시지) 튜플을 반환한다."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data, None
    except FileNotFoundError:
        return [], f"파일을 찾을 수 없습니다: {path}"
    except json.JSONDecodeError as e:
        return [], f"JSON 파싱 오류: {e}"
    except Exception as e:
        return [], f"파일 로드 오류: {e}"


def get_customer_by_name(
    customers: list,
    name: str,
) -> dict | None:
    """고객사 이름으로 고객사 정보를 반환한다. 없으면 None."""
    for customer in customers:
        if customer.get("name") == name:
            return customer
    return None


def _resolve_roots(local_path: str, paths: list[str]) -> list[str]:
    """local_path와 paths 조합으로 실제 탐색 루트 목록을 반환한다."""
    if not paths or paths == [""]:
        return [local_path]
    roots = []
    for p in paths:
        if p:
            candidate = os.path.join(local_path, p)
            if os.path.isdir(candidate):
                roots.append(candidate)
        else:
            roots.append(local_path)
    return roots if roots else [local_path]


def _get_excerpt(content: str, keywords: list[str], max_chars: int = 200) -> str:
    """키워드가 포함된 줄 주변의 발췌문을 반환한다."""
    lines = content.splitlines()
    for i, line in enumerate(lines):
        if any(kw.lower() in line.lower() for kw in keywords):
            start = max(0, i - 1)
            end = min(len(lines), i + 3)
            return "\n".join(lines[start:end])[:max_chars]
    return content[:max_chars]


def search_files(
    local_path: str,
    paths: list[str],
    keywords: list[str],
    top_n: int = 12,
) -> tuple[list[dict], str | None]:
    """로컬 경로에서 키워드 매칭 코드 파일 Top-N을 반환한다.

    Returns:
        ([{"path": str, "score": int, "excerpt": str}], error | None)
    """
    if not keywords:
        return [], "키워드를 1개 이상 입력해주세요"

    if not os.path.isdir(local_path):
        return [], f"경로를 찾을 수 없습니다: {local_path}"

    roots = _resolve_roots(local_path, paths)
    scored: list[dict] = []

    for root in roots:
        for dirpath, dirnames, filenames in os.walk(root):
            # IGNORE_DIRS 제외 (dirnames[:] = ... 패턴이 중요!)
            dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS and not d.startswith(".")]

            for filename in filenames:
                ext = Path(filename).suffix.lower()
                if ext not in ALLOWED_EXTENSIONS:
                    continue

                filepath = os.path.join(dirpath, filename)

                try:
                    if os.path.getsize(filepath) > MAX_FILE_SIZE:
                        continue
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                except (OSError, IOError):
                    continue

                # 스코어링: 각 키워드 등장 횟수 합산
                score = sum(
                    content.lower().count(kw.lower())
                    for kw in keywords
                )

                if score > 0:
                    scored.append({
                        "path": filepath,
                        "score": score,
                        "excerpt": _get_excerpt(content, keywords),
                    })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_n], None
