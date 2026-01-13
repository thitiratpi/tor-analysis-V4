"""
================================================================================
WISESIGHT STREAMLIT APP V2.1 - REVISED
================================================================================
Full-featured TOR Analysis with Budget Engine
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
    
    [data-testid="stMetricDelta"] {
        font-size: 1rem;
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
    
    [data-testid="stSidebar"] .element-container {
        margin-bottom: 1rem;
    }
    
    /* ===== EXPANDER STYLES ===== */
    .streamlit-expanderHeader {
        font-weight: 600;
        font-size: 1.1rem;
        background-color: #f0f2f6;
        border-radius: 5px;
    }
    
    .streamlit-expanderHeader:hover {
        background-color: #e0e2e6;
    }
    
    /* ===== PROGRESS BAR ===== */
    .stProgress > div > div > div > div {
        background-color: #1f77b4;
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
    
    /* ===== DOWNLOAD BUTTON ===== */
    .stDownloadButton > button {
        background-color: #28a745;
        color: white;
        border: none;
    }
    
    .stDownloadButton > button:hover {
        background-color: #218838;
    }
    
    /* ===== DIVIDER ===== */
    hr {
        margin: 2rem 0;
        border: none;
        border-top: 2px solid #e0e2e6;
    }
    
    /* ===== HIDE STREAMLIT BRANDING ===== */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# API KEY CONFIGURATION (FROM SECRETS)
# ==========================================

try:
    # ดึง API key จาก Streamlit secrets
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    api_key_status = "✅ Connected"
    api_key_available = True
except Exception as e:
    GEMINI_API_KEY = None
    api_key_status = "❌ Not configured"
    api_key_available = False

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

# ==========================================
# SIDEBAR - CONFIGURATION
# ==========================================

with st.sidebar:
    st.title("🔧 Configuration")
    
    # ===== API KEY STATUS =====
    st.subheader("🔐 API Keys")
    if api_key_available:
        st.success(f"Gemini API: {api_key_status}")
    else:
        st.error(f"Gemini API: {api_key_status}")
        st.warning("""
        ⚠️ **API Key Required**
        
        Please configure in Streamlit Cloud:
        1. Go to **Settings** (⚙️)
        2. Click **Secrets**
        3. Add:
