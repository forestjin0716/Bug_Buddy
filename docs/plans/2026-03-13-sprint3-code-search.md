# Sprint 3: 코드 후보 검색 구현 계획

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 고객사 선택 + 키워드 3개 입력 후 "추천 코드 확인하기" 클릭 시 로컬 레포에서 키워드 매칭 코드 후보 Top-N 파일을 추천한다.

**Architecture:** `src/code_searcher.py`를 독립 서비스로 구현하여 기존 코드와 격리한다. `app.py`에는 UI 연결 코드만 추가하며, Sprint 0/1/2 코드를 건드리지 않는다. `data/customers.json`에서 고객사 정보를 로드하고, `os.walk` 기반 재귀 탐색으로 키워드 스코어링 후 Top-N을 반환한다.

**Tech Stack:** Python 3.x, Streamlit, pathlib, os.walk (표준 라이브러리만 사용, 외부 의존성 없음), pytest + tmp_path 픽스처

---

## Task 1: customers.json 로더 실패 테스트 작성

**Files:**
- Create: `tests/test_code_searcher.py`

**Step 1: 실패 테스트 작성**

`tests/test_code_searcher.py`를 새로 생성한다. `src/code_searcher.py`는 아직 비어있으므로 import에서 실패한다.

```python
import pytest
import json
from pathlib import Path
from src.code_searcher import load_customers, get_customer_by_name


def test_load_customers_returns_list(tmp_path):
    data = [{"id": "test", "name": "테스트", "source_targets": []}]
    (tmp_path / "customers.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    result, err = load_customers(str(tmp_path / "customers.json"))
    assert isinstance(result, list) and err is None


def test_load_customers_missing_file():
    result, err = load_customers("/nonexistent/customers.json")
    assert result == [] and err is not None


def test_load_customers_invalid_json(tmp_path):
    (tmp_path / "customers.json").write_text("not json", encoding="utf-8")
    result, err = load_customers(str(tmp_path / "customers.json"))
    assert result == [] and err is not None


def test_get_customer_by_name_found():
    customers = [{"id": "a", "name": "대웅제약", "source_targets": []}]
    result = get_customer_by_name(customers, "대웅제약")
    assert result["id"] == "a"


def test_get_customer_by_name_not_found():
    result = get_customer_by_name([], "없는회사")
    assert result is None
```

**Step 2: 테스트 실패 확인**

Run: `pytest tests/test_code_searcher.py -v`

Expected:
```
FAILED - ImportError: cannot import name 'load_customers' from 'src.code_searcher'
5 errors in 5 items
```

**Step 3: 커밋**

```bash
git add tests/test_code_searcher.py
git commit -m "test: customers.json 로더 실패 테스트 작성 (TDD Red)"
```

---

## Task 2: customers.json 로더 구현

**Files:**
- Modify: `src/code_searcher.py`

**Step 1: load_customers 및 get_customer_by_name 구현**

`src/code_searcher.py`의 기존 docstring을 아래 내용으로 전체 교체한다.

```python
"""고객사 코드 후보 파일 검색 모듈."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def load_customers(
    path: str = "data/customers.json",
) -> tuple[list, str | None]:
    """customers.json을 로드하여 (고객사 목록, 에러 메시지) 튜플을 반환한다.

    Returns:
        (customers, None)     - 정상 로드
        ([], error_message)   - 파일 미존재 또는 파싱 실패
    """
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f), None
    except FileNotFoundError:
        return [], f"customers.json을 찾을 수 없어요: {path}"
    except json.JSONDecodeError as e:
        return [], f"customers.json 형식을 확인해 주세요: {e}"


def get_customer_by_name(customers: list, name: str) -> dict | None:
    """고객사 목록에서 이름으로 조회한다. 없으면 None을 반환한다."""
    return next((c for c in customers if c.get("name") == name), None)
```

**Step 2: 테스트 통과 확인**

Run: `pytest tests/test_code_searcher.py -v`

Expected:
```
PASSED test_load_customers_returns_list
PASSED test_load_customers_missing_file
PASSED test_load_customers_invalid_json
PASSED test_get_customer_by_name_found
PASSED test_get_customer_by_name_not_found
5 passed in 0.XXs
```

**Step 3: 커밋**

```bash
git add src/code_searcher.py tests/test_code_searcher.py
git commit -m "feat: customers.json 로더 및 고객사 조회 함수 구현 (TDD Green)"
```

