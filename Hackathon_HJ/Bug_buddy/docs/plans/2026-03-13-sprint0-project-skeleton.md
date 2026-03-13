# Sprint 0 구현 계획: 프로젝트 스켈레톤

**날짜:** 2026-03-13
**스프린트:** Sprint 0
**목표:** Streamlit 앱이 `localhost:8501`에서 정상 구동되며, 좌/우 레이아웃 셸과 버그버디 테마가 적용된 빈 페이지를 확인할 수 있다.

---

## Task 목록

1. 프로젝트 기본 구조 생성
2. customers.json 스키마 및 샘플 데이터 (TDD)
3. Streamlit 앱 기본 셸 (app.py)
4. 환경 설정 검증 및 경고 로직
5. 버그버디 테마 적용

---

## Task 1: 프로젝트 기본 구조 생성

- `requirements.txt`
- `.env.example`
- `.gitignore`
- `src/__init__.py`
- `src/template_builder.py`
- `src/claude_analyzer.py`
- `src/code_searcher.py`
- `src/redmine_client.py`
- `tests/__init__.py`

커밋: `chore: 프로젝트 구조 및 의존성 초기 설정`

## Task 2: customers.json 스키마 및 샘플 데이터 (TDD)

1. `tests/test_customers_schema.py` 작성
2. `pytest tests/test_customers_schema.py -v` → FAIL 확인
3. `data/customers.json` 작성
4. `pytest tests/test_customers_schema.py -v` → 3 PASSED 확인

커밋: `feat: customers.json 초기 스키마 및 샘플 데이터 추가`

## Task 3: Streamlit 앱 기본 셸

- `app.py` 작성 (좌/우 레이아웃)

커밋: `feat: Streamlit 기본 셸 및 좌/우 레이아웃 구현`

## Task 4: 환경 설정 검증 및 경고 로직

- `app.py`에 `check_environment()`, `show_env_warnings()` 추가
- `main()`에 호출 추가

커밋: `feat: 환경 설정 검증 및 친근한 경고 메시지 표시 로직 추가`

## Task 5: 버그버디 테마 적용

- `.streamlit/config.toml` 생성
- `app.py`에 `inject_custom_css()` 추가

커밋: `feat: 버그버디 레드 계열 테마 및 CSS 커스텀 스타일 적용`