```
        GEMINI_API_KEY = "your-api-key-here"
```
        """)
    
    st.divider()
    
    # ===== GOOGLE SHEET =====
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
    
    # ===== OPTIONS =====
    st.subheader("⚙️ Options")
    
    enable_ai_formatting = st.checkbox(
        "🤖 AI Text Formatting",
        value=True,
        disabled=not api_key_available,
        help="Use AI to clean and format TOR text"
    )
    
    enable_fr_nfr = st.checkbox(
        "📊 FR/NFR Classification",
        value=True,
        disabled=not api_key_available,
        help="Classify Functional vs Non-Functional requirements"
    )
    
    enable_budget = st.checkbox(
        "💰 Budget Engine",
        value=True,
        disabled=not api_key_available,
        help="Calculate budget estimation"
    )
    
    if not api_key_available:
        st.info("💡 Configure API key to enable AI features")
    
    st.divider()
    
    # ===== SAVE HISTORY =====
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

# Warning if API key not available
if not api_key_available:
    st.warning("""
    ⚠️ **Gemini API Key Not Configured**
    
    Some features will be limited. Please configure API key in Streamlit Cloud settings.
    
    **How to configure:**
    1. Click **Manage app** (bottom right)
    2. Go to **Settings** → **Secrets**
    3. Add: `GEMINI_API_KEY = "your-api-key"`
    4. Click **Save**
    """)

# Progress bar (เดิม)
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
# ... (code เดิม แต่เปลี่ยน gemini_key เป็น GEMINI_API_KEY)

# ===== STEP 2: AI ANALYSIS =====
if st.session_state.file_uploaded and not st.session_state.analysis_done:
    st.markdown('<p class="step-header">2️⃣ AI Analysis</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("🧠 **AI Text Formatting**\nClean & structure TOR text")
    with col2:
        st.info("🎯 **Product Matching**\nMatch to Zocial Eye / Warroom")
    with col3:
        st.info("📊 **FR/NFR Classification**\nFunctional vs Non-Functional")
    
    # Check API key before analysis
    if not api_key_available:
        st.error("❌ Cannot start analysis: API key not configured")
        st.stop()
    
    if st.button("🚀 Start Analysis", type="primary", use_container_width=True):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # STEP 1: AI Text Formatting
            status_text.text("🤖 Step 1/3: AI Text Formatting...")
            progress_bar.progress(10)
            
            if enable_ai_formatting:
                formatted_text = extract_scope_smart_ai(
                    st.session_state.tor_raw_text,
                    GEMINI_API_KEY  # ← เปลี่ยนจาก gemini_key
                )
            else:
                formatted_text = st.session_state.tor_raw_text
            
            progress_bar.progress(30)
            
            # STEP 2: Extract sentences
            status_text.text("📝 Step 2/3: Extracting sentences...")
            sentences = extract_sentences_from_tor(formatted_text)
            progress_bar.progress(40)
            
            # STEP 3: Product Matching
            status_text.text("🎯 Step 3/3: Analyzing with AI...")
            matched_products, result_df = analyze_tor_sentences_full_mode(
                sentences,
                st.session_state.spec_df,
                GEMINI_API_KEY  # ← เปลี่ยนจาก gemini_key
            )
            progress_bar.progress(70)
            
            # STEP 4: FR/NFR Classification (if enabled)
            if enable_fr_nfr:
                status_text.text("📊 Bonus: FR/NFR Classification...")
                requirement_types = classify_scope_hybrid(sentences, GEMINI_API_KEY)  # ← เปลี่ยน
                result_df['Requirement_Type'] = requirement_types
            else:
                result_df['Requirement_Type'] = 'Functional'
            
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
    
    # Split multi-products into checkbox columns
    product_options = ['Zocial Eye', 'Warroom', 'Outsource', 'Other Product', 'Non-Compliant']
    impl_options = ['Standard', 'Customize/Integration', 'Non-Compliant']
    
    # Create checkbox columns
    for prod in product_options:
        df[prod] = df['Product_Match'].apply(lambda x: prod in str(x))
    
    for impl in impl_options:
        df[impl] = df['Implementation'].apply(lambda x: impl in str(x))
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["📊 Data Editor", "📈 Statistics", "🔍 Filter & Search"])
    
    with tab1:
        st.caption("✏️ Click checkboxes to edit. Changes are saved automatically.")
        
        edited_df = st.data_editor(
            df,
            column_config={
                # Hide original columns
                "Product_Match": None,
                "Implementation": None,
                
                # No. (Index)
                "TOR_Sentence": st.column_config.TextColumn(
                    "Requirement",
                    width="large",
                    help="Original requirement text"
                ),
                
                # ===== SELECTED PRODUCT GROUP =====
                "Zocial Eye": st.column_config.CheckboxColumn(
                    "Zocial Eye",
                    help="Check if this product applies",
                    default=False
                ),
                "Warroom": st.column_config.CheckboxColumn(
                    "Warroom",
                    help="Check if this product applies",
                    default=False
                ),
                "Outsource": st.column_config.CheckboxColumn(
                    "Outsource",
                    help="Check if this product applies",
                    default=False
                ),
                "Other Product": st.column_config.CheckboxColumn(
                    "Other Product",
                    help="Check if this product applies",
                    default=False
                ),
                "Non-Compliant": st.column_config.CheckboxColumn(
                    "Non-Compliant",
                    help="Check if non-compliant",
                    default=False
                ),
                
                # ===== IMPLEMENTATION GROUP =====
                "Standard": st.column_config.CheckboxColumn(
                    "Standard",
                    help="Standard implementation",
                    default=False
                ),
                "Customize/Integration": st.column_config.CheckboxColumn(
                    "Customize",
                    help="Custom/Integration needed",
                    default=False
                ),
                
                # Other columns
                "Matched_Keyword": st.column_config.TextColumn(
                    "Matched Spec",
                    width="medium"
                ),
                "Requirement_Type": st.column_config.SelectboxColumn(
                    "Requirement Type",
                    options=["Functional", "Non-Functional"],
                    width="small"
                )
            },
            disabled=["TOR_Sentence", "Matched_Keyword"],
            hide_index=False,
            use_container_width=True,
            num_rows="dynamic",
            key="data_editor",
            column_order=[
                "TOR_Sentence",
                "Zocial Eye", "Warroom", "Outsource", "Other Product", "Non-Compliant",
                "Standard", "Customize/Integration",
                "Matched_Keyword",
                "Requirement_Type"
            ]
        )
        
        # ===== VALIDATION: Non-Compliant Logic =====
        # If Non-Compliant is selected in products, force Implementation to Non-Compliant only
        for idx in edited_df.index:
            if edited_df.loc[idx, 'Non-Compliant']:
                # Force uncheck other products
                edited_df.loc[idx, 'Zocial Eye'] = False
                edited_df.loc[idx, 'Warroom'] = False
                edited_df.loc[idx, 'Outsource'] = False
                edited_df.loc[idx, 'Other Product'] = False
                
                # Force uncheck other implementations
                edited_df.loc[idx, 'Standard'] = False
                edited_df.loc[idx, 'Customize/Integration'] = False
        
        # Store edited data
        st.session_state.edited_df = edited_df
        
        # Validation message
        st.info("ℹ️ **Rule:** If Non-Compliant is selected, all other options will be automatically unchecked.")
    
    with tab2:
        # Statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_rows = len(edited_df)
            st.metric("Total Requirements", total_rows)
        
        with col2:
            non_compliant = edited_df['Non-Compliant'].sum()
            st.metric("Non-Compliant", non_compliant, delta=f"-{non_compliant}", delta_color="inverse")
        
        with col3:
            compliant = total_rows - non_compliant
            st.metric("Compliant", compliant, delta=f"+{compliant}")
        
        with col4:
            multi_product = sum(
                edited_df[['Zocial Eye', 'Warroom', 'Outsource', 'Other Product']].sum(axis=1) > 1
            )
            st.metric("Multi-Product", multi_product)
        
        # Charts
        st.subheader("📊 Visual Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Product distribution
            product_counts = {
                'Zocial Eye': edited_df['Zocial Eye'].sum(),
                'Warroom': edited_df['Warroom'].sum(),
                'Outsource': edited_df['Outsource'].sum(),
                'Other Product': edited_df['Other Product'].sum(),
                'Non-Compliant': edited_df['Non-Compliant'].sum()
            }
            st.bar_chart(product_counts)
        
        with col2:
            # FR/NFR distribution
            fr_nfr_counts = edited_df['Requirement_Type'].value_counts()
            st.bar_chart(fr_nfr_counts)
    
    with tab3:
        st.subheader("🔍 Search & Filter")
        
        search_term = st.text_input("Search in Requirement", "")
        
        filter_product = st.multiselect(
            "Filter by Product",
            product_options,
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
            mask = filtered_df[filter_product].any(axis=1)
            filtered_df = filtered_df[mask]
        
        if filter_type:
            filtered_df = filtered_df[filtered_df['Requirement_Type'].isin(filter_type)]
        
        st.write(f"**Showing {len(filtered_df)} of {len(edited_df)} rows**")
        st.dataframe(filtered_df, use_container_width=True, hide_index=False)

# ===== STEP 4: BUDGET CALCULATION (Always enabled) =====
if st.session_state.analysis_done:
    st.markdown('<p class="step-header">4️⃣ Budget Estimation</p>', unsafe_allow_html=True)
    
    if not st.session_state.budget_calculated:
        if st.button("💰 Calculate Budget", type="primary"):
            with st.spinner("🤖 AI analyzing budget factors..."):
                try:
                    budget_factors = extract_budget_factors(
                        st.session_state.tor_raw_text,
                        st.session_state.GEMINI_API_KEY
                    )
                    
                    st.session_state.budget_factors = budget_factors
                    st.session_state.budget_calculated = True
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Budget calculation failed: {e}")
    
    if st.session_state.budget_calculated:
        # Display factors
        with st.expander("🔍 Detected Budget Factors", expanded=True):
            factors = st.session_state.budget_factors
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Zocial Eye")
                ze_users = st.number_input("Number of Users", value=factors.get('num_users', 2), min_value=1)
                ze_backward = st.number_input("Data Backward (Days)", value=factors.get('data_backward_days', 90), min_value=30)
            
            with col2:
                st.subheader("Warroom")
                wr_users = st.number_input("Number of Users (WR)", value=factors.get('num_users', 5), min_value=1)
                wr_tx = st.number_input("Monthly Transactions", value=factors.get('monthly_transactions', 35000), min_value=1000)
                wr_channels = st.number_input("Social Channels", value=factors.get('social_channels_count', 0), min_value=0)
                wr_chatbot = st.checkbox("Chatbot Required", value=factors.get('chatbot_required', False))
            
            # Update factors
            updated_factors = {
                'num_users': ze_users,
                'data_backward_days': ze_backward,
                'monthly_transactions': wr_tx,
                'social_channels_count': wr_channels,
                'chatbot_required': wr_chatbot
            }
        
        # Calculate budget
        if st.button("🔄 Recalculate Budget"):
            st.session_state.budget_factors = updated_factors
        
        # Display budget
        try:
            budget_results = calculate_budget_sheets(
                st.session_state.budget_factors,
                st.session_state.matched_products,
                st.session_state.pricing_df,
                st.session_state.addon_df
            )
            
            if budget_results:
                for result in budget_results:
                    budget_html = format_budget_report(
                        result['Product'],
                        result['Package'],
                        st.session_state.budget_factors,
                        result['Breakdown']
                    )
                    st.markdown(budget_html, unsafe_allow_html=True)
            else:
                st.warning("⚠️ No suitable package found for the requirements")
                
        except Exception as e:
            st.error(f"❌ Budget display failed: {e}")

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
        # Preview
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
        # Export to Excel
        if st.button("📥 Export to Excel", use_container_width=True):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                save_data_filtered.to_excel(writer, sheet_name='Data', index=False)
                
                # Add instructions sheet
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
            # Clear all session state
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