---

## Task 3: 파일 검색 엔진 실패 테스트 추가

**Files:**
- Modify: `tests/test_code_searcher.py`

**Step 1: 검색 엔진 실패 테스트 추가**

`tests/test_code_searcher.py`에 아래 import와 테스트 함수들을 **기존 코드 아래에** 추가한다.

```python
from src.code_searcher import search_files


def test_search_finds_matching_file(tmp_path):
    src = tmp_path / "front-end"
    src.mkdir()
    (src / "order.vue").write_text(
        "주문관리 화면입니다\n<template>주문</template>", encoding="utf-8"
    )
    results, err = search_files(str(tmp_path), ["front-end/"], ["주문관리"])
    assert err is None and len(results) > 0
    assert results[0]["score"] > 0


def test_search_ignores_node_modules(tmp_path):
    nm = tmp_path / "node_modules"
    nm.mkdir()
    (nm / "big.js").write_text("주문관리" * 100, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    (src / "empty.ts").write_text("hello", encoding="utf-8")
    results, err = search_files(str(tmp_path), ["src/", "node_modules/"], ["주문관리"])
    assert all("node_modules" not in r["path"] for r in results)


def test_search_skips_large_files(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    large = src / "large.ts"
    large.write_bytes(b"x" * (2 * 1024 * 1024 + 1))  # > 2MB
    (src / "small.ts").write_text("주문관리", encoding="utf-8")
    results, err = search_files(str(tmp_path), ["src/"], ["주문관리"])
    assert all("large.ts" not in r["path"] for r in results)


def test_search_scores_by_keyword_count(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "high.ts").write_text("주문관리 " * 10, encoding="utf-8")
    (src / "low.ts").write_text("주문관리", encoding="utf-8")
    results, err = search_files(str(tmp_path), ["src/"], ["주문관리"])
    assert results[0]["path"].endswith("high.ts")


def test_search_local_path_not_exists():
    results, err = search_files("/nonexistent/path", ["src/"], ["keyword"])
    assert results == [] and "찾을 수 없어요" in err


def test_search_ignores_unsupported_extension(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "image.png").write_bytes(b"\x89PNG")
    (src / "main.ts").write_text("hello", encoding="utf-8")
    results, err = search_files(str(tmp_path), ["src/"], ["png"])
    assert all(not r["path"].endswith(".png") for r in results)


def test_search_returns_top_n(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    for i in range(15):
        (src / f"file{i}.ts").write_text(f"주문관리 {i}", encoding="utf-8")
    results, err = search_files(str(tmp_path), ["src/"], ["주문관리"], top_n=10)
    assert len(results) <= 10
```

**Step 2: 테스트 실패 확인**

Run: `pytest tests/test_code_searcher.py -v`

Expected:
```
... (기존 5개 PASSED)
FAILED - ImportError: cannot import name 'search_files' from 'src.code_searcher'
7 errors in 7 new items
```

**Step 3: 커밋**

```bash
git add tests/test_code_searcher.py
git commit -m "test: 파일 검색 엔진 실패 테스트 추가 (TDD Red)"
```

---

## Task 4: 파일 검색 엔진 구현

**Files:**
- Modify: `src/code_searcher.py`

**Step 1: 상수 및 search_files 구현**

`src/code_searcher.py`에서 `get_customer_by_name` 함수 **아래에** 아래 코드를 추가한다.

