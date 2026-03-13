# Sprint 3: 고객사-코드 매핑 + 코드 후보 검색 구현 계획

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 개발자가 고객사와 키워드를 입력하면, 해당 고객사의 로컬 레포에서 키워드 매칭으로 코드 후보 파일 Top-N을 추천한다.

**Architecture:** `src/code_searcher.py`를 독립 서비스로 구현하여 기존 코드와 격리한다. `app.py`에는 UI 연결 코드만 추가하며, Phase 1/2 코드를 건드리지 않는다. `data/customers.json`에서 고객사 정보를 로드하고, `os.walk` 기반 재귀 탐색으로 키워드 스코어링 후 Top-N을 반환한다.

**Tech Stack:** Python 3.x, Streamlit, pathlib, os.walk (표준 라이브러리만 사용, 외부 의존성 없음)

---

## 스프린트 정보

| 항목 | 내용 |
|------|------|
| **스프린트 번호** | Sprint 3 |
| **기간** | 2026-04-17 ~ 2026-05-01 (2주) |
| **마일스톤** | M3 - 개발자 트리아지 도구 |
| **MoSCoW** | Must Have (PRD 5.3) |
| **Karpathy Guideline** | Surgical Changes (독립 서비스로 구현, 기존 코드 최소 변경) |
| **의존성** | Sprint 0 완료 필요 (customers.json 스키마), Sprint 1/2와 병렬 가능하나 UI 통합 시 필요 |

---

## 구현 범위

### 포함 항목 (In Scope)
- `src/code_searcher.py`: customers.json 로더 + 키워드 기반 파일 검색 엔진
- `data/customers.json`: 24개 고객사 전체 데이터 등록
- `app.py`: "코드 후보 검색" 카드 UI + 검색 결과 표시 UI 추가
- `tests/test_code_searcher.py`: 파일 시스템 TDD 기반 단위 테스트 전체

### 제외 항목 (Out of Scope)
- Claude API 연동 (Sprint 2 범위)
- Redmine API 연동 (Sprint 4 범위)
- 시맨틱/임베딩 기반 검색 (v2 Backlog)
- 파일 검색 결과에서 직접 Redmine 이슈 생성 (v2 Backlog)
- 검색 취소/타임아웃 기능 (Should Have, v2 Backlog)

---

## Task 1: customers.json 로더 구현

**예상 소요 시간:** 0.5일

**Files:**
- Modify: `src/code_searcher.py`
- Create: `tests/test_code_searcher.py`

**Step 1: 실패 테스트 작성 - customers.json 로더**

`tests/test_code_searcher.py`를 생성하고 아래 테스트를 먼저 작성한다.

```python
"""code_searcher 모듈 단위 테스트."""

import json
import os
import tempfile
from pathlib import Path

import pytest

from src.code_searcher import (
    load_customers,
    get_customer_by_name,
    search_code_candidates,
)


# ── customers.json 로더 테스트 ──────────────────────────────────────

class TestLoadCustomers:
    def test_returns_list_when_valid_json(self, tmp_path):
        """유효한 customers.json 파일을 파싱하여 리스트를 반환한다."""
        customers_file = tmp_path / "customers.json"
        customers_file.write_text(
            json.dumps([{"id": "corp-a", "name": "A사", "source_targets": []}]),
            encoding="utf-8",
        )
        result = load_customers(customers_path=str(customers_file))
        assert isinstance(result, list)
        assert result[0]["name"] == "A사"

    def test_returns_empty_list_when_file_missing(self, tmp_path):
        """파일이 없으면 빈 리스트를 반환한다."""
        missing = tmp_path / "no_such.json"
        result, warning = load_customers(customers_path=str(missing))
        assert result == []
        assert warning is not None  # 경고 메시지가 있어야 함

    def test_returns_empty_list_when_invalid_json(self, tmp_path):
        """파싱 불가 파일이면 빈 리스트를 반환한다."""
        bad_file = tmp_path / "customers.json"
        bad_file.write_text("{not: valid json}", encoding="utf-8")
        result, error = load_customers(customers_path=str(bad_file))
        assert result == []
        assert "형식을 확인해 주세요" in error


class TestGetCustomerByName:
    def test_returns_customer_dict_when_name_matches(self):
        """이름이 일치하는 고객사 딕셔너리를 반환한다."""
        customers = [
            {"id": "corp-a", "name": "A제약", "source_targets": []},
            {"id": "corp-b", "name": "B제약", "source_targets": []},
        ]
        result = get_customer_by_name(customers, "A제약")
        assert result is not None
        assert result["id"] == "corp-a"

    def test_returns_none_when_not_found(self):
        """존재하지 않는 이름이면 None을 반환한다."""
        customers = [{"id": "corp-a", "name": "A제약", "source_targets": []}]
        result = get_customer_by_name(customers, "없는회사")
        assert result is None

    def test_returns_none_when_empty_list(self):
        """빈 리스트에서 조회하면 None을 반환한다."""
        result = get_customer_by_name([], "A제약")
        assert result is None
```

**Step 2: 테스트 실패 확인**

```bash
cd /c/Users/forestlim/cursor_test/Hackathon_HJ/Bug_buddy
pytest tests/test_code_searcher.py::TestLoadCustomers -v
```

Expected: FAIL with `ImportError: cannot import name 'load_customers'`

**Step 3: load_customers 및 get_customer_by_name 구현**

`src/code_searcher.py`를 아래와 같이 작성한다.

