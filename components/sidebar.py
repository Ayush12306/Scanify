"""Branded sidebar navigation and application styling."""
import streamlit as st

NAV_ITEMS = ["Dashboard", "New Scan", "Batch Scanning", "Document History", "OCR Text Extraction", "About Scanify", "Settings"]


def apply_styles() -> None:
    st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
    :root { --ink:#17233b; --muted:#75819a; --accent:#536dfe; --line:#e7eaf1; }
    html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
    .stApp { background:#f6f7fb; }
    [data-testid="stSidebar"] { background:#121b2c; border-right:0; }
    [data-testid="stSidebar"] * { color:#e7ebf4; }
    [data-testid="stSidebar"] .stRadio label { padding:9px 10px; border-radius:9px; }
    [data-testid="stSidebar"] .stRadio label:hover { background:#202c42; }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color:#aab5c9; }
    h1,h2,h3 { font-family:'Manrope',sans-serif!important; color:var(--ink); letter-spacing:-.025em; }
    .hero { padding:24px 28px; background:#fff; border:1px solid var(--line); border-radius:18px; box-shadow:0 6px 24px #17233b08; margin-bottom:18px; }
    .eyebrow { color:#536dfe; font-weight:700; font-size:.75rem; letter-spacing:.12em; text-transform:uppercase; }
    .metric-card { background:#fff; border:1px solid var(--line); border-radius:15px; padding:18px 20px; box-shadow:0 5px 18px #17233b07; min-height:112px; }
    .metric-label { color:#75819a; font-size:.85rem; margin-bottom:8px; }
    .metric-value { color:#17233b; font-family:'Manrope',sans-serif; font-size:1.75rem; font-weight:800; }
    .soft-card { background:#fff; border:1px solid var(--line); border-radius:16px; padding:20px; margin:10px 0; }
    .stButton>button, .stDownloadButton>button { border-radius:10px; font-weight:650; min-height:2.55rem; }
    .stButton>button[kind="primary"] { background:#536dfe; border-color:#536dfe; }
    [data-testid="stFileUploader"] { background:#fff; border-radius:14px; }
    [data-testid="stImage"] { border-radius:12px; overflow:hidden; }
    footer { visibility:hidden; }
    @media(max-width:700px){ .hero{padding:18px}.metric-card{min-height:90px;padding:14px} }
    </style>""", unsafe_allow_html=True)


def render_sidebar() -> str:
    with st.sidebar:
        st.markdown("<div style='padding:8px 8px 22px'><div style='display:flex;align-items:center;gap:11px'><div style='width:40px;height:40px;border:1px solid #536dfe;border-radius:12px;display:grid;place-items:center;color:#8da0ff;font-size:22px'>▤</div><div><div style='font-family:Manrope;font-weight:800;font-size:20px;color:white'>Scanify</div><div style='font-size:11px;color:#95a3ba'>SMART DOCUMENT SCANNER</div></div></div></div>", unsafe_allow_html=True)
        st.caption("WORKSPACE")
        selected = st.radio("Workspace", NAV_ITEMS, label_visibility="collapsed", key="navigation")
        st.divider()
        st.markdown("<div style='font-size:12px;color:#98a5ba;line-height:1.7'>Turn every document<br>into a perfect scan.</div>", unsafe_allow_html=True)
    return selected
