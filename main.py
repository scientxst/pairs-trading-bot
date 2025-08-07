"""
Pairs Trading Bot - Streamlit Delpoyed WebApp
=============================================
"""

import streamlit as st
import sys
import os
from pathlib import Path


root_path = Path(__file__).resolve().parent
sys.path.insert(0, str(root_path))
sys.path.insert(0, str(root_path / 'src'))


st.set_page_config(
    page_title="Pairs Trading Bot",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)


try:
    from src.ui.streamlit_app import run_app
    run_app()
except ImportError as e:
    st.error(f"Import Error: {str(e)}")
    st.info("Debug info:")
    st.code(f"Current working directory: {os.getcwd()}")
    st.code(f"Python path: {sys.path}")
    import os
    st.code(f"Files in current directory: {os.listdir('.')}")
    if os.path.exists('src'):
        st.code(f"Files in src: {os.listdir('src')}")