```python
"""고객사 코드 후보 파일 검색 모듈."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


# ── customers.json 로더 ───────────────────────────────────────────

def load_customers(
    customers_path: str = "data/customers.json",
) -> tuple[list[dict], str | None]:
    """customers.json을 로드하여 (고객사 목록, 경고/에러 메시지) 튜플을 반환한다.

    Returns:
        (customers, None)       - 정상 로드
        ([], warning_message)   - 파일 미존재
        ([], error_message)     - 파싱 실패
    """
    path = Path(customers_path)

    if not path.exists():
        return [], "customers.json 파일을 찾을 수 없어요. data/customers.json을 만들어 주세요."

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            return [], "customers.json 형식을 확인해 주세요. 최상위가 배열([ ])이어야 해요."
        return data, None
    except json.JSONDecodeError:
        return [], "customers.json 형식을 확인해 주세요. JSON 파싱에 실패했어요."
    except OSError as e:
        return [], f"customers.json을 읽는 중 오류가 발생했어요: {e}"


def get_customer_by_name(customers: list[dict], name: str) -> dict | None:
    """고객사 목록에서 이름으로 조회한다.

    Args:
        customers: load_customers()로 얻은 고객사 목록
        name: 검색할 고객사 이름

    Returns:
        일치하는 고객사 딕셔너리, 없으면 None
    """
    for customer in customers:
        if customer.get("name") == name:
            return customer
    return None
```

**Step 4: 테스트 통과 확인**

```bash
pytest tests/test_code_searcher.py::TestLoadCustomers tests/test_code_searcher.py::TestGetCustomerByName -v
```

Expected: 모든 테스트 PASS

**Step 5: 커밋**

```bash
git add src/code_searcher.py tests/test_code_searcher.py
git commit -m "feat: customers.json 로더 및 고객사 조회 함수 구현 (TDD)"
```

---

## Task 2: customers.json 실제 데이터 작성

**예상 소요 시간:** 1일

**Files:**
- Modify: `data/customers.json`

**Step 1: 기존 customers.json 백업 확인**

```bash
cat /c/Users/forestlim/cursor_test/Hackathon_HJ/Bug_buddy/data/customers.json
```

Expected: Sprint 0에서 생성한 샘플 1건이 표시됨

**Step 2: 24개 고객사 전체 데이터 작성**

`data/customers.json`을 아래 내용으로 교체한다. `local_path`는 개발 환경에서 실제 경로로 업데이트하기 전까지 placeholder를 사용한다.

