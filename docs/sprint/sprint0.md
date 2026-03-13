# Sprint 0: 프로젝트 스켈레톤 구현 계획

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Streamlit 앱이 `localhost:8501`에서 정상 구동되며, 좌/우 레이아웃 셸과 버그버디 테마가 적용된 빈 페이지를 확인할 수 있다.

**Architecture:** 단일 `app.py` 엔트리포인트 + `src/` 모듈 구조. Streamlit `st.columns([1, 1])` 레이아웃으로 좌측 입력/우측 출력 영역을 분리한다. `.streamlit/config.toml`로 레드 계열 테마를 적용하고, `python-dotenv`로 `.env`를 로드하여 환경 검증 로직을 구동한다.

**Tech Stack:** Python 3.x, Streamlit, python-dotenv, anthropic, requests

---

## 스프린트 정보

| 항목 | 내용 |
|------|------|
| **스프린트 번호** | Sprint 0 |
| **기간** | 2026-03-13 ~ 2026-03-20 (1주) |
| **마일스톤** | M0 - Streamlit 셸 구동 |
| **MoSCoW** | Must Have |
| **Karpathy Guideline** | Think Before Coding |
| **의존성** | 없음 (첫 번째 스프린트) |

---

## 구현 범위

### 포함 항목 (In Scope)
- 프로젝트 디렉터리 구조 전체 생성
- `customers.json` 초기 스키마 + 샘플 1건
- Streamlit 앱 기본 셸 (좌/우 레이아웃, placeholder 카드)
- 버그버디 레드 계열 테마 + CSS 커스텀
- `.env` 기반 환경 설정 검증 로직

### 제외 항목 (Out of Scope)
- 실제 이슈 입력 폼 UI (Sprint 1)
- Claude API 연동 (Sprint 2)
- 코드 후보 검색 기능 (Sprint 3)
- Redmine API 연동 (Sprint 4)

---

## Task 1: 프로젝트 구조 생성

**예상 소요 시간:** 0.5일

**Files:**
- Create: `app.py`
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `src/__init__.py`
- Create: `src/template_builder.py`
- Create: `src/claude_analyzer.py`
- Create: `src/code_searcher.py`
- Create: `src/redmine_client.py`
- Create: `data/customers.json`

**Step 1: `requirements.txt` 작성**

```
streamlit>=1.32.0
anthropic>=0.21.0
requests>=2.31.0
python-dotenv>=1.0.0
```

**Step 2: `.env.example` 작성**

```
# Anthropic Claude API
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Redmine 연동 (Phase 4에서 사용)
REDMINE_BASE_URL=https://your-redmine.internal
REDMINE_API_KEY=your_redmine_api_key_here
REDMINE_PROJECT_ID=your_project_id_here
```

**Step 3: `.gitignore` 작성**

```
# 환경 설정 (민감 정보)
.env
.streamlit/secrets.toml

# Python
__pycache__/
*.py[cod]
*.pyo
*.pyd
.Python
*.egg-info/
dist/
build/

# 가상환경
venv/
.venv/
env/

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# 로그
*.log
```

**Step 4: `src/` 디렉터리와 모듈 stub 파일 생성**

각 stub 파일에는 모듈 docstring만 작성한다.

`src/__init__.py`:
```python
"""버그버디 소스 패키지."""
```

`src/template_builder.py`:
```python
"""레드마인 Description 템플릿 생성 모듈. (Sprint 1에서 구현)"""
```

`src/claude_analyzer.py`:
```python
"""Claude API를 이용한 이슈 분석 모듈. (Sprint 2에서 구현)"""
```

`src/code_searcher.py`:
```python
"""고객사 코드 후보 파일 검색 모듈. (Sprint 3에서 구현)"""
```

`src/redmine_client.py`:
```python
"""Redmine REST API 클라이언트 모듈. (Sprint 4에서 구현)"""
```

**Step 5: 의존성 설치 확인**

```bash
pip install -r requirements.txt
```

Expected: 에러 없이 설치 완료

**Step 6: 커밋**

```bash
git add requirements.txt .env.example .gitignore src/
git commit -m "chore: 프로젝트 구조 및 의존성 초기 설정"
```

---

## Task 2: customers.json 스키마 정의

**예상 소요 시간:** 0.5일

