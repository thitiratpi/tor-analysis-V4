"""
AI Processing Functions
Port from Colab V29.0
"""

import re
import json
import requests
import time

def extract_scope_smart_ai(full_text, api_key):
    """
    AI INTELLIGENT FORMATTING (Language & Numeral Detection)
    Port from Colab code
    """
    if not api_key:
        print("⚠️ No API Key - using basic formatting")
        return full_text
    
    # STEP 0: LANGUAGE & NUMERAL DETECTION
    sample_text = full_text[:3000]
    thai_char_count = len(re.findall(r'[ก-ฮ]', sample_text))
    is_thai_doc = thai_char_count > 20
    
    thai_digits = len(re.findall(r'[๐-๙]', sample_text))
    is_thai_numeral = thai_digits > 5
    
    print(f"🌍 Language: {'THAI' if is_thai_doc else 'ENGLISH'}")
    print(f"🔢 Numerals: {'THAI' if is_thai_numeral else 'ARABIC'}")
    
    # STEP 1: PYTHON PRE-PROCESSING (Buffer Logic)
    raw_lines = full_text.split('\n')
    cleaned_lines = []
    
    page_num_pattern = re.compile(r'^\s*-?\s*(หน้า|Page)?\s*[\d๐-๙]+\s*-?\s*$', re.IGNORECASE)
    bullet_chars = r'\-\•\*\‣\⁃\●'
    
    bullet_pattern = re.compile(r'^(' +
        r'[\d๐-๙]+(\.[\d๐-๙]+)*\.|' +
        r'\([\d๐-๙]+\)|' +
        r'\([a-zA-Z]\)|' +
        r'[a-zA-Z]\.|' +
        r'[ก-ฮ]\.|' +
        r'[' + bullet_chars + r']|' +
        r'ข้อที่' +
        r')')
    
    current_buffer = ""
    
    for line in raw_lines:
        line = line.strip()
        if not line: 
            continue
        if page_num_pattern.match(line):
            if len(line) < 10: 
                continue
        
        should_split = False
        is_bullet = bool(bullet_pattern.match(line))
        
        if is_thai_doc:
            if is_bullet: 
                should_split = True
        else:
            is_header = (len(line) < 80) and \
                        (line[0].isupper()) and \
                        (not line.endswith('.')) and \
                        (not line.endswith(',')) and \
                        (not line.endswith(':')) and \
                        ("updated information" not in line.lower())
            
            if is_bullet or (is_header and current_buffer != ""):
                should_split = True
        
        if should_split:
            if current_buffer: 
                cleaned_lines.append(current_buffer)
            current_buffer = line
        else:
            if current_buffer:
                current_buffer = current_buffer + " " + line
            else:
                current_buffer = line
    
    if current_buffer: 
        cleaned_lines.append(current_buffer)
    pre_cleaned_text = "\n".join(cleaned_lines)
    
    # STEP 2: AI REFINEMENT
    models = ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"]
    headers = {'Content-Type': 'application/json'}
    
    if is_thai_doc:
        numeral_instruction = """
        🚨 NUMERAL RULE: The document uses THAI NUMERALS (๑, ๒).
        Please output THAI NUMERALS in the list.
        """ if is_thai_numeral else "🚨 NUMERAL RULE: Use ARABIC NUMERALS (1, 2)."
        
        prompt = f"""
        You are a TOR Specialist. Language: THAI.
        Target: Clean JSON List of ALL requirements.
        {numeral_instruction}
        🚧 RULES:
        1. TABLE DATA: Treat "TR 1.1", "REQ-01" as bullet points.
        2. NO TRANSLATION: Keep text exactly as found.
        3. NO FILTERING: Do NOT remove any sections. Keep Introduction, Commercial, Scope, EVERYTHING.
        Input: {pre_cleaned_text[:40000]}
        """
    else:
        prompt = f"""
        You are a TOR Specialist. Language: ENGLISH.
        Target: Clean JSON List of ALL requirements.
        🚧 RULES:
        1. TABLE DATA: Treat "TR 1.1" as bullet points.
        2. FUSED TEXT: Split items stuck together.
        3. NO FILTERING: Do NOT remove any sections. Keep Introduction, Commercial, Scope, EVERYTHING.
        Input: {pre_cleaned_text[:40000]}
        """
    
    ai_result_list = []
    for model in models:
        print(f"🔄 Trying AI Model: {model}...")
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            response = requests.post(
                url, 
                headers=headers, 
                data=json.dumps({"contents": [{"parts": [{"text": prompt}]}]}),
                timeout=30
            )
            if response.status_code == 200:
                print(f"✅ SUCCESS with {model}!")
                raw_text = response.json()['candidates'][0]['content']['parts'][0]['text']
                raw_text = raw_text.replace('```json', '').replace('```', '').strip()
                try:
                    ai_result_list = json.loads(raw_text)
                    print(f"✅ Parsed JSON successfully")
                    break
                except:
                    ai_result_list = raw_text.split('\n')
                    break
            elif response.status_code == 429: 
                time.sleep(2)
        except Exception as e:
            print(f"⚠️ Error with {model}: {e}")
            continue
    
    if not ai_result_list:
        print("⚠️ AI Failed, using pre-processed text.")
        return pre_cleaned_text
    
    # STEP 3: POST-PROCESSING (FORCE NUMERAL FIX)
    trans_to_thai = str.maketrans('0123456789', '๐๑๒๓๔๕๖๗๘๙')
    trans_to_arabic = str.maketrans('๐๑๒๓๔๕๖๗๘๙', '0123456789')
    final_lines = []
    
    for item in ai_result_list:
        item = str(item).strip()
        if not item: 
            continue
        
        match = re.match(r'^([\d๐-๙\.\(\)\-]+\.?)(.*)', item)
        if match:
            bullet_part = match.group(1)
            content_part = match.group(2)
            new_bullet = bullet_part.translate(trans_to_thai if is_thai_numeral else trans_to_arabic)
            final_lines.append(new_bullet + content_part)
        else:
            final_lines.append(item)
    
    return "\n".join(final_lines)