```json
[
  {
    "id": "web-security",
    "name": "웹취약점 개선",
    "source_targets": []
  },
  {
    "id": "dnc",
    "name": "DNC",
    "source_targets": [
      {
        "label": "DNC main (customer/dnc)",
        "repo_url": "https://git.internal/dnc.git",
        "branch": "main",
        "local_path": "/home/dev/repos/dnc",
        "paths": ["front-end/", "back-end/"],
        "priority": 1
      }
    ]
  },
  {
    "id": "fmc",
    "name": "FMC",
    "source_targets": [
      {
        "label": "FMC main (customer/fmc)",
        "repo_url": "https://git.internal/fmc.git",
        "branch": "main",
        "local_path": "/home/dev/repos/fmc",
        "paths": ["front-end/", "back-end/"],
        "priority": 1
      }
    ]
  },
  {
    "id": "nexpharm",
    "name": "넥스팜",
    "source_targets": [
      {
        "label": "넥스팜 main (customer/nexpharm)",
        "repo_url": "https://git.internal/nexpharm.git",
        "branch": "main",
        "local_path": "/home/dev/repos/nexpharm",
        "paths": ["front-end/", "back-end/"],
        "priority": 1
      }
    ]
  },
  {
    "id": "takeda",
    "name": "다케다",
    "source_targets": [
      {
        "label": "다케다 main (customer/takeda)",
        "repo_url": "https://git.internal/takeda.git",
        "branch": "main",
        "local_path": "/home/dev/repos/takeda",
        "paths": ["front-end/", "back-end/"],
        "priority": 1
      }
    ]
  },
  {
    "id": "daewoong-bio",
    "name": "대웅바이오",
    "source_targets": [
      {
        "label": "대웅바이오 main (customer/daewoong-bio)",
        "repo_url": "https://git.internal/daewoong-bio.git",
        "branch": "main",
        "local_path": "/home/dev/repos/daewoong-bio",
        "paths": ["front-end/", "back-end/"],
        "priority": 1
      }
    ]
  },
  {
    "id": "daewoong",
    "name": "대웅제약",
    "source_targets": [
      {
        "label": "대웅제약 main (customer/daewoong)",
        "repo_url": "https://git.internal/daewoong.git",
        "branch": "main",
        "local_path": "/home/dev/repos/daewoong",
        "paths": ["front-end/", "back-end/"],
        "priority": 1
      }
    ]
  },
  {
    "id": "donggu-bio",
    "name": "동구바이오",
    "source_targets": [
      {
        "label": "동구바이오 main (customer/donggu-bio)",
        "repo_url": "https://git.internal/donggu-bio.git",
        "branch": "main",
        "local_path": "/home/dev/repos/donggu-bio",
        "paths": ["front-end/", "back-end/"],
        "priority": 1
      }
    ]
  },
  {
    "id": "medtronic",
    "name": "메드트로닉",
    "source_targets": [
      {
        "label": "메드트로닉 main (customer/medtronic)",
        "repo_url": "https://git.internal/medtronic.git",
        "branch": "main",
        "local_path": "/home/dev/repos/medtronic",
        "paths": ["front-end/", "back-end/"],
        "priority": 1
      }
    ]
  },
  {
    "id": "baxter",
    "name": "박스터",
    "source_targets": [
      {
        "label": "박스터 main (customer/baxter)",
        "repo_url": "https://git.internal/baxter.git",
        "branch": "main",
        "local_path": "/home/dev/repos/baxter",
        "paths": ["front-end/", "back-end/"],
        "priority": 1
      }
    ]
  },
  {
    "id": "bd-korea",
    "name": "벡톤디킨스코리아",
    "source_targets": [
      {
        "label": "벡톤디킨스코리아 main (customer/bd-korea)",
        "repo_url": "https://git.internal/bd-korea.git",
        "branch": "main",
        "local_path": "/home/dev/repos/bd-korea",
        "paths": ["front-end/", "back-end/"],
        "priority": 1
      }
    ]
  },
  {
    "id": "boryung-consumer",
    "name": "보령컨슈머헬스케어",
    "source_targets": [
      {
        "label": "보령컨슈머헬스케어 main (customer/boryung-consumer)",
        "repo_url": "https://git.internal/boryung-consumer.git",
        "branch": "main",
        "local_path": "/home/dev/repos/boryung-consumer",
        "paths": ["front-end/", "back-end/"],
        "priority": 1
      }
    ]
  },
  {
    "id": "samil",
    "name": "삼일제약",
    "source_targets": [
      {
        "label": "삼일제약 main (customer/samil)",
        "repo_url": "https://git.internal/samil.git",
        "branch": "main",
        "local_path": "/home/dev/repos/samil",
        "paths": ["front-end/", "back-end/"],
        "priority": 1
      }
    ]
  },
  {
    "id": "sungbo",
    "name": "성보화학",
    "source_targets": [
      {
        "label": "성보화학 main (customer/sungbo)",
        "repo_url": "https://git.internal/sungbo.git",
        "branch": "main",
        "local_path": "/home/dev/repos/sungbo",
        "paths": ["front-end/", "back-end/"],
        "priority": 1
      }
    ]
  },
  {
    "id": "czbio",
    "name": "시지바이오",
    "source_targets": [
      {
        "label": "시지바이오 main (customer/czbio)",
        "repo_url": "https://git.internal/czbio.git",
        "branch": "main",
        "local_path": "/home/dev/repos/czbio",
        "paths": ["front-end/", "back-end/"],
        "priority": 1
      }
    ]
  },
  {
    "id": "shinpoong",
    "name": "신풍제약",
    "source_targets": [
      {
        "label": "신풍제약 main (customer/shinpoong)",
        "repo_url": "https://git.internal/shinpoong.git",
        "branch": "main",
        "local_path": "/home/dev/repos/shinpoong",
        "paths": ["front-end/", "back-end/"],
        "priority": 1
      }
    ]
  },
  {
    "id": "chongkundang",
    "name": "종근당",
    "source_targets": [
      {
        "label": "종근당 main (customer/chongkundang)",
        "repo_url": "https://git.internal/chongkundang.git",
        "branch": "main",
        "local_path": "/home/dev/repos/chongkundang",
        "paths": ["front-end/", "back-end/"],
        "priority": 1
      }
    ]
  },
  {
    "id": "canon-medical",
    "name": "캔논메디칼시스템즈",
    "source_targets": [
      {
        "label": "캔논메디칼시스템즈 main (customer/canon-medical)",
        "repo_url": "https://git.internal/canon-medical.git",
        "branch": "main",
        "local_path": "/home/dev/repos/canon-medical",
        "paths": ["front-end/", "back-end/"],
        "priority": 1
      }
    ]
  },
  {
    "id": "daiichi-sankyo-korea",
    "name": "한국다이이찌산쿄",
    "source_targets": [
      {
        "label": "한국다이이찌산쿄 main (customer/daiichi-sankyo-korea)",
        "repo_url": "https://git.internal/daiichi-sankyo-korea.git",
        "branch": "main",
        "local_path": "/home/dev/repos/daiichi-sankyo-korea",
        "paths": ["front-end/", "back-end/"],
        "priority": 1
      }
    ]
  },
  {
    "id": "astellas-korea",
    "name": "한국아스텔라스",
    "source_targets": [
      {
        "label": "한국아스텔라스 main (customer/astellas-korea)",
        "repo_url": "https://git.internal/astellas-korea.git",
        "branch": "main",
        "local_path": "/home/dev/repos/astellas-korea",
        "paths": ["front-end/", "back-end/"],
        "priority": 1
      }
    ]
  },
  {
    "id": "kowa-korea",
    "name": "한국코와",
    "source_targets": [
      {
        "label": "한국코와 main (customer/kowa-korea)",
        "repo_url": "https://git.internal/kowa-korea.git",
        "branch": "main",
        "local_path": "/home/dev/repos/kowa-korea",
        "paths": ["front-end/", "back-end/"],
        "priority": 1
      }
    ]
  },
  {
    "id": "handok",
    "name": "한독",
    "source_targets": [
      {
        "label": "한독 main (customer/handok)",
        "repo_url": "https://git.internal/handok.git",
        "branch": "main",
        "local_path": "/home/dev/repos/handok",
        "paths": ["front-end/", "back-end/"],
        "priority": 1
      }
    ]
  },
  {
    "id": "hanok-bio",
    "name": "한옥바이오",
    "source_targets": [
      {
        "label": "한옥바이오 main (customer/hanok-bio)",
        "repo_url": "https://git.internal/hanok-bio.git",
        "branch": "main",
        "local_path": "/home/dev/repos/hanok-bio",
        "paths": ["front-end/", "back-end/"],
        "priority": 1
      }
    ]
  },
  {
    "id": "huons",
    "name": "휴온스",
    "source_targets": [
      {
        "label": "휴온스 main (customer/huons)",
        "repo_url": "https://git.internal/huons.git",
        "branch": "main",
        "local_path": "/home/dev/repos/huons",
        "paths": ["front-end/", "back-end/"],
        "priority": 1
      }
    ]
  }
]
```

**Step 3: JSON 유효성 확인**

