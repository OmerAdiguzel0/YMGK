"""Geliştirilmiş PDF çıkarma - daha iyi soru ayırma ve görsel çıkarma."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple

import pdfplumber
from rich import print
from PIL import Image

try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False


def extract_page_as_image(pdf_path: Path, page_num: int, dpi: int = 400) -> Optional[Image.Image]:
    """Belirli bir sayfayı görsel olarak çıkar."""
    if not PDF2IMAGE_AVAILABLE:
        return None
    
    try:
        images = convert_from_path(str(pdf_path), dpi=dpi, first_page=page_num, last_page=page_num)
        return images[0] if images else None
    except Exception as e:
        print(f"[yellow]Uyarı:[/yellow] Sayfa {page_num} görsel çıkarılamadı: {e}")
        return None


def save_question_image(image: Image.Image, output_dir: Path, question_id: str) -> Path:
    """Soru görselini kaydet."""
    output_dir.mkdir(parents=True, exist_ok=True)
    image_path = output_dir / f"question_{question_id}.png"
    image.save(image_path, "PNG")
    return image_path


def find_question_boundaries(text: str) -> List[Tuple[int, int]]:
    """Metinde soru sınırlarını bul (daha akıllı algoritma)."""
    boundaries = []
    lines = text.split('\n')
    
    current_start = None
    question_pattern = re.compile(r'^\s*(\d+)[\.\)\-\s]+', re.MULTILINE)
    
    for i, line in enumerate(lines):
        # Soru numarası bulundu
        match = question_pattern.match(line)
        if match:
            # Önceki soruyu kaydet
            if current_start is not None:
                boundaries.append((current_start, i))
            current_start = i
    
    # Son soruyu ekle
    if current_start is not None:
        boundaries.append((current_start, len(lines)))
    
    return boundaries


def parse_single_question(text_lines: List[str], question_num: str) -> Optional[Dict]:
    """Tek bir soruyu parse et (daha iyi algoritma - soruları düzgün ayır)."""
    if not text_lines:
        return None
    
    # Metni birleştir
    full_text = ' '.join(text_lines).strip()
    
    # Çok kısa veya çok uzun soruları reddet
    if len(full_text) < 20 or len(full_text) > 2000:
        return None
    
    # İLK SORU İŞARETİNE KADAR AL (birleşmiş soruları ayır)
    first_q_mark = full_text.find('?')
    if first_q_mark > 0:
        # İlk soru işaretine kadar olan kısmı al
        first_question = full_text[:first_q_mark + 1]
        
        # Bu kısmın sonrasındaki seçenekleri bul
        after_first_q = full_text[first_q_mark + 1:]
        
        # İlk 4 seçeneği bul (sonraki soruya geçmeden)
        options = []
        option_pattern = re.compile(r'([A-D])[\.\)]\s*([^A-D]{0,50}?)(?=[A-D][\.\)]|$)', re.DOTALL)
        option_matches = list(option_pattern.finditer(after_first_q))
        
        # Eğer 4'ten fazla seçenek varsa, muhtemelen birleşmiş sorular var
        # Sadece ilk 4 seçeneği al
        for match in option_matches[:4]:
            letter = match.group(1)
            content = match.group(2).strip()
            if len(content) < 100:  # Çok uzun seçenekleri atla
                options.append(f"{letter}) {content}")
        
        # En az 2 seçenek olmalı
        if len(options) >= 2:
            question_text = first_question.strip()
            options_text = ' '.join(options)
            full_clean_text = question_text + ' ' + options_text
        else:
            return None
    else:
        # Soru işareti yoksa, ilk seçeneğe kadar al
        first_option = re.search(r'[A-D][\.\)]', full_text)
        if first_option:
            question_text = full_text[:first_option.start()].strip()
            options_text = full_text[first_option.start():].strip()
            
            # Seçenekleri parse et
            options = []
            option_pattern = re.compile(r'([A-D])[\.\)]\s*([^A-D]+?)(?=[A-D][\.\)]|$)', re.DOTALL)
            for match in option_pattern.finditer(options_text):
                letter = match.group(1)
                content = match.group(2).strip()
                if len(content) < 100:
                    options.append(f"{letter}) {content}")
            
            if len(options) < 2:
                return None
            
            full_clean_text = question_text + ' ' + ' '.join(options[:4])
        else:
            return None
    
    # Soru geçerli mi kontrol et
    if len(question_text) < 15:
        return None
    
    # Encoding sorunlarını temizle
    question_text = re.sub(r'\(cid:\d+\)', '', question_text)
    question_text = re.sub(r'\s+', ' ', question_text).strip()
    full_clean_text = re.sub(r'\(cid:\d+\)', '', full_clean_text)
    full_clean_text = re.sub(r'\s+', ' ', full_clean_text).strip()
    
    return {
        "question_number": question_num,
        "raw_text": question_text,
        "full_text": full_clean_text,
        "options": options[:4],  # Maksimum 4 seçenek
        "has_options": len(options) >= 2
    }


def extract_questions_improved(pdf_path: Path, save_images: bool = True) -> List[Dict]:
    """PDF'den soruları çıkar (geliştirilmiş versiyon)."""
    print(f"[bold cyan]Geliştirilmiş PDF İşleme:[/bold cyan] {pdf_path.name}\n")
    
    all_questions = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            print(f"[dim]Toplam sayfa:[/dim] {total_pages}\n")
            
            for page_num, page in enumerate(pdf.pages, 1):
                print(f"[dim]Sayfa {page_num}/{total_pages} işleniyor...[/dim]", end="\r")
                
                # Metin çıkar
                text = page.extract_text()
                if not text or len(text.strip()) < 20:
                    continue
                
                # Soru sınırlarını bul
                lines = text.split('\n')
                boundaries = find_question_boundaries(text)
                
                # Her soruyu parse et
                for start_idx, end_idx in boundaries:
                    question_lines = lines[start_idx:end_idx]
                    
                    # Soru numarasını bul
                    first_line = question_lines[0] if question_lines else ""
                    num_match = re.match(r'^\s*(\d+)[\.\)\-\s]+', first_line)
                    if not num_match:
                        continue
                    
                    question_num = num_match.group(1)
                    
                    # Soruyu parse et
                    question_data = parse_single_question(question_lines, question_num)
                    
                    if question_data and question_data.get("has_options"):
                        # Görsel çıkar (eğer isteniyorsa)
                        if save_images and PDF2IMAGE_AVAILABLE:
                            page_image = extract_page_as_image(pdf_path, page_num, dpi=400)
                            if page_image:
                                # Soru görselini kaydet
                                question_id = f"{pdf_path.stem}_p{page_num}_q{question_num}"
                                image_dir = Path("data/extracted_images")
                                image_path = save_question_image(page_image, image_dir, question_id)
                                question_data["image_path"] = str(image_path)
                                question_data["has_image"] = True
                        
                        question_data["source_file"] = pdf_path.name
                        question_data["page"] = page_num
                        all_questions.append(question_data)
            
            print(f"\n[green]✓ Toplam {len(all_questions)} soru çıkarıldı[/green]")
            
    except Exception as e:
        print(f"[red]Hata:[/red] {pdf_path.name} işlenirken hata: {e}")
    
    return all_questions


def reprocess_pdf(pdf_path: Path, output_path: Path, save_images: bool = True) -> None:
    """PDF'i yeniden işle ve daha iyi sonuçlar al."""
    print(f"[bold cyan]PDF Yeniden İşleniyor:[/bold cyan] {pdf_path.name}\n")
    
    questions = extract_questions_improved(pdf_path, save_images=save_images)
    
    # JSON'a kaydet
    import json
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)
    
    print(f"\n[green]✓ Kaydedildi:[/green] {output_path}")
    print(f"[green]✓ Toplam soru:[/green] {len(questions)}")
    
    # İstatistikler
    with_options = sum(1 for q in questions if q.get("has_options"))
    with_images = sum(1 for q in questions if q.get("has_image"))
    
    print(f"\n[dim]İstatistikler:[/dim]")
    print(f"  • Seçenekli soru: {with_options}/{len(questions)}")
    print(f"  • Görselli soru: {with_images}/{len(questions)}")