def classify_scope_regex(sentences):
    """
    Regex-based classifier (fallback when AI fails)
    Classifies as Functional or Non-Functional Requirements
    """
    results = []
    
    for sent in sentences:
        sent_lower = sent.lower()
        is_nfr = False  # Default: Functional
        
        # NON-FUNCTIONAL PATTERNS
        nfr_patterns = [
            # Performance & Scalability
            r'(รองรับ).*(ผู้ใช้งาน|users|บัญชี|concurrent)',
            r'(รองรับ).*([\d,]+\s*(คน|user|account))',
            r'(response time|เวลาตอบสนอง|ความเร็ว)',
            r'(performance|ประสิทธิภาพ|throughput)',
            r'(scalability|ขยายได้|scale)',
            
            # Availability & Reliability
            r'(uptime|availability|ความพร้อมใช้งาน)',
            r'(99\.9%|ตลอด\s*24\s*ชั่วโมง|24/7)',
            r'(backup|สำรองข้อมูล|recovery)',
            r'(disaster recovery|แผนฉุกเฉิน)',
            
            # Security
            r'(security|ความปลอดภัย|encryption|เข้ารหัส)',
            r'(authentication|authorization|SSO|OAuth)',
            r'(access control|สิทธิ์การเข้าถึง|role)',
            r'(audit|audit trail|log)',
            
            # Usability
            r'(usability|ใช้งานง่าย|user[\s-]*friendly)',
            r'(interface|ui|ux|หน้าจอ)',
            r'(responsive|รองรับ).*(มือถือ|mobile|tablet)',
            
            # Compatibility
            r'(compatibility|เข้ากันได้|รองรับ).*(browser|เบราว์เซอร์)',
            r'(รองรับ).*(chrome|firefox|safari|edge)',
            r'(cross[\s-]*platform|ข้ามแพลตฟอร์ม)',
            
            # Technical Constraints
            r'(cloud|คลาวด์)',
            r'(api|integration|เชื่อมต่อ).*(third[\s-]*party|ระบบภายนอก)',
        ]
        
        for pattern in nfr_patterns:
            if re.search(pattern, sent_lower, re.IGNORECASE):
                is_nfr = True
                break
        
        results.append(is_nfr)
    
    return results


