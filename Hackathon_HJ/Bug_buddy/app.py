"""버그버디 - 이슈 정리 도우미."""
import os
import json
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
st.set_page_config(page_title="버그버디", page_icon="🐛", layout="wide", initial_sidebar_state="collapsed")

def load_customers() -> list:
    customers_path = Path("data/customers.json")
    if not customers_path.exists():
        return []
    try:
        with open(customers_path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []

def inject_custom_css() -> None:
    st.markdown("""
        <style>
        .stButton>button { border-radius: 12px; background-color: #C0392B; color: white; border: none; font-weight: bold; }
        .stButton>button:hover { background-color: #A93226; color: white; }
        .block-container { padding: 1.5rem; }
        h1 { color: #C0392B; }
        h2, h3 { color: #922B21; }
        hr { border-color: #F5B7B1; }
        </style>""", unsafe_allow_html=True)

def check_environment() -> dict:
    return {
        "anthropic_api_key": bool(os.getenv("ANTHROPIC_API_KEY")),
        "redmine_base_url": bool(os.getenv("REDMINE_BASE_URL")),
        "redmine_api_key": bool(os.getenv("REDMINE_API_KEY")),
        "customers_json": Path("data/customers.json").exists(),
    }

def show_env_warnings(env_status: dict) -> None:
    warnings = []
    if not env_status["anthropic_api_key"]:
        warnings.append("⚠️ Claude API 키가 설정되지 않았어요. .env 파일에 ANTHROPIC_API_KEY를 추가해 주세요.")
    if not env_status["redmine_base_url"] or not env_status["redmine_api_key"]:
        warnings.append("⚠️ Redmine 연동 설정이 아직 안 되어 있어요. 템플릿 복붙만 사용할 수 있어요.")
    if not env_status["customers_json"]:
        warnings.append("⚠️ customers.json을 만들어 주세요. 코드 후보 검색 기능을 사용하려면 data/customers.json이 필요해요.")
    if warnings:
        with st.expander("아직 설정이 안 된 부분이 있어요 - 클릭해서 확인하기", expanded=True):
            for msg in warnings:
                st.warning(msg)

def render_left_column() -> None:
    st.subheader("📝 이슈 작성")
    with st.container(border=True):
        st.caption("이슈 정보를 입력하는 영역이에요. (Sprint 1에서 구현 예정)")
        st.info("여기에 Tracker, Status, 고객사, 에러 내용 등을 입력하게 될 거예요.")
    st.subheader("🔍 코드 후보 검색")
    with st.container(border=True):
        st.caption("키워드로 관련 코드를 찾는 영역이에요. (Sprint 3에서 구현 예정)")
        st.info("고객사와 키워드를 입력하면 관련 파일을 추천해 드릴게요.")

def render_right_column() -> None:
    st.subheader("📋 결과")
    with st.container(border=True):
        st.caption("생성된 템플릿과 분석 결과가 여기에 표시돼요. (Sprint 1~2에서 구현 예정)")
        st.info("버그버디가 정리한 이슈 템플릿과 Claude 분석 결과를 확인할 수 있어요.")

def main() -> None:
    inject_custom_css()
    st.title("🐛 버그버디 - 이슈 정리 도우미")
    st.caption("안녕하세요! 버그버디가 이슈 정리를 도와드릴게요.")
    st.divider()
    env_status = check_environment()
    show_env_warnings(env_status)
    left_col, right_col = st.columns([1, 1])
    with left_col:
        render_left_column()
    with right_col:
        render_right_column()

main()
