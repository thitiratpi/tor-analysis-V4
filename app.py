import streamlit as st
import pandas as pd
import json
import re
import time
from datetime import datetime
from io import BytesIO

# Import utility modules
from utils.ai_processor import extract_scope_smart_ai, classify_scope_hybrid
from utils.file_reader import read_file_content, extract_sentences_from_tor
from utils.product_matcher import analyze_tor_sentences_full_mode
from utils.budget_engine import extract_budget_factors, calculate_budget_sheets, format_budget_report
from utils.google_sheet import load_master_data, save_to_product_spec, undo_last_update
from utils.data_validator import validate_products, check_duplicates, prepare_save_data

# ==========================================
# PAGE CONFIG
# ==========================================

st.set_page_config(
    page_title="WiseTOR Sense",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/yourusername/wisesight-streamlit',
        'Report a bug': "https://github.com/yourusername/wisesight-streamlit/issues",
        'About': "# WiseTOR Sense\nVersion 2.5.0\nPowered by Streamlit + Gemini AI"
    }
)

# ==========================================
# ENHANCED CUSTOM CSS (PROFESSIONAL THEME)
# ==========================================
st.markdown("""
<style>
    /* ===== IMPORT GOOGLE FONTS ===== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
    
    /* ===== THEME VARIABLES (Enhanced Modern Palette) ===== */
    :root {
        --primary-blue: #3B82F6;
        --primary-blue-dark: #2563EB;
        --primary-blue-light: #60A5FA;
        --accent-indigo: #6366F1;
        --accent-purple: #8B5CF6;
        
        --success-green: #10B981;
        --success-green-dark: #059669;
        --warning-amber: #F59E0B;
        --warning-amber-dark: #D97706;
        --danger-red: #EF4444;
        --danger-red-dark: #DC2626;
        
        --neutral-50: #F8FAFC;
        --neutral-100: #F1F5F9;
        --neutral-200: #E2E8F0;
        --neutral-300: #CBD5E1;
        --neutral-400: #94A3B8;
        --neutral-500: #64748B;
        --neutral-600: #475569;
        --neutral-700: #334155;
        --neutral-800: #1E293B;
        --neutral-900: #0F172A;
        
        --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
    }

    /* ===== GLOBAL TYPOGRAPHY ===== */
    .stApp {
        background: linear-gradient(135deg, #F8FAFC 0%, #EFF6FF 100%);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        color: var(--neutral-700);
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: var(--neutral-900) !important;
        font-weight: 700 !important;
        letter-spacing: -0.025em;
        line-height: 1.2;
    }
    
    /* Main Header with Gradient Text */
    .main-header {
        font-size: 3rem;
        text-align: center;
        margin-bottom: 0.5rem;
        background: linear-gradient(135deg, var(--primary-blue-dark) 0%, var(--accent-indigo) 50%, var(--accent-purple) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 900;
        letter-spacing: -0.03em;
        text-shadow: 0 2px 10px rgba(59, 130, 246, 0.1);
        animation: fadeInDown 0.6s ease-out;
    }
    
    @keyframes fadeInDown {
        from {
            opacity: 0;
            transform: translateY(-20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    /* ===== CARDS & CONTAINERS (Elevated Design) ===== */
    .custom-card {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        padding: 2rem;
        border-radius: 20px;
        border: 1px solid var(--neutral-200);
        box-shadow: var(--shadow-lg);
        margin-bottom: 1.5rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .custom-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, var(--primary-blue) 0%, var(--accent-indigo) 100%);
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    .custom-card:hover {
        transform: translateY(-4px);
        box-shadow: var(--shadow-xl);
        border-color: var(--neutral-300);
    }
    
    .custom-card:hover::before {
        opacity: 1;
    }

    .file-info-card {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.05) 0%, rgba(99, 102, 241, 0.05) 100%);
        padding: 1.75rem;
        border-radius: 16px;
        border: 2px solid var(--neutral-200);
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        transition: all 0.3s ease;
    }
    
    .file-info-card:hover {
        border-color: var(--primary-blue-light);
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.08) 0%, rgba(99, 102, 241, 0.08) 100%);
    }

    /* ===== STATISTICS DASHBOARD (Modern Glass Effect) ===== */
    .stat-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: var(--neutral-500);
        font-weight: 700;
        margin-bottom: 1rem;
        text-align: center;
        position: relative;
        padding-bottom: 0.75rem;
    }
    
    .stat-label::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 40px;
        height: 3px;
        background: linear-gradient(90deg, var(--primary-blue) 0%, var(--accent-indigo) 100%);
        border-radius: 2px;
    }
    
    .stat-value-big {
        font-size: 3rem;
        font-weight: 900;
        background: linear-gradient(135deg, var(--primary-blue) 0%, var(--accent-indigo) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        line-height: 1;
        letter-spacing: -0.02em;
    }

    /* Professional List Row Style */
    .stat-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px 16px;
        border-bottom: 1px solid var(--neutral-100);
        transition: all 0.2s ease;
        border-radius: 8px;
        margin-bottom: 4px;
    }
    
    .stat-row:hover {
        background-color: var(--neutral-50);
        padding-left: 20px;
    }
    
    .stat-row:last-child {
        border-bottom: none;
    }
    
    .stat-name {
        font-size: 1rem;
        color: var(--neutral-700);
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .stat-name::before {
        content: '';
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: linear-gradient(135deg, var(--primary-blue) 0%, var(--accent-indigo) 100%);
    }
    
    .stat-count {
        font-size: 1.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, var(--primary-blue) 0%, var(--accent-indigo) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-family: 'JetBrains Mono', monospace;
    }

    /* ===== BUTTONS (Enhanced with Gradients) ===== */
    .stButton > button {
        width: 100%;
        border-radius: 12px;
        height: 3.5rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        border: 2px solid var(--neutral-200);
        background: white;
        color: var(--neutral-700);
        position: relative;
        overflow: hidden;
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(59, 130, 246, 0.1), transparent);
        transition: left 0.5s ease;
    }
    
    .stButton > button:hover::before {
        left: 100%;
    }
    
    .stButton > button:hover {
        border-color: var(--primary-blue);
        color: var(--primary-blue);
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.05) 0%, rgba(99, 102, 241, 0.05) 100%);
        transform: translateY(-2px);
        box-shadow: var(--shadow-lg);
    }

    /* Primary Button Override */
    div[data-testid="stForm"] button[kind="secondary"] {
        background: linear-gradient(135deg, var(--success-green) 0%, var(--success-green-dark) 100%);
        color: white;
        border: none;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
        margin-top: 10px;
        font-weight: 700;
    }
    
    div[data-testid="stForm"] button[kind="secondary"]:hover {
        box-shadow: 0 8px 20px rgba(16, 185, 129, 0.4);
        transform: translateY(-2px);
    }

    div[data-testid="stButton"] button[kind="primary"] {
        background: linear-gradient(135deg, var(--primary-blue) 0%, var(--primary-blue-dark) 100%);
        color: white;
        border: none;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
        font-weight: 700;
    }
    
    div[data-testid="stButton"] button[kind="primary"]:hover {
        box-shadow: 0 8px 20px rgba(59, 130, 246, 0.4);
        transform: translateY(-2px);
    }

    /* ===== TABS (Modern Pill Design) ===== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background: rgba(255, 255, 255, 0.6);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 8px;
        border: 1px solid var(--neutral-200);
        box-shadow: var(--shadow-sm);
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 3.5rem;
        font-weight: 600;
        font-size: 1.05rem;
        border-radius: 12px;
        background-color: transparent;
        color: var(--neutral-600);
        border: none;
        padding: 0 2rem;
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: var(--neutral-100);
        color: var(--neutral-900);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, var(--primary-blue) 0%, var(--accent-indigo) 100%);
        color: white !important;
        box-shadow: var(--shadow-md);
        border: none;
    }

    /* ===== DATA EDITOR & TABLES ===== */
    .stDataFrame {
        border: 2px solid var(--neutral-200);
        border-radius: 16px;
        overflow: hidden;
        box-shadow: var(--shadow-lg);
    }
    
    .stDataFrame thead tr th {
        background: linear-gradient(135deg, var(--neutral-50) 0%, var(--neutral-100) 100%) !important;
        color: var(--neutral-900) !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        font-size: 0.85rem;
        letter-spacing: 0.05em;
        padding: 1rem !important;
    }

    /* ===== LEGEND BOX (Enhanced Glassmorphism) ===== */
    .legend-box {
        background: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(20px);
        border: 2px solid var(--neutral-200);
        border-radius: 20px;
        padding: 2rem;
        margin-bottom: 2rem;
        box-shadow: var(--shadow-lg);
    }
    
    .legend-badge {
        display: inline-block;
        padding: 10px 20px;
        border-radius: 12px;
        font-weight: 700;
        font-size: 0.85rem;
        color: white;
        margin-bottom: 12px;
        box-shadow: var(--shadow-md);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        transition: all 0.3s ease;
    }
    
    .legend-badge:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-lg);
    }

    /* ===== UPLOAD AREA (Modern Drag-Drop Design) ===== */
    [data-testid="stFileUploader"] {
        background: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(10px);
        border: 3px dashed var(--neutral-300);
        border-radius: 20px;
        padding: 3rem;
        transition: all 0.3s ease;
    }
    
    [data-testid="stFileUploader"]:hover {
        border-color: var(--primary-blue);
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.05) 0%, rgba(99, 102, 241, 0.05) 100%);
        box-shadow: var(--shadow-lg);
    }

    /* ===== SIDEBAR STYLING ===== */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(255, 255, 255, 0.95) 0%, rgba(248, 250, 252, 0.95) 100%);
        backdrop-filter: blur(20px);
        border-right: 2px solid var(--neutral-200);
    }
    
    [data-testid="stSidebar"] .css-1d391kg {
        padding-top: 2rem;
    }

    /* ===== INPUT FIELDS ===== */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input {
        border-radius: 12px;
        border: 2px solid var(--neutral-200);
        padding: 0.75rem 1rem;
        font-size: 1rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border-color: var(--primary-blue);
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }

    /* ===== EXPANDER ===== */
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        border: 2px solid var(--neutral-200);
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .streamlit-expanderHeader:hover {
        border-color: var(--primary-blue);
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.05) 0%, rgba(99, 102, 241, 0.05) 100%);
    }

    /* ===== SUCCESS/WARNING/ERROR ALERTS ===== */
    .stSuccess {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.1) 100%);
        border-left: 4px solid var(--success-green);
        border-radius: 12px;
        padding: 1rem;
    }
    
    .stWarning {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(217, 119, 6, 0.1) 100%);
        border-left: 4px solid var(--warning-amber);
        border-radius: 12px;
        padding: 1rem;
    }
    
    .stError {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(220, 38, 38, 0.1) 100%);
        border-left: 4px solid var(--danger-red);
        border-radius: 12px;
        padding: 1rem;
    }

    /* ===== SPINNER ===== */
    .stSpinner > div {
        border-top-color: var(--primary-blue) !important;
    }

    /* ===== HIDE STREAMLIT BRANDING ===== */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* ===== SCROLLBAR STYLING ===== */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--neutral-100);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, var(--primary-blue) 0%, var(--accent-indigo) 100%);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, var(--primary-blue-dark) 0%, var(--accent-purple) 100%);
    }
    
    /* ===== CAPTION STYLING ===== */
    .stCaption {
        color: var(--neutral-500);
        font-size: 0.9rem;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# SESSION STATE INITIALIZATION
# ==========================================

if 'processed_df' not in st.session_state: st.session_state.processed_df = None
if 'edited_df' not in st.session_state: st.session_state.edited_df = None
if 'spec_df' not in st.session_state: st.session_state.spec_df = None
if 'pricing_df' not in st.session_state: st.session_state.pricing_df = None
if 'addon_df' not in st.session_state: st.session_state.addon_df = None
if 'file_uploaded' not in st.session_state: st.session_state.file_uploaded = False
if 'analysis_done' not in st.session_state: st.session_state.analysis_done = False
if 'budget_calculated' not in st.session_state: st.session_state.budget_calculated = False
if 'save_history' not in st.session_state: st.session_state.save_history = []
if 'tor_raw_text' not in st.session_state: st.session_state.tor_raw_text = None
if 'matched_products' not in st.session_state: st.session_state.matched_products = []
if 'is_excel' not in st.session_state: st.session_state.is_excel = False
# ✅ User edit tracking
if 'original_selections' not in st.session_state: st.session_state.original_selections = {}
if 'user_modified_rows' not in st.session_state: st.session_state.user_modified_rows = set()
# File Info
if 'file_name' not in st.session_state: st.session_state.file_name = ""
if 'file_size' not in st.session_state: st.session_state.file_size = 0

# ✅ Initialize API key from secrets
if 'gemini_key' not in st.session_state:
    try:
        st.session_state.gemini_key = st.secrets["GEMINI_API_KEY"]
    except:
        st.session_state.gemini_key = None

# ==========================================
# SIDEBAR - CONFIGURATION
# ==========================================

with st.sidebar:
    st.title("⚙️ Configuration")
    
    # ===== 1. API STATUS =====
    st.markdown("### 🔐 API Status")
    try:
        if 'gemini_key' not in st.session_state or st.session_state.gemini_key is None:
            st.session_state.gemini_key = st.secrets["GEMINI_API_KEY"]
        
        st.markdown("""
        <div style='background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.1) 100%); 
                    padding: 16px; border-radius: 12px; border-left: 4px solid #10B981; margin-bottom: 1.5rem;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);'>
            <p style='margin: 0; color: #065F46; font-weight: 700; font-size: 0.95rem;'>
                ✅ Gemini AI: Connected
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.caption("🔒 Secured via Streamlit Secrets")
    except Exception as e:
        st.markdown("""
        <div style='background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(220, 38, 38, 0.1) 100%); 
                    padding: 16px; border-radius: 12px; border-left: 4px solid #EF4444; margin-bottom: 1.5rem;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);'>
            <p style='margin: 0; color: #991B1B; font-weight: 700; font-size: 0.95rem;'>
                ❌ Gemini AI: Not Configured
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.session_state.gemini_key = None
    
    st.markdown("---")
    
    # ===== 2. GOOGLE SHEET =====
    st.markdown("### 📊 Data Source")
    sheet_url = st.text_input(
        "Google Sheet URL",
        value="https://docs.google.com/spreadsheets/d/1j-l7KmbwK7h5Sp023pu2K91NOzVRQascjVwLLmtvPX4",
        help="Link to the Master Data Sheet"
    )
    
    if st.button("🔄 Sync Master Data"):
        with st.spinner("Syncing data..."):
            try:
                pricing_df, addon_df, spec_df, def_dict = load_master_data(sheet_url)
                st.session_state.pricing_df = pricing_df
                st.session_state.addon_df = addon_df
                st.session_state.spec_df = spec_df
                st.session_state.def_dict = def_dict
                st.success(f"✅ Loaded {len(spec_df)} products")
            except Exception as e:
                st.error(f"❌ Sync Failed: {e}")
    
    st.markdown("---")
    
    # ===== 3. ANALYSIS OPTIONS =====
    st.markdown("### 🛠️ Options")
    enable_ai_formatting = st.checkbox("🤖 Enable AI Text Formatting", value=True)
    enable_fr_nfr = st.checkbox("📊 Enable FR/NFR Classification", value=True)
    
    st.markdown("---")
    
    # ===== 4. SAVE HISTORY =====
    st.markdown("### 📜 Save History")
    if st.session_state.save_history:
        for idx, record in enumerate(reversed(st.session_state.save_history[-5:])):
            with st.expander(f"🕐 Update #{len(st.session_state.save_history)-idx} - {record['timestamp'].split(' ')[1]}", expanded=False):
                st.caption(f"📅 {record['timestamp']}")
                st.write(f"**Saved:** {record['count']} rows")
                if st.button(f"⏮️ Undo this save", key=f"undo_{idx}"):
                    with st.spinner("Reverting..."):
                        try:
                            undo_last_update(record['data'], sheet_url)
                            st.session_state.save_history.pop(-1-idx)
                            st.success("✅ Reverted successfully!")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Undo Failed: {e}")
    else:
        st.info("📭 No save history yet")

# ==========================================
# MAIN APP
# ==========================================

st.markdown('<div class="main-header">WiseTOR Sense</div>', unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center; margin-bottom: 2rem;'>
    <p style='font-size: 1.1rem; color: var(--neutral-600); font-weight: 500;'>
        AI-Powered Compliance Checking & Budget Estimation Tool
    </p>
</div>
""", unsafe_allow_html=True)

# Create Tabs
tab_verify, tab_budget = st.tabs(["📊 Results & Verification", "💰 Budget Estimation"])

# ==========================================
# TAB 1: RESULTS & VERIFICATION
# ==========================================
with tab_verify:

    # ===== STEP 1: FILE UPLOAD =====
    st.markdown("### 📂 Upload TOR Document")
    
    col1, col2 = st.columns([3, 1])

    with col1:
        uploaded_file = st.file_uploader("Upload PDF, DOCX, Excel or Text file", type=['pdf', 'docx', 'txt', 'xlsx', 'xls'])

    with col2:
        # File Info Card
        if uploaded_file:
            f_name = uploaded_file.name
            f_size = f"{uploaded_file.size / 1024:.1f} KB"
        elif st.session_state.file_uploaded:
            f_name = st.session_state.file_name
            f_size = f"{st.session_state.file_size / 1024:.1f} KB"
        else:
            f_name = "No file selected"
            f_size = "-"
            
        st.markdown(f"""
        <div class="file-info-card">
            <div style="font-weight:700; margin-bottom:12px; color:var(--neutral-900); font-size: 0.95rem;">
                📄 Document Info
            </div>
            <div style="font-size:0.9rem; color:var(--neutral-700); margin-bottom: 6px;">
                <strong>Name:</strong> {f_name}
            </div>
            <div style="font-size:0.9rem; color:var(--neutral-700);">
                <strong>Size:</strong> {f_size}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # File Reading Logic
    if uploaded_file and not st.session_state.file_uploaded:
        with st.spinner("📂 Processing document..."):
            try:
                file_content = read_file_content(uploaded_file)
                
                if st.session_state.spec_df is None:
                    with st.spinner("🔄 Loading master data..."):
                        pricing_df, addon_df, spec_df, def_dict = load_master_data(sheet_url)
                        st.session_state.pricing_df = pricing_df
                        st.session_state.addon_df = addon_df
                        st.session_state.spec_df = spec_df
                        st.session_state.def_dict = def_dict
                
                st.session_state.tor_raw_text = file_content
                st.session_state.file_name = uploaded_file.name
                st.session_state.file_size = uploaded_file.size
                st.session_state.file_uploaded = True
                
                if uploaded_file.name.endswith(('.xlsx', '.xls')):
                    st.session_state.is_excel = True
                else:
                    st.session_state.is_excel = False
                
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error reading file: {e}")

    # ===== STEP 2: AI ANALYSIS TRIGGER =====
    if st.session_state.file_uploaded and not st.session_state.analysis_done:
        st.markdown("---")
        if st.button("🚀 Start AI Analysis", type="primary"):
            if not st.session_state.gemini_key:
                st.error("❌ Configure API Key in sidebar first"); st.stop()
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # 1. Formatting
                status_text.markdown("**🤖 Step 1/4:** AI Structuring & Formatting...")
                progress_bar.progress(10)
                if enable_ai_formatting and not st.session_state.is_excel:
                    formatted_text = extract_scope_smart_ai(st.session_state.tor_raw_text, st.session_state.gemini_key)
                else:
                    formatted_text = st.session_state.tor_raw_text
                
                # 2. Extract
                progress_bar.progress(30)
                status_text.markdown("**📝 Step 2/4:** Extracting requirements...")
                sentences = extract_sentences_from_tor(formatted_text)
                
                # 3. Matching
                progress_bar.progress(50)
                status_text.markdown("**🎯 Step 3/4:** Matching products...")
                matched_products, result_df = analyze_tor_sentences_full_mode(
                    sentences, st.session_state.spec_df, st.session_state.gemini_key
                )
                
                # 4. Classification
                progress_bar.progress(80)
                if enable_fr_nfr:
                    status_text.markdown("**📊 Step 4/4:** Classifying FR/NFR...")
                    result_df['Requirement_Type'] = classify_scope_hybrid(sentences, st.session_state.gemini_key)
                else:
                    result_df['Requirement_Type'] = 'Functional'
                
                progress_bar.progress(100)
                
                if '📝 Status' not in result_df.columns:
                    result_df['📝 Status'] = '🤖 Auto'
                    
                st.session_state.processed_df = result_df
                st.session_state.matched_products = matched_products
                st.session_state.analysis_done = True
                
                # Initialize original selections
                st.session_state.original_selections = {}
                for idx in result_df.index:
                    st.session_state.original_selections[idx] = {
                        'products': str(result_df.loc[idx, 'Product_Match']),
                        'implementation': str(result_df.loc[idx, 'Implementation'])
                    }
                
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Analysis failed: {e}")

    # ===== STEP 3: RESULTS & STATISTICS =====
    if st.session_state.analysis_done:
        st.markdown("### 📊 Analysis Results")
        
        # Use edited_df if available, else processed_df for stats
        df_stats = st.session_state.edited_df if st.session_state.edited_df is not None else st.session_state.processed_df.copy()
        
        # Calculate Stats
        total_req = len(df_stats)
        
        # Prepare cols if not exist for counting
        prod_opts = ['Zocial Eye', 'Warroom', 'Outsource', 'Other Product', 'Non-Compliant']
        impl_opts = ['Standard', 'Customize/Integration', 'Non-Compliant']
        
        for p in prod_opts:
            if f"📦 {p}" not in df_stats.columns:
                df_stats[f"📦 {p}"] = df_stats['Product_Match'].apply(lambda x: p in str(x))
        for i in impl_opts:
            if f"🔧 {i}" not in df_stats.columns:
                df_stats[f"🔧 {i}"] = df_stats['Implementation'].apply(lambda x: i in str(x))

        # Counts
        cnt_ze = df_stats["📦 Zocial Eye"].sum()
        cnt_wr = df_stats["📦 Warroom"].sum()
        cnt_out = df_stats["📦 Outsource"].sum()
        cnt_oth = df_stats["📦 Other Product"].sum()
        cnt_nc_prod = df_stats["📦 Non-Compliant"].sum()
        
        cnt_std = df_stats["🔧 Standard"].sum()
        cnt_cust = df_stats["🔧 Customize/Integration"].sum()
        cnt_nc_impl = df_stats["🔧 Non-Compliant"].sum()
        
        cnt_edited = len(df_stats[df_stats['📝 Status'] == '✅ Edited'])
        cnt_auto = total_req - cnt_edited

        # --- DISPLAY STATS ---
        sc1, sc2, sc3 = st.columns([1, 1.5, 1.5])
        
        with sc1:
            st.markdown(f"""
            <div class="custom-card" style="display:flex; flex-direction:column; justify-content:center; align-items:center;">
                <div class="stat-label">Total Requirements</div>
                <div class="stat-value-big">{total_req}</div>
                <div style="width:100%; border-top:2px solid var(--neutral-100); margin: 24px 0;"></div>
                <div style="width:100%; font-size:1rem; display:flex; justify-content:space-between; padding:0 20px; gap: 20px;">
                    <div style="text-align: center;">
                        <div style="color:var(--success-green); font-weight:700; font-size: 1.2rem;">{cnt_edited}</div>
                        <div style="color:var(--neutral-600); font-size: 0.85rem; font-weight: 600;">✅ Edited</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="color:var(--neutral-500); font-weight:700; font-size: 1.2rem;">{cnt_auto}</div>
                        <div style="color:var(--neutral-600); font-size: 0.85rem; font-weight: 600;">🤖 Auto</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with sc2:
            st.markdown(f"""
            <div class="custom-card">
                <div class="stat-label">Selected Products</div>
                <div class="stat-row">
                    <span class="stat-name">Zocial Eye</span> <span class="stat-count">{cnt_ze}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-name">Warroom</span> <span class="stat-count">{cnt_wr}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-name">Outsource</span> <span class="stat-count">{cnt_out}</span>
                </div>
                <div class="stat-row" style="border-bottom:none;">
                    <span class="stat-name">Other</span> <span class="stat-count">{cnt_oth}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with sc3:
            st.markdown(f"""
            <div class="custom-card">
                <div class="stat-label">Implementation Type</div>
                <div class="stat-row">
                    <span class="stat-name">Standard</span> <span class="stat-count">{cnt_std}</span>
                </div>
                <div class="stat-row" style="border-bottom:none;">
                    <span class="stat-name">Customize</span> <span class="stat-count">{cnt_cust}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("### 📋 Detailed Verification")

        # --- DATA EDITOR IN FORM ---
        with st.form("editor_form"):
            df = st.session_state.processed_df.copy()
            
            # Define options & Generate Checkbox Columns
            product_options = ['Zocial Eye', 'Warroom', 'Outsource', 'Other Product', 'Non-Compliant']
            impl_options = ['Standard', 'Customize/Integration', 'Non-Compliant']

            if 'original_selections' not in st.session_state or len(st.session_state.original_selections) == 0:
                st.session_state.original_selections = {}
                for idx in df.index:
                    st.session_state.original_selections[idx] = {
                        'products': str(df.loc[idx, 'Product_Match']),
                        'implementation': str(df.loc[idx, 'Implementation'])
                    }

            for prod in product_options:
                df[f"📦 {prod}"] = df['Product_Match'].apply(lambda x: prod in str(x))
            for impl in impl_options:
                df[f"🔧 {impl}"] = df['Implementation'].apply(lambda x: impl in str(x))
            
            if '📝 Status' not in df.columns: df['📝 Status'] = '🤖 Auto'
            df['_original_idx'] = df.index
            df.index = range(1, len(df) + 1)
            df.index.name = 'No.'

            # Column Config
            column_config = {
                "Product_Match": None, "Implementation": None, "_original_idx": None,
                "TOR_Sentence": st.column_config.TextColumn("Requirement", width="large", disabled=True),
                "Requirement_Type": st.column_config.SelectboxColumn("Type", options=["Functional", "Non-Functional"], width="medium"),
                "📝 Status": st.column_config.TextColumn("Status", width="small", disabled=True),
                "Matched_Keyword": st.column_config.TextColumn("Matched Spec", width="medium"),
            }
            for prod in product_options: column_config[f"📦 {prod}"] = st.column_config.CheckboxColumn(f"🔹 {prod}", width="small")
            for impl in impl_options: column_config[f"🔧 {impl}"] = st.column_config.CheckboxColumn(f"🔸 {impl}", width="small")

            # LEGEND
            st.markdown("""
            <div class="legend-box">
                <div style="display: flex; gap: 30px; flex-wrap: wrap;">
                    <div style="flex: 1; min-width: 200px;">
                        <span class="legend-badge" style="background: linear-gradient(135deg, #3B82F6, #6366F1);">📦 Selected Product</span>
                        <div style="font-size:0.9rem; color:var(--neutral-600); margin-top: 8px; line-height: 1.6;">
                            • Can select multiple options<br>
                            • Choose all that apply
                        </div>
                    </div>
                    <div style="flex: 1; min-width: 250px;">
                        <span class="legend-badge" style="background: linear-gradient(135deg, #F59E0B, #D97706);">🔧 Implementation</span>
                        <div style="font-size:0.9rem; color:var(--neutral-600); margin-top: 8px; line-height: 1.6;">
                            • Select <strong>ONLY ONE</strong><br>
                            • Auto-enforced for Non-Compliant
                        </div>
                    </div>
                    <div style="flex: 1; min-width: 200px;">
                        <span class="legend-badge" style="background: linear-gradient(135deg, #64748B, #475569);">📝 Status</span>
                        <div style="font-size:0.9rem; color:var(--neutral-600); margin-top: 8px; line-height: 1.6;">
                            🤖 Auto = System generated<br>
                            ✅ Edited = Manually changed
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # RENDER EDITOR
            edited_df_input = st.data_editor(
                df,
                column_config=column_config,
                column_order=[
                    "TOR_Sentence", "Requirement_Type",
                    "📦 Zocial Eye", "📦 Warroom", "📦 Outsource", "📦 Other Product", "📦 Non-Compliant",
                    "🔧 Standard", "🔧 Customize/Integration", "🔧 Non-Compliant",
                    "📝 Status", "Matched_Keyword"
                ],
                hide_index=False, use_container_width=True, num_rows="dynamic", height=500, key="data_editor_form"
            )
            
            submit_changes = st.form_submit_button("💾 Save Changes (Apply Logic)")

        # --- LOGIC ENFORCEMENT ON SUBMIT ---
        if submit_changes:
            st.session_state.edited_df = edited_df_input
            
            def normalize_selection(val_str):
                if not val_str or pd.isna(val_str) or val_str == 'nan': return []
                clean = str(val_str).replace("[","").replace("]","").replace("'","")
                return sorted([x.strip() for x in clean.split(',') if x.strip() and x.strip() != 'nan'])

            impl_cols = [f"🔧 {i}" for i in impl_options]
            
            working_df = edited_df_input.copy()

            for i in working_df.index:
                orig_idx = working_df.loc[i, '_original_idx']
                
                # 1. Single Select Logic (Implementation)
                checked_impls = [col for col in impl_cols if working_df.loc[i, col]]
                if len(checked_impls) > 1:
                    if working_df.loc[i, '🔧 Non-Compliant']:
                         working_df.loc[i, '🔧 Standard'] = False
                         working_df.loc[i, '🔧 Customize/Integration'] = False
                    elif working_df.loc[i, '🔧 Customize/Integration'] and working_df.loc[i, '🔧 Standard']:
                         working_df.loc[i, '🔧 Standard'] = False
                
                # 2. Non-Compliant Logic (Product)
                if working_df.loc[i, '📦 Non-Compliant']:
                    prod_cols_to_clear = ['📦 Zocial Eye', '📦 Warroom', '📦 Outsource', '📦 Other Product']
                    for c in prod_cols_to_clear: 
                        working_df.loc[i, c] = False
                    
                    working_df.loc[i, '🔧 Non-Compliant'] = True
                    working_df.loc[i, '🔧 Standard'] = False
                    working_df.loc[i, '🔧 Customize/Integration'] = False

                # 3. Construct Strings & Status Update
                curr_prods = [p for p in product_options if working_df.loc[i, f"📦 {p}"]]
                curr_impls = [imp for imp in impl_options if working_df.loc[i, f"🔧 {imp}"]]
                curr_prod_str = ", ".join(curr_prods)
                curr_impl_str = ", ".join(curr_impls)
                
                orig_data = st.session_state.original_selections.get(orig_idx, {})
                
                is_changed = (normalize_selection(curr_prod_str) != normalize_selection(orig_data.get('products'))) or \
                             (normalize_selection(curr_impl_str) != normalize_selection(orig_data.get('implementation')))
                
                new_status = '✅ Edited' if is_changed else '🤖 Auto'
                working_df.loc[i, '📝 Status'] = new_status
                
                st.session_state.processed_df.loc[orig_idx, 'Product_Match'] = curr_prod_str
                st.session_state.processed_df.loc[orig_idx, 'Implementation'] = curr_impl_str
                st.session_state.processed_df.loc[orig_idx, 'Requirement_Type'] = working_df.loc[i, 'Requirement_Type']
                st.session_state.processed_df.loc[orig_idx, '📝 Status'] = new_status

            st.session_state.edited_df = working_df
            st.success("✅ Changes Saved & Logic Applied!")
            time.sleep(0.5)
            st.rerun()

        # --- FOOTER ACTIONS ---
        st.markdown("### 💾 Export & Save")
        
        final_df = st.session_state.edited_df if st.session_state.edited_df is not None else st.session_state.processed_df.copy()
        
        raw_save_data = prepare_save_data(final_df, product_options, impl_options)
        valid_data = raw_save_data[~raw_save_data['Product'].str.contains('Non-Compliant', na=False)].copy()
        
        def split_languages(row):
            text = str(row['TOR_Sentence'])
            if re.search(r'[\u0E00-\u0E7F]', text): return pd.Series([text, ""]) 
            else: return pd.Series(["", text])
        
        if not valid_data.empty:
            valid_data[['Sentence_TH', 'Sentence_ENG']] = valid_data.apply(split_languages, axis=1)
            final_save_data = valid_data[['Product', 'Sentence_TH', 'Sentence_ENG', 'Implementation']]
        else:
            final_save_data = pd.DataFrame(columns=['Product', 'Sentence_TH', 'Sentence_ENG', 'Implementation'])

        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("💾 Save to Google Sheet", type="primary", disabled=len(final_save_data)==0):
                with st.spinner("Saving to Google Sheet..."):
                    try:
                        save_to_product_spec(final_save_data, sheet_url)
                        st.session_state.save_history.append({
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'count': len(final_save_data), 'products': list(final_save_data['Product'].unique()),
                            'data': final_save_data.to_dict('records')
                        })
                        st.success("✅ Saved successfully!"); st.balloons()
                        time.sleep(1.5)
                        st.rerun()
                    except Exception as e: st.error(f"❌ Failed: {e}")

        with c2:
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                export_df = st.session_state.processed_df.copy()
                cols_to_keep = ['TOR_Sentence', 'Product_Match', 'Implementation', 'Requirement_Type']
                available_cols = [c for c in cols_to_keep if c in export_df.columns]
                export_df = export_df[available_cols]
                export_df = export_df.rename(columns={'TOR_Sentence': 'Requirement', 'Product_Match': 'Selected product', 'Requirement_Type': 'Requirement type'})
                export_df.to_excel(writer, sheet_name='Data', index=False)
            
            original_name = st.session_state.file_name
            download_name = f"{original_name.rsplit('.', 1)[0]}_compliant.xlsx" if original_name else "compliant_export.xlsx"
            st.download_button("⬇️ Download Excel", data=output.getvalue(), file_name=download_name, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        with c3:
             if st.button("🔄 Reset Analysis"):
                st.session_state.clear(); st.rerun()

# ==========================================
# TAB 2: BUDGET ESTIMATION
# ==========================================
with tab_budget:
    st.markdown("### 💰 Budget Estimation")
    
    if not st.session_state.analysis_done:
        st.warning("⚠️ Please complete the 'Results & Verification' step first.")
    else:
        if not st.session_state.budget_calculated:
            if st.button("🎯 Generate Initial Budget", type="primary"):
                with st.spinner("🤖 AI Calculating..."):
                    try:
                        factors = extract_budget_factors(st.session_state.tor_raw_text, st.session_state.gemini_key)
                        st.session_state.budget_factors = factors
                        st.session_state.budget_calculated = True
                        st.rerun()
                    except Exception as e: st.error(f"❌ Failed: {e}")
        
        if st.session_state.budget_calculated:
            results = calculate_budget_sheets(
                st.session_state.budget_factors, st.session_state.matched_products,
                st.session_state.pricing_df, st.session_state.addon_df
            )
            
            st.markdown("#### 🧾 Cost Breakdown")
            
            total_budget = 0
            if results:
                for res in results:
                    with st.expander(f"📦 {res['Product']}", expanded=True):
                         raw_html = format_budget_report(res['Product'], res['Package'], st.session_state.budget_factors, res['Breakdown'])
                         clean_html = "\n".join([line.lstrip() for line in raw_html.split('\n')])
                         st.markdown(clean_html, unsafe_allow_html=True)
                    
                    init_fee = res['Package'].get('Initial_Fee (THB)', 0)
                    if init_fee and isinstance(init_fee, (int, float)): total_budget += res['Breakdown']['total'] + init_fee
                    else: total_budget += res['Breakdown']['total']
                
                mandays = st.session_state.budget_factors.get('mandays', 0)
                manday_cost = mandays * 22000
                other_expenses = st.session_state.budget_factors.get('other_expenses', 0.0)
                grand_total = total_budget + manday_cost + other_expenses
                
                if mandays != 0:
                    st.markdown(f"""
                    <div style='background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(99, 102, 241, 0.1) 100%); 
                                padding: 20px; border-radius: 16px; margin-top: 20px; border: 2px solid #BFDBFE;
                                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);'>
                        <h4 style='color: #1E40AF; margin:0 0 12px 0; font-weight: 700;'>🛠️ Customization Service</h4>
                        <p style='margin: 0; font-size: 1.2em; color: var(--neutral-700);'>
                            <span style='font-weight: 600;'>{mandays} Mandays</span> × 
                            <span style='font-weight: 600;'>22,000 THB</span> = 
                            <strong style='color: var(--primary-blue); font-size: 1.3em;'>{manday_cost:,.0f} THB</strong>
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                
                if other_expenses != 0:
                    st.markdown(f"""
                    <div style='background: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(217, 119, 6, 0.1) 100%); 
                                padding: 20px; border-radius: 16px; margin-top: 20px; border: 2px solid #FED7AA;
                                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);'>
                        <h4 style='color: #C2410C; margin:0 0 12px 0; font-weight: 700;'>💸 Other Expenses</h4>
                        <p style='margin: 0; font-size: 1.3em;'>
                            <strong style='color: var(--warning-amber-dark);'>{other_expenses:,.0f} THB</strong>
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown(f"""
                <div style='background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(5, 150, 105, 0.15) 100%); 
                            padding: 32px; border-radius: 20px; border-left: 6px solid var(--success-green); 
                            text-align: right; margin-top: 32px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);'>
                    <h4 style='color: #065F46; margin:0 0 12px 0; font-weight: 700; font-size: 1.2rem;'>
                        💎 TOTAL ANNUAL BUDGET
                    </h4>
                    <h1 style='color: #047857; margin:0; font-size: 2.5rem; font-weight: 900; letter-spacing: -0.02em;'>
                        {grand_total:,.2f} <span style='font-size: 1.5rem;'>THB/Year</span>
                    </h1>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.warning("⚠️ No suitable package found.")
            
            st.markdown("---")
            st.markdown("#### ✏️ Adjust Budget Factors")
            
            with st.container():
                factors = st.session_state.budget_factors
                
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("##### 🔵 Zocial Eye Configuration")
                    ze_users = st.number_input("Users", value=factors.get('num_users', 2), min_value=1)
                    ze_days = st.number_input("Data Backward (Days)", value=factors.get('data_backward_days', 90), step=30)
                
                with c2:
                    st.markdown("##### 🟡 Warroom Configuration")
                    wr_users = st.number_input("Warroom Users", value=factors.get('num_users', 5), min_value=1, key="wr_u")
                    wr_tx = st.number_input("Monthly Transaction", value=factors.get('monthly_transactions', 35000), step=1000)
                    
                c3, c4 = st.columns(2)
                with c3:
                    wr_ch = st.number_input("Social Channels", value=factors.get('social_channels_count', 0))
                    wr_bot = st.checkbox("Chatbot Required", value=factors.get('chatbot_required', False))
                
                st.markdown("<hr style='margin: 2rem 0; border-top: 2px solid var(--neutral-200);'>", unsafe_allow_html=True)
                
                st.markdown("##### 💵 Additional Costs")
                c5, c6 = st.columns(2)
                with c5:
                    md_input = st.number_input("Customization Mandays (22k/day)", value=factors.get('mandays', 0), step=1)
                with c6:
                    other_cost_input = st.number_input("Other Expenses (THB)", value=float(factors.get('other_expenses', 0.0)), step=1000.0)
                
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🔄 Recalculate Budget", type="primary"):
                    st.session_state.budget_factors.update({
                        'num_users': ze_users, 'data_backward_days': ze_days,
                        'monthly_transactions': wr_tx, 'social_channels_count': wr_ch,
                        'chatbot_required': wr_bot, 'mandays': md_input, 'other_expenses': other_cost_input
                    })
                    st.rerun()

# ===== FOOTER =====
st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 20px; color: var(--neutral-500);'>
    <p style='margin: 0; font-weight: 600;'>
        WiseTOR Sense <span style='color: var(--primary-blue);'>v2.5.0</span> | 
        Session: {date} | 
        Powered by <span style='color: var(--accent-indigo);'>Gemini AI</span>
    </p>
</div>
""".format(date=datetime.now().strftime('%Y-%m-%d')), unsafe_allow_html=True)