def calculate_regex_confidence(sentence):
    """
    Calculate confidence score for FR/NFR classification
    """
    sent_lower = sentence.lower()
    
    # High confidence NFR patterns
    high_conf_nfr = [
        r'รองรับ.*[\d,]+.*คน',
        r'รองรับ.*[\d,]+.*user',
        r'99\.9%',
        r'uptime',
        r'response time',
        r'performance',
        r'concurrent',
    ]
    
    # High confidence FR patterns
    high_conf_fr = [
        r'ระบบต้อง.*จัดเก็บ',
        r'ระบบต้อง.*แสดงผล',
        r'ระบบต้อง.*วิเคราะห์',
        r'system must.*provide',
        r'platform must.*support',
    ]
    
    for pattern in high_conf_nfr:
        if re.search(pattern, sent_lower):
            return 0.95
    
    for pattern in high_conf_fr:
        if re.search(pattern, sent_lower):
            return 0.95
    
    # Medium confidence
    medium_patterns = [
        r'สามารถ', r'รองรับ', r'แสดงผล',
        r'can', r'support', r'provide',
    ]
    
    for pattern in medium_patterns:
        if re.search(pattern, sent_lower):
            return 0.7
    
    return 0.3


def classify_scope_batch_fast(sentences, api_key, batch_size=20):
    """
    AI Classifier: Functional vs Non-Functional Requirements
    """
    results = []
    consecutive_rate_limits = 0
    
    models_to_try = [
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
    ]
    
    system_context = """You are a **Requirements Analysis Expert**.

🎯 MISSION: Classify requirements as "FUNCTIONAL" or "NON-FUNCTIONAL".

📘 DEFINITIONS:

**FUNCTIONAL REQUIREMENTS (FR):**
- Describe WHAT the system must do
- Features, functions, capabilities, deliverables
- Examples:
  • "ระบบต้องสามารถจัดเก็บข้อมูล" → FUNCTIONAL
  • "ระบบต้องแสดง Dashboard" → FUNCTIONAL
  • "System must provide search function" → FUNCTIONAL
  • "ผู้รับจ้างต้องจัดทำรายงาน" → FUNCTIONAL

**NON-FUNCTIONAL REQUIREMENTS (NFR):**
- Describe HOW the system must perform
- Quality attributes: Performance, Security, Usability, Availability, Scalability
- Examples:
  • "ระบบรองรับผู้ใช้งาน 1000 คน" → NON-FUNCTIONAL (Scalability)
  • "Response time ไม่เกิน 2 วินาที" → NON-FUNCTIONAL (Performance)
  • "Uptime 99.9%" → NON-FUNCTIONAL (Availability)
  • "ระบบต้องมีการเข้ารหัสข้อมูล" → NON-FUNCTIONAL (Security)
  • "รองรับ Chrome, Firefox, Safari" → NON-FUNCTIONAL (Compatibility)

⚠️ SPECIAL CASES:
- Background/Introduction → FUNCTIONAL (default)
- Commercial terms (penalties, payment) → FUNCTIONAL (default)
- Vendor qualifications → FUNCTIONAL (default)

📚 EXAMPLES:
Input: ["ระบบต้องรวบรวมข้อมูล Social Media", "ระบบรองรับผู้ใช้งาน 500 คน", "Response time < 2 seconds"]
Output: ["Functional", "Non-Functional", "Non-Functional"]

Input: ["Platform must analyze sentiment", "System must support 10,000 concurrent users", "99.9% uptime required"]
Output: ["Functional", "Non-Functional", "Non-Functional"]
"""
    
    total_batches = (len(sentences) + batch_size - 1) // batch_size
    
    for batch_idx in range(0, len(sentences), batch_size):
        batch = sentences[batch_idx:batch_idx+batch_size]
        batch_num = batch_idx // batch_size + 1
        
        progress_pct = int((batch_num / total_batches) * 100)
        print(f"[{progress_pct:3d}%] Batch {batch_num}/{total_batches}...", end=" ")
        
        final_prompt = f"""{system_context}

NOW ANALYZE THESE SENTENCES:
{json.dumps(batch, ensure_ascii=False, indent=2)}

INSTRUCTIONS:
1. For EACH sentence, decide: Is this FUNCTIONAL or NON-FUNCTIONAL?
2. Return ONLY a JSON array of strings: ["Functional", "Non-Functional", "Functional", ...]
3. Array MUST have EXACTLY {len(batch)} elements
4. Use EXACT spelling: "Functional" or "Non-Functional" (case-sensitive)
5. NO markdown, NO explanations, JUST the JSON array

OUTPUT:"""
        
        batch_results = None
        
        for model in models_to_try:
            if batch_results is not None:
                break
            
            for attempt in range(2):
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
                    
                    payload = {
                        "contents": [{"parts": [{"text": final_prompt}]}],
                        "generationConfig": {
                            "temperature": 0.1,
                            "topP": 0.8,
                            "topK": 10,
                            "maxOutputTokens": 500,
                        }
                    }
                    
                    response = requests.post(
                        url,
                        headers={'Content-Type': 'application/json'},
                        data=json.dumps(payload),
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        raw_res = response.json()['candidates'][0]['content']['parts'][0]['text']
                        raw_res = raw_res.replace('```json', '').replace('```', '').strip()
                        
                        try:
                            result_list = json.loads(raw_res)
                            if isinstance(result_list, list) and len(result_list) == len(batch):
                                batch_results = result_list
                                consecutive_rate_limits = 0
                                print(f"✅")
                                break
                        except:
                            # Fallback parsing
                            lines = raw_res.split('\n')
                            fallback_list = []
                            for line in lines:
                                line_lower = line.lower()
                                if 'non-functional' in line_lower or 'nonfunctional' in line_lower:
                                    fallback_list.append("Non-Functional")
                                elif 'functional' in line_lower:
                                    fallback_list.append("Functional")
                            
                            if len(fallback_list) == len(batch):
                                batch_results = fallback_list
                                consecutive_rate_limits = 0
                                print(f"✅ (fallback)")
                                break
                    
                    elif response.status_code == 429:
                        consecutive_rate_limits += 1
                        
                        if consecutive_rate_limits >= 3:
                            print(f"⏸️ (pause 60s)...", end=" ")
                            time.sleep(60)
                            consecutive_rate_limits = 0
                        else:
                            time.sleep(3)
                        
                        if attempt < 1:
                            continue
                        else:
                            break
                    
                    else:
                        if attempt < 1:
                            continue
                        else:
                            break
                
                except:
                    if attempt < 1:
                        continue
                    else:
                        break
                
                if batch_results is not None:
                    break
        
        if batch_results is None:
            print(f"⚠️ Regex")
            regex_results = classify_scope_regex(batch)
            batch_results = ["Non-Functional" if r else "Functional" for r in regex_results]
        
        results.extend(batch_results)
    
    return results


def classify_scope_hybrid(sentences, api_key):
    """
    HYBRID STRATEGY: Classify Functional vs Non-Functional Requirements
    
    Strategy:
    - Phase 1: Regex pre-filter (fast, ~70% accuracy)
    - Phase 2: AI selective (uncertain cases only)
    """
    print(f"🎯 Hybrid Classification: {len(sentences)} sentences")
    
    results = []
    uncertain_indices = []
    uncertain_sentences = []
    
    # PHASE 1: REGEX PRE-FILTER
    print("📊 Phase 1: Regex pre-filter...", end=" ")
    
    regex_results = classify_scope_regex(sentences)
    confidences = [calculate_regex_confidence(sent) for sent in sentences]
    
    for i, (sent, is_nfr, confidence) in enumerate(zip(sentences, regex_results, confidences)):
        if confidence >= 0.9:
            results.append("Non-Functional" if is_nfr else "Functional")
        else:
            uncertain_indices.append(i)
            uncertain_sentences.append(sent)
            results.append(None)
    
    print(f"Done! ({len(uncertain_sentences)} uncertain)")
    
    # PHASE 2: AI SELECTIVE
    if uncertain_sentences:
        print(f"🤖 Phase 2: AI classification ({len(uncertain_sentences)} items)...")
        print(f"Expected time: ~{len(uncertain_sentences) // 20 * 10}s")
        
        ai_results = classify_scope_batch_fast(
            uncertain_sentences, 
            api_key,
            batch_size=20
        )
        
        for idx, ai_result in zip(uncertain_indices, ai_results):
            results[idx] = ai_result
    
    print(f"✅ Hybrid classification complete!")
    return results
