"""PDF'den görsel çıkarıp OCR ile işleme modülü (şekilli sorular için)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Optional

from PIL import Image
from rich import print

try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False
    print("[yellow]Uyarı:[/yellow] pdf2image bulunamadı. Görsel çıkarma devre dışı.")

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    print("[yellow]Uyarı:[/yellow] pytesseract bulunamadı. OCR devre dışı.")

from src.data.koklu_filter import is_koklu_question


def extract_pages_as_images(pdf_path: Path, dpi: int = 300) -> List[Image.Image]:
    """PDF sayfalarını görsel olarak çıkarır."""
    if not PDF2IMAGE_AVAILABLE:
        return []
    
    try:
        images = convert_from_path(str(pdf_path), dpi=dpi)
        print(f"[green]✓[/green] {len(images)} sayfa görsel olarak çıkarıldı")
        return images
    except Exception as e:
        print(f"[red]Hata:[/red] Görsel çıkarma hatası: {e}")
        return []


def preprocess_image_for_ocr(image: Image.Image) -> Image.Image:
    """Görseli OCR için ön işleme (kalite artırma)."""
    try:
        import cv2
        import numpy as np
        
        # PIL Image'ı numpy array'e çevir
        img_array = np.array(image.convert('RGB'))
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        
        # Gri tonlamaya çevir
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        
        # Gürültü azaltma (daha agresif)
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        
        # Kontrast artırma (CLAHE)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)
        
        # Eşikleme (thresholding) - daha iyi okuma için
        _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Numpy array'i PIL Image'a çevir
        processed = Image.fromarray(thresh)
        return processed
    except ImportError:
        # cv2 yoksa orijinal görseli döndür
        return image
    except Exception as e:
        print(f"[yellow]Uyarı:[/yellow] Görsel preprocessing hatası: {e}")
        return image


def ocr_page_image(image: Image.Image, lang: str = "tur", use_preprocessing: bool = True) -> str:
    """Bir sayfa görselinden OCR ile metin çıkarır."""
    if not TESSERACT_AVAILABLE:
        return ""
    
    try:
        # Görsel preprocessing (kalite artırma)
        if use_preprocessing:
            processed_image = preprocess_image_for_ocr(image)
        else:
            processed_image = image
        
        # OCR ile metin çıkar (Türkçe + İngilizce - matematik sembolleri için)
        # PSM 6: Tek blok metin (soru formatı için ideal)
        # Daha yüksek kalite için whitelist kaldırıldı (tüm karakterleri tanıyabilir)
        text = pytesseract.image_to_string(
            processed_image,
            lang=lang,
            config="--psm 6 -c preserve_interword_spaces=1"
        )
        return text.strip()
    except Exception as e:
        print(f"[yellow]Uyarı:[/yellow] OCR hatası: {e}")
        return ""


def extract_questions_with_ocr(pdf_path: Path, filter_koklu: bool = True) -> List[dict]:
    """PDF'den sayfaları görsel olarak çıkarıp OCR ile soruları bulur."""
    print(f"[bold cyan]PDF OCR işleme:[/bold cyan] {pdf_path.name}")
    
    if not PDF2IMAGE_AVAILABLE or not TESSERACT_AVAILABLE:
        print("[red]Hata:[/red] pdf2image veya pytesseract yüklü değil.")
        return []
    
    # Sayfaları görsel olarak çıkar (daha yüksek DPI = daha iyi kalite)
    page_images = extract_pages_as_images(pdf_path, dpi=400)
    if not page_images:
        return []
    
    all_questions = []
    
    # Her sayfayı OCR ile işle
    for page_num, image in enumerate(page_images, 1):
        print(f"[dim]Sayfa {page_num}/{len(page_images)} OCR işleniyor...[/dim]", end="\r")
        
        # OCR ile metin çıkar
        page_text = ocr_page_image(image, lang="tur")
        
        if not page_text:
            continue
        
        # Soruları bul
        questions = find_questions_in_text(page_text, page_num)
        all_questions.extend(questions)
    
    print(f"\n[green]Toplam soru bulundu:[/green] {len(all_questions)}")
    
    # Kareköklü ifadeler filtresi
    if filter_koklu:
        filtered = []
        for q in all_questions:
            full_text = q.get("full_text", q.get("raw_text", ""))
            
            # Bu PDF zaten sadece kareköklü ifadeler sorularını içeriyor
            # Sadece çok kısa veya geçersiz olanları atla
            if len(full_text.strip()) < 30:
                continue
            
            # Sayfa başlıklarını atla
            if "Kareköklü İfadeler LGS ÇIKMIŞ SORULAR" in full_text and len(full_text) < 100:
                continue
            
            # Geçerli soru - bu PDF'deki tüm sorular kareköklü
            q["is_koklu"] = True
            q["extraction_method"] = "ocr"
            filtered.append(q)
        
        print(f"[green]Kareköklü ifadeler soruları:[/green] {len(filtered)}")
        return filtered
    
    return all_questions


def find_questions_in_text(text: str, page_num: int) -> List[dict]:
    """Metin içinde soruları bulur."""
    questions = []
    lines = text.split("\n")
    
    current_question = None
    question_number = None
    
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped or len(line_stripped) < 3:
            continue
        
        # Soru numarası ara (örn: "15.", "15)", "15-", "Soru 15")
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
                "full_text": question_text,
                "page": page_num
            }
            continue
        
        # Seçenekleri bul (A), B), C), D))
        option_match = re.match(r"^\s*([A-D])[\.\)]\s*(.+)", line_stripped)
        if option_match and current_question:
            option_letter = option_match.group(1)
            option_text = option_match.group(2)
            current_question["options"].append(f"{option_letter}) {option_text}")
            current_question["full_text"] += " " + line_stripped
            continue
        
        # Soru metnini genişlet
        if current_question:
            if not re.match(r"^\s*[A-D][\.\)]", line_stripped):
                current_question["raw_text"] += " " + line_stripped
                current_question["full_text"] += " " + line_stripped
    
    # Son soruyu ekle
    if current_question and current_question.get("raw_text"):
        questions.append(current_question)
    
    return questions

