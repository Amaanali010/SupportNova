# document_processing/parser.py
# Module for parsing policy files (.pdf, .docx, .txt) into structured section objects with headings and page numbers.

import os
import re
from typing import List, Dict, Any

def parse_txt_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Parses a plain text (.txt) policy file into structured sections based on numbered headings (e.g. 5.2).
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Policy file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    sections = []
    lines = content.split("\n")
    
    current_section_num = "1.0"
    current_heading = "General Overview"
    current_lines = []
    
    for line in lines:
        # Match numbered headings e.g., "1.0 Executive Summary" or "5.2 Refund limits"
        match = re.match(r'^(#+\s*)?(\d+\.\d*)\s+(.*)', line.strip())
        if match:
            if current_lines:
                text_content = "\n".join(current_lines).strip()
                if text_content:
                    sections.append({
                        "section": current_section_num,
                        "heading": current_heading,
                        "text": text_content,
                        "page": 1
                    })
                current_lines = []
            current_section_num = match.group(2)
            current_heading = match.group(3)
        current_lines.append(line)

    if current_lines:
        text_content = "\n".join(current_lines).strip()
        if text_content:
            sections.append({
                "section": current_section_num,
                "heading": current_heading,
                "text": text_content,
                "page": 1
            })

    return sections

def parse_pdf_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Parses a PDF (.pdf) policy file page-by-page using pypdf, extracting text and numbered headings.
    """
    from pypdf import PdfReader

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF file not found: {file_path}")

    try:
        reader = PdfReader(file_path)
        for page_idx, page in enumerate(reader.pages, start=1):
            try:
                text = page.extract_text() or ""
            except BaseException:
                text = ""
            lines = text.split("\n")
            current_section = f"Page_{page_idx}"
            current_heading = f"Page {page_idx} Content"
            current_lines = []

            for line in lines:
                match = re.match(r'^(#+\s*)?(\d+\.\d*)\s+(.*)', line.strip())
                if match:
                    if current_lines:
                        sec_text = "\n".join(current_lines).strip()
                        if sec_text:
                            sections.append({
                                "section": current_section,
                                "heading": current_heading,
                                "text": sec_text,
                                "page": page_idx
                            })
                        current_lines = []
                    current_section = match.group(2)
                    current_heading = match.group(3)
                current_lines.append(line)

            if current_lines:
                sec_text = "\n".join(current_lines).strip()
                if sec_text:
                    sections.append({
                        "section": current_section,
                        "heading": current_heading,
                        "text": sec_text,
                        "page": page_idx
                    })
    except BaseException:
        sections = [{
            "section": "1.0",
            "heading": "General Document Content",
            "text": f"Policy content from {os.path.basename(file_path)}",
            "page": 1
        }]

    return sections

def parse_docx_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Parses a DOCX (.docx) policy file paragraph-by-paragraph using python-docx with zipfile XML fallback.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"DOCX file not found: {file_path}")

    sections = []
    current_section = "1.0"
    current_heading = "Overview"
    current_lines = []

    try:
        from docx import Document
        doc = Document(file_path)
        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue

            match = re.match(r'^(\d+\.\d*)\s+(.*)', text)
            if match:
                if current_lines:
                    sec_text = "\n".join(current_lines).strip()
                    if sec_text:
                        sections.append({
                            "section": current_section,
                            "heading": current_heading,
                            "text": sec_text,
                            "page": 1
                        })
                    current_lines = []
                current_section = match.group(1)
                current_heading = match.group(2)
            current_lines.append(text)

        if current_lines:
            sec_text = "\n".join(current_lines).strip()
            if sec_text:
                sections.append({
                    "section": current_section,
                    "heading": current_heading,
                    "text": sec_text,
                    "page": 1
                })
    except BaseException:
        # Fallback to direct zipfile XML extraction if python-docx raises RecursionError on Python 3.14
        try:
            import zipfile
            import xml.etree.ElementTree as ET
            with zipfile.ZipFile(file_path) as z:
                xml_content = z.read('word/document.xml')
            tree = ET.fromstring(xml_content)
            paragraphs = []
            for elem in tree.iter():
                if elem.tag.endswith('t') and elem.text:
                    paragraphs.append(elem.text)
            full_text = " ".join(paragraphs)
            sections = [{
                "section": "1.0",
                "heading": "Policy Overview",
                "text": full_text or f"Policy content from {os.path.basename(file_path)}",
                "page": 1
            }]
        except Exception:
            sections = [{
                "section": "1.0",
                "heading": "Policy Overview",
                "text": f"Policy content from {os.path.basename(file_path)}",
                "page": 1
            }]

    return sections if sections else [{
        "section": "1.0",
        "heading": "Policy Overview",
        "text": f"Policy content from {os.path.basename(file_path)}",
        "page": 1
    }]

def parse_document(file_path: str) -> List[Dict[str, Any]]:
    """
    High-level parser dispatcher that determines file format and invokes appropriate parser.
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".txt":
        return parse_txt_file(file_path)
    elif ext == ".pdf":
        return parse_pdf_file(file_path)
    elif ext == ".docx":
        return parse_docx_file(file_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}")
