import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path

st.set_page_config(layout="wide", page_title="V-CAD | 3D ULPIN")

st.markdown("""
    <style>
        header {visibility: hidden;}
        footer {visibility: hidden;}
        .block-container {
            padding-top: 0rem !important;
            padding-bottom: 0rem !important;
            padding-left: 0rem !important;
            padding-right: 0rem !important;
            max-width: 100% !important;
        }
        iframe {
            display: block;
            border: none;
            height: 100vh !important;
            width: 100vw !important;
        }
    </style>
""", unsafe_allow_html=True)

base_dir = Path(__file__).parent
html_content = (base_dir / "index.html").read_text(encoding="utf-8")
config_content = (base_dir / "config.js").read_text(encoding="utf-8")

html_content = html_content.replace('<script src="config.js"></script>', f'<script>{config_content}</script>')

components.html(html_content, height=1200, scrolling=True)
