# 🗺️ 버그버디 프로젝트 로드맵

## 📊 프로젝트 현황 대시보드

| 항목 | 내용 |
|------|------|
| **프로젝트 목표** | 사업팀/운영팀의 레드마인 이슈를 구조화하고, 개발자가 어디를 먼저 봐야 할지 빠르게 파악하도록 돕는 내부용 도구 |
| **전체 예상 기간** | 9주 (2026-03-13 ~ 2026-05-15) |
| **현재 단계** | 📋 Phase 0 예정 |
| **전체 진행률** | 0% |
| **기술 스택** | Python 3.x, Streamlit, Anthropic Claude API, Redmine REST API |
| **팀 규모** | 소규모 2~4명 |

### 마일스톤 요약

| 마일스톤 | 목표일 | 내용 | 상태 |
|----------|--------|------|------|
| M0 | 2026-03-20 (Week 1) | Streamlit 셸 구동 | 📋 예정 |
| M1 | 2026-04-03 (Week 3) | 템플릿 생성 MVP | 📋 예정 |
| M2 | 2026-04-17 (Week 5) | Claude 지능 분석 | 📋 예정 |
| M3 | 2026-05-01 (Week 7) | 개발자 트리아지 도구 | 📋 예정 |
| M4 | 2026-05-15 (Week 9) | v1 릴리스 | 📋 예정 |

## 진행 상태 범례

- ✅ 완료
- 🔄 진행 중
- 📋 예정
- ⏸️ 보류

---

## 🏗️ 기술 아키텍처 결정 사항

| 결정 | 선택 | 이유 |
|------|------|------|
| UI 프레임워크 | Streamlit | 빠른 프로토타이핑, Python 단일 스택, 내부용 도구에 적합 |
| LLM | Anthropic Claude (텍스트 전용) | PII/PHI 리스크 최소화, 스크린샷 전송 없음 |
| 코드 검색 | 키워드 기반 단순 스코어링 | v1 범위에 적합한 구현 복잡도, 3시간 내 구현 가능 |
| Redmine 연동 | read-only REST API | 안전하고 롤백 용이, 기존 프로세스 최소 간섭 |
| 고객사 매핑 | `customers.json` 정적 파일 | DB 불필요, 운영팀이 직접 편집 가능 |
| 배포 | 내부망 직접 실행 | `streamlit run app.py`로 즉시 실행 |

---

## 🔗 의존성 맵

```
Phase 0 (프로젝트 스켈레톤)
  ├──→ Phase 1 (이슈 입력 폼 + 템플릿)  ── 프로젝트 구조 필요
  │       └──→ Phase 2 (Claude 분석)     ── 템플릿 출력이 Claude 입력
  ├──→ Phase 3 (고객사-코드 매핑)        ── customers.json 스키마 필요
  │
  └── Phase 1 + Phase 2 + Phase 3
              └──→ Phase 4 (Redmine 연동) ── 드롭다운을 API 응답으로 교체
```

---

## Phase 0: 프로젝트 스켈레톤 (Sprint 0, 1주)

> **MoSCoW**: Must Have
> **기간**: 2026-03-13 ~ 2026-03-20
> **마일스톤**: M0 - Streamlit 셸 구동

### 🎯 Karpathy Guideline: Think Before Coding
- 프로젝트 디렉터리 구조를 먼저 명시하고, 불확실한 부분은 구현 전에 질문한다.
- 가정 사항을 README나 주석에 명시한다.
- Streamlit 버전, Python 버전 등 환경 가정을 문서화한다.

### 목표
Streamlit 앱이 `localhost:8501`에서 정상 구동되며, 좌/우 레이아웃 셸과 버그버디 테마가 적용된 빈 페이지를 확인할 수 있다.

### 작업 목록

- ⬜ **프로젝트 구조 생성** (복잡도: 낮음, 0.5일)
  - `app.py` - Streamlit 엔트리포인트
  - `requirements.txt` - 의존성 목록 (streamlit, anthropic, requests, python-dotenv)
  - `.env.example` - 환경변수 템플릿 (`ANTHROPIC_API_KEY`, `REDMINE_BASE_URL`, `REDMINE_API_KEY`, `REDMINE_PROJECT_ID`)
  - `.gitignore` - `.env`, `__pycache__`, `.streamlit/secrets.toml` 등
  - `src/` 디렉터리: `__init__.py`, `template_builder.py`, `claude_analyzer.py`, `code_searcher.py`, `redmine_client.py`
  - `data/customers.json` - 초기 스키마 파일 (빈 배열 또는 샘플 1건)
  - `docs/` 디렉터리: 기존 PRD.md, ROADMAP.md

- ⬜ **customers.json 스키마 정의** (복잡도: 낮음, 0.5일)
  - 아래 스키마로 샘플 파일 생성:
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

- ⬜ **Streamlit 기본 셸 구현** (복잡도: 낮음, 1일)
  - `st.set_page_config(page_title="버그버디", page_icon="🐛", layout="wide")`
  - 좌측/우측 `st.columns([1, 1])` 레이아웃 구성
  - 좌측: "이슈 작성" 카드 영역 placeholder, "코드 후보 검색" 카드 영역 placeholder
  - 우측: "결과" 영역 placeholder

