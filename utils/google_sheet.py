"""
Google Sheet Operations
"""

import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st
import re

def load_master_data(sheet_url):
    """
    Load master data from Google Sheet
    """
    try:
        # Use Streamlit secrets for credentials
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(
            creds_dict,
            scopes=[
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
        )
        client = gspread.authorize(creds)
        
        # Open sheet
        sh = client.open_by_url(sheet_url)
        
        print(f"✅ Connected to: {sh.title}")
        
        # Load tabs
        def get_sheet_data(sheet_obj, tab_names):
            for name in tab_names:
                try:
                    ws = sheet_obj.worksheet(name)
                    print(f"   Found tab: '{name}'")
                    return pd.DataFrame(ws.get_all_records())
                except: 
                    continue
            print(f"   ⚠️ Warning: Tab not found (Tried: {tab_names})")
            return pd.DataFrame()
        
        pricing_df = get_sheet_data(sh, ["Pricing_Rules", "Pricing Rules", "pricing_rules"])
        addon_df = get_sheet_data(sh, ["AddOns", "Addons", "Add-ons"])
        spec_df = get_sheet_data(sh, ["Product_Spec", "Product Spec", "Keywords"])
        def_df = get_sheet_data(sh, ["Definitions", "Definition", "definitions"])
        
        def_dict = {}
        if not def_df.empty:
            try:
                def_dict = dict(zip(def_df.iloc[:,0], def_df.iloc[:,1]))
            except: 
                pass
        
        return pricing_df, addon_df, spec_df, def_dict
    
    except Exception as e:
        st.error(f"❌ Failed to load Google Sheet: {e}")
        raise e


def save_to_product_spec(data_df, sheet_url):
    """
    Save verified data to Product_Spec sheet
    
    Args:
        data_df: DataFrame with columns [Product, Sentence_TH, Sentence_ENG, Implementation]
    """
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(
            creds_dict,
            scopes=[
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
        )
        client = gspread.authorize(creds)
        
        sh = client.open_by_url(sheet_url)
        spec_ws = sh.worksheet("Product_Spec")
        
        # Prepare rows
        rows_to_append = []
        for _, row in data_df.iterrows():
            rows_to_append.append([
                row['Product'],
                row['Sentence_TH'],
                row['Sentence_ENG'],
                row['Implementation']
            ])
        
        # Append to sheet
        spec_ws.append_rows(rows_to_append, value_input_option='RAW')
        
        return {"status": "success", "rows": len(rows_to_append)}
    
    except Exception as e:
        raise Exception(f"Failed to save to Google Sheet: {e}")


def undo_last_update(last_save_data, sheet_url):
    """
    Undo last save operation
    """
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(
            creds_dict,
            scopes=[
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
        )
        client = gspread.authorize(creds)
        
        sh = client.open_by_url(sheet_url)
        spec_ws = sh.worksheet("Product_Spec")
        
        # Find and delete rows
        all_rows = spec_ws.get_all_values()
        rows_to_delete = []
        
        for i, row in enumerate(all_rows[1:], start=2):  # Skip header
            if any(
                (row[1] == item['Sentence_TH'] and row[1] != '') or 
                (row[2] == item['Sentence_ENG'] and row[2] != '')
                for item in last_save_data
            ):
                rows_to_delete.append(i)
        
        # Delete in reverse order
        for row_idx in reversed(rows_to_delete):
            spec_ws.delete_rows(row_idx)
        
        return {"status": "success", "deleted": len(rows_to_delete)}
    
    except Exception as e:
        raise Exception(f"Failed to undo: {e}")
