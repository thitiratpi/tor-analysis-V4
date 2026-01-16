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
    page_title="WiseSight TOR Analyzer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/yourusername/wisesight-streamlit',
        'Report a bug': "https://github.com/yourusername/wisesight-streamlit/issues",
        'About': "# WiseSight TOR Analyzer\nVersion 2.4.2\nPowered by Streamlit + Gemini AI"
    }
)

# ==========================================
# CUSTOM CSS (PROFESSIONAL THEME)
# ==========================================
st.markdown("""
<style>
    /* ===== THEME VARIABLES ===== */
    :root {
        --primary-color: #2563EB; /* Royal Blue */
        --secondary-color: #1E293B; /* Slate Dark */
        --bg-light: #F8FAFC;
        --border-color: #E2E8F0;
        --success-color: #10B981;
        --warning-color: #F59E0B;
        --text-color: #334155;
    }

    /* ===== GLOBAL TYPOGRAPHY ===== */
    .stApp {
        background-color: white;
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        color: var(--text-color);
    }
    
    h1, h2, h3, h4, h5 {
        color: var(--secondary-color) !important;
        font-weight: 700 !important;
        letter-spacing: -0.5px;
    }
    
    .main-header {
        font-size: 2.2rem;
        text-align: center;
        margin-bottom: 0.5rem;
        background: -webkit-linear-gradient(45deg, #1E3A8A, #3B82F6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* ===== CARDS & CONTAINERS ===== */
    .custom-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid var(--border-color);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 1rem;
        transition: transform 0.2s;
    }
    
    .custom-card:hover {
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
    }

    .file-info-card {
        background-color: #F1F5F9;
        padding: 1.25rem;
        border-radius: 10px;
        border-left: 5px solid var(--primary-color);
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    /* ===== STATISTICS DASHBOARD ===== */
    .stat-label {
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #64748B;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    .stat-value {
        font-size: 2rem;
        font-weight: 800;
        color: var(--primary-color);
    }
    
    .stat-list {
        font-size: 0.95rem;
        color: var(--text-color);
        line-height: 2.0; /* Increased line height */
    }

    /* ===== BUTTONS ===== */
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        height: 3.2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.2s ease-in-out;
        border: 1px solid var(--border-color);
        background-color: white;
        color: var(--secondary-color);
    }
    
    .stButton > button:hover {
        border-color: var(--primary-color);
        color: var(--primary-color);
        background-color: #EFF6FF;
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    /* Primary Button Override */
    div[data-testid="stButton"] button[kind="primary"] {
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
        color: white;
        border: none;
        box-shadow: 0 4px 6px rgba(37, 99, 235, 0.3);
    }
    div[data-testid="stButton"] button[kind="primary"]:hover {
        box-shadow: 0 6px 10px rgba(37, 99, 235, 0.4);
    }

    /* ===== TABS ===== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
        border-bottom: 2px solid #E2E8F0;
        padding-bottom: 0px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 3.5rem;
        font-weight: 600;
        font-size: 1.1rem;
        border-radius: 8px 8px 0 0;
        background-color: transparent;
        color: #64748B;
        border: none;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: white;
        color: var(--primary-color);
        border-bottom: 3px solid var(--primary-color);
    }

    /* ===== DATA EDITOR & TABLES ===== */
    .stDataFrame {
        border: 1px solid var(--border-color);
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }

    /* ===== LEGEND BOX ===== */
    .legend-box {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
    }
    
    .legend-badge {
        display: inline-block;
        padding: 6px 12px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.9rem;
        color: white;
        margin-bottom: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    /* ===== UPLOAD AREA ===== */
    [data-testid="stFileUploader"] {
        background-color: #F8FAFC;
        border: 2px dashed #CBD5E1;
        border-radius: 12px;
        padding: 2rem;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: var(--primary-color);
        background-color: #EFF6FF;
    }

    /* ===== HIDE STREAMLIT BRANDING ===== */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
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
        <div style='background-color: #DCFCE7; padding: 12px; border-radius: 8px; border-left: 4px solid #10B981; margin-bottom: 1rem;'>
            <p style='margin: 0; color: #065F46; font-weight: 600; font-size: 0.9rem;'>
                ✅ Gemini AI: Connected
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.caption("via Streamlit Secrets")
    except Exception as e:
        st.markdown("""
        <div style='background-color: #FEE2E2; padding: 12px; border-radius: 8px; border-left: 4px solid #EF4444; margin-bottom: 1rem;'>
            <p style='margin: 0; color: #991B1B; font-weight: 600; font-size: 0.9rem;'>
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
                st.success(f"Loaded {len(spec_df)} products")
            except Exception as e:
                st.error(f"Sync Failed: {e}")
    
    st.markdown("---")
    
    # ===== 3. ANALYSIS OPTIONS =====
    st.markdown("### 🛠️ Options")
    enable_ai_formatting = st.checkbox("Enable AI Text Formatting", value=True)
    enable_fr_nfr = st.checkbox("Enable FR/NFR Classification", value=True)
    
    st.markdown("---")
    
    # ===== 4. SAVE HISTORY =====
    st.markdown("### 📜 History")
    if st.session_state.save_history:
        for idx, record in enumerate(reversed(st.session_state.save_history[-5:])):
            with st.expander(f"Update #{len(st.session_state.save_history)-idx} - {record['timestamp'].split(' ')[1]}", expanded=False):
                st.caption(f"Date: {record['timestamp']}")
                st.write(f"**Saved:** {record['count']} rows")
                if st.button(f"⏮️ Undo this save", key=f"undo_{idx}"):
                    with st.spinner("Reverting..."):
                        try:
                            undo_last_update(record['data'], sheet_url)
                            st.session_state.save_history.pop(-1-idx)
                            st.success("Reverted successfully!")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Undo Failed: {e}")
    else:
        st.info("No save history yet")

# ==========================================
# MAIN APP
# ==========================================

st.markdown('<div class="main-header">🔍 WiseSight TOR Analyzer</div>', unsafe_allow_html=True)
st.caption("AI-Powered Compliance Checking & Budget Estimation Tool")
st.markdown("<br>", unsafe_allow_html=True)

# Create Tabs
tab_verify, tab_budget = st.tabs(["📊 Results & Verification", "💰 Budget Estimation"])

# ==========================================
# TAB 1: RESULTS & VERIFY
# ==========================================
with tab_verify:

    # ===== STEP 1: FILE UPLOAD =====
    st.markdown("### 📂 1. Upload TOR Document")
    
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
            <div style="font-weight:700; margin-bottom:8px; color:#1E293B;">📄 Document Info</div>
            <div style="font-size:0.9rem; color:#475569;"><strong>Name:</strong> {f_name}</div>
            <div style="font-size:0.9rem; color:#475569;"><strong>Size:</strong> {f_size}</div>
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
        st.markdown("### 📊 2. Analysis Results")
        
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

        # --- DISPLAY STATS (FIXED DISPLAY) ---
        sc1, sc2, sc3 = st.columns([1, 1.5, 1.5])
        
        with sc1:
            st.markdown(f"""
            <div class="custom-card" style="text-align:center;">
                <div class="stat-label">Total Requirements</div>
                <div class="stat-value">{total_req}</div>
                <hr style="margin: 10px 0; border:0; border-top:1px solid #eee;">
                <div style="font-size:0.9rem; display:flex; justify-content:space-between;">
                    <span style="color:#10B981;">✅ Edited: <b>{cnt_edited}</b></span>
                    <span style="color:#64748B;">🤖 Auto: <b>{cnt_auto}</b></span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with sc2:
            st.markdown(f"""
            <div class="custom-card">
                <div class="stat-label">Selected Products</div>
                <div class="stat-list">
                    🔹 Zocial Eye: <b>{cnt_ze}</b><br>
                    🔹 Warroom: <b>{cnt_wr}</b><br>
                    🔹 Outsource: <b>{cnt_out}</b><br>
                    🔹 Other: <b>{cnt_oth}</b><br>
                    <span style="color:#EF4444;">🔴 Non-Compliant: <b>{cnt_nc_prod}</b></span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with sc3:
            st.markdown(f"""
            <div class="custom-card">
                <div class="stat-label">Implementation Type</div>
                <div class="stat-list">
                    🔸 Standard: <b>{cnt_std}</b><br>
                    🔸 Customize: <b>{cnt_cust}</b><br>
                    <span style="color:#EF4444;">🔴 Non-Compliant: <b>{cnt_nc_impl}</b></span>
                </div>
                <div style="height:2.6rem;"></div> </div>
            """, unsafe_allow_html=True)

        st.markdown("### 📋 3. Detailed Verification")

        # --- DATA EDITOR ---
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
        for prod in product_options: column_config[f"📦 {prod}"] = st.column_config.CheckboxColumn(f"🔵 {prod}", width="small")
        for impl in impl_options: column_config[f"🔧 {impl}"] = st.column_config.CheckboxColumn(f"🟠 {impl}", width="small")

        # LEGEND (New Design)
        st.markdown("""
        <div class="legend-box">
            <div style="display: flex; gap: 30px; flex-wrap: wrap;">
                <div style="flex: 1; min-width: 200px;">
                    <span class="legend-badge" style="background: linear-gradient(135deg, #2563EB, #60A5FA);">Selected Product</span>
                    <div style="font-size:0.85rem; color:#475569;">
                        • Can select multiple options<br>• Choose all that apply
                    </div>
                </div>
                <div style="flex: 1; min-width: 250px;">
                    <span class="legend-badge" style="background: linear-gradient(135deg, #F59E0B, #FBBF24);">Implementation</span>
                    <div style="font-size:0.85rem; color:#475569;">
                        • ⚠️ Select <strong>ONLY ONE</strong><br>• Auto-enforced for Non-Compliant
                    </div>
                </div>
                <div style="flex: 1; min-width: 200px;">
                    <span class="legend-badge" style="background: linear-gradient(135deg, #64748B, #94A3B8);">Status</span>
                    <div style="font-size:0.85rem; color:#475569;">
                        🤖 Auto = System generated<br>✅ Edited = Manually changed
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # RENDER EDITOR
        edited_df = st.data_editor(
            df,
            column_config=column_config,
            column_order=[
                "TOR_Sentence", "Requirement_Type",
                "📦 Zocial Eye", "📦 Warroom", "📦 Outsource", "📦 Other Product", "📦 Non-Compliant",
                "🔧 Standard", "🔧 Customize/Integration", "🔧 Non-Compliant",
                "📝 Status", "Matched_Keyword"
            ],
            hide_index=False, use_container_width=True, num_rows="dynamic", height=500, key="data_editor"
        )

        # LOGIC ENFORCEMENT
        needs_rerun = False
        def normalize_selection(val_str):
            if not val_str or pd.isna(val_str) or val_str == 'nan': return []
            clean = str(val_str).replace("[","").replace("]","").replace("'","")
            return sorted([x.strip() for x in clean.split(',') if x.strip() and x.strip() != 'nan'])

        impl_cols = [f"🔧 {i}" for i in impl_options]

        for i in edited_df.index:
            # Single Select Logic
            checked_impls = [col for col in impl_cols if edited_df.loc[i, col]]
            if len(checked_impls) > 1:
                newly_checked = [col for col in impl_cols if edited_df.loc[i, col] and not df.loc[i, col]]
                if newly_checked:
                    keep_col = newly_checked[0]
                    for col in impl_cols:
                        if col != keep_col: edited_df.loc[i, col] = False
                else:
                    if edited_df.loc[i, '🔧 Non-Compliant']:
                        edited_df.loc[i, '🔧 Standard'] = False; edited_df.loc[i, '🔧 Customize/Integration'] = False
                    elif edited_df.loc[i, '🔧 Customize/Integration']: edited_df.loc[i, '🔧 Standard'] = False
                needs_rerun = True

            # Non-Compliant Logic
            if edited_df.loc[i, '📦 Non-Compliant']:
                prod_cols_to_clear = ['📦 Zocial Eye', '📦 Warroom', '📦 Outsource', '📦 Other Product']
                if any(edited_df.loc[i, c] for c in prod_cols_to_clear):
                    for c in prod_cols_to_clear: edited_df.loc[i, c] = False
                    needs_rerun = True
                if not edited_df.loc[i, '🔧 Non-Compliant']:
                    edited_df.loc[i, '🔧 Non-Compliant'] = True; edited_df.loc[i, '🔧 Standard'] = False; edited_df.loc[i, '🔧 Customize/Integration'] = False
                    needs_rerun = True

            # Status Update
            curr_prods = [p for p in product_options if edited_df.loc[i, f"📦 {p}"]]
            curr_impls = [imp for imp in impl_options if edited_df.loc[i, f"🔧 {imp}"]]
            curr_prod_str = ", ".join(curr_prods)
            curr_impl_str = ", ".join(curr_impls)
            
            orig_idx = edited_df.loc[i, '_original_idx']
            orig_data = st.session_state.original_selections.get(orig_idx, {})
            
            is_changed = (normalize_selection(curr_prod_str) != normalize_selection(orig_data.get('products'))) or \
                         (normalize_selection(curr_impl_str) != normalize_selection(orig_data.get('implementation')))
            
            new_status = '✅ Edited' if is_changed else '🤖 Auto'
            
            if edited_df.loc[i, '📝 Status'] != new_status:
                edited_df.loc[i, '📝 Status'] = new_status
                needs_rerun = True
            
            st.session_state.processed_df.loc[orig_idx, 'Product_Match'] = curr_prod_str
            st.session_state.processed_df.loc[orig_idx, 'Implementation'] = curr_impl_str
            st.session_state.processed_df.loc[orig_idx, 'Requirement_Type'] = edited_df.loc[i, 'Requirement_Type']
            
            if '📝 Status' not in st.session_state.processed_df.columns:
                 st.session_state.processed_df['📝 Status'] = '🤖 Auto'
            st.session_state.processed_df.loc[orig_idx, '📝 Status'] = new_status

        if needs_rerun: st.rerun()
        st.session_state.edited_df = edited_df

        # --- FOOTER ACTIONS ---
        st.markdown("### 💾 4. Export & Save")
        
        # Prepare Data
        raw_save_data = prepare_save_data(edited_df, product_options, impl_options)
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
# TAB 2: BUDGET
# ==========================================
with tab_budget:
    st.markdown("### 💰 Budget Estimation")
    
    if not st.session_state.analysis_done:
        st.warning("⚠️ Please complete the 'Results & Verify' step first.")
    else:
        if not st.session_state.budget_calculated:
            if st.button("Generate Initial Budget", type="primary"):
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
                    st.markdown(f"""<div style='background-color: #EFF6FF; padding: 15px; border-radius: 8px; margin-top: 15px; border: 1px solid #BFDBFE;'><h4 style='color: #1E40AF; margin:0;'>🛠️ Customization Service</h4><p style='margin: 5px 0 0 0; font-size: 1.1em;'>{mandays} Mandays × 22,000 THB = <strong>{manday_cost:,.0f} THB</strong></p></div>""", unsafe_allow_html=True)
                
                if other_expenses != 0:
                    st.markdown(f"""<div style='background-color: #FFF7ED; padding: 15px; border-radius: 8px; margin-top: 15px; border: 1px solid #FED7AA;'><h4 style='color: #C2410C; margin:0;'>💸 Other Expenses</h4><p style='margin: 5px 0 0 0; font-size: 1.1em;'><strong>{other_expenses:,.0f} THB</strong></p></div>""", unsafe_allow_html=True)

                st.markdown(f"""<div style='background-color: #DCFCE7; padding: 25px; border-radius: 12px; border-left: 6px solid #10B981; text-align: right; margin-top:25px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);'><h4 style='color: #065F46; margin:0;'>TOTAL ANNUAL BUDGET</h4><h1 style='color: #047857; margin:0; font-size: 2.5rem;'>{grand_total:,.2f} THB/Year</h1></div>""", unsafe_allow_html=True)
            else:
                st.warning("⚠️ No suitable package found.")
            
            st.markdown("---")
            st.markdown("#### ✏️ Adjust Budget Factors")
            
            with st.container():
                # ✅ REMOVED <div class='custom-card'> wrapper
                factors = st.session_state.budget_factors
                
                c1, c2 = st.columns(2)
                with c1:
                    # ✅ CHANGED st.caption to st.markdown H5
                    st.markdown("##### 🔹 Zocial Eye Configuration")
                    ze_users = st.number_input("Users", value=factors.get('num_users', 2), min_value=1)
                    ze_days = st.number_input("Data Backward (Days)", value=factors.get('data_backward_days', 90), step=30)
                
                with c2:
                    # ✅ CHANGED st.caption to st.markdown H5
                    st.markdown("##### 🔸 Warroom Configuration")
                    wr_users = st.number_input("Warroom Users", value=factors.get('num_users', 5), min_value=1, key="wr_u")
                    wr_tx = st.number_input("Monthly Tx", value=factors.get('monthly_transactions', 35000), step=1000)
                    
                c3, c4 = st.columns(2)
                with c3:
                    wr_ch = st.number_input("Social Channels", value=factors.get('social_channels_count', 0))
                    wr_bot = st.checkbox("Chatbot Required", value=factors.get('chatbot_required', False))
                
                st.markdown("<hr style='margin: 1.5rem 0; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)
                
                # ✅ CHANGED st.caption to st.markdown H5
                st.markdown("##### ➕ Additional Costs")
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
                # ✅ REMOVED </div> closure

# ===== FOOTER =====
st.markdown("---")
st.caption(f"WiseSight TOR Analyzer v2.4.2 | Session: {datetime.now().strftime('%Y-%m-%d')}")
