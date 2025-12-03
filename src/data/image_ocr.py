"""Görsel dosyalarından OCR ile metin çıkarma modülü."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PIL import Image
from rich import print

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    print("[yellow]Uyarı:[/yellow] pytesseract bulunamadı. OCR özelliği devre dışı.")


def preprocess_image(image_path: Path) -> np.ndarray:
    """Görseli OCR için ön işleme (gürültü azaltma, kontrast artırma)."""
    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Görsel yüklenemedi: {image_path}")
    
    # Gri tonlamaya çevir
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Gürültü azaltma
    denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
    
    # Kontrast artırma (CLAHE)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(denoised)
    
    # Eşikleme (thresholding)
    _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return thresh


def extract_text_from_image(image_path: Path, lang: str = "tur") -> str:
    """Görselden Türkçe metin çıkarır."""
    if not TESSERACT_AVAILABLE:
        return ""
    
    try:
        # Ön işleme
        processed_img = preprocess_image(image_path)
        
        # OCR (Türkçe dil desteği)
        # Tesseract Türkçe dil paketi yüklü olmalı: tesseract-lang
        text = pytesseract.image_to_string(
            processed_img,
            lang=lang,
            config="--psm 6"  # Tek blok metin varsayımı
        )
        
        return text.strip()
    except Exception as e:
        print(f"[red]Hata:[/red] {image_path.name} OCR hatası: {e}")
        return ""


def extract_question_from_image(image_path: Path) -> Optional[dict]:
    """Görselden soru metnini çıkarır ve yapılandırır."""
    print(f"[cyan]Görsel işleniyor:[/cyan] {image_path.name}")
    
    text = extract_text_from_image(image_path)
    if not text:
        return None
    
    # Soru yapısını parse et
    question_data = {
        "raw_text": text,
        "question_text": "",
        "options": [],
        "image_path": str(image_path),
        "has_keyword": any(kw in text.lower() for kw in ["kök", "√", "kareköklü"])
    }
    
    # Seçenekleri bul (A), B), C), D))
    lines = text.split("\n")
    for line in lines:
        if re.match(r"^\s*[A-D][\.\)]\s*", line):
            question_data["options"].append(line.strip())
        elif line.strip() and not question_data["question_text"]:
            question_data["question_text"] = line.strip()
    
    return question_data

