"""
Budget Calculation Engine
Port from Colab V29.0
"""

import pandas as pd
import numpy as np
import json
import requests
import re

def extract_budget_factors(tor_text, api_key):
    """
    Extract budget factors using AI
    """
    if not api_key:
        print("⚠️ No API Key - skipping budget extraction")
        return {}
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    prompt = f"""Act as Sales Engineer. Analyze TOR text. Return JSON (null if not found):
    - "product_type": "Zocial Eye" or "Warroom"
    - "num_users": Integer
    - "data_backward_days": Integer
    - "monthly_transactions": Integer
    - "social_channels_count": Integer
    - "chatbot_required": Boolean
    
    Text: {tor_text[:30000]}"""
    
    try:
        res = requests.post(
            url, 
            headers={'Content-Type': 'application/json'}, 
            data=json.dumps({"contents": [{"parts": [{"text": prompt}]}]}),
            timeout=30
        )
        if res.status_code == 200:
            raw_text = res.json()['candidates'][0]['content']['parts'][0]['text']
            raw_text = raw_text.replace('```json', '').replace('```', '').strip()
            return json.loads(raw_text)
    except Exception as e:
        print(f"⚠️ Budget extraction failed: {e}")
    
    return {}


def format_money(val):
    """Format money value"""
    try:
        if pd.isna(val) or val == '' or val == '-': 
            return "-"
        return f"{int(float(val)):,}"
    except: 
        return str(val)


def calculate_budget_sheets(factors, matched_products, pricing_df, addon_df):
    """
    Calculate budget for matched products
    Returns list of budget results
    """
    if pricing_df is None or pricing_df.empty:
        return []
    
    # Build addon dictionary
    addon_dict = {}
    if addon_df is not None and not addon_df.empty:
        for _, row in addon_df.iterrows():
            key = f"{str(row.get('Product','')).strip()}_{str(row.get('AddOn_Name','')).strip()}"
            if 'User_Limit' in key: 
                key = 'Warroom_User'
            elif 'Owned_Social_Channel' in key: 
                key = 'Warroom_Channel'
            addon_dict[key] = row.get('Price (THB)', 0)
    
    prod_type = factors.get('product_type')
    if not prod_type: 
        prod_type = " & ".join(matched_products)
    
    results = []
    
    # === ZOCIAL EYE ===
    if "Zocial Eye" in prod_type:
        users = factors.get('num_users') or 2
        bw = factors.get('data_backward_days') or 90
        
        df_z = pricing_df[pricing_df['Product'] == 'Zocial Eye'].copy()
        if not df_z.empty:
            df_z['Data_Backward (Days)'] = pd.to_numeric(df_z['Data_Backward (Days)'], errors='coerce').fillna(0)
            df_z['User_Limit (User)'] = pd.to_numeric(df_z['User_Limit (User)'], errors='coerce').fillna(0)
            
            valid = df_z[
                (df_z['Data_Backward (Days)'] >= bw) & 
                (df_z['User_Limit (User)'] >= users)
            ]
            
            best = valid.sort_values('Total_Price_Per_Year (THB)').iloc[0] if not valid.empty else df_z.iloc[-1]
            
            results.append({
                'Product': 'Zocial Eye',
                'Package': best,
                'Breakdown': {
                    'addon_cost': 0,
                    'details': [],
                    'total': best['Total_Price_Per_Year (THB)']
                }
            })
    
    # === WARROOM ===
    if "Warroom" in prod_type:
        users = factors.get('num_users') or 5
        tx = factors.get('monthly_transactions')
        ch = factors.get('social_channels_count')
        chatbot = factors.get('chatbot_required', False)
        
        df_w = pricing_df[pricing_df['Product'] == 'Warroom'].copy()
        if not df_w.empty:
            tx_col = 'Transaction_Limit_PerMonth (Messages)' if 'Transaction_Limit_PerMonth (Messages)' in df_w.columns else 'Message_Limit_PerMonth (Messages)'
            ch_col = 'Owned_Social_Channel (Account)'
            
            df_w['Tx_Num'] = pd.to_numeric(df_w[tx_col], errors='coerce').fillna(999999999)
            df_w['Ch_Num'] = pd.to_numeric(df_w[ch_col], errors='coerce').fillna(999)
            
            base_pack = None
            addon_cost = 0
            details = []
            
            # Select package based on chatbot/channels
            if chatbot or (ch and ch > 0):
                target_ch = ch if ch else 2
                unlimits = df_w[df_w['Tx_Num'] > 1000000].sort_values('Ch_Num')
                
                for _, row in unlimits.iterrows():
                    if row['Ch_Num'] >= target_ch: 
                        base_pack = row
                        break
                
                if base_pack is None:
                    base_pack = unlimits.iloc[-1]
                    extra_ch = target_ch - base_pack['Ch_Num']
                    cost = extra_ch * addon_dict.get('Warroom_Channel', 60000)
                    addon_cost += cost
                    details.append(f"{extra_ch} Extra Channels ({format_money(cost)} THB)")
            else:
                target_tx = tx if tx else 35000
                limits = df_w[df_w['Tx_Num'] < 1000000].sort_values('Tx_Num')
                
                for _, row in limits.iterrows():
                    if row['Tx_Num'] >= target_tx: 
                        base_pack = row
                        break
                
                if base_pack is None: 
                    base_pack = limits.iloc[-1]
            
            # Check user limit
            pkg_users = pd.to_numeric(base_pack['User_Limit (User)'], errors='coerce')
            if users > pkg_users:
                extra_u = users - pkg_users
                cost = extra_u * addon_dict.get('Warroom_User', 12000)
                addon_cost += cost
                details.append(f"{extra_u} Extra Users ({format_money(cost)} THB)")
            
            results.append({
                'Product': 'Warroom',
                'Package': base_pack,
                'Breakdown': {
                    'addon_cost': addon_cost,
                    'details': details,
                    'total': base_pack['Total_Price_Per_Year (THB)'] + addon_cost
                }
            })
    
    return results


