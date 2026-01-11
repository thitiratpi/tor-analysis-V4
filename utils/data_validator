"""
Data Validation & Processing
"""

import pandas as pd
import re

def prepare_save_data(edited_df, product_options, impl_options):
    """
    Convert edited DataFrame to save format
    Expands multi-product rows into separate rows
    """
    save_rows = []
    
    for _, row in edited_df.iterrows():
        # Get selected products
        selected_products = [
            prod for prod in product_options
            if row.get(prod, False) == True and prod != 'Non-Compliant'
        ]
        
        # Get selected implementations
        selected_impls = [
            impl for impl in impl_options
            if row.get(impl, False) == True and impl != 'Non-Compliant'
        ]
        
        # Skip if Non-Compliant
        if row.get('Non-Compliant', False):
            continue
        
        # Skip if no product selected
        if len(selected_products) == 0:
            continue
        
        # Detect language
        sentence = row['TOR_Sentence']
        is_thai = bool(re.search(r'[ก-ฮ]', sentence))
        
        # Create rows for each product
        for product in selected_products:
            for impl in (selected_impls if selected_impls else ['Standard']):
                save_rows.append({
                    'Product': product,
                    'Sentence_TH': sentence if is_thai else '',
                    'Sentence_ENG': sentence if not is_thai else '',
                    'Implementation': impl,
                    'TOR_Sentence': sentence  # For duplicate check
                })
    
    return pd.DataFrame(save_rows)


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