- ⬜ **버그버디 테마 및 스타일 적용** (복잡도: 낮음, 1일)
  - `.streamlit/config.toml`에 레드 계열 기본 테마 설정
  - CSS 커스텀: 라운드 박스, 부드러운 색감 (버디버디 느낌)
  - 버그버디 타이틀 헤더: "🐛 버그버디 - 이슈 정리 도우미"
  - 친근한 안내 문구: "안녕하세요! 버그버디가 이슈 정리를 도와드릴게요."

- ⬜ **환경 설정 검증 로직** (복잡도: 낮음, 0.5일)
  - `.env` 로드 (`python-dotenv`)
  - API 키 미설정 시 사이드바에 친근한 경고: "아직 설정이 안 된 부분이 있어요."
  - `customers.json` 미존재 시 경고: "customers.json을 만들어 주세요."

### 완료 기준 (Definition of Done)
- [ ] `pip install -r requirements.txt` 성공
- [ ] `streamlit run app.py` 실행 시 `localhost:8501`에서 페이지 렌더링
- [ ] 좌/우 레이아웃이 표시되고, 레드 계열 테마 적용 확인
- [ ] `.env` 미설정 시 친근한 경고 메시지 표시
- [ ] `customers.json` 미존재 시 경고 메시지 표시

### 🧪 Playwright MCP 검증 시나리오
> `streamlit run app.py` 실행 후 아래 순서로 검증

```
1. browser_navigate → http://localhost:8501 접속
2. browser_snapshot → "버그버디" 타이틀 텍스트 존재 확인
3. browser_snapshot → 좌측/우측 레이아웃 컬럼 렌더링 확인
4. browser_snapshot → 환경 미설정 경고 메시지 확인 (API 키 없는 상태)
5. browser_console_messages(level: "error") → 콘솔 에러 없음 확인
```

### 기술 고려사항
- Streamlit의 `st.columns`는 반응형이므로 모바일에서는 세로 스택으로 전환됨
- `.streamlit/config.toml`의 테마는 앱 재시작 시 적용
- `python-dotenv`로 `.env` 로드 시 시스템 환경변수와 충돌 주의

---

## Phase 1: 이슈 입력 폼 + 템플릿 생성 (Sprint 1, 2주)

> **MoSCoW**: Must Have (PRD 5.1)
> **기간**: 2026-03-20 ~ 2026-04-03
> **마일스톤**: M1 - 템플릿 생성 MVP
> **의존성**: Phase 0 완료 필요

### 🎯 Karpathy Guideline: Simplicity First
- 순수 문자열 포매팅으로 템플릿 생성. Jinja2 등 템플릿 엔진 도입하지 않는다.
- 불필요한 추상화 없이, 입력 → 문자열 조합 → 출력의 직선적 흐름.
- 단일 함수로 충분한 로직을 클래스로 감싸지 않는다.

### 목표
사업팀 담당자가 이슈 정보를 입력하고 "버그버디에게 정리 부탁하기" 버튼을 누르면, 레드마인 Description 형식의 템플릿이 생성되어 복사할 수 있다.

### 작업 목록

- ⬜ **입력 폼 UI 구현 - 메타데이터 영역** (복잡도: 중간, 1.5일)
  - Tracker 드롭다운: `Common / Feature / Defect / Request / Patch / Issue / Review`
  - Status 드롭다운: `New / Confirm / Assigned / In progress / Resolved / Closed / Need Feedback / Rejected` (기본값 New)
  - Start date: `st.date_input` (기본값 오늘)
  - Priority 드롭다운: `낮음 / 보통 / 높음 / 즉시`
  - Category 드롭다운: `SFE / 주문,반품,수금 / 지출보고`
  - 고객사 드롭다운: 24개 고객사 목록 (하드코딩, Phase 4에서 API 교체 예정)
    - `웹취약점 개선 / DNC / FMC / 넥스팜 / 다케다 / 대웅바이오 / 대웅제약 / 동구바이오 / 메드트로닉 / 박스터 / 벡톤디킨스코리아 / 보령컨슈머헬스케어 / 삼일제약 / 성보화학 / 시지바이오 / 신풍제약 / 종근당 / 캔논메디칼시스템즈 / 한국다이이찌산쿄 / 한국아스텔라스 / 한국코와 / 한독 / 한옥바이오 / 휴온스`

- ⬜ **입력 폼 UI 구현 - 상세 정보 영역** (복잡도: 중간, 1일)
  - 메뉴명: `st.text_input`
  - URL/라우트(알면): `st.text_input`
  - 사용자 ID: `st.text_input`
  - 문서 키/번호: `st.text_input`
  - 기타 키값: `st.text_input`
  - 발생일시(알면): `st.text_input` (자유 형식)
  - 브라우저/앱 정보(알면): `st.text_input`

- ⬜ **입력 폼 UI 구현 - 본문 영역** (복잡도: 중간, 1일)
  - 에러 내용/이슈사항/문의내용: `st.text_area` (멀티라인)
  - 재현 절차: `st.text_area` (멀티라인)
  - 기대 결과: `st.text_area`
  - 실제 결과: `st.text_area`
  - 에러 메시지/로그(원문): `st.text_area` (멀티라인)
  - PII 경고 안내문: "환자명/주민번호 등은 올리지 말아 주세요. 내부 ID로만 적어 주세요."

