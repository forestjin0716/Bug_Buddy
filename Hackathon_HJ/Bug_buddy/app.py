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
    st.title("🐛 버그버디 - 이슈 정리 도우미")
    st.caption("안녕하세요! 버그버디가 이슈 정리를 도와드릴게요.")
    st.divider()
    left_col, right_col = st.columns([1, 1])
    with left_col:
        render_left_column()
    with right_col:
        render_right_column()

main()