**Files:**
- Create: `data/customers.json`

**Step 1: `data/` 디렉터리 생성 및 `customers.json` 작성**

```json
[
  {
    "id": "sample-corp",
    "name": "샘플제약",
    "source_targets": [
      {
        "label": "샘플제약 main (customer/sample-corp)",
        "repo_url": "https://git.internal/sample-corp.git",
        "branch": "main",
        "local_path": "/home/dev/repos/sample-corp",
        "paths": ["front-end/", "back-end/"],
        "priority": 1
      }
    ]
  }
]
```

**Step 2: JSON 스키마 유효성 수동 확인**

Python 인터프리터로 파싱이 정상 동작하는지 확인한다.

```bash
python -c "import json; data = json.load(open('data/customers.json')); print('OK:', data[0]['name'])"
```

Expected output: `OK: 샘플제약`

**Step 3: 커밋**

```bash
git add data/customers.json
git commit -m "chore: customers.json 초기 스키마 및 샘플 데이터 추가"
```

---

## Task 3: Streamlit 기본 셸 구현

**예상 소요 시간:** 1일

**Files:**
- Create: `app.py`

**Step 1: `app.py` 기본 구조 작성**

```python
"""버그버디 - 이슈 정리 도우미."""

import os
import json
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 페이지 설정 (반드시 첫 번째 Streamlit 호출이어야 함)
st.set_page_config(
    page_title="버그버디",
    page_icon="🐛",
    layout="wide",
    initial_sidebar_state="collapsed",
)
```

**Step 2: 환경 설정 검증 함수 추가**

`app.py`에 이어서 작성한다.

```python
def check_environment() -> dict:
    """환경 설정 상태를 확인하고 결과를 반환한다."""
    status = {
        "anthropic_api_key": bool(os.getenv("ANTHROPIC_API_KEY")),
        "redmine_base_url": bool(os.getenv("REDMINE_BASE_URL")),
        "redmine_api_key": bool(os.getenv("REDMINE_API_KEY")),
        "customers_json": Path("data/customers.json").exists(),
    }
    return status


def load_customers() -> list:
    """customers.json을 로드하여 고객사 목록을 반환한다. 실패 시 빈 리스트."""
    customers_path = Path("data/customers.json")
    if not customers_path.exists():
        return []
    try:
        with open(customers_path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []
```

**Step 3: 환경 경고 표시 함수 추가**

```python
def show_env_warnings(env_status: dict) -> None:
    """환경 설정 미완료 항목에 대해 친근한 경고를 표시한다."""
    warnings = []

    if not env_status["anthropic_api_key"]:
        warnings.append("ANTHROPIC_API_KEY가 설정되지 않았어요. Claude 분석 기능을 사용하려면 .env 파일에 추가해 주세요.")

    if not env_status["redmine_base_url"] or not env_status["redmine_api_key"]:
        warnings.append("Redmine 연동 설정이 아직 안 되어 있어요. 템플릿 복붙만 사용할 수 있어요.")

    if not env_status["customers_json"]:
        warnings.append("customers.json을 만들어 주세요. 코드 후보 검색 기능을 사용하려면 data/customers.json이 필요해요.")

    if warnings:
        with st.expander("아직 설정이 안 된 부분이 있어요 - 클릭해서 확인하기", expanded=True):
            for warning in warnings:
                st.warning(f"⚠️ {warning}")
```

**Step 4: 메인 레이아웃 함수 추가**

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


def render_right_column() -> None:
    """우측 출력 영역 placeholder를 렌더링한다."""
    st.subheader("📋 결과")
    with st.container(border=True):
        st.caption("생성된 템플릿과 분석 결과가 여기에 표시돼요. (Sprint 1~2에서 구현 예정)")
        st.info("버그버디가 정리한 이슈 템플릿과 Claude 분석 결과를 확인할 수 있어요.")


def main() -> None:
    """버그버디 메인 앱."""
    # 헤더
    st.title("🐛 버그버디 - 이슈 정리 도우미")
    st.caption("안녕하세요! 버그버디가 이슈 정리를 도와드릴게요.")
    st.divider()

    # 환경 설정 검증 및 경고 표시
    env_status = check_environment()
    show_env_warnings(env_status)

    # 좌/우 레이아웃
    left_col, right_col = st.columns([1, 1])

    with left_col:
        render_left_column()

    with right_col:
        render_right_column()