```python
ALLOWED_EXTENSIONS: frozenset[str] = frozenset({
    ".vue", ".ts", ".tsx", ".js", ".java",
    ".xml", ".yml", ".yaml", ".sql", ".md", ".properties",
})

IGNORE_DIRS: frozenset[str] = frozenset({
    "node_modules", "dist", "build", "target",
    ".git", "__pycache__", ".next", "coverage",
})

MAX_FILE_SIZE: int = 2 * 1024 * 1024  # 2MB


def search_files(
    local_path: str,
    paths: list[str],
    keywords: list[str],
    top_n: int = 12,
) -> tuple[list[dict[str, Any]], str | None]:
    """키워드 기반으로 코드 후보 파일을 탐색하여 Top-N을 반환한다.

    Args:
        local_path: 레포가 클론된 로컬 디렉터리 절대 경로
        paths: 탐색할 하위 디렉터리 목록 (예: ["front-end/", "back-end/"])
        keywords: 검색 키워드 1~3개
        top_n: 반환할 최대 결과 수 (기본 12)

    Returns:
        (results, None)       - 정상 검색 (results가 빈 리스트일 수 있음)
        ([], error_message)   - local_path 미존재 등 치명적 오류
    """
    if not os.path.isdir(local_path):
        return (
            [],
            f"로컬 경로를 찾을 수 없어요. "
            f"이 경로에 레포를 클론했는지 확인해 주세요: {local_path}",
        )

    normalized_keywords = [kw.lower() for kw in keywords if kw.strip()]
    if not normalized_keywords:
        return [], None

    search_roots = _resolve_roots(local_path, paths)
    scored: list[dict[str, Any]] = []

    for root in search_roots:
        for dirpath, dirnames, filenames in os.walk(root):
            # in-place 수정으로 무시 디렉터리 진입 방지
            dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]

            for filename in filenames:
                filepath = Path(dirpath) / filename

                if filepath.suffix.lower() not in ALLOWED_EXTENSIONS:
                    continue

                try:
                    if filepath.stat().st_size > MAX_FILE_SIZE:
                        continue
                    content = filepath.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue

                content_lower = content.lower()
                score = sum(content_lower.count(kw) for kw in normalized_keywords)

                if score == 0:
                    continue

                rel_path = str(filepath.relative_to(local_path))
                excerpt = _get_excerpt(content, normalized_keywords)
                scored.append({"path": rel_path, "score": score, "excerpt": excerpt})

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_n], None


def _resolve_roots(local_path: str, paths: list[str]) -> list[Path]:
    """paths 목록을 local_path 기준 실제 존재하는 Path 목록으로 변환한다."""
    base = Path(local_path)
    if not paths or paths == ["."]:
        return [base]
    roots = [base / p.rstrip("/") for p in paths if (base / p.rstrip("/")).is_dir()]
    return roots if roots else [base]


def _get_excerpt(content: str, keywords: list[str], max_len: int = 200) -> str:
    """키워드가 처음 등장하는 라인을 발췌하여 반환한다 (최대 max_len자)."""
    for line in content.splitlines():
        if any(kw in line.lower() for kw in keywords):
            stripped = line.strip()
            return stripped[:max_len]
    return ""
```

**Step 2: 테스트 통과 확인**

Run: `pytest tests/test_code_searcher.py -v`

Expected:
```
PASSED test_load_customers_returns_list
PASSED test_load_customers_missing_file
PASSED test_load_customers_invalid_json
PASSED test_get_customer_by_name_found
PASSED test_get_customer_by_name_not_found
PASSED test_search_finds_matching_file
PASSED test_search_ignores_node_modules
PASSED test_search_skips_large_files
PASSED test_search_scores_by_keyword_count
PASSED test_search_local_path_not_exists
PASSED test_search_ignores_unsupported_extension
PASSED test_search_returns_top_n
12 passed in 0.XXs
```

**Step 3: 커밋**

```bash
git add src/code_searcher.py
git commit -m "feat: 키워드 기반 파일 검색 엔진 구현 (TDD Green, top_n/IGNORE_DIRS/MAX_FILE_SIZE)"
```

---

## Task 5: 코드 후보 검색 카드 UI 구현

**Files:**
- Modify: `app.py`

**Step 1: app.py 현재 상태 파악**

```bash
grep -n "def render_left_column\|def render_right_column\|def main\|코드 후보" /c/Users/forestlim/cursor_test/Hackathon_HJ/Bug_buddy/app.py
```

Sprint 0 기준으로 `render_left_column()` 안에 `st.subheader("🔍 코드 후보 검색")` placeholder가 있다.

**Step 2: render_code_search_card 함수 추가**

`app.py`에서 `render_left_column()` 정의 **바로 위**에 아래 함수를 추가한다.

