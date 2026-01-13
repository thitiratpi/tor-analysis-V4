"""
Product Matching Logic
Port from Colab V29.0
"""

import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import gc

def analyze_tor_sentences_full_mode(tor_sentences, spec_df, api_key):
    """
    Main product matching function
    Multi-product matching with score >= 65%
    """
    print("\n" + "="*80)
    print("🎯 PRODUCT MATCHING + FR/NFR CLASSIFICATION")
    print("="*80)
    
    model_name = "paraphrase-multilingual-mpnet-base-v2"
    
    comparison_results = []
    matched_products = []
    
    keywords_th = spec_df['Sentence (TH)'].fillna('').astype(str).tolist()
    keywords_eng = spec_df['Sentence (ENG)'].fillna('').astype(str).tolist()
    implementations = spec_df['Implementation'].fillna('').astype(str).tolist()
    products_list = spec_df['Product'].fillna('').astype(str).tolist()
    
    # PART 1: PRODUCT MATCHING
    print(f"⏳ Matching Product ({model_name})...", end=" ")
    try:
        model = SentenceTransformer(model_name)
        
        tor_emb = model.encode(tor_sentences, show_progress_bar=False)
        th_emb = model.encode(keywords_th, show_progress_bar=False)
        eng_emb = model.encode(keywords_eng, show_progress_bar=False)
        
        sim_th = cosine_similarity(tor_emb, th_emb) * 100
        sim_eng = cosine_similarity(tor_emb, eng_emb) * 100
        
        for i, sent in enumerate(tor_sentences):
            # ✅ Use max similarity score between TH and ENG for each keyword
            max_scores = np.maximum(sim_th[i, :], sim_eng[i, :])
            
            # ✅ Find ALL products with score >= 65%
            matched_indices = np.where(max_scores >= 65)[0]
            
            if len(matched_indices) > 0:
                # Has matching products
                matched_prods = []
                matched_impls = []
                matched_keywords = []
                
                for idx in matched_indices:
                    prod = products_list[idx]
                    impl = implementations[idx]
                    
                    # Select better keyword between TH vs ENG
                    if sim_th[i, idx] >= sim_eng[i, idx]:
                        keyword = keywords_th[idx]
                    else:
                        keyword = keywords_eng[idx]
                    
                    matched_prods.append(prod)
                    matched_impls.append(impl if impl else "Standard")
                    matched_keywords.append(keyword)
                
                # ✅ Combine unique products
                unique_prods = list(dict.fromkeys(matched_prods))  # Preserve order
                unique_impls = list(dict.fromkeys(matched_impls))
                
                product_match = "; ".join(unique_prods)
                implementation_val = "; ".join(unique_impls)
                matched_keyword_val = matched_keywords[0]  # Take first
                
                matched_products.extend(unique_prods)
                
            else:
                # No matching products
                product_match = "Non-Compliant"
                implementation_val = "Non-Compliant"
                matched_keyword_val = "-"
            
            comparison_results.append({
                'TOR_Sentence': sent,
                'Product_Match': product_match,
                'Implementation': implementation_val,
                'Matched_Keyword': matched_keyword_val
            })
        
        print("Done!")
        
        del model, tor_emb, th_emb, eng_emb
        gc.collect()
        
    except Exception as e: 
        print(f"❌ Error: {e}")
        return [], pd.DataFrame()
    
    # Create DataFrame
    df_compare = pd.DataFrame(comparison_results)
    
    # ✅ Arrange columns (no Similarity_Score)
    df_compare = df_compare[[
        'TOR_Sentence', 
        'Product_Match',       # Multiple products
        'Implementation',      # Multiple implementations
        'Matched_Keyword'
    ]]
    
    # Add index
    df_compare.index = range(1, len(df_compare) + 1)
    df_compare.index.name = 'Index'
    
    print(f"\n📊 ANALYSIS RESULT ({len(df_compare)} lines):")
    print("   ℹ️  Multi-product format: 'Zocial Eye; Warroom'")
    print("   ℹ️  Products & Implementation can be edited")
    
    # Return unique products
    matched_products = list(set(matched_products))
    
    return matched_products, df_compare
