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
        'About': "# WiseTOR Sense\nVersion 2.5.2\nPowered by Streamlit + Gemini AI"
    }
)

# ==========================================
# CUSTOM CSS (PROFESSIONAL THEME & TABLE STYLING)
# ==========================================
st.markdown("""
<style>
    /* ===== THEME VARIABLES ===== */
    :root {
        --primary-color: #2563EB;
        --secondary-color: #1E293B;
        --bg-light: #F8FAFC;
        --border-color: #E2E8F0;
    }

    /* ===== TABLE HEADER COLORING (THE KEY FIX) ===== */
    /* Product Columns (Blue) */
    th[aria-label="Zocial Eye"], 
    th[aria-label="Warroom"], 
    th[aria-label="Outsource"], 
    th[aria-label="Other Product"] {
        background-color: #EFF6FF !important; /* Light Blue */
        color: #1E3A8A !important;
        border-bottom: 2px solid #2563EB !important;
    }

    /* Implementation Columns (Orange) */
    th[aria-label="Standard"], 
    th[aria-label="Customize/Integration"] {
        background-color: #FFF7ED !important; /* Light Orange */
        color: #9A3412 !important;
        border-bottom: 2px solid #F97316 !important;
    }

    /* Non-Compliant Columns (Red) - For both Product and Impl */
    th[aria-label="NC (Prod)"],
    th[aria-label="NC (Impl)"] {
        background-color: #FEF2F2 !important; /* Light Red */
        color: #991B1B !important;
        border-bottom: 2px solid #EF4444 !important;
    }

    /* Requirement & Type Columns (Gray) */
    th[aria-label="Requirement"], 
    th[aria-label="Type"],
    th[aria-label="Status"],
    th[aria-label="Matched Spec"] {
        background-color: #F8FAFC !important;
        color: #475569 !important;
        border-bottom: 2px solid #CBD5E1 !important;
    }

    /* Adjust Header Font */
    th {
        font-size: 0.95rem !important;
        font-weight: 700 !important;
    }

    /* ===== GLOBAL TYPOGRAPHY ===== */
    .stApp {
        background-color: white;
        color: #334155;
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }
    
    h1, h2, h3, h4, h5 {
        color: #1E293B !important;
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
        font-weight: 800;
    }

    /* ===== CARDS ===== */
    .custom-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 16px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
        transition: transform 0.2s;
        /* height: 100%; Removed to allow content fit */
    }
    
    .custom-card:hover {
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
    }

    .file-info-card {
        background-color: #F8FAFC;
        padding: 1.25rem;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    /* ===== STATS ===== */
    .stat-label {
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #64748B;
        font-weight: 700;
        margin-bottom: 1.5rem;
        text-align: center;
    }
    
    .stat-value-big {
        font-size: 2.0rem;
        font-weight: 800;
        color: #2563EB;
        line-height: 1;
    }
    
    .stat-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 10px;
        border-bottom: 1px solid #F1F5F9;
    }
    
    .stat-row:last-child {
        border-bottom: none;
    }
    
    .stat-name {
        font-size: 1.05rem;
        color: #334155;
        font-weight: 500;
    }
    
    .stat-count {
        font-size: 1.2rem;
        font-weight: 700;
        color: #2563EB;
    }

    /* ===== BUTTONS ===== */
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        height: 3.2rem;
        font-weight: 600;
        border: 1px solid #E2E8F0;
        background-color: white;
        color: #1E293B;
        transition: all 0.2s ease-in-out;
    }
    
    .stButton > button:hover {
        border-color: #2563EB;
        color: #2563EB;
        background-color: #EFF6FF;
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Secondary Button (Save Changes) */
    div[data-testid="stForm"] button[kind="secondary"] {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%);
        color: white;
        border: none;
        margin-top: 10px;
        box-shadow: 0 4px 6px rgba(16, 185, 129, 0.3);
    }
    div[data-testid="stForm"] button[kind="secondary"]:hover {
        box-shadow: 0 6px 10px rgba(16, 185, 129, 0.4);
        color: white;
    }
    
    /* Primary Button */
    div[data-testid="stButton"] button[kind="primary"] {
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
        color: white;
        border: none;
    }

    /* ===== UPLOAD AREA ===== */
    [data-testid="stFileUploader"] {
        background-color: #F8FAFC;
        border: 2px dashed #CBD5E1;
        border-radius: 12px;
        padding: 2rem;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: #2563EB;
        background-color: #EFF6FF;
    }

    /* Hide Branding */
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
# User edit tracking
if 'original_selections' not in st.session_state: st.session_state.original_selections = {}
if 'user_modified_rows' not in st.session_state: st.session_state.user_modified_rows = set()
# File Info
if 'file_name' not in st.session_state: st.session_state.file_name = ""
if 'file_size' not in st.session_state: st.session_state.file_size = 0

# Initialize API key
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
                st.write(f"**Saved:** {record['count']} rows")
                if st.button(f"⏮️ Undo", key=f"undo_{idx}"):
                    with st.spinner("Reverting..."):
                        try:
                            undo_last_update(record['data'], sheet_url)
                            st.session_state.save_history.pop(-1-idx)
                            st.success("Reverted!")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Undo Failed: {e}")
    else:
        st.info("No save history yet")

# ==========================================
# MAIN APP
# ==========================================

st.markdown('<div class="main-header">WiseTOR Sense</div>', unsafe_allow_html=True)
st.caption("AI-Powered Compliance Checking & Budget Estimation Tool")
st.markdown("<br>", unsafe_allow_html=True)

# Create Tabs
tab_verify, tab_budget = st.tabs(["📊 Results & Verification", "💰 Budget Estimation"])

# ==========================================
# TAB 1: RESULTS & VERIFY
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
        st.markdown("### 📊 Analysis Results")
        
        # Use edited_df if available, else processed_df for stats
        df_stats = st.session_state.edited_df if st.session_state.edited_df is not None else st.session_state.processed_df.copy()
        
        # Calculate Stats
        total_req = len(df_stats)
        
        # Manual Check for internal logic because we are about to rename cols in display
        # Counts
        cnt_ze = df_stats['Product_Match'].apply(lambda x: 'Zocial Eye' in str(x)).sum()
        cnt_wr = df_stats['Product_Match'].apply(lambda x: 'Warroom' in str(x)).sum()
        cnt_out = df_stats['Product_Match'].apply(lambda x: 'Outsource' in str(x)).sum()
        cnt_oth = df_stats['Product_Match'].apply(lambda x: 'Other Product' in str(x)).sum()
        
        cnt_std = df_stats['Implementation'].apply(lambda x: 'Standard' in str(x)).sum()
        cnt_cust = df_stats['Implementation'].apply(lambda x: 'Customize' in str(x)).sum()
        
        cnt_edited = len(df_stats[df_stats['📝 Status'] == '✅ Edited'])
        cnt_auto = total_req - cnt_edited

        # --- DISPLAY STATS ---
        sc1, sc2, sc3 = st.columns([1, 1.5, 1.5])
        
        with sc1:
            st.markdown(f"""
            <div class="custom-card" style="display:flex; flex-direction:column; justify-content:center; align-items:center;">
                <div class="stat-label">Total Requirements</div>
                <div class="stat-value-big">{total_req}</div>
                <div style="width:100%; border-top:1px solid #F1F5F9; margin: 20px 0;"></div>
                <div style="width:100%; font-size:0.95rem; display:flex; justify-content:space-between; padding:0 15px;">
                    <span style="color:#10B981; font-weight:600;">✅ Edited: {cnt_edited}</span>
                    <span style="color:#64748B; font-weight:600;">🤖 Auto: {cnt_auto}</span>
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
            
            # 1. Define INTERNAL column names (Prefix to separate groups)
            # Products
            p_cols = {
                'Zocial Eye': 'P_Zocial Eye',
                'Warroom': 'P_Warroom',
                'Outsource': 'P_Outsource',
                'Other Product': 'P_Other Product',
                'Non-Compliant': 'P_Non-Compliant'
            }
            # Implementation
            i_cols = {
                'Standard': 'I_Standard',
                'Customize/Integration': 'I_Customize/Integration',
                'Non-Compliant': 'I_Non-Compliant'
            }

            # 2. Generate Checkbox Columns with INTERNAL names
            for name, col_key in p_cols.items():
                df[col_key] = df['Product_Match'].apply(lambda x: name in str(x))
            
            for name, col_key in i_cols.items():
                df[col_key] = df['Implementation'].apply(lambda x: name in str(x))
            
            if '📝 Status' not in df.columns: df['📝 Status'] = '🤖 Auto'
            df['_original_idx'] = df.index
            df.index = range(1, len(df) + 1)
            
            # 3. Configure Columns (Display names WITHOUT icons)
            column_config = {
                "Product_Match": None, "Implementation": None, "_original_idx": None,
                "TOR_Sentence": st.column_config.TextColumn("Requirement", width="large", disabled=True),
                "Requirement_Type": st.column_config.SelectboxColumn("Type", options=["Functional", "Non-Functional"], width="medium"),
                "📝 Status": st.column_config.TextColumn("Status", width="small", disabled=True),
                "Matched_Keyword": st.column_config.TextColumn("Matched Spec", width="medium"),
            }
            
            # Map Internal Keys to Clean Display Labels
            for name, col_key in p_cols.items():
                label = name if name != 'Non-Compliant' else 'NC (Prod)'
                column_config[col_key] = st.column_config.CheckboxColumn(label, width="small")
                
            for name, col_key in i_cols.items():
                label = name if name != 'Non-Compliant' else 'NC (Impl)'
                column_config[col_key] = st.column_config.CheckboxColumn(label, width="small")

            # 4. Legend (Simplified)
            st.markdown("""
            <div class="legend-box">
                <div style="display: flex; gap: 20px; flex-wrap: wrap; align-items:center;">
                    <div style="display:flex; align-items:center; gap:8px;">
                        <div style="width:15px; height:15px; background-color:#EFF6FF; border:2px solid #2563EB; border-radius:4px;"></div>
                        <span style="font-weight:600; color:#334155;">Product (Multi-Select)</span>
                    </div>
                    <div style="display:flex; align-items:center; gap:8px;">
                        <div style="width:15px; height:15px; background-color:#FFF7ED; border:2px solid #F97316; border-radius:4px;"></div>
                        <span style="font-weight:600; color:#334155;">Implementation (Single Select)</span>
                    </div>
                    <div style="display:flex; align-items:center; gap:8px;">
                        <div style="width:15px; height:15px; background-color:#FEF2F2; border:2px solid #EF4444; border-radius:4px;"></div>
                        <span style="font-weight:600; color:#334155;">Non-Compliant</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # 5. Render
            ordered_cols = ["TOR_Sentence", "Requirement_Type"] + list(p_cols.values()) + list(i_cols.values()) + ["📝 Status", "Matched_Keyword"]
            
            edited_df_input = st.data_editor(
                df,
                column_config=column_config,
                column_order=ordered_cols,
                hide_index=False, use_container_width=True, num_rows="dynamic", height=600, key="data_editor_form"
            )
            
            submit_changes = st.form_submit_button("💾 Save Changes & Apply Logic", type="secondary")

        # --- LOGIC ENFORCEMENT ON SUBMIT ---
        if submit_changes:
            working_df = edited_df_input.copy()
            
            # Helper to reconstruct list from checked columns
            def get_checked_items(row, col_map):
                return [name for name, col_key in col_map.items() if row.get(col_key, False)]

            for i in working_df.index:
                orig_idx = working_df.loc[i, '_original_idx']
                
                # A. Single Select Logic for Implementation
                checked_impls = get_checked_items(working_df.loc[i], i_cols)
                
                # Logic: If NC(Impl) is checked, uncheck others. Else if Custom/Standard, enforce single.
                if 'Non-Compliant' in checked_impls:
                    for name in checked_impls:
                        if name != 'Non-Compliant': working_df.loc[i, i_cols[name]] = False
                elif len(checked_impls) > 1:
                    # Priority rule: If customize is checked, keep it (assume user wants to override standard)
                    if 'Customize/Integration' in checked_impls:
                        working_df.loc[i, i_cols['Standard']] = False
                
                # B. Non-Compliant Logic for Product
                if working_df.loc[i, p_cols['Non-Compliant']]:
                    # Clear other products
                    for name, col_key in p_cols.items():
                        if name != 'Non-Compliant': working_df.loc[i, col_key] = False
                    
                    # Force Implementation to NC
                    working_df.loc[i, i_cols['Non-Compliant']] = True
                    working_df.loc[i, i_cols['Standard']] = False
                    working_df.loc[i, i_cols['Customize/Integration']] = False

                # C. Reconstruct Strings for Backend
                curr_prods = get_checked_items(working_df.loc[i], p_cols)
                curr_impls = get_checked_items(working_df.loc[i], i_cols) # Re-get after logic
                
                curr_prod_str = ", ".join(curr_prods)
                curr_impl_str = ", ".join(curr_impls)
                
                # D. Check Change
                orig_data = st.session_state.original_selections.get(orig_idx, {})
                def clean_set(s): 
                    return set([x.strip() for x in str(s).replace('[','').replace(']','').replace("'",'').split(',') if x.strip() and x.strip() != 'nan'])
                
                is_changed = (clean_set(curr_prod_str) != clean_set(orig_data.get('products'))) or \
                             (clean_set(curr_impl_str) != clean_set(orig_data.get('implementation')))
                
                new_status = '✅ Edited' if is_changed else '🤖 Auto'
                working_df.loc[i, '📝 Status'] = new_status
                
                # Update Main State
                st.session_state.processed_df.loc[orig_idx, 'Product_Match'] = curr_prod_str
                st.session_state.processed_df.loc[orig_idx, 'Implementation'] = curr_impl_str
                st.session_state.processed_df.loc[orig_idx, 'Requirement_Type'] = working_df.loc[i, 'Requirement_Type']
                st.session_state.processed_df.loc[orig_idx, '📝 Status'] = new_status

            st.session_state.edited_df = working_df
            st.success("✅ Changes Saved!"); time.sleep(0.5); st.rerun()

        # --- EXPORT ---
        st.markdown("### 💾 Export & Save")
        final_df = st.session_state.edited_df if st.session_state.edited_df is not None else st.session_state.processed_df.copy()
        
        # Prepare for Save (Filter NC)
        valid_rows = final_df[~final_df['Product_Match'].str.contains('Non-Compliant', na=False)].copy()
        
        def split_lang(row):
            txt = str(row['TOR_Sentence'])
            return pd.Series([txt, ""]) if re.search(r'[\u0E00-\u0E7F]', txt) else pd.Series(["", txt])
        
        if not valid_rows.empty:
            valid_rows[['Sentence_TH', 'Sentence_ENG']] = valid_rows.apply(split_lang, axis=1)
            save_data = valid_rows[['Product_Match', 'Sentence_TH', 'Sentence_ENG', 'Implementation']].rename(columns={'Product_Match':'Product'})
        else: 
            save_data = pd.DataFrame(columns=['Product', 'Sentence_TH', 'Sentence_ENG', 'Implementation'])

        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("💾 Save to Google Sheet", type="primary", disabled=len(save_data)==0):
                with st.spinner("Saving..."):
                    try:
                        save_to_product_spec(save_data, sheet_url)
                        st.session_state.save_history.append({'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'count': len(save_data), 'data': save_data.to_dict('records')})
                        st.success("✅ Saved!"); time.sleep(1.5); st.rerun()
                    except Exception as e: st.error(f"Failed: {e}")
        with c2:
            out = BytesIO()
            with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
                exp = final_df[['TOR_Sentence', 'Product_Match', 'Implementation', 'Requirement_Type']].rename(columns={'TOR_Sentence':'Requirement', 'Product_Match':'Selected product', 'Requirement_Type':'Requirement type'})
                exp.to_excel(writer, sheet_name='Data', index=False)
            fname = f"{st.session_state.file_name.rsplit('.', 1)[0]}_compliant.xlsx" if st.session_state.file_name else "export.xlsx"
            st.download_button("⬇️ Download Excel", data=out.getvalue(), file_name=fname, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        with c3:
            if st.button("🔄 Reset Analysis"): st.session_state.clear(); st.rerun()

# ==========================================
# TAB 2: BUDGET
# ==========================================
with tab_budget:
    st.markdown("### 💰 Budget Estimation")
    if not st.session_state.analysis_done: 
        st.warning("⚠️ Please complete verification first.")
    else:
        if not st.session_state.budget_calculated:
            if st.button("Generate Budget", type="primary"):
                with st.spinner("Calculating..."):
                    try:
                        st.session_state.budget_factors = extract_budget_factors(st.session_state.tor_raw_text, st.session_state.gemini_key)
                        st.session_state.budget_calculated = True; st.rerun()
                    except: st.error("Failed")
        
        if st.session_state.budget_calculated:
            res = calculate_budget_sheets(st.session_state.budget_factors, st.session_state.matched_products, st.session_state.pricing_df, st.session_state.addon_df)
            st.markdown("#### 🧾 Cost Breakdown")
            total = 0
            for r in res:
                with st.expander(f"📦 {r['Product']}", expanded=True):
                    st.markdown("\n".join([l.lstrip() for l in format_budget_report(r['Product'], r['Package'], st.session_state.budget_factors, r['Breakdown']).split('\n')]), unsafe_allow_html=True)
                total += r['Breakdown']['total'] + (r['Package'].get('Initial_Fee (THB)', 0) if isinstance(r['Package'].get('Initial_Fee (THB)'), (int, float)) else 0)
            
            md_cost = st.session_state.budget_factors.get('mandays', 0) * 22000
            oth_cost = st.session_state.budget_factors.get('other_expenses', 0.0)
            
            if md_cost: st.markdown(f"<div style='background:#EFF6FF; padding:15px; border-radius:8px; margin-top:15px; border:1px solid #BFDBFE;'><h4 style='color:#1E40AF; margin:0;'>🛠️ Customization</h4><p style='margin:5px 0 0 0;'>{st.session_state.budget_factors.get('mandays')} Mandays × 22,000 = <strong>{md_cost:,.0f} THB</strong></p></div>", unsafe_allow_html=True)
            if oth_cost: st.markdown(f"<div style='background:#FFF7ED; padding:15px; border-radius:8px; margin-top:15px; border:1px solid #FED7AA;'><h4 style='color:#C2410C; margin:0;'>💸 Other</h4><p style='margin:5px 0 0 0;'><strong>{oth_cost:,.0f} THB</strong></p></div>", unsafe_allow_html=True)
            
            st.markdown(f"<div style='background:#DCFCE7; padding:25px; border-radius:12px; border-left:6px solid #10B981; text-align:right; margin-top:25px;'><h4 style='color:#065F46; margin:0;'>TOTAL ANNUAL BUDGET</h4><h1 style='color:#047857; margin:0; font-size:1.8rem;'>{total + md_cost + oth_cost:,.2f} THB/Year</h1></div>", unsafe_allow_html=True)
            
            st.markdown("---"); st.markdown("#### ✏️ Adjust Factors")
            f = st.session_state.budget_factors
            c1, c2 = st.columns(2)
            with c1: st.markdown("##### 🔹 Zocial Eye"); zu = st.number_input("Users", value=f.get('num_users', 2)); zd = st.number_input("Days", value=f.get('data_backward_days', 90))
            with c2: st.markdown("##### 🔸 Warroom"); wu = st.number_input("Users", value=f.get('num_users', 5), key='wu'); wt = st.number_input("Tx", value=f.get('monthly_transactions', 35000))
            c3, c4 = st.columns(2)
            with c3: wc = st.number_input("Channels", value=f.get('social_channels_count', 0)); wb = st.checkbox("Chatbot", value=f.get('chatbot_required', False))
            st.markdown("<hr style='margin:1.5rem 0; border-top:1px solid #E2E8F0;'>", unsafe_allow_html=True)
            st.markdown("##### ➕ Additional")
            c5, c6 = st.columns(2)
            with c5: md = st.number_input("Mandays", value=f.get('mandays', 0))
            with c6: ot = st.number_input("Other (THB)", value=float(f.get('other_expenses', 0.0)))
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔄 Recalculate"):
                st.session_state.budget_factors.update({'num_users': zu, 'data_backward_days': zd, 'monthly_transactions': wt, 'social_channels_count': wc, 'chatbot_required': wb, 'mandays': md, 'other_expenses': ot})
                st.rerun()

st.markdown("---"); st.caption(f"WiseTOR Sense v2.5.2 | Session: {datetime.now().strftime('%Y-%m-%d')}")
