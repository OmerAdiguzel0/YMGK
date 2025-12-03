"""Kareköklü ifadeler sorularını filtreleme modülü."""

from __future__ import annotations

import re
from typing import List


def is_koklu_question(text: str) -> bool:
    """Bir metnin kareköklü ifadeler sorusu olup olmadığını kontrol eder."""
    if not text or len(text.strip()) < 10:
        return False
    
    text_lower = text.lower()
    
    # Anahtar kelimeler
    keywords = [
        "kök", "kareköklü", "karekök", "irrasyonel",
        "√", "kök içinde", "kök dışına", "kök dışına çıkarma",
        "kök içine alma", "kök içine", "kök dışına çıkarma"
    ]
    
    # Anahtar kelime kontrolü
    has_keyword = any(kw in text_lower for kw in keywords)
    
    # √ sembolü kontrolü (farklı Unicode varyasyonları)
    sqrt_symbols = ["√", "√", "√", "√", "√"]
    has_sqrt_symbol = any(symbol in text for symbol in sqrt_symbols)
    
    # Kök içinde sayı pattern'i (örn: √48, √12, √(a+b))
    sqrt_patterns = [
        r'√\s*\d+',  # √48, √12
        r'√\s*\([^)]+\)',  # √(a+b)
        r'√\s*[a-zA-Z]',  # √a, √x
        r'\d+\s*√',  # 3√, 5√
        r'√\s*\d+\s*[+\-*/]\s*√',  # √48 + √12
    ]
    
    has_sqrt_pattern = any(re.search(pattern, text) for pattern in sqrt_patterns)
    
    # Kök işlemleri (toplama, çıkarma, çarpma, bölme)
    sqrt_operations = [
        r'√\s*\d+\s*[+\-]\s*√\s*\d+',  # √48 + √12
        r'√\s*\d+\s*[*/]\s*√\s*\d+',  # √48 * √12
        r'√\s*\d+\s*:\s*√\s*\d+',  # √48 : √12
    ]
    
    has_sqrt_operation = any(re.search(pattern, text) for pattern in sqrt_operations)
    
    # Kök dışına çıkarma ifadeleri
    extraction_keywords = [
        "dışına çıkarma", "dışına çıkar", "dışına", 
        "sadeleştir", "sadeleştirme", "en sade"
    ]
    has_extraction = any(kw in text_lower for kw in extraction_keywords)
    
    # En az bir kriter sağlanmalı
    return (
        has_keyword or 
        has_sqrt_symbol or 
        has_sqrt_pattern or 
        has_sqrt_operation or 
        has_extraction
    )


def filter_koklu_questions(questions: List[dict]) -> List[dict]:
    """Soru listesinden sadece kareköklü ifadeler sorularını filtreler."""
    filtered = []
    
    for q in questions:
        # Soru metnini birleştir
        question_text = q.get("raw_text", "") or q.get("question_text", "")
        options_text = " ".join(q.get("options", []))
        full_text = f"{question_text} {options_text}"
        
        # Kareköklü ifadeler kontrolü
        if is_koklu_question(full_text):
            q["is_koklu"] = True
            q["filter_reason"] = "kareköklü_ifadeler"
            filtered.append(q)
    
    return filtered


def extract_sqrt_numbers(text: str) -> List[str]:
    """Metinden kök içindeki sayıları çıkarır."""
    patterns = [
        r'√\s*(\d+)',  # √48 -> 48
        r'√\s*\(([^)]+)\)',  # √(a+b) -> a+b
    ]
    
    numbers = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        numbers.extend(matches)
    
    return numbers