if __name__ == "__main__" or True:
    main()
```

**Step 5: 앱 실행 확인**

```bash
streamlit run app.py
```

Expected: 브라우저에서 `http://localhost:8501` 접속 시 버그버디 타이틀과 좌/우 레이아웃이 표시됨

**Step 6: 커밋**

```bash
git add app.py
git commit -m "feat: Streamlit 기본 셸 및 환경 검증 로직 구현"
```

---

## Task 4: 버그버디 테마 및 스타일 적용

**예상 소요 시간:** 1일

**Files:**
- Create: `.streamlit/config.toml`
- Modify: `app.py` (CSS 인젝션 추가)

**Step 1: `.streamlit/config.toml` 작성**

```toml
[theme]
primaryColor = "#C0392B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#FDFAFA"
textColor = "#2C2C2C"
font = "sans serif"

[server]
headless = true
```

**Step 2: CSS 커스텀 스타일 함수 추가**

`app.py`의 `main()` 함수 상단 (타이틀 출력 이전)에 CSS 인젝션을 추가한다.

```python
def inject_custom_css() -> None:
    """버그버디 커스텀 CSS를 주입한다."""
    st.markdown(
        """
        <style>
        /* 전체 폰트 및 배경 */
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }

        /* 타이틀 스타일 */
        h1 {
            color: #C0392B;
            font-size: 2rem !important;
        }

        /* 컨테이너 라운드 박스 */
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 12px !important;
            border: 1.5px solid #F5B7B1 !important;
            background-color: #FDFAFA;
            padding: 1rem;
        }

        /* 버튼 스타일 */
        .stButton > button {
            border-radius: 20px;
            background-color: #C0392B;
            color: white;
            border: none;
            font-weight: bold;
        }

        .stButton > button:hover {
            background-color: #A93226;
            color: white;
        }

        /* 경고 박스 스타일 */
        [data-testid="stAlert"] {
            border-radius: 10px;
        }

        /* 서브헤더 색상 */
        h2, h3 {
            color: #922B21;
        }

        /* 구분선 색상 */
        hr {
            border-color: #F5B7B1;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
```

**Step 3: `main()` 함수에 CSS 인젝션 호출 추가**

`main()` 함수의 가장 첫 줄에 추가한다.

```python
def main() -> None:
    """버그버디 메인 앱."""
    inject_custom_css()  # 이 줄을 추가

    # 헤더
    st.title("🐛 버그버디 - 이슈 정리 도우미")
    ...
```

**Step 4: 앱 재시작 후 테마 확인**

Streamlit은 `config.toml` 변경 시 재시작이 필요하다.

```bash
# Ctrl+C로 기존 프로세스 종료 후
streamlit run app.py
```

Expected:
- 브라우저에서 레드 계열 테마 확인
- 타이틀이 빨간색으로 표시됨
- 카드 영역이 라운드 박스로 렌더링됨

**Step 5: 커밋**

```bash
git add .streamlit/config.toml app.py
git commit -m "feat: 버그버디 레드 계열 테마 및 CSS 커스텀 스타일 적용"
```

---

## Task 5: 환경 설정 검증 로직 검증 및 마무리

**예상 소요 시간:** 0.5일

**Files:**
- Verify: `app.py` (환경 검증 로직이 Task 3에서 이미 구현됨)

**Step 1: `.env` 없이 앱 구동하여 경고 확인**

`.env` 파일이 없는 상태에서 앱을 실행한다.

```bash
# .env 파일이 없는지 확인
ls .env 2>/dev/null && echo "EXISTS" || echo "NOT FOUND"

# 앱 실행
streamlit run app.py
```

Expected: 브라우저에서 "아직 설정이 안 된 부분이 있어요" 섹션이 펼쳐진 상태로 표시됨

**Step 2: `.env` 없이 `customers.json` 제거 후 경고 확인**

```bash
# 임시로 customers.json 이름 변경
mv data/customers.json data/customers.json.bak

# 앱 실행 후 브라우저에서 경고 확인
streamlit run app.py
```

Expected: "customers.json을 만들어 주세요." 경고가 표시됨

**Step 3: customers.json 복원**

