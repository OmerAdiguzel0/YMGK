"""PDF dosyalarından metin ve görsel çıkarma modülü."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Optional

import pdfplumber
from rich import print

from src.data.koklu_filter import filter_koklu_questions, is_koklu_question


def extract_text_from_pdf(pdf_path: Path) -> str:
    """PDF dosyasından tüm metni çıkarır."""
    text_content = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text:
                    text_content.append(f"--- Sayfa {page_num} ---\n{text}\n")
        
        return "\n".join(text_content)
    except Exception as e:
        print(f"[red]Hata:[/red] {pdf_path.name} işlenirken hata oluştu: {e}")
        return ""


def extract_images_from_pdf(pdf_path: Path, output_dir: Path) -> List[Path]:
    """PDF dosyasından görselleri çıkarır ve kaydeder."""
    extracted_images = []
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                images = page.images
                for img_idx, img in enumerate(images):
                    # PDF'den görsel çıkarma (pdfplumber sınırlı destek verir)
                    # Daha iyi sonuç için pdf2image kullanılabilir
                    img_path = output_dir / f"{pdf_path.stem}_page{page_num}_img{img_idx}.png"
                    # Bu kısım pdf2image ile tamamlanabilir
                    extracted_images.append(img_path)
        
        return extracted_images
    except Exception as e:
        print(f"[yellow]Uyarı:[/yellow] Görsel çıkarma sırasında hata: {e}")
        return []


def find_math_questions(text: str, keywords: List[str] = None) -> List[dict]:
    """Metin içinde matematik sorularını bulur."""
    questions = []
    lines = text.split("\n")
    
    current_question = None
    question_number = None
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if not line_stripped:
            continue
        
        # Soru numarası arıyoruz (örn: "15.", "15)", "Soru 15:", "15-")
        question_match = re.match(r"^\s*(\d+)[\.\)\-\s]+", line_stripped)
        if question_match:
            # Önceki soruyu kaydet
            if current_question and current_question.get("raw_text"):
                questions.append(current_question)
            
            # Yeni soru başlat
            question_number = question_match.group(1)
            question_text = re.sub(r"^\s*\d+[\.\)\-\s]+", "", line_stripped)
            current_question = {
                "question_number": question_number,
                "raw_text": question_text,
                "options": [],
                "full_text": question_text
            }
            continue
        
        # Seçenekleri bul (A), B), C), D) veya A., B., C., D.)
        option_match = re.match(r"^\s*([A-D])[\.\)]\s*(.+)", line_stripped)
        if option_match and current_question:
            option_letter = option_match.group(1)
            option_text = option_match.group(2)
            current_question["options"].append(f"{option_letter}) {option_text}")
            current_question["full_text"] += " " + line_stripped
            continue
        
        # Soru metnini genişlet (seçenek değilse)
        if current_question:
            # Seçenek başlangıcı değilse soru metnine ekle
            if not re.match(r"^\s*[A-D][\.\)]", line_stripped):
                current_question["raw_text"] += " " + line_stripped
                current_question["full_text"] += " " + line_stripped
    
    # Son soruyu ekle
    if current_question and current_question.get("raw_text"):
        questions.append(current_question)
    
    return questions


def extract_questions_from_pdf(pdf_path: Path, filter_keywords: bool = True) -> List[dict]:
    """PDF'den kareköklü ifadeler sorularını çıkarır."""
    print(f"[cyan]PDF işleniyor:[/cyan] {pdf_path.name}")
    
    # Metin çıkar
    text = extract_text_from_pdf(pdf_path)
    if not text:
        print(f"[yellow]Uyarı:[/yellow] {pdf_path.name} dosyasından metin çıkarılamadı.")
        return []
    
    # Soruları bul
    all_questions = find_math_questions(text)
    print(f"[dim]Toplam soru bulundu:[/dim] {len(all_questions)}")
    
    # Kareköklü ifadeler filtresi
    if filter_keywords:
        # Önce tüm soruları kontrol et
        for q in all_questions:
            full_text = q.get("full_text", q.get("raw_text", ""))
            q["is_koklu"] = is_koklu_question(full_text)
        
        # Sadece kareköklü ifadeler sorularını filtrele
        questions = [q for q in all_questions if q.get("is_koklu", False)]
        print(f"[green]Kareköklü ifadeler soruları:[/green] {len(questions)}")
    else:
        questions = all_questions
    
    # Her soruya kaynak bilgisi ekle
    for q in questions:
        q["source_file"] = pdf_path.name
        q["source_type"] = "pdf"
    
    return questions

