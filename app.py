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
        'About': "# WiseSight TOR Analyzer\nVersion 2.3.2\nPowered by Streamlit + Gemini AI"
    }
)

# Custom CSS
st.markdown("""
<style>
    /* ===== GLOBAL STYLES ===== */
    .main { padding: 0rem 1rem; }
    
    /* ===== HEADER STYLES ===== */
    .main-header { font-size: 2.5rem; font-weight: bold; color: #1f77b4; margin-bottom: 0.5rem; text-align: center; }
    
    /* ===== CARD & BOX STYLES ===== */
    .file-info-card {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #dee2e6;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .stat-list {
        font-size: 0.9rem;
        color: #333;
        line-height: 1.6;
    }

    /* ===== TAB STYLES ===== */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        font-weight: 600;
        font-size: 1.1rem;
    }
    
    /* ===== BUTTON STYLES ===== */
    .stButton > button { width: 100%; border-radius: 5px; height: 3rem; font-weight: 600; transition: all 0.3s ease; }
    .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
    
    /* ===== DATA EDITOR STYLES ===== */
    .stDataFrame { border-radius: 10px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    
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
    st.title("🔧 Configuration")
    
    # ===== 1. API STATUS =====
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

# ==========================================
# MAIN APP
# ==========================================

st.markdown('<p class="main-header">🔍 WiseSight TOR Analyzer</p>', unsafe_allow_html=True)
st.caption("AI-powered compliance checking with interactive verification & budget estimation")

# Create Tabs
tab_verify, tab_budget = st.tabs(["📊 Results & Verify", "💰 Budget"])

# ==========================================
# TAB 1: RESULTS & VERIFY
# ==========================================
with tab_verify:

    # ===== STEP 1: FILE UPLOAD =====
    st.markdown("### 📂 Upload TOR Document")
    col1, col2 = st.columns([3, 1])

    with col1:
        uploaded_file = st.file_uploader("Choose TOR file", type=['pdf', 'docx', 'txt', 'xlsx', 'xls'])

    with col2:
        # File Info Card logic
        if uploaded_file:
            f_name = uploaded_file.name
            f_size = f"{uploaded_file.size / 1024:.1f} KB"
        elif st.session_state.file_uploaded:
            f_name = st.session_state.file_name
            f_size = f"{st.session_state.file_size / 1024:.1f} KB"
        else:
            f_name = "-"
            f_size = "-"
            
        st.markdown(f"""
        <div class="file-info-card">
            <div style="font-weight:bold; margin-bottom:5px;">📄 File Info</div>
            <div>Name: {f_name}</div>
            <div>Size: {f_size}</div>
        </div>
        """, unsafe_allow_html=True)

    # File Reading Logic
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
        if st.button("🚀 Start Analysis", type="primary"):
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

        # Count Products
        cnt_ze = df_stats["📦 Zocial Eye"].sum()
        cnt_wr = df_stats["📦 Warroom"].sum()
        cnt_out = df_stats["📦 Outsource"].sum()
        cnt_oth = df_stats["📦 Other Product"].sum()
        cnt_nc_prod = df_stats["📦 Non-Compliant"].sum()
        
        # Count Implementations
        cnt_std = df_stats["🔧 Standard"].sum()
        cnt_cust = df_stats["🔧 Customize/Integration"].sum()
        cnt_nc_impl = df_stats["🔧 Non-Compliant"].sum()
        
        # Count Status
        cnt_edited = len(df_stats[df_stats['📝 Status'] == '✅ Edited'])
        cnt_auto = total_req - cnt_edited

        # Display Stats Area
        sc1, sc2, sc3 = st.columns([1, 2, 2])
        
        with sc1:
            st.metric("Total Requirement", total_req)
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f"**✅ User Edited:** {cnt_edited}")
            st.markdown(f"**🤖 Auto Suggestions:** {cnt_auto}")
            
        with sc2:
            st.markdown("**Selected Product (By system)**")
            st.markdown(f"""
            <div class='stat-list'>
            - Zocial Eye ({cnt_ze})<br>
            - Warroom ({cnt_wr})<br>
            - Outsource ({cnt_out})<br>
            - Other Product ({cnt_oth})<br>
            - Non-Compliants ({cnt_nc_prod})
            </div>
            """, unsafe_allow_html=True)
            
        with sc3:
            st.markdown("**Implementation (By system)**")
            st.markdown(f"""
            <div class='stat-list'>
            - Standard ({cnt_std})<br>
            - Customize ({cnt_cust})<br>
            - Non-Compliants ({cnt_nc_impl})
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 📋 Detailed Analysis")

        # --- DATA EDITOR (Logic from v2.2.2) ---
        df = st.session_state.processed_df.copy()
        
        # Define options
        product_options = ['Zocial Eye', 'Warroom', 'Outsource', 'Other Product', 'Non-Compliant']
        impl_options = ['Standard', 'Customize/Integration', 'Non-Compliant']

        # Ensure Original Selections Exist (Robust check)
        if 'original_selections' not in st.session_state or len(st.session_state.original_selections) == 0:
            st.session_state.original_selections = {}
            for idx in df.index:
                st.session_state.original_selections[idx] = {
                    'products': str(df.loc[idx, 'Product_Match']),
                    'implementation': str(df.loc[idx, 'Implementation'])
                }

        # Generate Checkbox Columns
        for prod in product_options:
            df[f"📦 {prod}"] = df['Product_Match'].apply(lambda x: prod in str(x))
        for impl in impl_options:
            df[f"🔧 {impl}"] = df['Implementation'].apply(lambda x: impl in str(x))
        
        if '📝 Status' not in df.columns:
            df['📝 Status'] = '🤖 Auto'
            
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
        for prod in product_options:
            column_config[f"📦 {prod}"] = st.column_config.CheckboxColumn(f"🔵 {prod}", width="small")
        for impl in impl_options:
            column_config[f"🔧 {impl}"] = st.column_config.CheckboxColumn(f"🟠 {impl}", width="small")

        # UI Legend
        st.markdown("""
        <div style='background-color: #f0f2f6; padding: 15px; border-radius: 8px; margin-bottom: 15px;'>
            <strong style='font-size: 1.1em;'>📌 Column Groups & Status Indicators:</strong><br><br>
            <div style='display: flex; gap: 20px; flex-wrap: wrap;'>
                <div style='flex: 1; min-width: 200px;'>
                    <div style='background: linear-gradient(135deg, #2196f3 0%, #64b5f6 100%); color: white; padding: 8px 12px; border-radius: 5px; margin-bottom: 8px;'><strong>🔵 Selected Product</strong></div>
                    <small style='color: #333;'>✓ Can select multiple<br>✓ Choose all that apply</small>
                </div>
                <div style='flex: 1; min-width: 250px;'>
                    <div style='background: linear-gradient(135deg, #ff9800 0%, #ffb74d 100%); color: white; padding: 8px 12px; border-radius: 5px; margin-bottom: 8px;'><strong>🟠 Implementation</strong></div>
                    <small style='color: #333;'>⚠️ Select ONLY ONE<br>⚠️ If the product is marked as Non-Compliant, only Non-Compliant can be selected</small>
                </div>
                <div style='flex: 1; min-width: 200px;'>
                    <div style='background: linear-gradient(135deg, #9e9e9e 0%, #bdbdbd 100%); color: white; padding: 8px 12px; border-radius: 5px; margin-bottom: 8px;'><strong>📝 Status</strong></div>
                    <small style='color: #333;'>🤖 Auto = System<br>✅ Edited = You changed</small>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Editor
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

        # --- LOGIC ENFORCEMENT & STATUS UPDATE (From v2.2.2) ---
        needs_rerun = False
        def normalize_selection(val_str):
            if not val_str or pd.isna(val_str) or val_str == 'nan': return []
            clean = str(val_str).replace("[","").replace("]","").replace("'","")
            return sorted([x.strip() for x in clean.split(',') if x.strip() and x.strip() != 'nan'])

        impl_cols = [f"🔧 {i}" for i in impl_options]

        for i in edited_df.index:
            # 1. Enforce Single Select (Implementation)
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
                    elif edited_df.loc[i, '🔧 Customize/Integration']:
                        edited_df.loc[i, '🔧 Standard'] = False
                needs_rerun = True

            # 2. Product Non-Compliant Logic
            if edited_df.loc[i, '📦 Non-Compliant']:
                prod_cols_to_clear = ['📦 Zocial Eye', '📦 Warroom', '📦 Outsource', '📦 Other Product']
                if any(edited_df.loc[i, c] for c in prod_cols_to_clear):
                    for c in prod_cols_to_clear: edited_df.loc[i, c] = False
                    needs_rerun = True
                if not edited_df.loc[i, '🔧 Non-Compliant']:
                    edited_df.loc[i, '🔧 Non-Compliant'] = True; edited_df.loc[i, '🔧 Standard'] = False; edited_df.loc[i, '🔧 Customize/Integration'] = False
                    needs_rerun = True

            # 3. Status Check & Sync
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

        # --- FOOTER BUTTONS (SAVE/EXPORT) ---
        st.markdown("### 💾 Export Results")
        save_data = prepare_save_data(edited_df, product_options, impl_options)
        save_data = save_data[~save_data['Product'].str.contains('Non-Compliant', na=False)]

        col_save, col_export, col_reset = st.columns(3)
        with col_save:
            if st.button("💾 Save to Sheet", type="primary", disabled=len(save_data)==0):
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

        with col_export:
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                save_data.to_excel(writer, sheet_name='Data', index=False)
            st.download_button("⬇️ Download Excel", data=output.getvalue(), file_name="export.xlsx", mime="application/vnd.ms-excel")

        with col_reset:
             if st.button("🔄 Reset"):
                st.session_state.clear(); st.rerun()

# ==========================================
# TAB 2: BUDGET
# ==========================================
with tab_budget:
    st.markdown("### 💰 Budget Estimation")
    
    if not st.session_state.analysis_done:
        st.warning("⚠️ Please complete the 'Results & Verify' step first.")
    else:
        # Trigger Calc (if not yet)
        if not st.session_state.budget_calculated:
            if st.button("Generate Budget", type="primary"):
                with st.spinner("🤖 AI analyzing..."):
                    try:
                        factors = extract_budget_factors(st.session_state.tor_raw_text, st.session_state.gemini_key)
                        st.session_state.budget_factors = factors
                        st.session_state.budget_calculated = True
                        st.rerun()
                    except Exception as e: st.error(f"❌ Failed: {e}")
        
        if st.session_state.budget_calculated:
            # Calc
            results = calculate_budget_sheets(
                st.session_state.budget_factors, st.session_state.matched_products,
                st.session_state.pricing_df, st.session_state.addon_df
            )
            
            st.markdown("#### 🧾 Budget Breakdown")
            
            total_budget = 0
            if results:
                for res in results:
                    # Formatting HTML for Accordion style
                    with st.expander(f"📦 {res['Product']}", expanded=True):
                         # ✅ FIX 1: Clean raw HTML to prevent indentation issues in Markdown
                         raw_html = format_budget_report(res['Product'], res['Package'], st.session_state.budget_factors, res['Breakdown'])
                         clean_html = "\n".join([line.lstrip() for line in raw_html.split('\n')])
                         
                         st.markdown(clean_html, unsafe_allow_html=True)
                    
                    init_fee = res['Package'].get('Initial_Fee (THB)', 0)
                    if init_fee and isinstance(init_fee, (int, float)):
                         total_budget += res['Breakdown']['total'] + init_fee
                    else:
                         total_budget += res['Breakdown']['total']
                
                # --- ✅ MODIFIED: CALCULATE MANDAYS COST ---
                mandays = st.session_state.budget_factors.get('mandays', 0)
                manday_cost = mandays * 22000
                grand_total = total_budget + manday_cost
                
                # Show Manday Cost (If added)
                if mandays != 0:
                    st.markdown(f"""
                    <div style='background-color: #e3f2fd; padding: 15px; border-radius: 8px; margin-top: 15px; border: 1px solid #90caf9;'>
                        <h4 style='color: #1565c0; margin:0;'>🛠️ Customization Service</h4>
                        <p style='margin: 5px 0 0 0; font-size: 1.1em;'>
                            {mandays} Mandays × 22,000 THB = <strong>{manday_cost:,.0f} THB</strong>
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown(f"""
                <div style='background-color: #d4edda; padding: 20px; border-radius: 10px; border-left: 5px solid #28a745; text-align: right; margin-top:20px;'>
                    <h2 style='color: #155724; margin:0;'>💰 GRAND TOTAL: {grand_total:,.2f} THB/Year</h2>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.warning("⚠️ No suitable package found.")
            
            # --- EDIT FACTORS (Moved to bottom) ---
            st.markdown("---")
            st.markdown("#### ✏️ Edit Factors")
            
            with st.container():
                factors = st.session_state.budget_factors
                
                st.caption("Zocial Eye Parameters")
                col_ze1, col_ze2 = st.columns(2)
                ze_users = col_ze1.number_input("Number of Users", value=factors.get('num_users', 2), min_value=1)
                ze_days = col_ze2.number_input("Data Backward (Days)", value=factors.get('data_backward_days', 90), step=30)
                
                st.caption("Warroom Parameters")
                col_wr1, col_wr2 = st.columns(2)
                wr_users = col_wr1.number_input("Warroom Users", value=factors.get('num_users', 5), min_value=1, key="wr_u")
                wr_tx = col_wr2.number_input("Monthly Transactions", value=factors.get('monthly_transactions', 35000), step=1000)
                
                col_wr3, col_wr4 = st.columns(2)
                wr_ch = col_wr3.number_input("Social Channels", value=factors.get('social_channels_count', 0))
                wr_bot = col_wr4.checkbox("Chatbot Required", value=factors.get('chatbot_required', False))
                
                # --- ✅ MODIFIED: ADD CUSTOMIZATION INPUT ---
                st.caption("Customization Service")
                md_input = st.number_input(
                    "Customization Mandays (1 Manday = 22,000 THB)", 
                    value=factors.get('mandays', 0), 
                    step=1,
                    help="Add or subtract mandays for custom requirements"
                )
                
                if st.button("🔄 Recalculate Budget"):
                    st.session_state.budget_factors.update({
                        'num_users': ze_users, 
                        'data_backward_days': ze_days,
                        'monthly_transactions': wr_tx, 
                        'social_channels_count': wr_ch,
                        'chatbot_required': wr_bot,
                        'mandays': md_input  # Save mandays to session state
                    })
                    st.rerun()

# ===== FOOTER =====
st.markdown("---")
st.caption(f"WiseSight TOR Analyzer v2.3.2 | Session: {datetime.now().strftime('%Y-%m-%d')}")