```bash
mv data/customers.json.bak data/customers.json
```

**Step 4: `pip install` 재현성 확인**

클린 환경에서 의존성 설치가 성공하는지 확인한다.

```bash
pip install -r requirements.txt
```

Expected: 에러 없이 설치 완료

**Step 5: 최종 통합 실행 확인**

```bash
streamlit run app.py
```

아래 항목을 브라우저에서 수동 확인한다.

- [ ] "🐛 버그버디 - 이슈 정리 도우미" 타이틀 표시
- [ ] 좌측 "이슈 작성" 카드 + "코드 후보 검색" 카드 렌더링
- [ ] 우측 "결과" 카드 렌더링
- [ ] 레드 계열 테마 적용 (primaryColor #C0392B)
- [ ] `.env` 미설정 시 친근한 경고 메시지 표시
- [ ] `customers.json` 미존재 시 경고 메시지 표시

**Step 6: 최종 커밋**

```bash
git add .
git commit -m "feat: Sprint 0 완료 - Streamlit 셸 구동 및 버그버디 테마 적용"
```

---

## Playwright MCP 검증 시나리오

`streamlit run app.py` 실행 후 아래 순서로 검증한다.

```
1. browser_navigate → http://localhost:8501 접속
2. browser_snapshot → "버그버디" 타이틀 텍스트 존재 확인
3. browser_snapshot → 좌측/우측 레이아웃 컬럼 렌더링 확인
4. browser_snapshot → 환경 미설정 경고 메시지 확인 (API 키 없는 상태)
5. browser_console_messages(level: "error") → 콘솔 에러 없음 확인
```

---

## 완료 기준 (Definition of Done)

- [ ] `pip install -r requirements.txt` 성공
- [ ] `streamlit run app.py` 실행 시 `localhost:8501`에서 페이지 렌더링
- [ ] 좌/우 레이아웃이 표시되고, 레드 계열 테마 적용 확인
- [ ] `.env` 미설정 시 친근한 경고 메시지 표시
- [ ] `customers.json` 미존재 시 경고 메시지 표시

---

## 의존성 및 리스크

| 항목 | 내용 |
|------|------|
| **외부 의존성** | 없음 (Claude/Redmine API는 이번 스프린트에서 미사용) |
| **리스크 1** | Streamlit 버전에 따라 `st.container(border=True)` 미지원 가능 → `streamlit>=1.32.0` 명시로 완화 |
| **리스크 2** | `.streamlit/config.toml` 테마는 앱 재시작 시에만 반영됨 → 팀원 안내 필요 |
| **리스크 3** | Windows 환경에서 파일 경로 구분자 차이 → `pathlib.Path` 사용으로 완화 |

---

## 기술 고려사항

- Streamlit의 `st.columns`는 반응형이므로 모바일에서는 세로 스택으로 전환됨
- `python-dotenv`의 `load_dotenv()`는 시스템 환경변수를 덮어쓰지 않음 (기본 동작)
- `app.py`에서 `if __name__ == "__main__" or True:` 패턴 대신 Streamlit의 기본 실행 방식을 따름 (모든 최상위 코드가 실행됨)
- CSS 인젝션(`st.markdown(..., unsafe_allow_html=True)`)은 Streamlit 내부 DOM 구조 변경 시 깨질 수 있음 → 테마 변경은 `config.toml` 우선

---

## 예상 산출물

Sprint 0 완료 시 아래 파일 구조가 완성된다.

```
Bug_buddy/
├── app.py                      # Streamlit 엔트리포인트 (셸 구현)
├── requirements.txt            # Python 의존성
├── .env.example                # 환경변수 템플릿
├── .gitignore                  # Git 제외 파일 목록
├── .streamlit/
│   └── config.toml             # 버그버디 레드 계열 테마
├── src/
│   ├── __init__.py
│   ├── template_builder.py     # stub (Sprint 1)
│   ├── claude_analyzer.py      # stub (Sprint 2)
│   ├── code_searcher.py        # stub (Sprint 3)
│   └── redmine_client.py       # stub (Sprint 4)
├── data/
│   └── customers.json          # 초기 스키마 + 샘플 1건
└── docs/
    ├── PRD.md
    ├── ROADMAP.md
    └── sprint/
        └── sprint0.md          # 이 파일
```
