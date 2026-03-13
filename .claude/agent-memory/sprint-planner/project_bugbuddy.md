---
name: 버그버디 프로젝트 핵심 정보
description: 버그버디(Bug_buddy) 프로젝트의 기술 스택, 아키텍처, 마일스톤, 스프린트 진행 현황
type: project
---

사업팀/운영팀의 레드마인 이슈를 구조화하고, 개발자가 어디를 먼저 봐야 할지 빠르게 파악하도록 돕는 내부용 도구.

**Why:** 이슈 접수 품질 향상 + 개발자 초기 트리아지 시간 단축. 가장 중요한 지표는 "개발자가 이슈를 처음 열고 어디를 봐야 할지 결론을 내리기까지 걸리는 시간 단축".

**How to apply:** 스프린트 계획 수립 시 이 맥락을 반영하여 기능 범위와 우선순위를 결정한다.

---

## 기술 스택
- Python 3.x + Streamlit (내부망 직접 실행, `streamlit run app.py`)
- Anthropic Claude API (텍스트 전용, 스크린샷 전송 없음 - PII/PHI 리스크 최소화)
- Redmine REST API (read-only)
- python-dotenv, requests
- 고객사 매핑: `data/customers.json` 정적 파일

## 아키텍처 결정 사항
- 단일 페이지 Streamlit 앱 (좌측: 입력, 우측: 출력)
- `src/` 모듈 구조: `template_builder.py`, `claude_analyzer.py`, `code_searcher.py`, `redmine_client.py`
- 코드 검색: 키워드 기반 단순 스코어링 (v1), 시맨틱 검색은 v2
- LLM JSON 강제 출력 + 파싱 실패 시 1회 재시도 + fallback 패턴

## 전체 일정 (9주, 2026-03-13 ~ 2026-05-15)

| 마일스톤 | 스프린트 | 목표일 | 상태 |
|----------|----------|--------|------|
| M0 | Sprint 0 | 2026-03-20 | 계획 완료 (sprint0.md 작성됨) |
| M1 | Sprint 1 | 2026-04-03 | 예정 |
| M2 | Sprint 2 | 2026-04-17 | 예정 |
| M3 | Sprint 3 | 2026-05-01 | 예정 |
| M4 | Sprint 4 | 2026-05-15 | 예정 |

## 완료된 스프린트
- Sprint 0 계획 수립: 2026-03-13 (sprint0.md 작성)
- Sprint 1 계획 수립: 2026-03-13 (sprint1.md 작성)
- Sprint 2 계획 수립: 2026-03-13 (sprint2.md 작성)
- Sprint 3 계획 수립: 2026-03-13 (sprint3.md 작성)

## 수립된 스프린트 계획 파일
- `docs/sprint/sprint1.md` — Sprint 1 (2026-03-20 ~ 2026-04-03, 이슈 입력 폼 + 템플릿 생성 MVP)
- `docs/sprint/sprint2.md` — Sprint 2 (2026-04-03 ~ 2026-04-17, Claude 분석 통합)
- `docs/sprint/sprint3.md` — Sprint 3 (2026-04-17 ~ 2026-05-01, 고객사-코드 매핑 + 코드 후보 검색)

## 현재 스프린트
- Sprint 0 (2026-03-13 ~ 2026-03-20): Streamlit 셸 구동, 레드 계열 테마, 환경 검증 로직

## Sprint 1 핵심 설계 결정
- `src/template_builder.py`: 단일 함수 `build_template(data: dict) -> str` 구조
- 내부 헬퍼 `_val(data, key)`: 빈 값 → "입력되지 않음" 변환
- 7개 섹션: (1)에러내용 (2)메뉴명/페이지 (3)상세키값 (4)발생환경/시간 (5)재현절차 (6)기대vs실제 (7)에러로그
- TDD: 9개 단위 테스트 (TestBuildTemplate 클래스)
- st.form 사용으로 위젯 변경마다 리렌더링 방지
- 복사 기능: st.code 내장 복사 아이콘 활용 (외부 JS 불필요)
- 고객사 24개 하드코딩 (Phase 3에서 customers.json 전환 예정)

