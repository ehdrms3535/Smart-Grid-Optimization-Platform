# Streamlit 기반 SGOP 애플리케이션의 진입점이다.
from __future__ import annotations

import streamlit as st

from src.config.settings import settings


def main() -> None:
    st.set_page_config(
        page_title="SGOP",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("Smart Grid Optimization Platform")
    st.caption(f"실행 환경: {settings.sgop_env}")

    with st.sidebar:
        st.subheader("설정 정보")
        st.write(f".env 경로: `{settings.env_file}`")
        st.write(f"비밀 정보 폴더: `{settings.secrets_dir}`")
        st.write(f"비공개 데이터 폴더: `{settings.private_data_dir}`")

        st.subheader("API 키 상태")
        st.write(
            {
                "VWORLD_API_KEY": bool(settings.vworld_api_key),
                "PUBLIC_DATA_API_KEY": bool(settings.public_data_api_key),
                "OPENAI_API_KEY": bool(settings.openai_api_key),
            }
        )

    st.write("SGOP 기본 앱 화면입니다.")
    st.info("세부 기능은 pages 디렉토리의 Streamlit 페이지에서 확장합니다.")


if __name__ == "__main__":
    main()
