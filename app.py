"""
================================================================================
WISESIGHT STREAMLIT APP V2.1 - COMPLETE
================================================================================
Full-featured TOR Analysis with Budget Engine
- Advanced file reading (PDF/Word/Excel)
- AI text formatting (optional)
- Product matching (multi-product)
- FR/NFR classification (optional)
- Budget estimation
- Interactive verification
- Google Sheet integration
================================================================================
"""

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
        'About': "# WiseSight TOR Analyzer\nVersion 2.1.0\nPowered by Streamlit + Gemini AI"
    }
)

# Custom CSS
st.markdown("""
<style>
    /* ===== GLOBAL STYLES ===== */
    .main {
        padding: 0rem 1rem;
    }
    
    /* ===== HEADER STYLES ===== */
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
        text-align: center;
    }
    
    .step-header {
        font-size: 1.8rem;
        font-weight: bold;
        color: #ff7f0e;
        margin-top: 2rem;
        margin-bottom: 1rem;
        padding-left: 0.5rem;
        border-left: 5px solid #ff7f0e;
    }
    
    /* ===== CARD STYLES ===== */
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border-left: 5px solid #28a745;
        margin: 1rem 0;
    }
    
    .warning-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
        margin: 1rem 0;
    }
    
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border-left: 5px solid #dc3545;
        margin: 1rem 0;
    }
    
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border-left: 5px solid #17a2b8;
        margin: 1rem 0;
    }
    
    /* ===== BUTTON STYLES ===== */
    .stButton > button {
        width: 100%;
        border-radius: 5px;
        height: 3rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    /* ===== DATA EDITOR STYLES ===== */
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* ===== METRICS STYLES ===== */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: bold;
    }
    
    /* ===== FILE UPLOADER ===== */
    [data-testid="stFileUploader"] {
        border: 2px dashed #1f77b4;
        border-radius: 10px;
        padding: 2rem;
        background-color: #f8f9fa;
        transition: all 0.3s ease;
    }
    
    [data-testid="stFileUploader"]:hover {
        border-color: #ff7f0e;
        background-color: #fff;
    }
    
    /* ===== SIDEBAR STYLES ===== */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
    }
    
    /* ===== TABS ===== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        background-color: #f0f2f6;
        padding: 0.5rem;
        border-radius: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 3rem;
        border-radius: 5px;
        padding: 0 1.5rem;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #1f77b4;
        color: white;
    }
    
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
if 'gemini_key' not in st.session_state:
    st.session_state.gemini_key = None
if 'is_excel' not in st.session_state:
    st.session_state.is_excel = False

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
        # Try to load from Streamlit secrets
        if 'gemini_key' not in st.session_state or st.session_state.gemini_key is None:
            st.session_state.gemini_key = st.secrets["GEMINI_API_KEY"]
        
        # Success - show connected status
        st.markdown("""
        <div style='background-color: #d4edda; padding: 12px; border-radius: 8px; border-left: 4px solid #28a745;'>
            <p style='margin: 0; color: #155724; font-weight: 600;'>
                ✅ Gemini AI: Connected
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.caption("🔗 Loaded from Streamlit secrets")
        
    except Exception as e:
        # Failed - show error
        st.markdown("""
        <div style='background-color: #f8d7da; padding: 12px; border-radius: 8px; border-left: 4px solid #dc3545;'>
            <p style='margin: 0; color: #721c24; font-weight: 600;'>
                ❌ Gemini AI: Not configured
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("⚙️ How to configure", expanded=False):
            st.markdown("""
            **Step 1:** Go to App Settings
            - Click **Manage app** (⋮ menu)
            - Select **Settings** ⚙️
            
            **Step 2:** Add Secret
            - Click **Secrets** tab 🔐
            - Add the following:
```toml
            GEMINI_API_KEY = "AIzaSy..."
```
            
            **Step 3:** Reboot App
            - Click **Reboot app** to apply changes
            
            **Get API Key:** [Google AI Studio](https://makersuite.google.com/app/apikey)
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
    
    enable_ai_formatting = st.checkbox(
        "🤖 AI Text Formatting",
        value=True,
        help="Use AI to clean and format TOR text (skipped for Excel files)"
    )
    
    enable_fr_nfr = st.checkbox(
        "📊 FR/NFR Classification",
        value=True,
        help="Classify Functional vs Non-Functional requirements"
    )
    
    st.info("💡 Both features use Gemini API")
    
    st.divider()
    
    # ===== 4. SAVE HISTORY =====
    st.subheader("📜 Save History")
    if st.session_state.save_history:
        for idx, record in enumerate(reversed(st.session_state.save_history[-5:])):
            with st.expander(f"#{len(st.session_state.save_history)-idx}: {record['timestamp']}", expanded=False):
                st.write(f"**Rows saved:** {record['count']}")
                st.write(f"**Products:** {', '.join(record['products'])}")
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
if st.session_state.file_uploaded:
    progress_steps.append("📂 File Uploaded")
if st.session_state.analysis_done:
    progress_steps.append("🤖 Analysis Done")
if st.session_state.budget_calculated:
    progress_steps.append("💰 Budget Calculated")

if progress_steps:
    st.info(" → ".join(progress_steps))

# ===== STEP 1: FILE UPLOAD =====
st.markdown('<p class="step-header">1️⃣ Upload TOR File</p>', unsafe_allow_html=True)

col1, col2 = st.columns([3, 1])

with col1:
    uploaded_file = st.file_uploader(
        "Choose TOR file",
        type=['pdf', 'docx', 'txt', 'xlsx', 'xls'],
        help="Supported formats: PDF, Word, Excel, Text"
    )

with col2:
    if uploaded_file:
        st.metric("File Size", f"{uploaded_file.size / 1024:.1f} KB")

if uploaded_file and not st.session_state.file_uploaded:
    with st.spinner("📂 Reading file..."):
        try:
            # Read file content
            file_content = read_file_content(uploaded_file)
            
            # Load master data if not loaded
            if st.session_state.spec_df is None:
                with st.spinner("🔄 Loading master data from Google Sheet..."):
                    pricing_df, addon_df, spec_df, def_dict = load_master_data(sheet_url)
                    st.session_state.pricing_df = pricing_df
                    st.session_state.addon_df = addon_df
                    st.session_state.spec_df = spec_df
                    st.session_state.def_dict = def_dict
            
            # Store in session
            st.session_state.tor_raw_text = file_content
            st.session_state.file_name = uploaded_file.name
            st.session_state.file_uploaded = True
            
            # Detect Excel file
            if uploaded_file.name.endswith(('.xlsx', '.xls')):
                st.session_state.is_excel = True
                st.info("📊 Excel file detected: Will preserve row structure (AI formatting will be skipped)")
            else:
                st.session_state.is_excel = False
            
            # Display preview
            with st.expander("👀 Preview Raw Text", expanded=False):
                st.text_area("Raw content", file_content[:2000] + "...", height=200, disabled=True)
            
            st.success(f"✅ File loaded: {uploaded_file.name} ({len(file_content)} characters)")
            
        except Exception as e:
            st.error(f"❌ Error reading file: {e}")
            import traceback
            st.code(traceback.format_exc())

# ===== STEP 2: AI ANALYSIS =====
if st.session_state.file_uploaded and not st.session_state.analysis_done:
    st.markdown('<p class="step-header">2️⃣ AI Analysis</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status = "✅ Enabled" if enable_ai_formatting else "⏭️ Skipped"
        st.info(f"🧠 **AI Text Formatting**\nClean & structure TOR text\n\n{status}")
    with col2:
        st.info(f"🎯 **Product Matching**\nMatch to Zocial Eye / Warroom\n\n✅ Always Enabled")
    with col3:
        status = "✅ Enabled" if enable_fr_nfr else "⏭️ Skipped"
        st.info(f"📊 **FR/NFR Classification**\nFunctional vs Non-Functional\n\n{status}")
    
    if st.button("🚀 Start Analysis", type="primary", use_container_width=True):
        
        # Check API key
        if not st.session_state.gemini_key:
            st.error("❌ Please enter Gemini API Key in sidebar")
            st.stop()
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # STEP 1: AI Text Formatting (OPTIONAL)
            status_text.text("🤖 Step 1/4: AI Text Formatting...")
            progress_bar.progress(10)
            
            if enable_ai_formatting and not st.session_state.is_excel:
                formatted_text = extract_scope_smart_ai(
                    st.session_state.tor_raw_text,
                    st.session_state.gemini_key
                )
            else:
                formatted_text = st.session_state.tor_raw_text
                if st.session_state.is_excel:
                    print("   📊 Excel file: Skipping AI formatting to preserve structure")
                else:
                    print("   ⏭️ AI Formatting disabled by user")
            
            progress_bar.progress(30)
            
            # STEP 2: Extract sentences
            status_text.text("📝 Step 2/4: Extracting sentences...")
            sentences = extract_sentences_from_tor(formatted_text)
            progress_bar.progress(40)
            
            # STEP 3: Product Matching
            status_text.text("🎯 Step 3/4: Product Matching...")
            matched_products, result_df = analyze_tor_sentences_full_mode(
                sentences,
                st.session_state.spec_df,
                st.session_state.gemini_key
            )
            progress_bar.progress(70)
            
            # STEP 4: FR/NFR Classification (OPTIONAL)
            if enable_fr_nfr:
                status_text.text("📊 Step 4/4: FR/NFR Classification...")
                requirement_types = classify_scope_hybrid(
                    sentences, 
                    st.session_state.gemini_key
                )
                result_df['Requirement_Type'] = requirement_types
            else:
                # Default to Functional if disabled
                result_df['Requirement_Type'] = 'Functional'
                print("   ⏭️ FR/NFR Classification disabled by user")
            
            progress_bar.progress(100)
            
            # Store results
            st.session_state.processed_df = result_df
            st.session_state.matched_products = matched_products
            st.session_state.analysis_done = True
            
            status_text.empty()
            progress_bar.empty()
            
            st.balloons()
            st.success(f"✅ Analysis complete! Found {len(result_df)} requirements")
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Analysis failed: {e}")
            import traceback
            st.code(traceback.format_exc())

# ===== STEP 3: INTERACTIVE VERIFICATION =====
if st.session_state.analysis_done:
    st.markdown('<p class="step-header">3️⃣ Verify & Edit Results</p>', unsafe_allow_html=True)
    
    # Prepare editable dataframe
    df = st.session_state.processed_df.copy()
    
    # Define product and implementation options
    product_options = ['Zocial Eye', 'Warroom', 'Outsource', 'Other Product', 'Non-Compliant']
    impl_options = ['Standard', 'Customize/Integration', 'Non-Compliant']
    
    # Create checkbox columns with grouped naming
    for prod in product_options:
        col_name = f"📦 {prod}"
        df[col_name] = df['Product_Match'].apply(lambda x: prod in str(x))
    
    for impl in impl_options:
        col_name = f"🔧 {impl}"
        df[col_name] = df['Implementation'].apply(lambda x: impl in str(x))
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["📊 Data Editor", "📈 Statistics", "🔍 Filter & Search"])
    
    with tab1:
        st.caption("✏️ Click checkboxes to edit. Changes are saved automatically.")
        
        # Column configuration
        column_config = {
            # Hide original columns
            "Product_Match": None,
            "Implementation": None,
            
            # Main columns
            "TOR_Sentence": st.column_config.TextColumn(
                "Requirement",
                width="large",
                help="Original requirement text from TOR"
            ),
            "Matched_Keyword": st.column_config.TextColumn(
                "Matched Spec",
                width="medium",
                help="Matched specification from master data"
            ),
            "Requirement_Type": st.column_config.SelectboxColumn(
                "Requirement Type",
                options=["Functional", "Non-Functional"],
                width="medium",
                help="FR (Functional) or NFR (Non-Functional)"
            ),
            
            # ===== SELECTED PRODUCT GROUP =====
            "📦 Zocial Eye": st.column_config.CheckboxColumn(
                "Zocial Eye",
                help="Social media monitoring platform",
                default=False,
                width="small"
            ),
            "📦 Warroom": st.column_config.CheckboxColumn(
                "Warroom",
                help="Customer engagement platform",
                default=False,
                width="small"
            ),
            "📦 Outsource": st.column_config.CheckboxColumn(
                "Outsource",
                help="External development required",
                default=False,
                width="small"
            ),
            "📦 Other Product": st.column_config.CheckboxColumn(
                "Other Product",
                help="Other WiseSight products",
                default=False,
                width="small"
            ),
            "📦 Non-Compliant": st.column_config.CheckboxColumn(
                "Non-Compliant",
                help="Does not match any product",
                default=False,
                width="small"
            ),
            
            # ===== IMPLEMENTATION GROUP =====
            "🔧 Standard": st.column_config.CheckboxColumn(
                "Standard",
                help="Standard package implementation",
                default=False,
                width="small"
            ),
            "🔧 Customize/Integration": st.column_config.CheckboxColumn(
                "Customize",
                help="Custom development or integration required",
                default=False,
                width="small"
            ),
            "🔧 Non-Compliant": st.column_config.CheckboxColumn(
                "Non-Compliant",
                help="Cannot be implemented",
                default=False,
                width="small"
            ),
        }
        
        # Display grouped header info
        st.markdown("""
        <div style='background-color: #f0f2f6; padding: 10px; border-radius: 5px; margin-bottom: 10px;'>
            <strong>Column Groups:</strong><br>
            📦 = <strong>Selected Product</strong> (Zocial Eye, Warroom, Outsource, Other Product, Non-Compliant)<br>
            🔧 = <strong>Implementation</strong> (Standard, Customize/Integration, Non-Compliant)
        </div>
        """, unsafe_allow_html=True)
        
        # Data editor
        edited_df = st.data_editor(
            df,
            column_config=column_config,
            disabled=["TOR_Sentence", "Matched_Keyword"],
            hide_index=False,
            use_container_width=True,
            num_rows="dynamic",
            key="data_editor",
            column_order=[
                "TOR_Sentence",
                "Matched_Keyword",
                "Requirement_Type",
                "📦 Zocial Eye", "📦 Warroom", "📦 Outsource", "📦 Other Product", "📦 Non-Compliant",
                "🔧 Standard", "🔧 Customize/Integration", "🔧 Non-Compliant"
            ]
        )
        
        # Validation logic
        for idx in edited_df.index:
            if edited_df.loc[idx, '📦 Non-Compliant']:
                edited_df.loc[idx, '📦 Zocial Eye'] = False
                edited_df.loc[idx, '📦 Warroom'] = False
                edited_df.loc[idx, '📦 Outsource'] = False
                edited_df.loc[idx, '📦 Other Product'] = False
                edited_df.loc[idx, '🔧 Standard'] = False
                edited_df.loc[idx, '🔧 Customize/Integration'] = False
                edited_df.loc[idx, '🔧 Non-Compliant'] = True
            
            if edited_df.loc[idx, '🔧 Non-Compliant']:
                edited_df.loc[idx, '🔧 Standard'] = False
                edited_df.loc[idx, '🔧 Customize/Integration'] = False
        
        st.session_state.edited_df = edited_df
        
        st.info("""
        ℹ️ **Validation Rules:**
        - If **Product Non-Compliant** is selected → All other products unchecked + Implementation forced to Non-Compliant
        - If **Implementation Non-Compliant** is selected → Standard and Customize unchecked
        """)
    
    with tab2:
        # Statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_rows = len(edited_df)
            st.metric("Total Requirements", total_rows)
        
        with col2:
            non_compliant = edited_df['📦 Non-Compliant'].sum()
            st.metric("Non-Compliant", non_compliant, delta=f"-{non_compliant}", delta_color="inverse")
        
        with col3:
            compliant = total_rows - non_compliant
            st.metric("Compliant", compliant, delta=f"+{compliant}")
        
        with col4:
            multi_product = sum(
                edited_df[['📦 Zocial Eye', '📦 Warroom', '📦 Outsource', '📦 Other Product']].sum(axis=1) > 1
            )
            st.metric("Multi-Product", multi_product)
        
        # Charts
        st.subheader("📊 Visual Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Product Distribution**")
            product_counts = {
                'Zocial Eye': edited_df['📦 Zocial Eye'].sum(),
                'Warroom': edited_df['📦 Warroom'].sum(),
                'Outsource': edited_df['📦 Outsource'].sum(),
                'Other Product': edited_df['📦 Other Product'].sum(),
                'Non-Compliant': edited_df['📦 Non-Compliant'].sum()
            }
            st.bar_chart(product_counts)
        
        with col2:
            st.markdown("**Requirement Type Distribution**")
            fr_nfr_counts = edited_df['Requirement_Type'].value_counts()
            st.bar_chart(fr_nfr_counts)
        
        st.markdown("**Implementation Distribution**")
        impl_counts = {
            'Standard': edited_df['🔧 Standard'].sum(),
            'Customize/Integration': edited_df['🔧 Customize/Integration'].sum(),
            'Non-Compliant': edited_df['🔧 Non-Compliant'].sum()
        }
        st.bar_chart(impl_counts)
    
    with tab3:
        st.subheader("🔍 Search & Filter")
        
        search_term = st.text_input("Search in Requirement", "")
        
        filter_product = st.multiselect(
            "Filter by Product",
            ['Zocial Eye', 'Warroom', 'Outsource', 'Other Product', 'Non-Compliant'],
            default=[]
        )
        
        filter_impl = st.multiselect(
            "Filter by Implementation",
            ['Standard', 'Customize/Integration', 'Non-Compliant'],
            default=[]
        )
        
        filter_type = st.multiselect(
            "Filter by Requirement Type",
            ["Functional", "Non-Functional"],
            default=[]
        )
        
        # Apply filters
        filtered_df = edited_df.copy()
        
        if search_term:
            filtered_df = filtered_df[
                filtered_df['TOR_Sentence'].str.contains(search_term, case=False, na=False)
            ]
        
        if filter_product:
            prod_cols = [f'📦 {p}' for p in filter_product]
            mask = filtered_df[prod_cols].any(axis=1)
            filtered_df = filtered_df[mask]
        
        if filter_impl:
            impl_cols = [f'🔧 {i}' for i in filter_impl]
            mask = filtered_df[impl_cols].any(axis=1)
            filtered_df = filtered_df[mask]
        
        if filter_type:
            filtered_df = filtered_df[filtered_df['Requirement_Type'].isin(filter_type)]
        
        st.write(f"**Showing {len(filtered_df)} of {len(edited_df)} rows**")
        
        display_cols = [
            "TOR_Sentence",
            "Matched_Keyword",
            "Requirement_Type",
            "📦 Zocial Eye", "📦 Warroom", "📦 Outsource", "📦 Other Product", "📦 Non-Compliant",
            "🔧 Standard", "🔧 Customize/Integration", "🔧 Non-Compliant"
        ]
        st.dataframe(filtered_df[display_cols], use_container_width=True, hide_index=False)

# ===== STEP 4: BUDGET CALCULATION =====
if st.session_state.analysis_done:
    st.markdown('<p class="step-header">4️⃣ Budget Estimation</p>', unsafe_allow_html=True)
    
    if not st.session_state.budget_calculated:
        if st.button("💰 Calculate Budget", type="primary", use_container_width=True):
            with st.spinner("🤖 AI analyzing budget factors..."):
                try:
                    budget_factors = extract_budget_factors(
                        st.session_state.tor_raw_text,
                        st.session_state.gemini_key
                    )
                    
                    st.session_state.budget_factors = budget_factors
                    st.session_state.budget_calculated = True
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Budget calculation failed: {e}")
    
    if st.session_state.budget_calculated:
        # Display & Edit factors
        with st.expander("🔍 Budget Factors (Click to Edit)", expanded=True):
            factors = st.session_state.budget_factors
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 Zocial Eye")
                ze_users = st.number_input(
                    "Number of Users",
                    value=factors.get('num_users', 2),
                    min_value=1,
                    key="ze_users"
                )
                ze_backward = st.number_input(
                    "Data Backward (Days)",
                    value=factors.get('data_backward_days', 90),
                    min_value=30,
                    step=30,
                    key="ze_backward"
                )
            
            with col2:
                st.subheader("💬 Warroom")
                wr_users = st.number_input(
                    "Number of Users",
                    value=factors.get('num_users', 5),
                    min_value=1,
                    key="wr_users"
                )
                wr_tx = st.number_input(
                    "Monthly Transactions",
                    value=factors.get('monthly_transactions', 35000),
                    min_value=1000,
                    step=1000,
                    key="wr_tx"
                )
                wr_channels = st.number_input(
                    "Social Channels",
                    value=factors.get('social_channels_count', 0),
                    min_value=0,
                    key="wr_channels"
                )
                wr_chatbot = st.checkbox(
                    "Chatbot Required",
                    value=factors.get('chatbot_required', False),
                    key="wr_chatbot"
                )
            
            # Update factors
            updated_factors = {
                'num_users': ze_users,
                'data_backward_days': ze_backward,
                'monthly_transactions': wr_tx,
                'social_channels_count': wr_channels,
                'chatbot_required': wr_chatbot
            }
            
            if st.button("🔄 Recalculate with New Factors", use_container_width=True):
                st.session_state.budget_factors = updated_factors
                st.rerun()
        
        # Calculate & Display Budget
        st.subheader("💰 Budget Report")
        
        try:
            budget_results = calculate_budget_sheets(
                st.session_state.budget_factors,
                st.session_state.matched_products,
                st.session_state.pricing_df,
                st.session_state.addon_df
            )
            
            if budget_results:
                total_budget = 0
                
                for result in budget_results:
                    budget_html = format_budget_report(
                        result['Product'],
                        result['Package'],
                        st.session_state.budget_factors,
                        result['Breakdown']
                    )
                    
                    st.markdown(budget_html, unsafe_allow_html=True)
                    
                    # Calculate total
                    init_fee = result['Package'].get('Initial_Fee (THB)', 0)
                    if init_fee and init_fee != '-' and isinstance(init_fee, (int, float)):
                        total_budget += result['Breakdown']['total'] + init_fee
                    else:
                        total_budget += result['Breakdown']['total']
                
                # Summary
                if len(budget_results) > 1:
                    from utils.budget_engine import format_money
                    
                    st.markdown(f"""
                    <div style='background-color: #d4edda; padding: 20px; border-radius: 10px; border-left: 5px solid #28a745;'>
                        <h3 style='color: #155724; margin-top: 0;'>📋 Budget Summary</h3>
                    """, unsafe_allow_html=True)
                    
                    for result in budget_results:
                        init_fee = result['Package'].get('Initial_Fee (THB)', 0)
                        if init_fee and init_fee != '-' and isinstance(init_fee, (int, float)):
                            prod_total = result['Breakdown']['total'] + init_fee
                        else:
                            prod_total = result['Breakdown']['total']
                        
                        st.markdown(f"<p style='font-size: 1.1em;'><strong>{result['Product']}:</strong> {format_money(prod_total)} THB</p>", unsafe_allow_html=True)
                    
                    st.markdown(f"""
                        <hr style='border: 1px solid #c3e6cb;'>
                        <h2 style='color: #155724; text-align: right;'>💰 GRAND TOTAL: {format_money(total_budget)} THB/Year</h2>
                    </div>
                    """, unsafe_allow_html=True)
            
            else:
                st.warning("⚠️ No suitable package found. Please adjust requirements or contact sales team.")
        
        except Exception as e:
            st.error(f"❌ Budget calculation failed: {e}")
            import traceback
            st.code(traceback.format_exc())

# ===== STEP 5: SAVE TO GOOGLE SHEET =====
if st.session_state.edited_df is not None:
    st.markdown('<p class="step-header">5️⃣ Save to Google Sheet</p>', unsafe_allow_html=True)
    
    # Prepare data for save
    save_data = prepare_save_data(st.session_state.edited_df, product_options, impl_options)
    
    # Filter Non-Compliant
    save_data_filtered = save_data[~save_data['Product'].str.contains('Non-Compliant', na=False)]
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.info(f"📊 **Ready to save:** {len(save_data_filtered)} rows (Non-Compliant excluded)")
    
    with col2:
        if st.button("👀 Preview Data"):
            with st.expander("Data to be saved", expanded=True):
                st.dataframe(save_data_filtered, use_container_width=True)
    
    # Duplicate check
    if len(save_data_filtered) > 0:
        duplicates = check_duplicates(
            save_data_filtered,
            st.session_state.spec_df
        )
        
        if len(duplicates) > 0:
            st.warning(f"⚠️ Found {len(duplicates)} potential duplicates")
            with st.expander("🔍 View Duplicates", expanded=False):
                st.dataframe(duplicates, use_container_width=True)
                
                handle_dup = st.radio(
                    "How to handle duplicates?",
                    ["Skip duplicates", "Save all (create duplicates)", "Cancel save"],
                    index=0,
                    horizontal=True
                )
                
                if handle_dup == "Skip duplicates":
                    save_data_filtered = save_data_filtered[
                        ~save_data_filtered['TOR_Sentence'].isin(duplicates['TOR_Sentence'])
                    ]
                    st.info(f"✅ Will save {len(save_data_filtered)} rows (duplicates skipped)")
                elif handle_dup == "Cancel save":
                    st.stop()
        else:
            st.success("✅ No duplicates found")
    
    # Save buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Save to Google Sheet", type="primary", disabled=len(save_data_filtered)==0, use_container_width=True):
            with st.spinner("📤 Saving to Google Sheet..."):
                try:
                    result = save_to_product_spec(
                        save_data_filtered,
                        sheet_url
                    )
                    
                    # Update history
                    st.session_state.save_history.append({
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'count': len(save_data_filtered),
                        'products': list(save_data_filtered['Product'].unique()),
                        'data': save_data_filtered.to_dict('records')
                    })
                    
                    st.success(f"✅ Saved {len(save_data_filtered)} rows successfully!")
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"❌ Save failed: {e}")
    
    with col2:
        if st.button("📥 Export to Excel", use_container_width=True):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                save_data_filtered.to_excel(writer, sheet_name='Data', index=False)
                
                instructions = pd.DataFrame({
                    'Instructions': [
                        'This file contains verified TOR requirements',
                        '',
                        'Columns:',
                        '- Product: Matched product (Zocial Eye, Warroom, etc.)',
                        '- Sentence_TH: Thai sentence',
                        '- Sentence_ENG: English sentence',
                        '- Implementation: Standard or Customize/Integration',
                        '',
                        'Generated by WiseSight TOR Analyzer',
                        f'Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
                    ]
                })
                instructions.to_excel(writer, sheet_name='README', index=False)
            
            st.download_button(
                label="⬇️ Download Excel",
                data=output.getvalue(),
                file_name=f"wisesight_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    
    with col3:
        if st.button("🔄 Reset & Start Over", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

# ===== FOOTER =====
st.divider()
col1, col2, col3 = st.columns(3)

with col1:
    st.caption("WiseSight TOR Analyzer v2.1")
with col2:
    st.caption("Powered by Streamlit + Gemini AI")
with col3:
    st.caption(f"Session: {datetime.now().strftime('%Y-%m-%d')}")
