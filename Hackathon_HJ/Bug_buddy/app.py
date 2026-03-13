"""Bug Buddy (버그버디) - 레드마인 이슈 구조화 도우미."""

import datetime
import os

import streamlit as st
from dotenv import load_dotenv

from src.template_builder import build_template
from src.code_searcher import load_customers, get_customer_by_name, search_files
from src.redmine_client import load_trackers_with_fallback, load_statuses_with_fallback

load_dotenv()

# --- 이슈 입력 폼 상수 ---
PRIORITIES = ["낮음", "보통", "높음", "즉시"]
CATEGORIES = ["SFE", "주문,반품,수금", "지출보고"]

# Redmine API에서 동적 로드 (실패 시 fallback 사용)
_redmine_url = os.getenv("REDMINE_URL", "")
_redmine_key = os.getenv("REDMINE_API_KEY", "")
TRACKERS = load_trackers_with_fallback(_redmine_url, _redmine_key)
STATUSES = load_statuses_with_fallback(_redmine_url, _redmine_key)

# Phase 3에서 customers.json 기반으로 교체 예정
CUSTOMERS = [
    "웹취약점 개선", "DNC", "FMC", "넥스팜", "다케다", "대웅바이오", "대웅제약",
    "동구바이오", "메드트로닉", "박스터", "벡톤디킨스코리아", "보령컨슈머헬스케어",
    "삼일제약", "성보화학", "시지바이오", "신풍제약", "종근당", "캔논메디칼시스템즈",
    "한국다이이찌산쿄", "한국아스텔라스", "한국코와", "한독", "한옥바이오", "휴온스",
]

ENV_VARS = {
    "ANTHROPIC_API_KEY": "Claude 분석 기능",
    "REDMINE_URL": "레드마인 연동",
    "REDMINE_API_KEY": "레드마인 연동",
}


def check_environment() -> dict[str, bool]:
    """환경변수 설정 여부를 확인하여 {변수명: 설정됨} 딕셔너리를 반환한다."""
    return {key: bool(os.getenv(key)) for key in ENV_VARS}


def show_env_warnings(env_status: dict[str, bool]) -> None:
    """미설정 환경변수에 대해 친근한 경고 메시지를 표시한다."""
    missing = [key for key, ok in env_status.items() if not ok]
    if missing:
        msgs = [f"- **{key}** 없음 → {ENV_VARS[key]} 사용 불가" for key in missing]
        st.warning("⚠️ 일부 기능이 제한됩니다:\n" + "\n".join(msgs))


