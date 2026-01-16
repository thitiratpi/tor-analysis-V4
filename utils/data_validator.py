"""
Data Validation & Processing
"""

import pandas as pd
import re

def prepare_save_data(edited_df, product_options, impl_options):
    """Prepare data for saving"""
    save_data = []
    
    for idx in edited_df.index:
        # Get selected products
        products = [
            prod for prod in product_options 
            if edited_df.loc[idx, f'📦 {prod}']
        ]
        
        # ✅ Get implementation from selectbox (not checkboxes!)
        implementation = edited_df.loc[idx, '🔧 Implementation']
        
        for product in products:
            save_data.append({
                'Product': product,
                'TOR_Sentence': edited_df.loc[idx, 'TOR_Sentence'],
                'Matched_Keyword': edited_df.loc[idx, 'Matched_Keyword'],
                'Requirement_Type': edited_df.loc[idx, 'Requirement_Type'],
                'Implementation': implementation
            })
    
    return pd.DataFrame(save_data)


def check_duplicates(save_data, spec_df):
    """
    Check for duplicate sentences in existing sheet
    """
    existing_sentences_th = set(spec_df['Sentence (TH)'].dropna().astype(str).str.strip())
    existing_sentences_eng = set(spec_df['Sentence (ENG)'].dropna().astype(str).str.strip())
    
    duplicates = []
    
    for _, row in save_data.iterrows():
        is_duplicate = False
        
        if row['Sentence_TH'] and row['Sentence_TH'].strip() in existing_sentences_th:
            is_duplicate = True
        
        if row['Sentence_ENG'] and row['Sentence_ENG'].strip() in existing_sentences_eng:
            is_duplicate = True
        
        if is_duplicate:
            duplicates.append(row)
    
    return pd.DataFrame(duplicates)


def validate_products(edited_df, product_options):
    """
    Validate product selections
    
    Rules:
    - At least one product must be selected (or Non-Compliant)
    - If Non-Compliant, no other products can be selected
    """
    errors = []
    
    for idx, row in edited_df.iterrows():
        # Check if any product selected
        products_selected = sum([
            row.get(prod, False) for prod in product_options
        ])
        
        if products_selected == 0:
            errors.append(f"Row {idx+1}: No product selected")
        
        # Check Non-Compliant logic
        if row.get('Non-Compliant', False):
            other_products = sum([
                row.get(prod, False) for prod in product_options
                if prod != 'Non-Compliant'
            ])
            if other_products > 0:
                errors.append(f"Row {idx+1}: Non-Compliant cannot be selected with other products")
    
    return errors