def format_budget_report(product, package_row, factors, breakdown):
    """
    Format budget report as HTML for Streamlit
    """
    def get_val(col_name, suffix=""):
        val = package_row.get(col_name)
        if pd.isna(val) or val == "": 
            return "-"
        return f"{val} {suffix}".strip()
    
    def format_days(days):
        try:
            d = float(days)
            return f"{d:.1f} days ({d/30:.1f} months)"
        except: 
            return "-"
    
    # Build HTML
    html = f"""
    <div style="border: 2px solid #1f77b4; border-radius: 10px; padding: 20px; margin: 20px 0; background-color: #f8f9fa;">
        <h2 style="color: #1f77b4; margin-top: 0;">📦 {product}</h2>
        <h4 style="color: #666;">Package: {package_row.get('Package', 'Custom')}</h4>
        <hr style="border: 1px solid #ddd;">
        
        <h3 style="color: #ff7f0e;">📝 Factor Checklist</h3>
        <ul style="list-style-type: none; padding-left: 0;">
    """
    
    # Factors
    if product == 'Zocial Eye':
        users = factors.get('num_users')
        bw = factors.get('data_backward_days')
        html += f"""
            <li>{'✅' if users else '❌'} <b>Number of Users:</b> {users if users else 'Not found (Using Default)'}</li>
            <li>{'✅' if bw else '❌'} <b>Data Backward:</b> {bw if bw else 'Not found (Using Default)'} Days</li>
        """
    elif product == 'Warroom':
        users = factors.get('num_users')
        tx = factors.get('monthly_transactions')
        chatbot = factors.get('chatbot_required')
        html += f"""
            <li>{'✅' if users else '❌'} <b>Number of Users:</b> {users if users else 'Not found (Using Default)'}</li>
            <li>{'✅' if tx else '❌'} <b>Monthly Transactions:</b> {tx if tx else 'Not found (Using Default)'} Msgs</li>
            <li>✅ <b>Chatbot Required:</b> {'Yes' if chatbot else 'No (Assumed)'}</li>
        """
    
    html += """
        </ul>
        <hr style="border: 1px solid #ddd;">
        
        <h3 style="color: #ff7f0e;">📋 Package Details</h3>
        <ul>
    """
    
    # Package details
    init_fee = package_row.get('Initial_Fee (THB)', 0)
    html += f"<li><b>Initial Fee:</b> {format_money(init_fee)} THB (one-time)</li>"
    
    if product == 'Zocial Eye':
        html += f"""
            <li><b>Message limit per contract:</b> {format_money(package_row.get('Message_Limit_PerContract (Messages)'))} messages</li>
            <li><b>Campaign limit:</b> {get_val('Campaign_Limit', 'Campaigns')}</li>
            <li><b>User limit:</b> {get_val('User_Limit (User)', 'users')}</li>
            <li><b>Data backward:</b> {format_days(package_row.get('Data_Backward (Days)'))}</li>
            <li><b>Insight prompts:</b> {get_val('Insight_Prompts')}</li>
        """
    elif product == 'Warroom':
        tx_limit = package_row.get('Transaction_Limit_PerMonth (Messages)') or package_row.get('Message_Limit_PerMonth (Messages)')
        html += f"""
            <li><b>Message/Transaction limit:</b> {format_money(tx_limit) if tx_limit else 'Unlimited'}</li>
            <li><b>User limit:</b> {get_val('User_Limit (User)', 'users')}</li>
            <li><b>Owned social channel:</b> {get_val('Owned_Social_Channel (Account)', 'channels')}</li>
            <li><b>Chat history:</b> {get_val('Chat_History')}</li>
        """
    
    html += f"<li><b>Annual Base Price:</b> {format_money(package_row.get('Total_Price_Per_Year (THB)'))} THB</li>"
    html += "</ul>"
    
    # Add-ons
    if breakdown['addon_cost'] > 0:
        html += """
            <hr style="border: 1px solid #ddd;">
            <h3 style="color: #ff7f0e;">🔧 Add-ons</h3>
            <ul>
        """
        for detail in breakdown['details']:
            html += f"<li>{detail}</li>"
        html += f"<li><b>Total Add-ons Cost:</b> {format_money(breakdown['addon_cost'])} THB/Year</li>"
        html += "</ul>"
    
    # Total
    grand_total = breakdown['total']
    if init_fee and isinstance(init_fee, (int, float)):
        grand_total += init_fee
    
    html += f"""
        <hr style="border: 2px solid #1f77b4;">
        <h2 style="color: #28a745; text-align: center;">💰 TOTAL ANNUAL PRICE: {format_money(grand_total)} THB/Year</h2>
    </div>
    """
    
    return html
