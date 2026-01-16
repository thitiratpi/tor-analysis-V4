import streamlit as st
import pandas as pd
import json
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
        'About': "# WiseSight TOR Analyzer\nVersion 2.2.2\nPowered by Streamlit + Gemini AI"
    }
)

# Custom CSS
st.markdown("""
<style>
    /* ===== GLOBAL STYLES ===== */
    .main { padding: 0rem 1rem; }
    
    /* ===== HEADER STYLES ===== */
    .main-header { font-size: 2.5rem; font-weight: bold; color: #1f77b4; margin-bottom: 0.5rem; text-align: center; }
    .step-header { font-size: 1.8rem; font-weight: bold; color: #ff7f0e; margin-top: 2rem; margin-bottom: 1rem; padding-left: 0.5rem; border-left: 5px solid #ff7f0e; }
    
    /* ===== CARD STYLES ===== */
    .success-box { padding: 1rem; border-radius: 0.5rem; background-color: #d4edda; border-left: 5px solid #28a745; margin: 1rem 0; }
    .warning-box { padding: 1rem; border-radius: 0.5rem; background-color: #fff3cd; border-left: 5px solid #ffc107; margin: 1rem 0; }
    .error-box { padding: 1rem; border-radius: 0.5rem; background-color: #f8d7da; border-left: 5px solid #dc3545; margin: 1rem 0; }
    .info-box { padding: 1rem; border-radius: 0.5rem; background-color: #d1ecf1; border-left: 5px solid #17a2b8; margin: 1rem 0; }
    
    /* ===== BUTTON STYLES ===== */
    .stButton > button { width: 100%; border-radius: 5px; height: 3rem; font-weight: 600; transition: all 0.3s ease; }
    .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
    
    /* ===== DATA EDITOR STYLES ===== */
    .stDataFrame { border-radius: 10px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    
    /* ===== METRICS STYLES ===== */
    [data-testid="stMetricValue"] { font-size: 2rem; font-weight: bold; }
    
    /* ===== FILE UPLOADER ===== */
    [data-testid="stFileUploader"] { border: 2px dashed #1f77b4; border-radius: 10px; padding: 2rem; background-color: #f8f9fa; transition: all 0.3s ease; }
    [data-testid="stFileUploader"]:hover { border-color: #ff7f0e; background-color: #fff; }
    
    /* ===== SIDEBAR STYLES ===== */
    [data-testid="stSidebar"] { background-color: #f8f9fa; }
    
    /* ===== TABS ===== */
    .stTabs [data-baseweb="tab-list"] { gap: 2rem; background-color: #f0f2f6; padding: 0.5rem; border-radius: 10px; }
    .stTabs [data-baseweb="tab"] { height: 3rem; border-radius: 5px; padding: 0 1.5rem; font-weight: 600; }
    .stTabs [aria-selected="true"] { background-color: #1f77b4; color: white; }
    
    /* ===== HIDE STREAMLIT BRANDING ===== */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# SESSION STATE INITIALIZATION
# ==========================================

if 'processed_df' not in st.session_state:
    st.session_state.processed_df = None
if 'edited_df' not in st.session_state:
    st.session_state.edited_df = None
if 'spec_df' not in st.session_state:
    st.session_state.spec_df = None
if 'pricing_df' not in st.session_state:
    st.session_state.pricing_df = None
if 'addon_df' not in st.session_state:
    st.session_state.addon_df = None
if 'file_uploaded' not in st.session_state:
    st.session_state.file_uploaded = False
if 'analysis_done' not in st.session_state:
    st.session_state.analysis_done = False
if 'budget_calculated' not in st.session_state:
    st.session_state.budget_calculated = False
if 'save_history' not in st.session_state:
    st.session_state.save_history = []
if 'tor_raw_text' not in st.session_state:
    st.session_state.tor_raw_text = None
if 'matched_products' not in st.session_state:
    st.session_state.matched_products = []
if 'is_excel' not in st.session_state:
    st.session_state.is_excel = False
# ✅ User edit tracking
if 'original_selections' not in st.session_state:
    st.session_state.original_selections = {}
if 'user_modified_rows' not in st.session_state:
    st.session_state.user_modified_rows = set()

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
    st.title("🔧 Configuration")
    
    # ===== 1. API STATUS (AUTO-LOAD FROM SECRETS) =====
    st.subheader("🔐 API Status")
    
    try:
        if 'gemini_key' not in st.session_state or st.session_state.gemini_key is None:
            st.session_state.gemini_key = st.secrets["GEMINI_API_KEY"]
        
        st.markdown("""
        <div style='background-color: #d4edda; padding: 12px; border-radius: 8px; border-left: 4px solid #28a745;'>
            <p style='margin: 0; color: #155724; font-weight: 600;'>
                ✅ Gemini AI: Connected
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.caption("🔗 Loaded from Streamlit secrets")
        
    except Exception as e:
        st.markdown("""
        <div style='background-color: #f8d7da; padding: 12px; border-radius: 8px; border-left: 4px solid #dc3545;'>
            <p style='margin: 0; color: #721c24; font-weight: 600;'>
                ❌ Gemini AI: Not configured
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("⚙️ How to configure", expanded=False):
            st.markdown("""
            **Step 1:** App Settings > Secrets
            **Step 2:** Add: `GEMINI_API_KEY = "AIzaSy..."`
            """)
        st.session_state.gemini_key = None
    
    st.divider()
    
    # ===== 2. GOOGLE SHEET =====
    st.subheader("📊 Google Sheet")
    sheet_url = st.text_input(
        "Sheet URL",
        value="https://docs.google.com/spreadsheets/d/1j-l7KmbwK7h5Sp023pu2K91NOzVRQascjVwLLmtvPX4",
        help="Master data sheet URL"
    )
    
    if st.button("🔄 Reload Master Data"):
        with st.spinner("Loading..."):
            try:
                pricing_df, addon_df, spec_df, def_dict = load_master_data(sheet_url)
                st.session_state.pricing_df = pricing_df
                st.session_state.addon_df = addon_df
                st.session_state.spec_df = spec_df
                st.session_state.def_dict = def_dict
                st.success(f"✅ Loaded {len(spec_df)} products")
            except Exception as e:
                st.error(f"❌ Failed: {e}")
    
    st.divider()
    
    # ===== 3. ANALYSIS OPTIONS =====
    st.subheader("⚙️ Analysis Options")
    enable_ai_formatting = st.checkbox("🤖 AI Text Formatting", value=True)
    enable_fr_nfr = st.checkbox("📊 FR/NFR Classification", value=True)
    
    st.divider()
    
    # ===== 4. SAVE HISTORY =====
    st.subheader("📜 Save History")
    if st.session_state.save_history:
        for idx, record in enumerate(reversed(st.session_state.save_history[-5:])):
            with st.expander(f"#{len(st.session_state.save_history)-idx}: {record['timestamp']}", expanded=False):
                st.write(f"**Rows saved:** {record['count']}")
                if st.button(f"⏮️ Undo", key=f"undo_{idx}"):
                    with st.spinner("Undoing..."):
                        try:
                            undo_last_update(record['data'], sheet_url)
                            st.session_state.save_history.pop(-1-idx)
                            st.success("✅ Undo successful!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Undo failed: {e}")
    else:
        st.info("No save history yet")

# ==========================================
# MAIN APP
# ==========================================

st.markdown('<p class="main-header">🔍 WiseSight TOR Analyzer</p>', unsafe_allow_html=True)
st.caption("AI-powered compliance checking with interactive verification & budget estimation")

# Progress bar
progress_steps = []
if st.session_state.file_uploaded: progress_steps.append("📂 File Uploaded")
if st.session_state.analysis_done: progress_steps.append("🤖 Analysis Done")
if st.session_state.budget_calculated: progress_steps.append("💰 Budget Calculated")
if progress_steps: st.info(" → ".join(progress_steps))

# ===== STEP 1: FILE UPLOAD =====
st.markdown('<p class="step-header">1️⃣ Upload TOR File</p>', unsafe_allow_html=True)
col1, col2 = st.columns([3, 1])

with col1:
    uploaded_file = st.file_uploader("Choose TOR file", type=['pdf', 'docx', 'txt', 'xlsx', 'xls'])

with col2:
    if uploaded_file: st.metric("File Size", f"{uploaded_file.size / 1024:.1f} KB")

if uploaded_file and not st.session_state.file_uploaded:
    with st.spinner("📂 Reading file..."):
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
            st.session_state.file_uploaded = True
            
            if uploaded_file.name.endswith(('.xlsx', '.xls')):
                st.session_state.is_excel = True
                st.info("📊 Excel file detected: Structure preserved")
            else:
                st.session_state.is_excel = False
            
            with st.expander("👀 Preview Raw Text", expanded=False):
                st.text_area("Raw content", file_content[:2000] + "...", height=200, disabled=True)
            
            st.success(f"✅ File loaded: {uploaded_file.name}")
        except Exception as e:
            st.error(f"❌ Error reading file: {e}")

# ===== STEP 2: AI ANALYSIS =====
if st.session_state.file_uploaded and not st.session_state.analysis_done:
    st.markdown('<p class="step-header">2️⃣ AI Analysis</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1: st.info(f"🧠 **AI Formatting**\n\n{'✅ Enabled' if enable_ai_formatting else '⏭️ Skipped'}")
    with col2: st.info(f"🎯 **Product Matching**\n\n✅ Always Enabled")
    with col3: st.info(f"📊 **FR/NFR Classify**\n\n{'✅ Enabled' if enable_fr_nfr else '⏭️ Skipped'}")
    
    if st.button("🚀 Start Analysis", type="primary", use_container_width=True):
        if not st.session_state.gemini_key:
            st.error("❌ Configure API Key first"); st.stop()
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # 1. Formatting
            status_text.text("🤖 Step 1/4: AI Text Formatting...")
            progress_bar.progress(10)
            if enable_ai_formatting and not st.session_state.is_excel:
                formatted_text = extract_scope_smart_ai(st.session_state.tor_raw_text, st.session_state.gemini_key)
            else:
                formatted_text = st.session_state.tor_raw_text
            
            # 2. Extract
            progress_bar.progress(30)
            status_text.text("📝 Step 2/4: Extracting sentences...")
            sentences = extract_sentences_from_tor(formatted_text)
            
            # 3. Matching
            progress_bar.progress(50)
            status_text.text("🎯 Step 3/4: Product Matching...")
            matched_products, result_df = analyze_tor_sentences_full_mode(
                sentences, st.session_state.spec_df, st.session_state.gemini_key
            )
            
            # 4. Classification
            progress_bar.progress(80)
            if enable_fr_nfr:
                status_text.text("📊 Step 4/4: FR/NFR Classification...")
                result_df['Requirement_Type'] = classify_scope_hybrid(sentences, st.session_state.gemini_key)
            else:
                result_df['Requirement_Type'] = 'Functional'
            
            progress_bar.progress(100)
            
            # Store results
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
            import traceback; st.code(traceback.format_exc())

# ===== STEP 3: INTERACTIVE VERIFICATION =====
if st.session_state.analysis_done:
    st.markdown('<p class="step-header">3️⃣ Verify & Edit Results</p>', unsafe_allow_html=True)
    
    # -----------------------------------------------
    # PREPARE DATAFRAME FOR DISPLAY
    # -----------------------------------------------
    # Use processed_df as Source of Truth
    df = st.session_state.processed_df.copy()
    
    # Define options
    product_options = ['Zocial Eye', 'Warroom', 'Outsource', 'Other Product', 'Non-Compliant']
    impl_options = ['Standard', 'Customize/Integration', 'Non-Compliant']
    
    # Ensure Original Selections Exist
    if 'original_selections' not in st.session_state or len(st.session_state.original_selections) == 0:
        st.session_state.original_selections = {}
        for idx in df.index:
            st.session_state.original_selections[idx] = {
                'products': str(df.loc[idx, 'Product_Match']),
                'implementation': str(df.loc[idx, 'Implementation'])
            }

    # Generate Checkbox Columns from String Columns
    for prod in product_options:
        df[f"📦 {prod}"] = df['Product_Match'].apply(lambda x: prod in str(x))
    
    for impl in impl_options:
        df[f"🔧 {impl}"] = df['Implementation'].apply(lambda x: impl in str(x))
    
    # Ensure Status Column
    if '📝 Status' not in df.columns:
        df['📝 Status'] = '🤖 Auto'

    # Store index
    df['_original_idx'] = df.index
    df.index = range(1, len(df) + 1) # Display index
    df.index.name = 'No.'

    # -----------------------------------------------
    # TABS
    # -----------------------------------------------
    tab1, tab2, tab3 = st.tabs(["📊 Data Editor", "📈 Statistics", "🔍 Filter & Search"])
    
    with tab1:
        st.caption("✏️ Click checkboxes to edit. Status updates to '✅ Edited' automatically.")
        
        # CSS for Better Table
        st.markdown("""
        <style>
        div[data-testid="stDataFrame"] div[role="gridcell"] {
            white-space: pre-wrap !important; word-wrap: break-word !important;
            padding: 12px 8px !important; line-height: 1.5 !important;
        }
        div[data-testid="stDataFrame"] [aria-colindex="4"], div[data-testid="stDataFrame"] [aria-colindex="5"],
        div[data-testid="stDataFrame"] [aria-colindex="6"], div[data-testid="stDataFrame"] [aria-colindex="7"],
        div[data-testid="stDataFrame"] [aria-colindex="8"] { background-color: #f5f9ff !important; }
        div[data-testid="stDataFrame"] [aria-colindex="9"], div[data-testid="stDataFrame"] [aria-colindex="10"],
        div[data-testid="stDataFrame"] [aria-colindex="11"] { background-color: #fffbf5 !important; }
        </style>
        """, unsafe_allow_html=True)

        column_config = {
            "Product_Match": None, "Implementation": None, "_original_idx": None,
            "TOR_Sentence": st.column_config.TextColumn("Requirement", width="large", disabled=True),
            "Requirement_Type": st.column_config.SelectboxColumn("Type", options=["Functional", "Non-Functional"], width="medium"),
            "📝 Status": st.column_config.TextColumn("Status", width="small", disabled=True),
            "Matched_Keyword": st.column_config.TextColumn("Matched Spec", width="medium"),
        }
        
        # Add Checkbox Configs
        for prod in product_options:
            column_config[f"📦 {prod}"] = st.column_config.CheckboxColumn(f"🔵 {prod}", width="small")
        for impl in impl_options:
            column_config[f"🔧 {impl}"] = st.column_config.CheckboxColumn(f"🟠 {impl}", width="small")

        # -----------------------------------------------
        # ✅ DISPLAY UI LEGEND (Updated per request)
        # -----------------------------------------------
        st.markdown("""
        <div style='background-color: #f0f2f6; padding: 15px; border-radius: 8px; margin-bottom: 15px;'>
            <strong style='font-size: 1.1em;'>📌 Column Groups & Status Indicators:</strong><br><br>
            <div style='display: flex; gap: 20px; flex-wrap: wrap;'>
                <div style='flex: 1; min-width: 200px;'>
                    <div style='background: linear-gradient(135deg, #2196f3 0%, #64b5f6 100%); 
                                color: white; padding: 8px 12px; border-radius: 5px; margin-bottom: 8px;'>
                        <strong>🔵 Selected Product</strong>
                    </div>
                    <small style='color: #333;'>
                        ✓ Can select multiple<br>
                        ✓ Choose all that apply
                    </small>
                </div>
                <div style='flex: 1; min-width: 250px;'>
                    <div style='background: linear-gradient(135deg, #ff9800 0%, #ffb74d 100%); 
                                color: white; padding: 8px 12px; border-radius: 5px; margin-bottom: 8px;'>
                        <strong>🟠 Implementation</strong>
                    </div>
                    <small style='color: #333;'>
                        ⚠️ Select ONLY ONE<br>
                        ⚠️ If the product is marked as Non-Compliant, only Non-Compliant can be selected
                    </small>
                </div>
                <div style='flex: 1; min-width: 200px;'>
                    <div style='background: linear-gradient(135deg, #9e9e9e 0%, #bdbdbd 100%); 
                                color: white; padding: 8px 12px; border-radius: 5px; margin-bottom: 8px;'>
                        <strong>📝 Status</strong>
                    </div>
                    <small style='color: #333;'>
                        🤖 Auto = System<br>
                        ✅ Edited = You changed
                    </small>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # -----------------------------------------------
        # DATA EDITOR RENDERING
        # -----------------------------------------------
        edited_df = st.data_editor(
            df,
            column_config=column_config,
            column_order=[
                "TOR_Sentence", "Requirement_Type",
                "📦 Zocial Eye", "📦 Warroom", "📦 Outsource", "📦 Other Product", "📦 Non-Compliant",
                "🔧 Standard", "🔧 Customize/Integration", "🔧 Non-Compliant",
                "📝 Status", "Matched_Keyword"
            ],
            hide_index=False,
            use_container_width=True,
            num_rows="dynamic",
            height=600,
            key="data_editor"
        )
        
        # -----------------------------------------------
        # ✅ LOGIC ENFORCEMENT & STATUS UPDATE
        # -----------------------------------------------
        needs_rerun = False
        
        # Helper to normalize list for comparison
        def normalize_selection(val_str):
            if not val_str or pd.isna(val_str) or val_str == 'nan': return []
            clean = str(val_str).replace("[","").replace("]","").replace("'","")
            return sorted([x.strip() for x in clean.split(',') if x.strip() and x.strip() != 'nan'])

        impl_cols = [f"🔧 {i}" for i in impl_options]

        for i in edited_df.index:
            # --- 1. ENFORCE SINGLE SELECT (IMPLEMENTATION) ---
            checked_impls = [col for col in impl_cols if edited_df.loc[i, col]]
            
            if len(checked_impls) > 1:
                # Find which one was newly checked by comparing with 'df' (Pre-edit state)
                newly_checked = [col for col in impl_cols if edited_df.loc[i, col] and not df.loc[i, col]]
                
                if newly_checked:
                    keep_col = newly_checked[0]
                    for col in impl_cols:
                        if col != keep_col: edited_df.loc[i, col] = False
                else:
                    # Fallback priority if multiple exist initially
                    if edited_df.loc[i, '🔧 Non-Compliant']:
                        edited_df.loc[i, '🔧 Standard'] = False
                        edited_df.loc[i, '🔧 Customize/Integration'] = False
                    elif edited_df.loc[i, '🔧 Customize/Integration']:
                        edited_df.loc[i, '🔧 Standard'] = False
                
                needs_rerun = True

            # --- 2. PRODUCT NON-COMPLIANT LOGIC ---
            if edited_df.loc[i, '📦 Non-Compliant']:
                prod_cols_to_clear = ['📦 Zocial Eye', '📦 Warroom', '📦 Outsource', '📦 Other Product']
                if any(edited_df.loc[i, c] for c in prod_cols_to_clear):
                    for c in prod_cols_to_clear: edited_df.loc[i, c] = False
                    needs_rerun = True
                
                # Auto-force Implementation
                if not edited_df.loc[i, '🔧 Non-Compliant']:
                    edited_df.loc[i, '🔧 Non-Compliant'] = True
                    edited_df.loc[i, '🔧 Standard'] = False
                    edited_df.loc[i, '🔧 Customize/Integration'] = False
                    needs_rerun = True

            # --- 3. STATUS CHECK (AUTO vs EDITED) & SYNC ---
            # Reconstruct Strings
            curr_prods = [p for p in product_options if edited_df.loc[i, f"📦 {p}"]]
            curr_impls = [imp for imp in impl_options if edited_df.loc[i, f"🔧 {imp}"]]
            
            curr_prod_str = ", ".join(curr_prods)
            curr_impl_str = ", ".join(curr_impls)
            
            # Get Original
            orig_idx = edited_df.loc[i, '_original_idx']
            orig_data = st.session_state.original_selections.get(orig_idx, {})
            
            # Compare Lists
            is_changed = (normalize_selection(curr_prod_str) != normalize_selection(orig_data.get('products'))) or \
                         (normalize_selection(curr_impl_str) != normalize_selection(orig_data.get('implementation')))
            
            new_status = '✅ Edited' if is_changed else '🤖 Auto'
            
            # Update Status Column in Editor View
            if edited_df.loc[i, '📝 Status'] != new_status:
                edited_df.loc[i, '📝 Status'] = new_status
                needs_rerun = True
            
            # SYNC BACK TO SESSION STATE (SOURCE OF TRUTH)
            # This ensures next rerun uses updated values
            st.session_state.processed_df.loc[orig_idx, 'Product_Match'] = curr_prod_str
            st.session_state.processed_df.loc[orig_idx, 'Implementation'] = curr_impl_str
            st.session_state.processed_df.loc[orig_idx, 'Requirement_Type'] = edited_df.loc[i, 'Requirement_Type']
            
            if '📝 Status' not in st.session_state.processed_df.columns:
                 st.session_state.processed_df['📝 Status'] = '🤖 Auto'
            st.session_state.processed_df.loc[orig_idx, '📝 Status'] = new_status

        # If changes happened that need UI update
        if needs_rerun:
            st.rerun()

        # Update display pointer
        st.session_state.edited_df = edited_df
        
        # User Modification Stats
        user_edit_count = len(edited_df[edited_df['📝 Status'] == '✅ Edited'])
        auto_count = len(edited_df) - user_edit_count
        
        col1, col2 = st.columns(2)
        with col1: st.metric("✅ User Edited", user_edit_count)
        with col2: st.metric("🤖 Auto Suggestions", auto_count)

    with tab2:
        # Statistics
        col1, col2, col3, col4 = st.columns(4)
        total_rows = len(edited_df)
        with col1: st.metric("Total Requirements", total_rows)
        with col2: 
            nc = edited_df['📦 Non-Compliant'].sum()
            st.metric("Non-Compliant", nc, delta_color="inverse")
        with col3: 
            st.metric("Compliant", total_rows - nc)
        with col4: 
            mp = sum(edited_df[['📦 Zocial Eye', '📦 Warroom']].sum(axis=1) > 1)
            st.metric("Multi-Product", mp)
            
        st.subheader("📊 Visual Analysis")
        col1, col2 = st.columns(2)
        with col1:
            st.bar_chart({p: edited_df[f"📦 {p}"].sum() for p in product_options})
        with col2:
            st.bar_chart(edited_df['Requirement_Type'].value_counts())
            
    with tab3:
        st.subheader("🔍 Search & Filter")
        search_term = st.text_input("Search in Requirement", "")
        filter_status = st.multiselect("Filter by Status", ["🤖 Auto", "✅ Edited"])
        
        filtered_df = edited_df.copy()
        if search_term:
            filtered_df = filtered_df[filtered_df['TOR_Sentence'].str.contains(search_term, case=False, na=False)]
        if filter_status:
            filtered_df = filtered_df[filtered_df['📝 Status'].isin(filter_status)]
            
        st.dataframe(filtered_df, use_container_width=True)

# ===== STEP 4: BUDGET ESTIMATION =====
if st.session_state.analysis_done:
    st.markdown('<p class="step-header">4️⃣ Budget Estimation</p>', unsafe_allow_html=True)
    
    if not st.session_state.budget_calculated:
        if st.button("💰 Calculate Budget", type="primary", use_container_width=True):
            with st.spinner("🤖 AI analyzing..."):
                try:
                    factors = extract_budget_factors(st.session_state.tor_raw_text, st.session_state.gemini_key)
                    st.session_state.budget_factors = factors
                    st.session_state.budget_calculated = True
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Failed: {e}")
    
    if st.session_state.budget_calculated:
        with st.expander("🔍 Budget Factors", expanded=True):
            factors = st.session_state.budget_factors
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Zocial Eye")
                ze_users = st.number_input("Users", value=factors.get('num_users', 2), min_value=1)
                ze_days = st.number_input("Data (Days)", value=factors.get('data_backward_days', 90), step=30)
            with col2:
                st.subheader("Warroom")
                wr_tx = st.number_input("Transactions", value=factors.get('monthly_transactions', 35000), step=1000)
                wr_ch = st.number_input("Channels", value=factors.get('social_channels_count', 0))
            
            if st.button("🔄 Recalculate"):
                st.session_state.budget_factors.update({
                    'num_users': ze_users, 'data_backward_days': ze_days,
                    'monthly_transactions': wr_tx, 'social_channels_count': wr_ch
                })
                st.rerun()
                
        # Report
        results = calculate_budget_sheets(
            st.session_state.budget_factors, st.session_state.matched_products,
            st.session_state.pricing_df, st.session_state.addon_df
        )
        
        total_budget = 0
        if results:
            for res in results:
                st.markdown(format_budget_report(res['Product'], res['Package'], st.session_state.budget_factors, res['Breakdown']), unsafe_allow_html=True)
                total_budget += res['Breakdown']['total'] + (res['Package'].get('Initial_Fee (THB)', 0) if isinstance(res['Package'].get('Initial_Fee (THB)', 0), (int, float)) else 0)
            
            st.markdown(f"""
            <div style='background-color: #d4edda; padding: 20px; border-radius: 10px; border-left: 5px solid #28a745; text-align: right;'>
                <h2 style='color: #155724; margin:0;'>💰 GRAND TOTAL: {total_budget:,.2f} THB/Year</h2>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("⚠️ No suitable package found.")

# ===== STEP 5: SAVE =====
if st.session_state.edited_df is not None:
    st.markdown('<p class="step-header">5️⃣ Save & Export</p>', unsafe_allow_html=True)
    
    save_data = prepare_save_data(st.session_state.edited_df, product_options, impl_options)
    save_data = save_data[~save_data['Product'].str.contains('Non-Compliant', na=False)]
    
    col1, col2 = st.columns([2, 1])
    with col1: st.info(f"📊 Ready to save: {len(save_data)} rows")
    with col2: 
        if st.button("👀 Preview"): 
            st.dataframe(save_data, use_container_width=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("💾 Save to Sheet", type="primary", disabled=len(save_data)==0, use_container_width=True):
            with st.spinner("Saving..."):
                try:
                    save_to_product_spec(save_data, sheet_url)
                    st.session_state.save_history.append({
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'count': len(save_data), 'products': list(save_data['Product'].unique()),
                        'data': save_data.to_dict('records')
                    })
                    st.success("✅ Saved!"); st.balloons()
                except Exception as e: st.error(f"❌ Failed: {e}")
                
    with c2:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            save_data.to_excel(writer, sheet_name='Data', index=False)
        st.download_button("⬇️ Download Excel", data=output.getvalue(), file_name="export.xlsx", mime="application/vnd.ms-excel", use_container_width=True)
        
    with c3:
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.clear(); st.rerun()

st.divider()
st.caption(f"WiseSight TOR Analyzer v2.2.2 | Session: {datetime.now().strftime('%Y-%m-%d')}")