- ⬜ **템플릿 생성 함수 구현** (`src/template_builder.py`) (복잡도: 중간, 1.5일)
  - 입력 딕셔너리를 받아 레드마인 Description 문자열 반환
  - 7개 섹션 구조:
    - (1) 에러 내용/이슈사항/문의내용
    - (2) 메뉴명 / 페이지 정보
    - (3) 상세 키값
    - (4) 발생 환경/시간
    - (5) 재현 절차
    - (6) 기대 결과 vs 실제 결과
    - (7) 에러 메시지/로그(원문)
  - 빈 필드는 `입력되지 않음` placeholder로 통일
  - 순수 f-string / str.format 사용, 외부 템플릿 엔진 없음

- ⬜ **"버그버디에게 정리 부탁하기" 버튼 및 결과 표시** (복잡도: 낮음, 1일)
  - 우측 영역에 생성된 템플릿을 `st.code` 또는 `st.text_area(disabled=True)`로 표시
  - "복사하기" 기능: `st.button` + JavaScript clipboard 또는 Streamlit 내장 copy
  - 입력값 유효성 최소 검증: 에러 내용이 비어있으면 "무슨 일이 있었는지 알려주세요!" 안내

- ⬜ **단위 테스트** (복잡도: 낮음, 1일)
  - `tests/test_template_builder.py`
  - 모든 필드 입력 시 7개 섹션 모두 포함 확인
  - 빈 필드 시 `입력되지 않음` placeholder 확인
  - 특수문자/줄바꿈 포함 입력 정상 처리 확인

### 완료 기준 (Definition of Done)
- [ ] 모든 입력 필드가 Streamlit UI에 렌더링됨
- [ ] 24개 고객사가 드롭다운에 모두 표시됨
- [ ] "버그버디에게 정리 부탁하기" 클릭 시 7개 섹션의 템플릿이 우측에 표시됨
- [ ] 빈 필드는 `입력되지 않음`으로 채워짐
- [ ] 생성된 템플릿을 복사할 수 있음
- [ ] PII 경고 안내문이 입력 영역에 표시됨
- [ ] `pytest tests/test_template_builder.py` 전체 통과

### 🧪 Playwright MCP 검증 시나리오
> `streamlit run app.py` 실행 후 아래 순서로 검증

**입력 폼 렌더링 검증:**
```
1. browser_navigate → http://localhost:8501 접속
2. browser_snapshot → Tracker/Status/Priority/Category 드롭다운 존재 확인
3. browser_snapshot → 고객사 드롭다운 존재 확인
4. browser_select_option → 고객사 드롭다운에서 "대웅제약" 선택
5. browser_snapshot → 선택 반영 확인
```

**템플릿 생성 검증:**
```
1. browser_select_option → Tracker = "Defect" 선택
2. browser_select_option → Priority = "높음" 선택
3. browser_select_option → 고객사 = "종근당" 선택
4. browser_type → 메뉴명 필드에 "주문관리" 입력
5. browser_type → 에러 내용 필드에 "주문 목록 조회 시 500 에러 발생" 입력
6. browser_click → "버그버디에게 정리 부탁하기" 버튼 클릭
7. browser_wait_for → 우측 영역에 "(1) 에러 내용" 텍스트 대기
8. browser_snapshot → 7개 섹션 구조의 템플릿 출력 확인
9. browser_snapshot → 미입력 필드에 "입력되지 않음" 표시 확인
10. browser_console_messages(level: "error") → 콘솔 에러 없음 확인
```

**빈 입력 검증:**
```
1. browser_navigate → http://localhost:8501 접속 (새로고침)
2. browser_click → "버그버디에게 정리 부탁하기" 버튼 클릭
3. browser_wait_for → "무슨 일이 있었는지 알려주세요!" 메시지 대기
4. browser_snapshot → 유효성 안내 메시지 확인
```

### 기술 고려사항
- Streamlit의 `st.form`을 사용하면 입력 변경마다 리렌더링을 방지할 수 있음
- 고객사 목록은 Phase 1에서 하드코딩, Phase 4에서 Redmine API/customers.json 기반으로 교체
- 복사 기능은 Streamlit 네이티브에 한계가 있으므로 `st.code` 블록의 내장 복사 아이콘 활용 검토

---

## Phase 2: Claude 분석 + 질문 생성 (Sprint 2, 2주)

> **MoSCoW**: Must Have (PRD 5.2)
> **기간**: 2026-04-03 ~ 2026-04-17
> **마일스톤**: M2 - Claude 지능 분석
> **의존성**: Phase 1 완료 필요 (템플릿 출력이 Claude 입력으로 사용됨)

### 🎯 Karpathy Guideline: Goal-Driven Execution
- JSON 스키마를 먼저 정의하고, Claude 응답이 해당 스키마를 준수하는지 검증하는 것이 성공 기준.
- 검증 순서: (1) JSON 파싱 성공 (2) 필수 키 존재 (3) 타입 정합성 (4) confidence 범위 0.0~1.0

### 목표
생성된 템플릿을 Claude에 전달하여 누락 필드 탐지, 추가 질문 리스트, 추천 제목/Description, 리스크 플래그를 JSON으로 받아 UI에 표시한다.

### 작업 목록

