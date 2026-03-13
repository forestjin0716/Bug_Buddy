"""Bug Buddy (버그버디) - 레드마인 이슈 구조화 도우미."""

import datetime
import os

import streamlit as st
from dotenv import load_dotenv

from src.template_builder import build_template
from src.code_searcher import load_customers, get_customer_by_name, search_files
from src.redmine_client import load_trackers_with_fallback, load_statuses_with_fallback

load_dotenv()

# --- 상수 ---
PRIORITIES = ["낮음", "보통", "높음", "즉시"]
CATEGORIES = ["SFE", "주문,반품,수금", "지출보고"]
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

_redmine_url = os.getenv("REDMINE_URL", "")
_redmine_key = os.getenv("REDMINE_API_KEY", "")
TRACKERS = load_trackers_with_fallback(_redmine_url, _redmine_key)
STATUSES = load_statuses_with_fallback(_redmine_url, _redmine_key)


def check_environment() -> dict[str, bool]:
    return {key: bool(os.getenv(key)) for key in ENV_VARS}


def inject_custom_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap');
        /* ── 전체 배경 ── */
        .stApp {
            background: linear-gradient(135deg, #fff0f5 0%, #f0f9ff 50%, #f5fff0 100%);
            font-family: 'Nunito', sans-serif;
        }

        /* ── 헤더 영역 ── */
        .stApp header {
            background: transparent !important;
        }

        /* ── 타이틀 ── */
        h1 {
            font-family: 'Nunito', sans-serif !important;
            font-weight: 800 !important;
            background: linear-gradient(135deg, #ff6b9d, #ff9a3c);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        h2, h3 {
            font-family: 'Nunito', sans-serif !important;
            font-weight: 700 !important;
            color: #e05c8a !important;
        }

        /* ── 탭 스타일 ── */
        .stTabs [data-baseweb="tab-list"] {
            background: rgba(255,255,255,0.7);
            border-radius: 20px;
            padding: 4px;
            gap: 4px;
            backdrop-filter: blur(10px);
            border: 2px solid #ffd6e7;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 16px !important;
            font-family: 'Nunito', sans-serif !important;
            font-weight: 700 !important;
            font-size: 0.95rem !important;
            color: #c084a0 !important;
            padding: 8px 20px !important;
            transition: all 0.2s ease;
        }
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #ff6b9d, #ff9a3c) !important;
            color: white !important;
            box-shadow: 0 4px 12px rgba(255,107,157,0.4) !important;
        }

        /* ── 입력 필드 ── */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stSelectbox > div > div {
            border-radius: 16px !important;
            border: 2px solid #ffd6e7 !important;
            font-family: 'Nunito', sans-serif !important;
            background: rgba(255,255,255,0.9) !important;
            transition: border-color 0.2s ease;
        }
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {
            border-color: #ff6b9d !important;
            box-shadow: 0 0 0 3px rgba(255,107,157,0.15) !important;
        }

        /* ── 버튼 ── */
        .stButton > button {
            border-radius: 20px !important;
            font-family: 'Nunito', sans-serif !important;
            font-weight: 700 !important;
            transition: all 0.2s ease !important;
            border: none !important;
        }
        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #ff6b9d, #ff9a3c) !important;
            color: white !important;
            box-shadow: 0 4px 15px rgba(255,107,157,0.4) !important;
            padding: 0.6rem 1.5rem !important;
        }
        .stButton > button[kind="primary"]:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(255,107,157,0.5) !important;
        }
        .stButton > button:not([kind="primary"]) {
            background: rgba(255,255,255,0.9) !important;
            border: 2px solid #ffd6e7 !important;
            color: #e05c8a !important;
        }
        .stButton > button:not([kind="primary"]):hover {
            background: #fff0f5 !important;
            transform: translateY(-1px) !important;
        }

        /* ── 폼 제출 버튼 ── */
        .stFormSubmitButton > button {
            background: linear-gradient(135deg, #ff6b9d, #ff9a3c) !important;
            color: white !important;
            border-radius: 20px !important;
            font-family: 'Nunito', sans-serif !important;
            font-weight: 800 !important;
            font-size: 1.05rem !important;
            padding: 0.7rem !important;
            box-shadow: 0 4px 15px rgba(255,107,157,0.4) !important;
            border: none !important;
            transition: all 0.2s ease !important;
        }
        .stFormSubmitButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(255,107,157,0.5) !important;
        }

        /* ── 카드 컨테이너 ── */
        .stForm {
            background: rgba(255,255,255,0.75) !important;
            border-radius: 24px !important;
            border: 2px solid #ffd6e7 !important;
            padding: 1.5rem !important;
            backdrop-filter: blur(10px) !important;
            box-shadow: 0 8px 32px rgba(255,107,157,0.1) !important;
        }

        /* ── 알림/경고 ── */
        .stAlert {
            border-radius: 16px !important;
            font-family: 'Nunito', sans-serif !important;
        }
        .stSuccess {
            border-left: 4px solid #6ee7b7 !important;
        }
        .stWarning {
            border-left: 4px solid #fcd34d !important;
        }
        .stInfo {
            border-left: 4px solid #93c5fd !important;
        }

        /* ── 코드 블록 ── */
        .stCodeBlock {
            border-radius: 16px !important;
            border: 2px solid #ffd6e7 !important;
        }

        /* ── expander ── */
        .streamlit-expanderHeader {
            border-radius: 12px !important;
            font-family: 'Nunito', sans-serif !important;
            font-weight: 700 !important;
            color: #e05c8a !important;
        }

        /* ── 섹션 라벨 ── */
        .stMarkdown p, .stMarkdown li {
            font-family: 'Nunito', sans-serif !important;
        }
        label {
            font-family: 'Nunito', sans-serif !important;
            font-weight: 600 !important;
            color: #b06080 !important;
        }

        /* ── 데코 파티클 배경 ── */
        .stApp::before {
            content: '';
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background-image:
                radial-gradient(circle at 20% 20%, rgba(255,182,193,0.15) 0%, transparent 50%),
                radial-gradient(circle at 80% 80%, rgba(167,243,208,0.15) 0%, transparent 50%),
                radial-gradient(circle at 80% 20%, rgba(196,181,253,0.10) 0%, transparent 40%);
            pointer-events: none;
            z-index: 0;
        }

        /* ── divider ── */
        hr {
            border-color: #ffd6e7 !important;
            margin: 1rem 0 !important;
        }

        /* ── caption ── */
        .stCaption {
            font-family: 'Nunito', sans-serif !important;
            color: #c084a0 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    """상단 히어로 섹션."""
    st.markdown(
        """
        <div style="text-align:center; padding: 1.5rem 0 0.5rem;">
            <div style="font-size:3.5rem; margin-bottom:0.2rem;">🐛✨</div>
            <h1 style="font-size:2.4rem; margin:0;">버그버디</h1>
            <p style="color:#c084a0; font-family:'Nunito',sans-serif; font-size:1.05rem; margin-top:0.4rem;">
                이슈 정리가 어려울 땐 버그버디한테 맡겨봐요 🍀
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_env_status() -> None:
    env_status = check_environment()
    missing = [f"**{k}**" for k, ok in env_status.items() if not ok]
    if missing:
        st.warning(f"⚙️ 설정 필요: {', '.join(missing)} — `.env` 파일을 확인해 주세요.")


def tab_issue_form() -> dict | None:
    """탭1: 이슈 작성 폼. 제출 시 form_data 반환, 미제출 시 None."""
    st.markdown(
        "<div style='color:#c084a0;font-family:Nunito,sans-serif;margin-bottom:1rem;'>"
        "📝 이슈 내용을 채워주시면 레드마인 템플릿을 만들어 드릴게요!</div>",
        unsafe_allow_html=True,
    )

    with st.form(key="issue_form"):
        # 기본 정보 — 2컬럼
        st.markdown("#### 🏷️ 기본 정보")
        c1, c2 = st.columns(2)
        with c1:
            tracker = st.selectbox("Tracker", TRACKERS, index=TRACKERS.index("Defect") if "Defect" in TRACKERS else 0)
            priority = st.selectbox("Priority", PRIORITIES, index=PRIORITIES.index("보통"))
            category = st.selectbox("Category", CATEGORIES)
        with c2:
            status = st.selectbox("Status", STATUSES, index=STATUSES.index("New") if "New" in STATUSES else 0)
            start_date = st.date_input("Start date", value=datetime.date.today())
            customer = st.selectbox("고객사", CUSTOMERS)

        st.divider()

        # 상세 정보 — 2컬럼
        st.markdown("#### 🔍 상세 정보 <span style='color:#c084a0;font-size:0.85rem'>(선택)</span>", unsafe_allow_html=True)
        c3, c4 = st.columns(2)
        with c3:
            menu_name   = st.text_input("메뉴명", placeholder="예: 주문관리")
            url_route   = st.text_input("URL/라우트", placeholder="예: /biz/ord/list")
            user_id     = st.text_input("사용자 ID", placeholder="이름/주민번호 입력 금지!")
            doc_key     = st.text_input("문서 키/번호", placeholder="예: ORD-20260320-001")
        with c4:
            other_keys  = st.text_input("기타 키값", placeholder="예: session_id=abc123")
            occurred_at = st.text_input("발생일시", placeholder="예: 2026-03-20 14:30")
            browser_info= st.text_input("브라우저/앱 정보", placeholder="예: Chrome 122")

        st.divider()

        # 이슈 본문
        st.markdown("#### 💬 이슈 내용")
        st.info("🔒 환자명·주민번호 등 개인정보는 입력하지 말아 주세요. 내부 ID만 사용해 주세요.")
        error_content   = st.text_area("에러 내용 / 이슈사항 *", placeholder="어떤 문제가 발생했나요?", height=110)
        c5, c6 = st.columns(2)
        with c5:
            repro_steps     = st.text_area("재현 절차", placeholder="1. 메뉴 진입\n2. 클릭\n3. 에러", height=100)
            expected_result = st.text_area("기대 결과", placeholder="정상이라면 어떤 화면?", height=80)
        with c6:
            actual_result   = st.text_area("실제 결과", placeholder="실제로 어떤 화면이 나왔나요?", height=100)
            error_log       = st.text_area("에러 로그 (원문)", placeholder="콘솔/팝업 오류를 붙여넣어 주세요.", height=80)

        submitted = st.form_submit_button(
            "🐛 버그버디에게 정리 부탁하기 ✨",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        if not error_content.strip():
            st.warning("😥 에러 내용을 입력해 주세요!")
            return None
        return {
            "tracker": tracker, "status": status, "start_date": str(start_date),
            "priority": priority, "category": category, "customer": customer,
            "menu_name": menu_name, "url_route": url_route, "user_id": user_id,
            "doc_key": doc_key, "other_keys": other_keys, "occurred_at": occurred_at,
            "browser_info": browser_info, "error_content": error_content,
            "repro_steps": repro_steps, "expected_result": expected_result,
            "actual_result": actual_result, "error_log": error_log,
        }
    return None


def tab_template() -> None:
    """탭2: 템플릿 결과."""
    if "template_text" not in st.session_state:
        st.markdown(
            """
            <div style="text-align:center;padding:3rem 1rem;color:#c084a0;font-family:Nunito,sans-serif;">
                <div style="font-size:3rem;margin-bottom:1rem;">📋</div>
                <p style="font-size:1.1rem;font-weight:600;">
                    먼저 <b>이슈 작성</b> 탭에서 내용을 입력하고<br>버튼을 눌러 주세요!</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    st.success("🎉 템플릿이 완성됐어요! 아래 내용을 레드마인에 붙여넣어 주세요.")
    st.code(st.session_state["template_text"], language="markdown")


def tab_claude() -> None:
    """탭3: Claude AI 분석."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "")

    if not api_key:
        st.markdown(
            """
            <div style="text-align:center;padding:2rem 1rem;color:#c084a0;font-family:Nunito,sans-serif;">
                <div style="font-size:2.5rem;margin-bottom:0.8rem;">🤖</div>
                <p style="font-weight:700;font-size:1.05rem;">ANTHROPIC_API_KEY를 설정하면<br>Claude가 이슈를 분석해드려요!</p>
                <p style="font-size:0.9rem;">.env 파일에 ANTHROPIC_API_KEY를 추가해 주세요.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    if "template_text" not in st.session_state:
        st.info("💡 이슈 작성 탭에서 먼저 템플릿을 생성해 주세요.")
        return

    if st.button("🤖 Claude에게 분석 요청하기", type="primary", use_container_width=True):
        from src.claude_analyzer import analyze_issue
        form_data = st.session_state.get("form_data", {})
        with st.spinner("🌀 Claude가 열심히 분석 중이에요..."):
            analysis, err = analyze_issue(form_data, api_key=api_key)
        if err:
            st.error(f"😢 분석 중 오류가 발생했어요: {err}")
        else:
            st.session_state["analysis"] = analysis

    if "analysis" in st.session_state and st.session_state["analysis"]:
        a = st.session_state["analysis"]
        st.success(f"✅ 분석 완료! 신뢰도: {a.get('confidence', 0):.0%}")

        c1, c2 = st.columns(2)
        with c1:
            if a.get("missing_fields"):
                st.markdown("**📌 누락된 정보**")
                for f in a["missing_fields"]:
                    st.markdown(f"- {f}")
        with c2:
            if a.get("questions_to_ask"):
                st.markdown("**❓ 추가 질문**")
                for q in a["questions_to_ask"]:
                    st.markdown(f"- {q}")

        if a.get("risk_flags"):
            st.warning("⚠️ 위험 플래그: " + ", ".join(a["risk_flags"]))

        st.markdown("**💡 추천 레드마인 제목**")
        st.text_input("", value=a.get("redmine_subject", ""), key="suggested_subject", label_visibility="collapsed")

        with st.expander("🔍 원본 JSON 응답 보기"):
            import json as _json
            st.code(_json.dumps(a, ensure_ascii=False, indent=2), language="json")


def tab_code_search() -> None:
    """탭4: 코드 파일 추천."""
    customers_data, _ = load_customers("data/customers.json")

    if "form_data" not in st.session_state:
        st.info("💡 이슈 작성 탭에서 먼저 고객사를 선택하고 템플릿을 생성해 주세요.")
        return

    customer = st.session_state["form_data"].get("customer", "")
    selected = get_customer_by_name(customers_data, customer)

    if not selected or not selected.get("local_path"):
        st.markdown(
            f"""
            <div style="text-align:center;padding:2rem;color:#c084a0;font-family:Nunito,sans-serif;">
                <div style="font-size:2.5rem;margin-bottom:0.8rem;">🗂️</div>
                <p style="font-weight:700;">선택된 고객사: <b>{customer}</b></p>
                <p style="font-size:0.9rem;">data/customers.json에 local_path를 설정하면<br>관련 코드 파일을 찾아드릴 수 있어요!</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    st.markdown(f"**🏢 고객사:** {customer} &nbsp;|&nbsp; **📁 경로:** `{selected['local_path']}`")
    st.divider()

    keyword_input = st.text_input(
        "🔎 검색 키워드",
        placeholder="예: login, authenticate, session (쉼표로 구분)",
        key="search_keywords",
    )

    if st.button("✨ 추천 코드 확인하기", type="primary", use_container_width=True):
        keywords = [k.strip() for k in keyword_input.split(",") if k.strip()]
        if not keywords:
            st.warning("키워드를 1개 이상 입력해 주세요.")
        else:
            with st.spinner("🔍 코드베이스를 탐색 중이에요..."):
                results, err = search_files(
                    selected["local_path"],
                    selected.get("paths", [""]),
                    keywords,
                    top_n=12,
                )
            if err:
                st.error(f"검색 오류: {err}")
            elif not results:
                st.info("😔 매칭되는 파일을 찾지 못했어요.")
            else:
                st.success(f"🎯 {len(results)}개 파일을 찾았어요!")
                for r in results:
                    filename = r["path"].replace("\\", "/").split("/")[-1]
                    with st.expander(f"📄 **{filename}**  ·  점수 {r['score']}"):
                        st.caption(r["path"])
                        st.code(r["excerpt"], language="java")


def main() -> None:
    st.set_page_config(
        page_title="버그버디 🐛",
        page_icon="🐛",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    inject_custom_css()
    render_hero()
    render_env_status()

    st.markdown("<br>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs([
        "📝 이슈 작성",
        "📋 템플릿 결과",
        "🤖 Claude 분석",
        "🔍 코드 추천",
    ])

    with tab1:
        form_data = tab_issue_form()
        if form_data:
            template_text = build_template(form_data)
            st.session_state["template_text"] = template_text
            st.session_state["form_data"] = form_data
            st.success("✅ 템플릿 생성 완료! **템플릿 결과** 탭에서 확인하세요 🎉")

    with tab2:
        tab_template()

    with tab3:
        tab_claude()

    with tab4:
        tab_code_search()


if __name__ == "__main__":
    main()