```bash
python -c "
import json
data = json.load(open('data/customers.json', encoding='utf-8'))
print(f'고객사 수: {len(data)}')
for c in data:
    targets = len(c.get('source_targets', []))
    print(f'  {c[\"name\"]}: source_targets {targets}개')
"
```

Expected: 고객사 수: 24, 각 고객사 이름과 source_targets 개수 출력

**Step 4: 커밋**

```bash
git add data/customers.json
git commit -m "chore: customers.json 24개 고객사 전체 데이터 등록 (local_path는 placeholder)"
```

---

## Task 3: 키워드 기반 파일 검색 엔진 구현

**예상 소요 시간:** 3일

**Files:**
- Modify: `src/code_searcher.py`
- Modify: `tests/test_code_searcher.py`

**Step 1: 실패 테스트 작성 - 검색 엔진 핵심 로직**

`tests/test_code_searcher.py`에 아래 테스트 클래스를 추가한다.

```python
# ── 파일 검색 엔진 테스트 ──────────────────────────────────────────

class TestSearchCodeCandidates:
    """임시 디렉터리를 사용하여 파일 시스템 로직을 검증한다."""

    def _make_repo(self, tmp_path: Path) -> Path:
        """테스트용 가짜 레포 구조를 생성한다."""
        repo = tmp_path / "repo"
        repo.mkdir()

        # 매칭 대상 파일
        order_vue = repo / "front-end" / "OrderList.vue"
        order_vue.parent.mkdir(parents=True)
        order_vue.write_text(
            "// 주문관리 화면\n/biz/ord/list\n주문목록", encoding="utf-8"
        )

        api_ts = repo / "back-end" / "OrderApi.ts"
        api_ts.parent.mkdir(parents=True)
        api_ts.write_text("/biz/ord/create\n/biz/ord/update", encoding="utf-8")

        # 무시해야 할 디렉터리
        node_mod = repo / "node_modules" / "lodash" / "chunk.js"
        node_mod.parent.mkdir(parents=True)
        node_mod.write_text("주문관리", encoding="utf-8")

        # 무시 확장자 파일
        png_file = repo / "front-end" / "logo.png"
        png_file.write_bytes(b"\x89PNG\r\n")

        # 크기 초과 파일 (2MB + 1byte)
        big_file = repo / "front-end" / "BigFile.java"
        big_file.write_bytes(b"주" * (2 * 1024 * 1024 + 1))

        return repo

    def test_returns_top_n_results_sorted_by_score(self, tmp_path):
        """스코어가 높은 파일이 먼저 반환된다."""
        repo = self._make_repo(tmp_path)
        results, error = search_code_candidates(
            local_path=str(repo),
            paths=["front-end/", "back-end/"],
            keywords=["주문관리", "/biz/ord"],
            top_n=10,
        )
        assert error is None
        assert len(results) >= 1
        # 첫 번째 결과가 가장 스코어가 높아야 함
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_ignores_node_modules_directory(self, tmp_path):
        """node_modules 디렉터리는 탐색에서 제외된다."""
        repo = self._make_repo(tmp_path)
        results, _ = search_code_candidates(
            local_path=str(repo),
            paths=["."],
            keywords=["주문관리"],
            top_n=10,
        )
        paths = [r["relative_path"] for r in results]
        assert not any("node_modules" in p for p in paths)

    def test_ignores_unsupported_extensions(self, tmp_path):
        """지원하지 않는 확장자(.png 등)는 결과에 포함되지 않는다."""
        repo = self._make_repo(tmp_path)
        results, _ = search_code_candidates(
            local_path=str(repo),
            paths=["."],
            keywords=["png"],
            top_n=10,
        )
        paths = [r["relative_path"] for r in results]
        assert not any(p.endswith(".png") for p in paths)

    def test_skips_files_over_2mb(self, tmp_path):
        """2MB를 초과하는 파일은 스킵한다."""
        repo = self._make_repo(tmp_path)
        results, _ = search_code_candidates(
            local_path=str(repo),
            paths=["."],
            keywords=["주"],
            top_n=10,
        )
        paths = [r["relative_path"] for r in results]
        assert not any("BigFile.java" in p for p in paths)

    def test_returns_error_when_local_path_missing(self, tmp_path):
        """local_path가 존재하지 않으면 에러 메시지를 반환한다."""
        missing_path = str(tmp_path / "nonexistent_repo")
        results, error = search_code_candidates(
            local_path=missing_path,
            paths=["."],
            keywords=["주문"],
            top_n=10,
        )
        assert results == []
        assert "로컬 경로를 찾을 수 없어요" in error

    def test_result_contains_required_fields(self, tmp_path):
        """각 결과는 relative_path, score, excerpt 필드를 포함한다."""
        repo = self._make_repo(tmp_path)
        results, _ = search_code_candidates(
            local_path=str(repo),
            paths=["."],
            keywords=["주문관리"],
            top_n=10,
        )
        assert len(results) > 0
        first = results[0]
        assert "relative_path" in first
        assert "score" in first
        assert "excerpt" in first
        assert isinstance(first["score"], int)
        assert len(first["excerpt"]) <= 200

    def test_case_insensitive_matching(self, tmp_path):
        """키워드 매칭은 대소문자를 구분하지 않는다."""
        repo = tmp_path / "repo"
        repo.mkdir()
        ts_file = repo / "Service.ts"
        ts_file.write_text("function OrderService() {}", encoding="utf-8")

        results, _ = search_code_candidates(
            local_path=str(repo),
            paths=["."],
            keywords=["orderservice"],  # 소문자로 검색
            top_n=10,
        )
        assert len(results) > 0

    def test_returns_empty_when_no_match(self, tmp_path):
        """일치하는 파일이 없으면 빈 리스트와 None을 반환한다."""
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "dummy.ts").write_text("hello world", encoding="utf-8")

        results, error = search_code_candidates(
            local_path=str(repo),
            paths=["."],
            keywords=["존재하지않는키워드xyz"],
            top_n=10,
        )
        assert results == []
        assert error is None

    def test_top_n_limits_results(self, tmp_path):
        """top_n 파라미터가 반환 개수를 제한한다."""
        repo = tmp_path / "repo"
        repo.mkdir()
        for i in range(20):
            (repo / f"file{i}.ts").write_text("주문관리", encoding="utf-8")

        results, _ = search_code_candidates(
            local_path=str(repo),
            paths=["."],
            keywords=["주문관리"],
            top_n=5,
        )
        assert len(results) <= 5
```