- ⬜ **Claude 분석 서비스 구현** (`src/claude_analyzer.py`) (복잡도: 높음, 3일)
  - Anthropic Python SDK 사용 (`anthropic` 패키지)
  - 시스템 프롬프트 작성:
    - 역할: 소프트웨어 이슈 분석 전문가
    - PII/PHI 가이드: "주민번호/전화번호/환자명 등 PII 원문을 요구하지 말고, 마스킹된 키값이나 내부 환자 ID 형태로 요청할 것"
    - 출력 형식: JSON 고정
  - 사용자 프롬프트: 템플릿 초안 + Tracker/Status/Start date/고객사 정보
  - 응답 JSON 스키마:
    ```json
    {
      "missing_fields": ["string"],
      "questions_to_ask": ["string"],
      "redmine_subject": "string",
      "redmine_description": "string",
      "confidence": 0.0,
      "risk_flags": ["PII_POSSIBLE"]
    }
    ```
  - JSON 파싱 실패 시 최대 1회 재시도, 그래도 실패 시 에러 반환
  - 모델: `claude-3-5-sonnet-latest` (PRD 명시), `max_tokens` 적절히 설정

- ⬜ **JSON 응답 검증 로직** (복잡도: 중간, 1일)
  - 필수 키 존재 확인: `missing_fields`, `questions_to_ask`, `redmine_subject`, `redmine_description`, `confidence`, `risk_flags`
  - 타입 검증: `confidence`는 float 0.0~1.0, 나머지는 리스트/문자열
  - 검증 실패 시 기본값 fallback (빈 리스트, confidence=0.0 등)

- ⬜ **"추가로 뭐가 더 필요할지 물어보기" 버튼 및 UI** (복잡도: 중간, 2일)
  - Phase 1의 템플릿 생성 후 활성화되는 버튼
  - 클릭 시 `st.spinner("버그버디가 분석하고 있어요...")` 로딩 표시
  - 우측 결과 영역에 탭 또는 섹션으로 표시:
    - **추천 제목**: `st.text_input`으로 편집 가능하게 표시
    - **정제된 Description**: `st.text_area`로 편집 가능하게 표시 + 복사 버튼
    - **누락 필드**: `st.warning` 또는 리스트로 표시
    - **추가 질문 리스트**: 번호 매긴 리스트 + 복사 버튼
    - **신뢰도(confidence)**: `st.progress` 바 또는 텍스트
    - **리스크 플래그**: `PII_POSSIBLE` 등 배지 형태 표시
  - JSON 원본 디버그 뷰: `st.expander("디버그: JSON 원본")`로 접기/펼치기

- ⬜ **에러 처리 - LLM 호출 실패** (복잡도: 낮음, 0.5일)
  - 네트워크 에러: "지금은 버그버디가 쉬는 중이에요. 나중에 다시 시도해 주세요." + 에러 코드 표시
  - API 키 미설정: "Claude API 키가 설정되지 않았어요. .env 파일을 확인해주세요."
  - 타임아웃 (30초): "버그버디가 너무 오래 고민하고 있어요. 다시 시도해 주세요."
  - LLM 실패해도 Phase 1의 기본 템플릿은 항상 사용 가능해야 함

- ⬜ **단위 테스트 + 통합 테스트** (복잡도: 중간, 1.5일)
  - `tests/test_claude_analyzer.py`
  - Mock API 응답으로 JSON 파싱/검증 로직 테스트
  - 유효한 JSON / 잘못된 JSON / 필수 키 누락 JSON 각각 테스트
  - confidence 범위 벗어난 경우 클램핑 테스트
  - API 호출 실패 시 에러 핸들링 테스트

### 완료 기준 (Definition of Done)
- [ ] "추가로 뭐가 더 필요할지 물어보기" 클릭 시 Claude 호출 후 JSON 결과 표시
- [ ] 추천 제목/Description이 편집 가능한 필드로 표시됨
- [ ] 질문 리스트가 복사 가능한 형태로 표시됨
- [ ] 리스크 플래그(`PII_POSSIBLE` 등)가 시각적으로 구분되어 표시됨
- [ ] JSON 디버그 뷰가 expander로 제공됨
- [ ] API 키 미설정/호출 실패 시 친근한 에러 메시지 표시
- [ ] LLM 실패해도 기본 템플릿은 정상 표시
- [ ] `pytest tests/test_claude_analyzer.py` 전체 통과

### 🧪 Playwright MCP 검증 시나리오
> `streamlit run app.py` 실행 후 아래 순서로 검증 (유효한 `ANTHROPIC_API_KEY` 필요)

**Claude 분석 정상 흐름:**
```
1. browser_navigate → http://localhost:8501 접속
2. browser_select_option → Tracker = "Defect", 고객사 = "대웅제약" 선택
3. browser_type → 에러 내용 필드에 "SFE 앱에서 주문 등록 시 저장 버튼 클릭하면 화면이 멈추는 현상" 입력
4. browser_click → "버그버디에게 정리 부탁하기" 클릭
5. browser_wait_for → 템플릿 출력 대기
6. browser_click → "추가로 뭐가 더 필요할지 물어보기" 클릭
7. browser_wait_for → "버그버디가 분석하고 있어요" 로딩 표시 대기
8. browser_wait_for → 추천 제목 텍스트 출현 대기 (최대 15초)
9. browser_snapshot → 추천 제목/Description/질문 리스트/리스크 플래그 표시 확인
10. browser_click → "디버그: JSON 원본" expander 클릭
11. browser_snapshot → JSON 원본 표시 확인
12. browser_console_messages(level: "error") → 콘솔 에러 없음 확인
```

