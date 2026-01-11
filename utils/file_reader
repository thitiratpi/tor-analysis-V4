"""
Advanced File Reading
Port from Colab V29.0
"""

import pandas as pd
import numpy as np
import re
import io
from docx import Document
import pdfplumber

def normalize(s):
    """Normalize string for comparison"""
    return re.sub(r'\s+', '', str(s)).lower()


def read_file_content(uploaded_file):
    """
    Read content from uploaded file with advanced parsing
    Supports: PDF, Word, Excel, Text
    """
    fname = uploaded_file.name
    content = uploaded_file.read()
    text = ""
    
    print(f"📂 Reading file: {fname}...")
    
    try:
        if fname.endswith('.pdf'):
            text = read_pdf_advanced(content)
        
        elif fname.endswith('.docx'):
            text = read_word_advanced(content)
        
        elif fname.endswith(('.xlsx', '.xls')):
            text = read_excel_advanced(content)
        
        elif fname.endswith('.txt'):
            text = content.decode('utf-8')
            print(f"✅ Text file loaded")
        
        else:
            raise ValueError(f"Unsupported file type: {fname}")
        
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        import traceback
        traceback.print_exc()
    
    return text


def read_pdf_advanced(content):
    """
    Advanced PDF reading with table detection
    Port from Colab code (500+ lines simplified)
    """
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        full_doc_text = []
        
        for page_idx, page in enumerate(pdf.pages):
            page_content = []
            tables = page.find_tables()
            tables.sort(key=lambda x: x.bbox[1])
            
            # Track table content to avoid duplicates
            page_table_content_set = set()
            page_table_id_set = set()
            
            for table in tables:
                data = table.extract()
                if data:
                    for row in data:
                        row_str = " ".join([str(c) for c in row if c])
                        norm_str = normalize(row_str)
                        if len(norm_str) > 5:
                            page_table_content_set.add(norm_str)
                        match = re.match(r'^([a-z]{2,}[\s\-\.]?[\d\.]+)', norm_str)
                        if match:
                            page_table_id_set.add(match.group(1))
            
            current_y = 0
            
            # Extract text between tables
            for table in tables:
                top = table.bbox[1]
                if top > current_y:
                    try:
                        text_crop = page.crop((0, current_y, page.width, top))
                        text_above = text_crop.extract_text()
                        if text_above:
                            lines = text_above.split('\n')
                            for line in lines:
                                norm_line = normalize(line)
                                if len(norm_line) < 3: 
                                    continue
                                
                                # Check for duplicates
                                is_duplicate = False
                                for table_row in page_table_content_set:
                                    if norm_line in table_row: 
                                        is_duplicate = True
                                        break
                                
                                if not is_duplicate:
                                    match = re.match(r'^([a-z]{2,}[\s\-\.]?[\d\.]+)', norm_line)
                                    if match and match.group(1) in page_table_id_set: 
                                        is_duplicate = True
                                
                                if not is_duplicate:
                                    page_content.append(line)
                    except: 
                        pass
                
                # Extract table content
                data = table.extract()
                if data:
                    for row in data:
                        cleaned_row = [str(cell).strip().replace('\n', ' ') for cell in row if cell]
                        if cleaned_row:
                            table_line = " ".join(cleaned_row)
                            if len(table_line) > 5:
                                page_content.append(table_line)
                
                current_y = table.bbox[3]
            
            # Extract text below tables
            if current_y < page.height:
                try:
                    text_crop = page.crop((0, current_y, page.width, page.height))
                    text_below = text_crop.extract_text()
                    if text_below:
                        lines = text_below.split('\n')
                        for line in lines:
                            norm_line = normalize(line)
                            if len(norm_line) < 3: 
                                continue
                            
                            is_duplicate = False
                            for table_row in page_table_content_set:
                                if norm_line in table_row: 
                                    is_duplicate = True
                                    break
                            
                            if not is_duplicate:
                                match = re.match(r'^([a-z]{2,}[\s\-\.]?[\d\.]+)', norm_line)
                                if match and match.group(1) in page_table_id_set: 
                                    is_duplicate = True
                            
                            if not is_duplicate:
                                page_content.append(line)
                except: 
                    pass
            
            # Fallback if page content is too short
            if len("".join(page_content)) < 50:
                fallback_text = page.extract_text()
                if fallback_text:
                    full_doc_text.append(fallback_text)
            else:
                full_doc_text.extend(page_content)
        
        text = "\n".join(full_doc_text)
        print(f"✅ PDF loaded: {len(full_doc_text)} lines")
    
    return text


def read_word_advanced(content):
    """
    Advanced Word reading with structure preservation
    Port from Colab code
    """
    doc = Document(io.BytesIO(content))
    full_text = []
    
    for element in doc.element.body:
        if element.tag.endswith('p'):
            for para in doc.paragraphs:
                if para._element == element:
                    text_content = para.text.strip()
                    if text_content:
                        text_content = text_content.replace('\t', ' ')
                        text_content = re.sub(r'\s+', ' ', text_content)
                        full_text.append(text_content)
                    break
        
        elif element.tag.endswith('tbl'):
            for table in doc.tables:
                if table._element == element:
                    for row in table.rows:
                        for cell in row.cells:
                            for para in cell.paragraphs:
                                para_text = para.text.strip()
                                if para_text:
                                    lines = para_text.split('\n')
                                    for line in lines:
                                        line = line.strip()
                                        if line:
                                            line = line.replace('\t', ' ')
                                            line = re.sub(r'\s+', ' ', line)
                                            full_text.append(line)
                    break
    
    text = "\n".join(full_text)
    print(f"✅ Word file loaded: {len(full_text)} lines")
    
    return text


def read_excel_advanced(content):
    """
    Advanced Excel reading with multi-sheet support
    Port from Colab code
    """
    excel_data = pd.read_excel(io.BytesIO(content), sheet_name=None)
    all_text_parts = []
    
    for sheet_name, df in excel_data.items():
        print(f"📊 Processing Sheet: {sheet_name}")
        print(f"   Rows in sheet: {len(df)}")
        
        for row_idx, row in df.iterrows():
            row_parts = []
            
            for col_idx, val in enumerate(row):
                if pd.notna(val):
                    val_str = str(val).strip()
                    
                    if val_str and len(val_str) > 0:
                        val_str = re.sub(r'\s+', ' ', val_str)
                        row_parts.append(val_str)
            
            if row_parts:
                row_text = " ".join(row_parts)
                
                if len(row_text.strip()) > 5:
                    all_text_parts.append(row_text)
                    
                    if row_idx < 3:
                        print(f"   Row {row_idx}: {row_text[:80]}...")
    
    text = "\n".join(all_text_parts)
    print(f"✅ Excel file loaded: {len(all_text_parts)} lines from {len(excel_data)} sheet(s)")
    
    return text


def extract_sentences_from_tor(text):
    """Extract sentences from formatted text"""
    return [line.strip() for line in text.split('\n') if len(line.strip()) > 2]