**Step 2: 테스트 실패 확인**

```bash
pytest tests/test_code_searcher.py::TestSearchCodeCandidates -v
```

Expected: FAIL with `ImportError: cannot import name 'search_code_candidates'`

**Step 3: search_code_candidates 구현**

`src/code_searcher.py`에 아래 내용을 추가한다.

```python
# ── 파일 검색 엔진 상수 ────────────────────────────────────────────

SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({
    ".vue", ".ts", ".tsx", ".js", ".java",
    ".xml", ".yml", ".yaml", ".sql", ".md",
    ".properties",
})

IGNORED_DIRS: frozenset[str] = frozenset({
    "node_modules", "dist", "build", "target",
    ".git", "__pycache__",
})

MAX_FILE_SIZE_BYTES: int = 2 * 1024 * 1024  # 2MB


# ── 파일 검색 엔진 ────────────────────────────────────────────────

def search_code_candidates(
    local_path: str,
    paths: list[str],
    keywords: list[str],
    top_n: int = 10,
) -> tuple[list[dict[str, Any]], str | None]:
    """키워드 기반으로 코드 후보 파일을 탐색하여 Top-N을 반환한다.

    Args:
        local_path: 레포가 클론된 로컬 디렉터리 절대 경로
        paths: 탐색할 하위 디렉터리 목록 (예: ["front-end/", "back-end/"])
        keywords: 검색 키워드 1~3개
        top_n: 반환할 최대 결과 수 (기본 10)

    Returns:
        (results, None)        - 정상 검색 (results가 빈 리스트일 수 있음)
        ([], error_message)    - local_path 미존재 등 치명적 오류
    """
    base = Path(local_path)

    if not base.exists():
        return (
            [],
            "로컬 경로를 찾을 수 없어요. "
            f"이 경로에 레포를 클론했는지 확인해 주세요: {local_path}",
        )

    # 대소문자 무시를 위해 소문자로 정규화
    normalized_keywords = [kw.lower() for kw in keywords if kw.strip()]

    if not normalized_keywords:
        return [], None

    scored: list[dict[str, Any]] = []

    # paths 목록을 기준으로 탐색 루트 결정
    search_roots = _resolve_search_roots(base, paths)

    for root_dir in search_roots:
        for dirpath, dirnames, filenames in os.walk(root_dir):
            # 무시할 디렉터리를 in-place 수정하여 os.walk가 진입하지 않도록 함
            dirnames[:] = [
                d for d in dirnames if d not in IGNORED_DIRS
            ]

            for filename in filenames:
                filepath = Path(dirpath) / filename

                # 확장자 필터링
                if filepath.suffix not in SUPPORTED_EXTENSIONS:
                    continue

                # 크기 제한
                try:
                    if filepath.stat().st_size > MAX_FILE_SIZE_BYTES:
                        continue
                except OSError:
                    continue

                # 파일 내용 읽기 및 스코어링
                try:
                    content = filepath.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue

                content_lower = content.lower()
                score = sum(
                    content_lower.count(kw) for kw in normalized_keywords
                )

                if score == 0:
                    continue

                relative_path = str(filepath.relative_to(base))
                excerpt = _extract_excerpt(content, normalized_keywords)

                scored.append({
                    "relative_path": relative_path,
                    "score": score,
                    "excerpt": excerpt,
                })

    # 스코어 내림차순 정렬 후 Top-N 슬라이싱
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_n], None


def _resolve_search_roots(base: Path, paths: list[str]) -> list[Path]:
    """paths 목록을 base 기준 절대 경로로 변환한다.

    paths가 비어 있거나 '.'이면 base 자체를 루트로 사용한다.
    존재하지 않는 경로는 무시한다.
    """
    if not paths or paths == ["."]:
        return [base]

    roots: list[Path] = []
    for p in paths:
        candidate = base / p
        if candidate.exists():
            roots.append(candidate)

    return roots if roots else [base]


def _extract_excerpt(content: str, keywords: list[str], max_len: int = 200) -> str:
    """키워드가 처음 등장하는 라인을 발췌하여 반환한다.

    Args:
        content: 파일 전체 내용
        keywords: 소문자 정규화된 키워드 목록
        max_len: 발췌 최대 길이 (문자 수)

    Returns:
        발췌 문자열 (최대 max_len자). 찾지 못하면 빈 문자열.
    """
    lines = content.splitlines()
    for line in lines:
        line_lower = line.lower()
        if any(kw in line_lower for kw in keywords):
            stripped = line.strip()
            return stripped[:max_len] if len(stripped) > max_len else stripped
    return ""
```

**Step 4: 테스트 통과 확인**

```bash
pytest tests/test_code_searcher.py -v
```

Expected: 모든 테스트 PASS

**Step 5: 커밋**

```bash
git add src/code_searcher.py tests/test_code_searcher.py
git commit -m "feat: 키워드 기반 파일 검색 엔진 구현 및 단위 테스트 통과 (TDD)"
```

---

## Task 4: 코드 후보 검색 카드 UI 구현

**예상 소요 시간:** 1.5일

**Files:**
- Modify: `app.py`