**API 키 미설정 시 에러 처리:**
```
1. (.env에서 ANTHROPIC_API_KEY 제거 또는 빈값 설정)
2. browser_navigate → http://localhost:8501 접속
3. browser_click → "추가로 뭐가 더 필요할지 물어보기" 클릭
4. browser_wait_for → "Claude API 키가 설정되지 않았어요" 메시지 대기
5. browser_snapshot → 에러 메시지 확인 + 기본 템플릿은 여전히 표시됨 확인
```

### 기술 고려사항
- Claude 응답이 JSON이 아닌 경우를 대비해 `json.loads` 예외 처리 필수
- `anthropic` SDK의 `client.messages.create` 사용, streaming은 v1에서 불필요
- 시스템 프롬프트에 JSON 출력 강제 지시를 명확히 포함
- 요청당 토큰 비용 관리: `max_tokens=2048` 정도로 제한

---

## Phase 3: 고객사-코드 매핑 + 코드 후보 검색 (Sprint 3, 2주)

> **MoSCoW**: Must Have (PRD 5.3)
> **기간**: 2026-04-17 ~ 2026-05-01
> **마일스톤**: M3 - 개발자 트리아지 도구
> **의존성**: Phase 0 완료 필요 (customers.json 스키마), Phase 1/2와 병렬 가능하나 UI 통합 시 필요

### 🎯 Karpathy Guideline: Surgical Changes
- 독립 서비스(`src/code_searcher.py`)로 구현하여 기존 코드 최소 변경.
- `app.py`에는 UI 연결 코드만 추가, 검색 로직은 모듈 내부에 격리.
- 기존 Phase 1/2 코드를 건드리지 않는다.

### 목표
개발자가 고객사와 키워드를 입력하면, 해당 고객사의 로컬 레포에서 키워드 매칭으로 코드 후보 파일 Top-N을 추천한다.

### 작업 목록

- ⬜ **customers.json 로더 구현** (`src/code_searcher.py`) (복잡도: 낮음, 0.5일)
  - `data/customers.json` 파일 로드 및 파싱
  - 파일 미존재 시: `[]` 반환 + 경고 플래그
  - 파싱 실패 시: `[]` 반환 + 에러 메시지 ("customers.json 형식을 확인해 주세요.")
  - 고객사 이름으로 조회 함수: `get_customer_by_name(name: str) -> dict | None`

- ⬜ **customers.json 실제 데이터 작성** (복잡도: 중간, 1일)
  - 24개 고객사 전체 목록을 `data/customers.json`에 등록
  - 각 고객사별 `source_targets` 정보는 팀 내부 확인 후 채움
  - 초기에는 `local_path`를 placeholder로 두고, 실제 개발 환경에서 업데이트

- ⬜ **코드 후보 검색 카드 UI** (복잡도: 중간, 1.5일)
  - 좌측 영역 하단에 "코드 후보 검색" 카드 추가
  - 고객사 드롭다운 (Phase 1과 동일 목록, `customers.json` 기반으로 전환)
  - 소스 타겟 선택 드롭다운: 선택된 고객사의 `source_targets[].label` 목록
  - 키워드 입력 3개:
    - 키워드1: 메뉴명/화면명/한글 텍스트 (`st.text_input`)
    - 키워드2: API 경로 (`st.text_input`, placeholder: `/biz/ord/...`)
    - 키워드3: 에러 코드/메시지 일부 (`st.text_input`)
  - "추천 코드 확인하기" 버튼
  - `source_targets` 없는 고객사: 버튼 비활성화 + "이 고객사는 소스 타겟이 설정되지 않았어요." 안내

- ⬜ **키워드 기반 파일 검색 엔진** (`src/code_searcher.py`) (복잡도: 높음, 3일)
  - 입력: `local_path`, `paths` (검색 범위 디렉터리), `keywords` (1~3개)
  - `local_path` 존재 확인: 미존재 시 "로컬 경로를 찾을 수 없어요. 이 경로에 레포를 클론했는지 확인해 주세요." 반환
  - 재귀 탐색 대상 확장자: `.vue`, `.ts`, `.tsx`, `.js`, `.java`, `.xml`, `.yml`, `.yaml`, `.sql`, `.md`, `.properties`
  - 무시 디렉터리: `node_modules`, `dist`, `build`, `target`, `.git`, `__pycache__`
  - 파일 크기 제한: 2MB 초과 스킵
  - 스코어링: 각 파일 내용에서 키워드 등장 횟수의 합산 (대소문자 무시)
  - 상위 N개 (기본 10~12개) 반환
  - 각 후보 결과:
    - 상대 경로 (local_path 기준)
    - 스코어
    - 키워드가 처음 등장하는 라인 내용 (발췌, 최대 200자)

- ⬜ **검색 결과 UI 표시** (복잡도: 중간, 1.5일)
  - 우측 영역 하단에 "코드 후보" 섹션 추가
  - `st.spinner("버그버디가 코드를 찾고 있어요...")`로 로딩 표시
  - 리스트형 결과:
    - `[Score: X]` + 상대 경로 (복사 가능한 `st.code` 인라인)
    - 발췌 코드를 `st.code` 블록으로 1~2줄 표시
  - 결과 없음 시: "키워드와 일치하는 파일을 찾지 못했어요. 다른 키워드로 시도해 보세요."