```python
def render_code_search_card(customers: list) -> dict | None:
    """좌측 하단 '코드 후보 검색' 카드를 렌더링하고 검색 파라미터를 반환한다.

    Returns:
        검색 파라미터 딕셔너리 (버튼 클릭 시), 또는 None
    """
    st.divider()
    st.subheader("🔍 코드 후보 검색")

    if not customers:
        st.warning(
            "customers.json을 만들어 주세요. "
            "고객사 정보가 없으면 코드 검색을 사용할 수 없어요."
        )
        return None

    from src.code_searcher import get_customer_by_name

    customer_names = [c["name"] for c in customers]
    selected_name = st.selectbox(
        "고객사 선택",
        options=customer_names,
        key="code_search_customer",
    )

    selected_customer = get_customer_by_name(customers, selected_name)
    source_targets = selected_customer.get("source_targets", []) if selected_customer else []

    if not source_targets:
        st.info("이 고객사는 소스 타겟이 설정되지 않았어요.")
        st.button("🔎 추천 코드 확인하기", key="code_search_btn", disabled=True)
        return None

    target_labels = [t["label"] for t in source_targets]
    selected_label = st.selectbox(
        "소스 타겟 선택",
        options=target_labels,
        key="code_search_target",
    )
    selected_target = next(
        (t for t in source_targets if t["label"] == selected_label), None
    )

    keyword1 = st.text_input(
        "키워드 1 - 메뉴명/화면명",
        placeholder="예: 주문관리",
        key="keyword1",
    )
    keyword2 = st.text_input(
        "키워드 2 - API 경로",
        placeholder="예: /biz/ord/list",
        key="keyword2",
    )
    keyword3 = st.text_input(
        "키워드 3 - 에러 코드/메시지",
        placeholder="예: NullPointerException",
        key="keyword3",
    )

    if st.button("🔎 추천 코드 확인하기", key="code_search_btn"):
        keywords = [kw for kw in [keyword1, keyword2, keyword3] if kw.strip()]
        if not keywords:
            st.warning("키워드를 하나 이상 입력해 주세요.")
            return None
        return {
            "local_path": selected_target["local_path"],
            "paths": selected_target.get("paths", ["."]),
            "keywords": keywords,
        }

    return None
```

**Step 3: render_left_column() 수정**

기존 `render_left_column()` 함수의 placeholder "코드 후보 검색" 블록을 제거하고, 함수 반환값을 `render_code_search_card(customers)` 결과로 교체한다.

기존:
```python
def render_left_column() -> None:
    """좌측 입력 영역 placeholder를 렌더링한다."""
    st.subheader("📝 이슈 작성")
    with st.container(border=True):
        st.caption("이슈 정보를 입력하는 영역이에요. (Sprint 1에서 구현 예정)")
        st.info("여기에 Tracker, Status, 고객사, 에러 내용 등을 입력하게 될 거예요.")

    st.subheader("🔍 코드 후보 검색")
    with st.container(border=True):
        st.caption("키워드로 관련 코드를 찾는 영역이에요. (Sprint 3에서 구현 예정)")
        st.info("고객사와 키워드를 입력하면 관련 파일을 추천해 드릴게요.")
```

교체 후:
```python
def render_left_column(customers: list) -> dict | None:
    """좌측 입력 영역을 렌더링하고 코드 검색 파라미터를 반환한다."""
    st.subheader("📝 이슈 작성")
    with st.container(border=True):
        st.caption("이슈 정보를 입력하는 영역이에요. (Sprint 1에서 구현 예정)")
        st.info("여기에 Tracker, Status, 고객사, 에러 내용 등을 입력하게 될 거예요.")

    return render_code_search_card(customers)
```

**Step 4: main() 함수 수정**

`main()` 함수에서 customers 로드 및 함수 시그니처 변경을 반영한다.

기존 `main()`:
```python
def main() -> None:
    ...
    with left_col:
        render_left_column()

    with right_col:
        render_right_column()
```

수정 후:
```python
def main() -> None:
    """버그버디 메인 앱."""
    inject_custom_css()

    st.title("🐛 버그버디 - 이슈 정리 도우미")
    st.caption("안녕하세요! 버그버디가 이슈 정리를 도와드릴게요.")
    st.divider()

    # customers.json 로드
    from src.code_searcher import load_customers as _load_customers
    customers, _ = _load_customers()

    # 환경 설정 검증 및 경고 표시
    env_status = check_environment()
    show_env_warnings(env_status)

    # 좌/우 레이아웃
    left_col, right_col = st.columns([1, 1])

    with left_col:
        search_params = render_left_column(customers)

    with right_col:
        render_right_column(search_params)
```

**Step 5: 앱 실행 수동 확인**

```bash
streamlit run /c/Users/forestlim/cursor_test/Hackathon_HJ/Bug_buddy/app.py
```