**Step 1: app.py에 코드 후보 검색 카드 렌더링 함수 추가**

`app.py`에서 `render_left_column()` 함수를 수정하여 실제 카드 UI를 추가한다.
기존 `render_left_column()`의 "코드 후보 검색" placeholder 부분을 아래 코드로 교체한다.

```python
def render_code_search_card(customers: list[dict]) -> dict | None:
    """좌측 하단 '코드 후보 검색' 카드를 렌더링하고 검색 파라미터를 반환한다.

    Returns:
        검색 파라미터 딕셔너리 (버튼 클릭 시), 또는 None
    """
    st.subheader("코드 후보 검색")
    with st.container(border=True):
        if not customers:
            st.warning(
                "customers.json을 만들어 주세요. "
                "고객사 정보가 없으면 코드 검색을 사용할 수 없어요."
            )
            return None

        # 고객사 드롭다운
        customer_names = [c["name"] for c in customers]
        selected_customer_name = st.selectbox(
            "고객사 선택",
            options=customer_names,
            key="code_search_customer",
        )

        # 선택된 고객사 정보 조회
        from src.code_searcher import get_customer_by_name
        selected_customer = get_customer_by_name(customers, selected_customer_name)
        source_targets = selected_customer.get("source_targets", []) if selected_customer else []

        # 소스 타겟 드롭다운
        if not source_targets:
            st.info("이 고객사는 소스 타겟이 설정되지 않았어요.")
            st.button(
                "추천 코드 확인하기",
                key="code_search_btn",
                disabled=True,
            )
            return None

        target_labels = [t["label"] for t in source_targets]
        selected_target_label = st.selectbox(
            "소스 타겟 선택",
            options=target_labels,
            key="code_search_target",
        )
        selected_target = next(
            (t for t in source_targets if t["label"] == selected_target_label),
            None,
        )

        # 키워드 입력 3개
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

        # 검색 버튼
        if st.button("추천 코드 확인하기", key="code_search_btn"):
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

**Step 2: render_left_column() 수정**

기존 placeholder를 실제 함수 호출로 교체한다.

```python
def render_left_column(customers: list[dict]) -> dict | None:
    """좌측 입력 영역을 렌더링하고 코드 검색 파라미터를 반환한다."""
    st.subheader("이슈 작성")
    with st.container(border=True):
        st.caption("이슈 정보를 입력하는 영역이에요. (Sprint 1에서 구현 예정)")
        st.info("여기에 Tracker, Status, 고객사, 에러 내용 등을 입력하게 될 거예요.")

    return render_code_search_card(customers)
```

**Step 3: main() 함수에서 customers 로드 및 검색 파라미터 전달**

`main()` 함수를 수정하여 customers 데이터를 로드하고 검색 카드로 전달한다.

```python
def main() -> None:
    """버그버디 메인 앱."""
    inject_custom_css()

    # 헤더
    st.title("버그버디 - 이슈 정리 도우미")
    st.caption("안녕하세요! 버그버디가 이슈 정리를 도와드릴게요.")
    st.divider()

    # customers.json 로드
    from src.code_searcher import load_customers
    customers, customers_warning = load_customers()

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

**Step 4: 앱 실행 수동 확인**

```bash
streamlit run app.py
```

확인 항목:
- [ ] 좌측 하단에 "코드 후보 검색" 카드가 표시됨
- [ ] 고객사 드롭다운에 24개 고객사가 표시됨
- [ ] 고객사 선택 시 소스 타겟 드롭다운이 표시됨
- [ ] `source_targets`가 없는 "웹취약점 개선" 선택 시 버튼 비활성화 + 안내 메시지

**Step 5: 커밋**

```bash
git add app.py
git commit -m "feat: 코드 후보 검색 카드 UI 구현 (고객사/소스타겟 드롭다운, 키워드 입력)"
```

---

## Task 5: 검색 결과 UI 구현

**예상 소요 시간:** 1.5일

**Files:**
- Modify: `app.py`

**Step 1: render_right_column() 에 코드 후보 결과 섹션 추가**

기존 `render_right_column()` 함수를 수정하여 검색 결과를 표시한다.

```python
def render_right_column(search_params: dict | None) -> None:
    """우측 출력 영역을 렌더링한다."""
    st.subheader("결과")
    with st.container(border=True):
        st.caption("생성된 템플릿과 분석 결과가 여기에 표시돼요. (Sprint 1~2에서 구현 예정)")
        st.info("버그버디가 정리한 이슈 템플릿과 Claude 분석 결과를 확인할 수 있어요.")

    # 코드 후보 검색 결과 섹션
    if search_params is not None:
        _render_code_search_results(search_params)


def _render_code_search_results(search_params: dict) -> None:
    """코드 후보 검색 결과를 우측 하단에 렌더링한다."""
    from src.code_searcher import search_code_candidates

    st.subheader("코드 후보")

    with st.spinner("버그버디가 코드를 찾고 있어요..."):
        results, error = search_code_candidates(
            local_path=search_params["local_path"],
            paths=search_params["paths"],
            keywords=search_params["keywords"],
            top_n=12,
        )

    if error:
        st.error(f"{error}")
        return

    if not results:
        st.info(
            "키워드와 일치하는 파일을 찾지 못했어요. "
            "다른 키워드로 시도해 보세요."
        )
        return

    st.success(f"총 {len(results)}개의 후보 파일을 찾았어요.")

    for i, result in enumerate(results, start=1):
        with st.container(border=True):
            col_rank, col_path = st.columns([1, 8])
            with col_rank:
                st.markdown(f"**#{i}**")
            with col_path:
                st.markdown(f"**[Score: {result['score']}]**")

            st.code(result["relative_path"], language=None)

            if result["excerpt"]:
                st.code(result["excerpt"], language=None)
```