- ⬜ **단위 테스트** (복잡도: 중간, 1.5일)
  - `tests/test_code_searcher.py`
  - 테스트용 임시 디렉터리 구조 생성하여 검색 로직 검증
  - 확장자 필터링 정상 동작 확인
  - 무시 디렉터리 제외 확인
  - 2MB 초과 파일 스킵 확인
  - 스코어링 순서 정확성 확인
  - `local_path` 미존재 시 에러 처리 확인

### 완료 기준 (Definition of Done)
- [ ] `customers.json`에서 고객사 목록 로드 및 드롭다운 표시
- [ ] 고객사 선택 시 `source_targets` 목록이 드롭다운에 표시됨
- [ ] 3개 키워드 입력 후 "추천 코드 확인하기" 클릭 시 Top-N 후보 파일 표시
- [ ] 각 후보에 상대 경로, 스코어, 발췌 코드 표시
- [ ] `local_path` 미존재 시 친근한 에러 메시지 표시
- [ ] `source_targets` 없는 고객사는 검색 버튼 비활성화 + 안내 메시지
- [ ] `customers.json` 미존재 시 경고 메시지 표시
- [ ] `pytest tests/test_code_searcher.py` 전체 통과

### 🧪 Playwright MCP 검증 시나리오
> `streamlit run app.py` 실행 후 아래 순서로 검증 (유효한 `customers.json` 및 `local_path` 필요)

**코드 후보 검색 정상 흐름:**
```
1. browser_navigate → http://localhost:8501 접속
2. browser_snapshot → "코드 후보 검색" 카드 존재 확인
3. browser_select_option → 고객사 드롭다운에서 테스트용 고객사 선택
4. browser_snapshot → 소스 타겟 드롭다운에 항목 표시 확인
5. browser_select_option → 소스 타겟 선택
6. browser_type → 키워드1 필드에 "주문관리" 입력
7. browser_type → 키워드2 필드에 "/biz/ord" 입력
8. browser_click → "추천 코드 확인하기" 버튼 클릭
9. browser_wait_for → "버그버디가 코드를 찾고 있어요" 로딩 대기
10. browser_wait_for → 검색 결과 또는 "찾지 못했어요" 메시지 대기
11. browser_snapshot → 후보 파일 리스트 (상대 경로 + 스코어 + 발췌) 확인
12. browser_console_messages(level: "error") → 콘솔 에러 없음 확인
```

**customers.json 미존재 시:**
```
1. (data/customers.json 파일 이름 변경 또는 삭제)
2. browser_navigate → http://localhost:8501 접속
3. browser_snapshot → "customers.json을 만들어 주세요" 경고 확인
4. browser_snapshot → 코드 후보 검색 버튼 비활성화 확인
```

**local_path 미존재 시:**
```
1. (customers.json에 존재하지 않는 local_path 설정)
2. browser_navigate → http://localhost:8501 접속
3. browser_select_option → 해당 고객사 선택
4. browser_click → "추천 코드 확인하기" 클릭
5. browser_wait_for → "로컬 경로를 찾을 수 없어요" 메시지 대기
6. browser_snapshot → 에러 메시지 확인
```

### 기술 고려사항
- `os.walk`를 사용한 재귀 탐색, `pathlib`으로 경로 처리
- 파일 읽기 시 인코딩 에러 대비: `open(file, encoding='utf-8', errors='ignore')`
- 수천 개 파일 탐색 시 수 초 이내 목표 - 필요 시 `paths` 제한으로 범위 축소
- 검색 중 UI 블로킹 방지: Streamlit의 기본 동작으로 충분 (별도 비동기 불필요)

---

## Phase 4: Redmine 연동 + 통합 폴리시 (Sprint 4, 2주)

> **MoSCoW**: Should Have (PRD 5.4)
> **기간**: 2026-05-01 ~ 2026-05-15
> **마일스톤**: M4 - v1 릴리스
> **의존성**: Phase 1~3 완료 필요

### 🎯 Karpathy Guideline: Surgical Changes
- Phase 1에서 하드코딩된 Tracker/Status 목록을 Redmine API 응답으로 교체하는 것이 핵심 변경.
- 기존 코드의 다른 부분은 건드리지 않는다.
- API 실패 시 기존 하드코딩 값으로 fallback하여 동작을 보장한다.

### 목표
Redmine REST API에서 Tracker/Status 메타데이터를 읽어와 드롭다운을 동적으로 구성하고, 전체 기능을 통합 점검하여 v1을 릴리스한다.

### 작업 목록

- ⬜ **Redmine REST API 클라이언트 구현** (`src/redmine_client.py`) (복잡도: 중간, 1.5일)
  - `REDMINE_BASE_URL`, `REDMINE_API_KEY` 환경변수에서 로드
  - `get_trackers()`: `GET /trackers.json` → Tracker 목록 반환
  - `get_issue_statuses()`: `GET /issue_statuses.json` → Status 목록 반환
  - 각 API 호출: `requests.get` + `X-Redmine-API-Key` 헤더
  - 타임아웃: 5초
  - 에러 처리: 연결 실패/인증 실패/타임아웃 시 `None` 반환 + 에러 메시지