def inject_custom_css() -> None:
    """버그버디 브랜드 컬러 및 커스텀 스타일을 주입한다."""
    st.markdown(
        """
        <style>
        .stApp header { background-color: #C0392B; }
        .stButton > button[kind="primary"] {
            background-color: #C0392B;
            border-color: #C0392B;
        }
        .stButton > button[kind="primary"]:hover {
            background-color: #A93226;
            border-color: #A93226;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(
        page_title="버그버디 🐛",
        page_icon="🐛",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    inject_custom_css()

    st.title("🐛 버그버디")
    st.caption("레드마인 이슈를 빠르고 정확하게 작성하도록 도와드립니다.")

    env_status = check_environment()
    show_env_warnings(env_status)

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("이슈 작성")

        with st.form(key="issue_form"):
            # --- 메타데이터 영역 ---
            st.markdown("#### 기본 정보")

            tracker = st.selectbox("Tracker", options=TRACKERS, index=TRACKERS.index("Defect") if "Defect" in TRACKERS else 0)
            status = st.selectbox("Status", options=STATUSES, index=STATUSES.index("New") if "New" in STATUSES else 0)
            start_date = st.date_input("Start date", value=datetime.date.today())
            priority = st.selectbox("Priority", options=PRIORITIES, index=PRIORITIES.index("보통"))
            category = st.selectbox("Category", options=CATEGORIES)
            customer = st.selectbox("고객사", options=CUSTOMERS)

            # --- 상세 정보 영역 ---
            st.markdown("---")
            st.markdown("#### 상세 정보 (선택)")

            menu_name = st.text_input("메뉴명", placeholder="예: 주문관리, 반품처리")
            url_route = st.text_input("URL/라우트 (알면)", placeholder="예: /biz/ord/list")
            user_id = st.text_input("사용자 ID", placeholder="예: user_001 (이름/주민번호 입력 금지)")
            doc_key = st.text_input("문서 키/번호", placeholder="예: ORD-20260320-001")
            other_keys = st.text_input("기타 키값", placeholder="예: session_id=abc123")
            occurred_at = st.text_input("발생일시 (알면)", placeholder="예: 2026-03-20 14:30")
            browser_info = st.text_input("브라우저/앱 정보 (알면)", placeholder="예: Chrome 122, Windows 11")

            # --- 본문 영역 ---
            st.markdown("---")
            st.markdown("#### 이슈 내용")

            st.info("🔒 환자명/주민번호 등은 올리지 말아 주세요. 내부 ID로만 적어 주세요.")

            error_content = st.text_area(
                "에러 내용/이슈사항/문의내용",
                placeholder="어떤 문제가 발생했는지 자세히 적어 주세요.",
                height=120,
            )
            repro_steps = st.text_area(
                "재현 절차",
                placeholder="1. 메뉴 진입\n2. 버튼 클릭\n3. 에러 발생",
                height=100,
            )
            expected_result = st.text_area(
                "기대 결과",
                placeholder="정상 동작 시 어떤 화면이 보여야 하나요?",
                height=80,
            )
            actual_result = st.text_area(
                "실제 결과",
                placeholder="실제로 어떤 화면/동작이 나타났나요?",
                height=80,
            )
            error_log = st.text_area(
                "에러 메시지/로그 (원문)",
                placeholder="에러 팝업 문구 또는 콘솔 로그를 그대로 붙여넣어 주세요.",
                height=100,
            )

            submitted = st.form_submit_button(
                "🐛 버그버디에게 정리 부탁하기",
                type="primary",
                use_container_width=True,
            )

    with col_right:
        st.subheader("버그버디 결과")

        if submitted:
            if not error_content.strip():
                st.warning("무슨 일이 있었는지 알려주세요!")
            else:
                form_data = {
                    "tracker": tracker,
                    "status": status,
                    "start_date": str(start_date),
                    "priority": priority,
                    "category": category,
                    "customer": customer,
                    "menu_name": menu_name,
                    "url_route": url_route,
                    "user_id": user_id,
                    "doc_key": doc_key,
                    "other_keys": other_keys,
                    "occurred_at": occurred_at,
                    "browser_info": browser_info,
                    "error_content": error_content,
                    "repro_steps": repro_steps,
                    "expected_result": expected_result,
                    "actual_result": actual_result,
                    "error_log": error_log,
                }

                template_text = build_template(form_data)
                st.session_state["template_text"] = template_text

                st.success("템플릿이 생성됐어요! 아래 내용을 레드마인에 붙여넣어 주세요.")
                st.subheader("📋 레드마인 Description 템플릿")
                st.code(template_text, language="markdown")

                # --- 코드 후보 검색 (Sprint 3) ---
                st.divider()
                st.subheader("🔍 관련 코드 파일 추천")
                customers_data, _ = load_customers("data/customers.json")
                selected_customer = get_customer_by_name(customers_data, customer)

                if not selected_customer or not selected_customer.get("local_path"):
                    st.info("💡 data/customers.json에 고객사 local_path를 설정하면 관련 코드 파일을 추천해드려요.")
                else:
                    keyword_input = st.text_input(
                        "검색 키워드 (쉼표로 구분)",
                        placeholder="예: login, authenticate, token",
                        key="search_keywords",
                    )
                    if st.button("🔎 추천 코드 확인하기", use_container_width=True):
                        keywords = [k.strip() for k in keyword_input.split(",") if k.strip()]
                        if not keywords:
                            st.warning("키워드를 입력해 주세요.")
                        else:
                            local_path = selected_customer["local_path"]
                            paths = selected_customer.get("paths", [""])
                            with st.spinner("코드 파일을 검색하고 있어요..."):
                                results, err = search_files(local_path, paths, keywords, top_n=12)
                            if err:
                                st.error(f"검색 오류: {err}")
                            elif not results:
                                st.info("매칭되는 파일을 찾지 못했어요.")
                            else:
                                st.success(f"{len(results)}개 파일을 찾았어요.")
                                for r in results:
                                    with st.expander(f"📄 {r['path'].split('/')[-1]}  (점수: {r['score']})"):
                                        st.caption(r["path"])
                                        st.code(r["excerpt"], language="java")
        else:
            st.markdown(
                "왼쪽에서 이슈 정보를 입력하고\n"
                "**🐛 버그버디에게 정리 부탁하기** 버튼을 눌러 주세요."
            )


if __name__ == "__main__":
    main()