**Step 2: 앱 실행 수동 확인**

```bash
streamlit run app.py
```

확인 항목:
- [ ] "추천 코드 확인하기" 클릭 시 "버그버디가 코드를 찾고 있어요..." 스피너 표시
- [ ] `local_path` 미존재 시 에러 메시지 표시
- [ ] 결과 없음 시 "키워드와 일치하는 파일을 찾지 못했어요." 표시
- [ ] 결과 있음 시 `[Score: X]` + 상대 경로 + 발췌 코드 표시

**Step 3: 커밋**

```bash
git add app.py
git commit -m "feat: 코드 후보 검색 결과 UI 구현 (스코어, 경로, 발췌 코드 표시)"
```

---

## Task 6: 단위 테스트 보완 및 전체 검증

**예상 소요 시간:** 1.5일

**Files:**
- Modify: `tests/test_code_searcher.py`

**Step 1: 누락된 엣지 케이스 테스트 추가**

`tests/test_code_searcher.py`에 아래 테스트를 추가한다.

```python
class TestSearchEdgeCases:
    """추가 엣지 케이스 검증."""

    def test_ignores_dist_directory(self, tmp_path):
        """dist 디렉터리는 탐색에서 제외된다."""
        repo = tmp_path / "repo"
        (repo / "dist").mkdir(parents=True)
        (repo / "dist" / "bundle.js").write_text("주문관리", encoding="utf-8")
        (repo / "src" / "main.ts").write_text("주문관리", encoding="utf-8")
        (repo / "src").mkdir(exist_ok=True)
        (repo / "src" / "main.ts").write_text("주문관리", encoding="utf-8")

        results, _ = search_code_candidates(
            local_path=str(repo), paths=["."], keywords=["주문관리"], top_n=10
        )
        paths = [r["relative_path"] for r in results]
        assert not any("dist" in p for p in paths)

    def test_ignores_build_directory(self, tmp_path):
        """build 디렉터리는 탐색에서 제외된다."""
        repo = tmp_path / "repo"
        (repo / "build").mkdir(parents=True)
        (repo / "build" / "output.java").write_text("주문관리", encoding="utf-8")

        results, _ = search_code_candidates(
            local_path=str(repo), paths=["."], keywords=["주문관리"], top_n=10
        )
        paths = [r["relative_path"] for r in results]
        assert not any("build" in p for p in paths)

    def test_ignores_git_directory(self, tmp_path):
        """.git 디렉터리는 탐색에서 제외된다."""
        repo = tmp_path / "repo"
        (repo / ".git" / "objects").mkdir(parents=True)
        (repo / ".git" / "objects" / "commit.yml").write_text(
            "주문관리", encoding="utf-8"
        )

        results, _ = search_code_candidates(
            local_path=str(repo), paths=["."], keywords=["주문관리"], top_n=10
        )
        paths = [r["relative_path"] for r in results]
        assert not any(".git" in p for p in paths)

    def test_multiple_keywords_cumulative_score(self, tmp_path):
        """여러 키워드 모두 포함한 파일이 더 높은 스코어를 가진다."""
        repo = tmp_path / "repo"
        repo.mkdir()

        # 키워드 2개 포함
        high_score_file = repo / "high.ts"
        high_score_file.write_text(
            "주문관리\n/biz/ord", encoding="utf-8"
        )

        # 키워드 1개만 포함
        low_score_file = repo / "low.ts"
        low_score_file.write_text("주문관리", encoding="utf-8")

        results, _ = search_code_candidates(
            local_path=str(repo),
            paths=["."],
            keywords=["주문관리", "/biz/ord"],
            top_n=10,
        )

        assert len(results) >= 2
        assert results[0]["relative_path"].endswith("high.ts")

    def test_excerpt_truncated_at_200_chars(self, tmp_path):
        """발췌 텍스트가 200자를 초과하지 않는다."""
        repo = tmp_path / "repo"
        repo.mkdir()
        long_line = "주문관리 " + "x" * 300
        (repo / "long.ts").write_text(long_line, encoding="utf-8")

        results, _ = search_code_candidates(
            local_path=str(repo), paths=["."], keywords=["주문관리"], top_n=10
        )
        assert len(results) > 0
        assert len(results[0]["excerpt"]) <= 200

    def test_empty_keywords_returns_empty(self, tmp_path):
        """키워드가 없으면 빈 결과를 반환한다."""
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "file.ts").write_text("내용", encoding="utf-8")

        results, error = search_code_candidates(
            local_path=str(repo), paths=["."], keywords=[], top_n=10
        )
        assert results == []
        assert error is None


class TestLoadCustomersReturn:
    """load_customers 반환값 형식 검증."""

    def test_returns_tuple_on_success(self, tmp_path):
        """정상 로드 시 (list, None) 튜플을 반환한다."""
        customers_file = tmp_path / "customers.json"
        customers_file.write_text(
            json.dumps([{"id": "a", "name": "A사", "source_targets": []}]),
            encoding="utf-8",
        )
        result = load_customers(customers_path=str(customers_file))
        assert isinstance(result, tuple)
        customers, warning = result
        assert isinstance(customers, list)
        assert warning is None
```

**Step 2: 전체 테스트 실행**

```bash
pytest tests/test_code_searcher.py -v
```

Expected: 모든 테스트 PASS

**Step 3: 전체 테스트 커버리지 확인 (선택)**

```bash
pytest tests/test_code_searcher.py -v --tb=short
```

**Step 4: 통합 실행 최종 확인**

```bash
streamlit run app.py
```

아래 시나리오를 수동으로 검증한다.