- ⬜ **Redmine 미설정 시 Fallback 로직** (복잡도: 낮음, 0.5일)
  - `REDMINE_BASE_URL` 또는 `REDMINE_API_KEY` 미설정 시:
    - "연동 설정이 아직 안 되어 있어요. 템플릿 복붙만 사용할 수 있어요." 안내
    - Phase 1의 하드코딩 Tracker/Status 목록을 그대로 사용
  - API 호출 실패 시에도 하드코딩 값으로 fallback

- ⬜ **Phase 1 드롭다운을 API 응답으로 교체** (복잡도: 중간, 1일)
  - `app.py`의 Tracker 드롭다운: Redmine API 성공 시 API 값 사용, 실패 시 기존 하드코딩 값
  - Status 드롭다운: 동일 로직
  - 각 항목에 Redmine ID를 내부적으로 매핑 (향후 이슈 생성 API 대비)
  - UI에는 이름만 표시, ID는 내부 상태로 보관

- ⬜ **Redmine 메타데이터 표시 섹션** (복잡도: 낮음, 1일)
  - 우측 영역에 "Redmine 정보" 섹션 (접기/펼치기)
  - 선택된 Tracker/Status의 이름과 ID를 표시
  - "이슈 생성 시 참고하세요" 안내
  - 향후 쓰기 기능을 위한 함수 시그니처만 정의 (`create_issue` stub)

- ⬜ **전체 통합 테스트 및 UI 폴리시** (복잡도: 중간, 2일)
  - 전체 플로우 end-to-end 수동 테스트
  - UI 일관성 점검: 모든 버튼 문구, 에러 메시지, 로딩 상태가 버그버디 톤 유지
  - 좌/우 레이아웃 정렬 및 여백 조정
  - 반응형 확인 (Streamlit 기본 반응형)
  - 에러 상태 조합 테스트:
    - Claude API 키 없음 + Redmine 설정 없음 + customers.json 없음 → 기본 템플릿만 정상 동작
    - 모든 설정 완료 → 전체 기능 정상 동작

- ⬜ **단위 테스트** (복잡도: 낮음, 1일)
  - `tests/test_redmine_client.py`
  - Mock HTTP 응답으로 Tracker/Status 파싱 테스트
  - 인증 실패 (401) 처리 테스트
  - 타임아웃 처리 테스트
  - 환경변수 미설정 시 동작 테스트

- ⬜ **README.md 및 배포 가이드** (복잡도: 낮음, 1일)
  - 설치 방법 (`pip install -r requirements.txt`)
  - `.env` 설정 가이드
  - `customers.json` 작성 가이드 (스키마 + 예시)
  - 실행 방법 (`streamlit run app.py`)
  - 주요 기능 사용법 스크린샷 또는 설명

### 완료 기준 (Definition of Done)
- [ ] Redmine API 연동 시 Tracker/Status 목록이 API에서 동적 로드됨
- [ ] Redmine 미설정 시 하드코딩 값으로 fallback + 친근한 안내 메시지
- [ ] Redmine 메타데이터 (ID + 이름) 표시 섹션 제공
- [ ] 전체 플로우 (입력 → 템플릿 → Claude 분석 → 코드 검색) 정상 동작
- [ ] 모든 에러 상태 조합에서 앱 크래시 없음
- [ ] 모든 버튼/메시지가 버그버디 톤 유지
- [ ] `pytest` 전체 테스트 통과
- [ ] README.md에 설치/설정/실행 가이드 포함

### 🧪 Playwright MCP 검증 시나리오
> `streamlit run app.py` 실행 후 아래 순서로 검증

**Redmine 연동 정상 흐름 (유효한 REDMINE 설정 필요):**
```
1. browser_navigate → http://localhost:8501 접속
2. browser_snapshot → Tracker 드롭다운에 Redmine API 기반 목록 표시 확인
3. browser_snapshot → Status 드롭다운에 Redmine API 기반 목록 표시 확인
4. browser_select_option → Tracker 선택
5. browser_select_option → Status 선택
6. browser_click → "Redmine 정보" 섹션 펼치기
7. browser_snapshot → 선택한 Tracker/Status의 ID와 이름 표시 확인
8. browser_network_requests → /trackers.json, /issue_statuses.json 호출 200 확인
```

**Redmine 미설정 시 Fallback:**
```
1. (.env에서 REDMINE_BASE_URL 제거)
2. browser_navigate → http://localhost:8501 접속
3. browser_snapshot → "연동 설정이 아직 안 되어 있어요" 메시지 확인
4. browser_snapshot → Tracker/Status 드롭다운에 하드코딩 값 표시 확인
5. browser_select_option → Tracker = "Defect" 선택 (하드코딩 값)
6. browser_click → "버그버디에게 정리 부탁하기" 클릭
7. browser_wait_for → 템플릿 정상 생성 확인
```