확인 항목:
- [ ] 좌측 하단에 "코드 후보 검색" 제목과 고객사 드롭다운 표시
- [ ] "웹취약점 개선" 선택 시 버튼 비활성화 + "소스 타겟이 설정되지 않았어요." 안내 표시
- [ ] customers.json이 없으면 경고 메시지 표시

**Step 6: 커밋**

```bash
git add app.py
git commit -m "feat: 코드 후보 검색 카드 UI 구현 (고객사/소스타겟 드롭다운, 키워드 입력 3개)"
```

---

## Task 6: 검색 결과 UI 구현

**Files:**
- Modify: `app.py`

**Step 1: render_right_column() 시그니처 및 결과 렌더링 추가**

기존 `render_right_column()` 함수를 아래로 교체한다.

기존:
```python
def render_right_column() -> None:
    """우측 출력 영역 placeholder를 렌더링한다."""
    st.subheader("📋 결과")
    with st.container(border=True):
        st.caption("생성된 템플릿과 분석 결과가 여기에 표시돼요. (Sprint 1~2에서 구현 예정)")
        st.info("버그버디가 정리한 이슈 템플릿과 Claude 분석 결과를 확인할 수 있어요.")
```

교체 후:
```python
def render_right_column(search_params: dict | None) -> None:
    """우측 출력 영역을 렌더링한다."""
    st.subheader("📋 결과")
    with st.container(border=True):
        st.caption("생성된 템플릿과 분석 결과가 여기에 표시돼요. (Sprint 1~2에서 구현 예정)")
        st.info("버그버디가 정리한 이슈 템플릿과 Claude 분석 결과를 확인할 수 있어요.")

    if search_params is not None:
        _render_code_search_results(search_params)


def _render_code_search_results(search_params: dict) -> None:
    """코드 후보 검색 결과를 우측 하단에 렌더링한다."""
    from src.code_searcher import search_files

    st.divider()
    st.subheader("🔎 코드 후보")

    with st.spinner("버그버디가 코드를 찾고 있어요..."):
        results, error = search_files(
            local_path=search_params["local_path"],
            paths=search_params["paths"],
            keywords=search_params["keywords"],
            top_n=12,
        )

    if error:
        st.error(error)
        return

    if not results:
        st.info(
            "키워드와 일치하는 파일을 찾지 못했어요. "
            "다른 키워드로 시도해 보세요."
        )
        return

    st.success(f"총 {len(results)}개의 후보 파일을 찾았어요.")

    for i, r in enumerate(results, start=1):
        with st.container(border=True):
            st.markdown(f"**#{i}** &nbsp; Score: {r['score']}")
            st.code(r["path"], language=None)
            if r["excerpt"]:
                st.code(r["excerpt"], language=None)
```

**Step 2: 앱 실행 수동 확인**

```bash
streamlit run /c/Users/forestlim/cursor_test/Hackathon_HJ/Bug_buddy/app.py
```

확인 항목:
- [ ] "추천 코드 확인하기" 클릭 시 "버그버디가 코드를 찾고 있어요..." 스피너 표시
- [ ] `local_path` 미존재 시 "로컬 경로를 찾을 수 없어요." 에러 메시지 표시
- [ ] 결과 없음 시 "키워드와 일치하는 파일을 찾지 못했어요." 안내 표시
- [ ] 결과 있음 시 `Score: X` + 상대 경로 + 발췌 코드 표시

**Step 3: 커밋**

```bash
git add app.py
git commit -m "feat: 코드 후보 검색 결과 UI 구현 (스코어/경로/발췌 표시, 에러/빈 결과 처리)"
```

---

## Task 7: Playwright MCP 검증

**사전 조건:** `streamlit run app.py` 실행 중 상태

**Step 1: 정상 검색 흐름 검증**

```
1. browser_navigate → http://localhost:8501
2. browser_snapshot → "코드 후보 검색" 카드 존재 확인
3. browser_select_option → 고객사 드롭다운에서 소스 타겟이 있는 고객사 선택 (예: "DNC")
4. browser_snapshot → 소스 타겟 드롭다운 + 키워드 입력 필드 3개 표시 확인
5. browser_type → 키워드1 필드에 "주문관리" 입력
6. browser_type → 키워드2 필드에 "/biz/ord" 입력
7. browser_click → "🔎 추천 코드 확인하기" 버튼 클릭
8. browser_wait_for → "버그버디가 코드를 찾고 있어요" 스피너 표시 확인
9. browser_wait_for → 결과 카드 또는 "찾지 못했어요" 메시지 표시
10. browser_snapshot → 우측 하단에 코드 후보 섹션 렌더링 확인
11. browser_console_messages(level: "error") → 콘솔 에러 없음 확인
```