**정상 흐름 검증:**
- [ ] `http://localhost:8501` 접속 → "코드 후보 검색" 카드 표시 확인
- [ ] 고객사 드롭다운 → "종근당" 선택 → 소스 타겟 드롭다운 표시 확인
- [ ] 소스 타겟 선택 → 키워드1: "주문관리", 키워드2: "/biz/ord" 입력
- [ ] "추천 코드 확인하기" 클릭 → 스피너 표시 → 결과 또는 미존재 메시지 표시 확인

**에러 시나리오 검증:**
- [ ] "웹취약점 개선" 선택 → 버튼 비활성화 + "소스 타겟이 설정되지 않았어요." 안내 확인
- [ ] customers.json 없을 때 → "customers.json을 만들어 주세요." 경고 확인

**Step 5: 최종 커밋**

```bash
git add tests/test_code_searcher.py
git commit -m "test: code_searcher 단위 테스트 엣지 케이스 보완"
```

---

## Playwright MCP 검증 시나리오

`streamlit run app.py` 실행 후 아래 순서로 검증한다.

### 코드 후보 검색 정상 흐름

```
1. browser_navigate → http://localhost:8501
2. browser_snapshot → "코드 후보 검색" 카드 존재 확인
3. browser_select_option → 고객사 드롭다운에서 테스트용 고객사 선택
4. browser_snapshot → 소스 타겟 드롭다운에 항목 표시 확인
5. browser_select_option → 소스 타겟 선택
6. browser_type → 키워드1 필드에 "주문관리" 입력
7. browser_type → 키워드2 필드에 "/biz/ord" 입력
8. browser_click → "추천 코드 확인하기" 버튼 클릭
9. browser_wait_for → "버그버디가 코드를 찾고 있어요" 로딩 표시
10. browser_wait_for → 결과 또는 "찾지 못했어요" 메시지
11. browser_snapshot → 후보 파일 리스트 (상대 경로 + 스코어 + 발췌) 확인
12. browser_console_messages(level: "error") → 콘솔 에러 없음
```

### customers.json 미존재 시

```
1. (data/customers.json 파일 이름 변경)
2. browser_navigate → http://localhost:8501
3. browser_snapshot → "customers.json을 만들어 주세요" 경고 확인
4. browser_snapshot → 검색 카드에 드롭다운 없음 확인
```

### local_path 미존재 시

```
1. (customers.json에 존재하지 않는 local_path 설정)
2. browser_navigate → http://localhost:8501
3. browser_select_option → 해당 고객사 선택
4. browser_click → "추천 코드 확인하기" 클릭
5. browser_wait_for → "로컬 경로를 찾을 수 없어요" 메시지 표시
6. browser_snapshot → 에러 메시지 확인
```

---

## 완료 기준 (Definition of Done)

- [ ] `customers.json`에서 고객사 목록(24개) 로드 및 드롭다운 표시
- [ ] 고객사 선택 시 `source_targets` 목록이 드롭다운에 표시됨
- [ ] 3개 키워드 입력 후 "추천 코드 확인하기" 클릭 시 Top-N 후보 파일 표시
- [ ] 각 후보에 상대 경로, 스코어(`[Score: X]`), 발췌 코드(최대 200자) 표시
- [ ] `local_path` 미존재 시 "로컬 경로를 찾을 수 없어요. 이 경로에 레포를 클론했는지 확인해 주세요." 표시
- [ ] `source_targets`가 없는 고객사 선택 시 버튼 비활성화 + "이 고객사는 소스 타겟이 설정되지 않았어요." 안내
- [ ] `customers.json` 미존재 시 "customers.json을 만들어 주세요." 경고 표시
- [ ] `pytest tests/test_code_searcher.py` 전체 통과

---

## 의존성 및 리스크

| 항목 | 내용 |
|------|------|
| **외부 의존성** | 없음 (표준 라이브러리 `os`, `pathlib`, `json`만 사용) |
| **리스크 1** | 대규모 레포(수만 파일) 탐색 시 수 초 이상 소요 가능 → `paths`로 범위를 제한하고, 향후 타임아웃을 추가하는 것으로 완화 |
| **리스크 2** | Windows 경로 구분자 차이(`\` vs `/`) → `pathlib.Path` 사용으로 완화 |
| **리스크 3** | 파일 인코딩 다양성(EUC-KR 등) → `errors='ignore'`로 읽기 실패 방지 |
| **리스크 4** | Sprint 1/2 UI와 `app.py`에서 충돌 가능 → 함수 분리(render_code_search_card)로 격리 |

---

## 기술 고려사항

- `os.walk`에서 `dirnames[:] = [...]` 패턴을 사용해야 무시 디렉터리를 실제로 건너뛸 수 있음 (`dirnames = [...]`는 로컬 변수 재할당으로 효과 없음)
- `pathlib.Path.relative_to(base)`는 `base` 외부 경로를 전달하면 `ValueError`를 발생시킴 → `_resolve_search_roots()`에서 base 내부 경로만 사용하여 예방
- Streamlit의 `st.session_state`를 사용하면 검색 결과를 재계산 없이 유지할 수 있으나, v1에서는 단순성 우선으로 적용하지 않음
- `st.button` 클릭 후 Streamlit이 페이지를 재렌더링하므로, 검색 파라미터를 반환값으로 넘겨 `render_right_column()`에서 처리하는 패턴을 사용

---

## 예상 산출물

Sprint 3 완료 시 추가/변경되는 파일 구조는 아래와 같다.

```
Bug_buddy/
├── app.py                          # 코드 후보 검색 카드 UI + 결과 표시 추가
├── data/
│   └── customers.json              # 24개 고객사 전체 데이터 (local_path placeholder)
├── src/
│   └── code_searcher.py            # 로더 + 검색 엔진 완성
└── tests/
    └── test_code_searcher.py       # TDD 기반 단위 테스트 전체
```