## Sprint 2 핵심 설계 결정
- `src/claude_analyzer.py`: `_get_client()`, `analyze_issue()`, `validate_analysis_response()` 3개 함수로 구성
- 응답 JSON 스키마: missing_fields, questions_to_ask, redmine_subject, redmine_description, confidence(float 0~1), risk_flags
- JSON 파싱 실패 시 최대 1회 재시도, 그 후 에러 반환
- 모델: `claude-3-5-sonnet-latest`, max_tokens=2048
- TDD: Mock 기반 13개 테스트 (TestValidateAnalysisResponse 7개 + TestAnalyzeIssue 6개)
- LLM 실패해도 Sprint 1 기본 템플릿은 항상 표시 (session_state 독립)

## Sprint 3 핵심 설계 결정 (2026-03-13 추가)
- `src/code_searcher.py`: `load_customers()`, `get_customer_by_name()`, `search_code_candidates()`, `_resolve_search_roots()`, `_extract_excerpt()` 5개 함수 구성
- 반환 패턴: 모든 함수가 `(result, error_or_warning)` 튜플 반환 (예외 비사용)
- 탐색 확장자 (frozenset): .vue .ts .tsx .js .java .xml .yml .yaml .sql .md .properties
- 무시 디렉터리 (frozenset): node_modules dist build target .git __pycache__
- 파일 크기 제한: 2MB (2*1024*1024 bytes) 초과 스킵
- 스코어링: 대소문자 무시 (lower() 정규화), 키워드 등장 횟수 합산
- Top-N 기본값: 12개
- TDD: pytest tmp_path 픽스처 기반 파일 시스템 테스트 (임시 디렉터리 구조 직접 생성)
- data/customers.json: 24개 고객사 전체 등록, local_path는 /home/dev/repos/{id} placeholder
- app.py: render_code_search_card() 함수로 카드 UI 격리, render_right_column()이 search_params를 받아 결과 렌더링
- os.walk에서 `dirnames[:] = [...]` 패턴 사용 필수 (로컬 재할당은 효과 없음)

## Sprint 4 핵심 설계 결정 (2026-03-13 추가)
- `src/redmine_client.py`: `_get_credentials()`, `_get()`, `get_trackers()`, `get_issue_statuses()`, `create_issue()` 함수 구성
- `src/redmine_config.py`: `get_tracker_options()`, `get_status_options()` — app.py 단일 진입점, fallback 로직 포함
- Fallback 패턴: REDMINE_BASE_URL 또는 REDMINE_API_KEY 미설정 시, 또는 API 호출 실패(401/Timeout/ConnectionError) 시 → None 반환 → FALLBACK_TRACKERS/FALLBACK_STATUSES 사용
- 안내 메시지: "연동 설정이 아직 안 되어 있어요. 템플릿 복붙만 사용할 수 있어요."
- Streamlit 캐싱: `@st.cache_data(ttl=300)` (5분) 으로 API 호출 횟수 최소화
- ID 내부 매핑: UI에는 이름만 표시 (format_func 사용), tracker_id/status_id는 session_state에 별도 보관
- create_issue stub: 함수 시그니처 + docstring + `raise NotImplementedError("v2에서 구현 예정")` 만 작성
- TDD: 21개 테스트 (TestGetTrackers 7개 + TestGetIssueStatuses 5개 + TestFallbackConstants 4개 + TestGetTrackerOptions 3개 + TestGetStatusOptions 2개)
- Surgical Changes 원칙: app.py에서 Tracker/Status 드롭다운 구성 코드 2곳만 수정

## 수립된 스프린트 계획 파일 (전체)
- `docs/sprint/sprint0.md` — Sprint 0 (2026-03-13 ~ 2026-03-20, Streamlit 셸 구동)
- `docs/sprint/sprint1.md` — Sprint 1 (2026-03-20 ~ 2026-04-03, 이슈 입력 폼 + 템플릿 생성 MVP)
- `docs/sprint/sprint2.md` — Sprint 2 (2026-04-03 ~ 2026-04-17, Claude 분석 통합)
- `docs/sprint/sprint3.md` — Sprint 3 (2026-04-17 ~ 2026-05-01, 고객사-코드 매핑 + 코드 후보 검색)
- `docs/sprint/sprint4.md` — Sprint 4 (2026-05-01 ~ 2026-05-15, Redmine 연동 + v1 릴리스) ← 2026-03-13 작성 완료