**Step 2: customers.json 미존재 시 경고 확인**

```
1. (data/customers.json을 임시로 다른 이름으로 변경: mv data/customers.json data/customers.json.bak)
2. streamlit run app.py (재시작)
3. browser_navigate → http://localhost:8501
4. browser_snapshot → "customers.json을 만들어 주세요." 경고 메시지 확인
5. browser_snapshot → 고객사 드롭다운이 표시되지 않음 확인
6. (복구: mv data/customers.json.bak data/customers.json)
```

**Step 3: local_path 미존재 시 에러 메시지 확인**

```
1. (customers.json에서 테스트 고객사의 local_path를 "/nonexistent/path"로 임시 변경)
2. browser_navigate → http://localhost:8501
3. browser_select_option → 해당 고객사 선택
4. browser_type → 키워드1에 "테스트" 입력
5. browser_click → "🔎 추천 코드 확인하기" 버튼 클릭
6. browser_wait_for → "로컬 경로를 찾을 수 없어요" 에러 메시지 표시
7. browser_snapshot → 빨간 에러 박스 확인
8. (customers.json 원복)
```

---

## 완료 기준 (Definition of Done)

- [ ] `pytest tests/test_code_searcher.py -v` → 12 passed
- [ ] `customers.json` 고객사 드롭다운에 source_targets 있는 고객사 선택 시 소스 타겟 드롭다운 표시
- [ ] 키워드 3개 입력 후 "추천 코드 확인하기" 클릭 시 Top-12 후보 파일 표시
- [ ] 각 후보에 상대 경로, 스코어(`Score: X`), 발췌 코드(최대 200자) 표시
- [ ] `local_path` 미존재 시 "로컬 경로를 찾을 수 없어요." 에러 표시
- [ ] `source_targets` 없는 고객사 선택 시 버튼 비활성화 + "소스 타겟이 설정되지 않았어요." 안내
- [ ] `customers.json` 미존재 시 "customers.json을 만들어 주세요." 경고 표시
- [ ] 브라우저 콘솔 에러 없음

---

## 의존성 및 리스크

| 항목 | 내용 |
|------|------|
| **외부 의존성** | 없음 (표준 라이브러리 `os`, `pathlib`, `json`만 사용) |
| **리스크 1** | 대규모 레포(수만 파일) 탐색 시 수 초 이상 소요 가능 → `paths`로 탐색 범위를 제한하는 것으로 완화 |
| **리스크 2** | Windows 경로 구분자 차이(`\` vs `/`) → `pathlib.Path` + `os.path.relpath` 사용으로 완화 |
| **리스크 3** | 파일 인코딩 다양성(EUC-KR 등) → `errors='ignore'`로 읽기 실패 방지 |
| **리스크 4** | Sprint 1/2 UI와 `app.py` 충돌 가능 → `render_code_search_card()` 함수 분리로 격리 |

---

## 기술 고려사항

- `os.walk`에서 `dirnames[:] = [...]` 패턴을 반드시 사용해야 무시 디렉터리를 실제로 건너뜀. `dirnames = [...]`는 로컬 변수 재할당이라 효과 없음
- `pathlib.Path.relative_to(base)`는 base 외부 경로 전달 시 `ValueError` 발생 → `_resolve_roots()`에서 base 내부 경로만 사용하여 예방
- Streamlit의 `st.button` 클릭 후 페이지 전체가 재렌더링되므로, 검색 파라미터를 반환값으로 전달하여 `render_right_column()`에서 처리하는 패턴 사용
- `st.session_state` 미사용: v1에서는 단순성 우선. 버튼을 클릭하지 않으면 결과가 사라지는 동작은 의도된 것

---

## 예상 산출물 파일 구조

```
Bug_buddy/
├── app.py                          # render_code_search_card + _render_code_search_results 추가
├── src/
│   └── code_searcher.py            # load_customers + get_customer_by_name + search_files 완성
└── tests/
    └── test_code_searcher.py       # 12개 단위 테스트 (TDD, tmp_path 픽스처)
```