**전체 End-to-End 플로우:**
```
1. browser_navigate → http://localhost:8501 접속
2. browser_select_option → Tracker, Status, Priority, Category, 고객사 모두 선택
3. browser_type → 메뉴명, 에러 내용, 재현 절차 입력
4. browser_click → "버그버디에게 정리 부탁하기" 클릭
5. browser_wait_for → 템플릿 출력 대기
6. browser_snapshot → 7개 섹션 템플릿 확인
7. browser_click → "추가로 뭐가 더 필요할지 물어보기" 클릭
8. browser_wait_for → Claude 분석 결과 대기 (최대 15초)
9. browser_snapshot → 추천 제목/Description/질문 리스트/리스크 플래그 확인
10. browser_select_option → 코드 후보 검색에서 고객사/소스 타겟 선택
11. browser_type → 키워드 입력
12. browser_click → "추천 코드 확인하기" 클릭
13. browser_wait_for → 코드 후보 결과 대기
14. browser_snapshot → 전체 UI 일관성 최종 확인
15. browser_console_messages(level: "error") → 콘솔 에러 없음 확인
```

### 기술 고려사항
- Redmine API는 HTTPS 전제 (PRD 명시)
- API 키는 `.env`에서만 관리, 코드에 하드코딩 금지
- `create_issue` stub은 함수 시그니처와 docstring만 작성, 본문은 `raise NotImplementedError("v2에서 구현 예정")`
- Streamlit 캐싱(`@st.cache_data`)으로 Redmine API 호출 횟수 최소화 (TTL 5분)

---

## ⚠️ 리스크 및 완화 전략

| 리스크 | 영향도 | 발생 확률 | 완화 전략 |
|--------|--------|-----------|-----------|
| Claude API 응답이 JSON이 아닌 자유 텍스트 | 높음 | 중간 | 시스템 프롬프트에 JSON 강제 + 파싱 실패 시 1회 재시도 + fallback |
| `local_path`가 대규모 리포 → 검색 성능 저하 | 중간 | 중간 | 확장자/크기/디렉터리 필터링, `paths`로 범위 제한, 향후 타임아웃 추가 |
| Redmine API 접근 권한 미확보 | 중간 | 낮음 | Phase 4는 Should Have, 실패해도 하드코딩 fallback으로 기본 기능 유지 |
| PII/PHI가 Claude로 전송될 위험 | 높음 | 낮음 | UI 경고문, 시스템 프롬프트 가이드, 텍스트 전용 정책 |
| customers.json 유지보수 부담 | 낮음 | 중간 | 스키마 문서화, 예시 제공, 향후 관리 도구 고려 |
| Streamlit 동시 접속 성능 한계 | 낮음 | 낮음 | 내부용 소규모 사용, 문제 발생 시 다중 인스턴스 검토 |

---

## 📈 마일스톤 상세

### M0: Streamlit 셸 구동 (2026-03-20)
- Streamlit 앱이 `localhost:8501`에서 구동
- 버그버디 테마/레이아웃 적용
- 환경 설정 검증 동작

### M1: 템플릿 생성 MVP (2026-04-03)
- **사업팀이 즉시 사용 가능한 최소 기능**
- 이슈 입력 → 레드마인 Description 템플릿 복사 가능
- Claude 없이도 기본 템플릿 생성 동작

### M2: Claude 지능 분석 (2026-04-17)
- 누락 필드 탐지 + 추가 질문 리스트 생성
- 추천 제목/Description 편집 가능
- 리스크 플래그 표시

### M3: 개발자 트리아지 도구 (2026-05-01)
- 고객사별 코드 후보 파일 Top-N 추천
- 개발자가 IDE에서 바로 열 수 있는 경로 제공

### M4: v1 릴리스 (2026-05-15)
- Redmine API 연동 (read-only)
- 전체 기능 통합 + UI 폴리시
- README + 배포 가이드 완성

---

## 🔮 향후 계획 (Backlog, v2 이후)

> PRD 10장 기반. v1 릴리스 후 사용자 피드백에 따라 우선순위 결정.

| 항목 | 설명 | MoSCoW |
|------|------|--------|
| Redmine 이슈 생성/수정 API | write 연동으로 완전 자동화 | Could Have |
| 스크린샷 + Vision LLM | 화면 자동 식별/메뉴 추정 | Won't Have (v1) |
| 시맨틱 코드 검색 | 임베딩 기반 코드 인덱싱 | Could Have |
| 커밋 히스토리 분석 | "수정 후보 커밋" 제안 | Won't Have (v1) |
| 배포 히스토리 연동 | "이 배포 이후 급증한 이슈" 탐지 | Won't Have (v1) |
| 고객 포털 확장 | CS 시스템 직접 연동 | Won't Have (v1) |
| PII 자동 마스킹 | 주민번호/전화번호 패턴 자동 감지 및 마스킹 | Could Have |
| 검색 시간 제한/취소 | 대규모 리포 성능 안전장치 | Should Have |

---

## 🔧 기술 부채 관리

| 항목 | 발생 시점 | 해소 계획 |
|------|-----------|-----------|
| Tracker/Status 하드코딩 목록 | Phase 1 | Phase 4에서 API 교체 |
| 고객사 목록 하드코딩 | Phase 1 | Phase 3에서 customers.json 기반 전환 |
| Claude JSON 파싱 단순 로직 | Phase 2 | v2에서 structured output 또는 Pydantic 검증 도입 검토 |
| `create_issue` 미구현 stub | Phase 4 | v2에서 write 연동 시 구현 |
| 코드 검색 단순 키워드 매칭 | Phase 3 | v2에서 시맨틱 검색 도입 시 교체 |
