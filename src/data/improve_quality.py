"""Veri kalitesini iyileştirme modülü - encoding, parse, seçenek düzeltmeleri."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List

from rich import print
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.utils.io import read_json, write_json


def clean_encoding_better(text: str, preserve_content: bool = True) -> str:
    """Encoding sorunlarını daha iyi temizler - metni korur."""
    if not text:
        return ""
    
    # (cid:...) karakterlerini kaldır (ama metni koru)
    # Önce (cid:XX) formatını kaldır - sadece bu karakterleri kaldır, metni koru
    cleaned = re.sub(r'\(cid:\d+\)', '', text)
    
    # Eğer temizleme sonrası çok az karakter kaldıysa, orijinal metni koru
    if preserve_content and len(cleaned.strip()) < len(text.strip()) * 0.3:
        # Çok fazla silindi, daha dikkatli temizle
        # Sadece (cid:) karakterlerini boşlukla değiştir
        cleaned = re.sub(r'\(cid:\d+\)', ' ', text)
    
    # Çoklu boşlukları tek boşluğa indir (ama satır sonlarını koru)
    cleaned = re.sub(r'[ \t]+', ' ', cleaned)  # Sadece boşluk ve tab
    cleaned = re.sub(r'\n\s*\n+', '\n\n', cleaned)  # Çoklu satır sonlarını koru
    
    # Başta/sonda boşlukları temizle
    cleaned = cleaned.strip()
    
    # Eğer temizlenmiş metin çok kısaysa, orijinal metni döndür
    if preserve_content and len(cleaned) < 20 and len(text) > 50:
        # Orijinal metni döndür ama (cid:) karakterlerini boşlukla değiştir
        return re.sub(r'\(cid:\d+\)', ' ', text).strip()
    
    return cleaned


def extract_options_from_text(text: str) -> List[str]:
    """Metinden seçenekleri çıkarır (daha gelişmiş ve güvenilir)."""
    options = []
    
    # Pattern 1: A) ... B) ... C) ... D) ... (en yaygın)
    # Daha esnek: seçenekler arasında boşluk olabilir
    pattern1 = r'([A-D])[\.\)]\s*([^A-D]+?)(?=\s*[A-D][\.\)]|$)'
    matches = re.findall(pattern1, text, re.IGNORECASE | re.DOTALL)
    if matches and len(matches) >= 2:  # En az 2 seçenek bulunmalı
        for letter, content in matches:
            option_text = content.strip()
            # Çok kısa veya çok uzun seçenekleri filtrele
            if 1 < len(option_text) < 300:
                # Anlamsız karakterler içermemeli
                if not re.match(r'^[\s\d\.\-]+$', option_text):  # Sadece sayı/boşluk değilse
                    options.append(f"{letter.upper()}) {option_text}")
    
    # Pattern 2: A. ... B. ... C. ... D. ...
    if len(options) < 2:
        pattern2 = r'([A-D])\.\s*([^A-D\.]+?)(?=\s*[A-D]\.|$)'
        matches = re.findall(pattern2, text, re.IGNORECASE | re.DOTALL)
        if matches and len(matches) >= 2:
            options = []
            for letter, content in matches:
                option_text = content.strip()
                if 1 < len(option_text) < 300:
                    if not re.match(r'^[\s\d\.\-]+$', option_text):
                        options.append(f"{letter.upper()}) {option_text}")
    
    # Pattern 3: Seçenekler satır sonlarında olabilir (her satır bir seçenek)
    if len(options) < 2:
        lines = text.split('\n')
        line_options = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            option_match = re.match(r'^\s*([A-D])[\.\)]\s*(.+)', line)
            if option_match:
                letter = option_match.group(1).upper()
                content = option_match.group(2).strip()
                if 1 < len(content) < 300:
                    if not re.match(r'^[\s\d\.\-]+$', content):
                        line_options.append(f"{letter}) {content}")
        if len(line_options) >= 2:
            options = line_options
    
    # Pattern 4: Seçenekler arasında boşluk olabilir (daha esnek)
    if len(options) < 2:
        # Tüm metni tarayarak A), B), C), D) pattern'lerini bul
        all_matches = list(re.finditer(r'([A-D])[\.\)]\s*([^\n]+)', text, re.IGNORECASE))
        if len(all_matches) >= 2:
            options = []
            for match in all_matches:
                letter = match.group(1).upper()
                content = match.group(2).strip()
                if 1 < len(content) < 300:
                    if not re.match(r'^[\s\d\.\-]+$', content):
                        options.append(f"{letter}) {content}")
    
    # Duplikasyon kontrolü (daha akıllı)
    unique_options = []
    seen_content = set()
    seen_letters = set()
    
    for opt in options:
        # Seçenek harfini çıkar
        letter_match = re.match(r'^([A-D])\)\s*', opt)
        if not letter_match:
            continue
        
        letter = letter_match.group(1)
        content = opt[len(letter) + 2:].strip()  # "A) " kısmını çıkar
        
        # Aynı harf veya çok benzer içerik varsa atla
        if letter in seen_letters:
            continue
        
        # İçerik benzerliği kontrolü (ilk 20 karakter)
        content_key = content[:20].lower().strip()
        if content_key in seen_content:
            continue
        
        unique_options.append(opt)
        seen_letters.add(letter)
        seen_content.add(content_key)
    
    # Sıralama: A, B, C, D sırasına göre
    def get_option_letter(opt: str) -> str:
        match = re.match(r'^([A-D])\)', opt)
        return match.group(1) if match else 'Z'
    
    unique_options.sort(key=get_option_letter)
    
    return unique_options[:4]  # Maksimum 4 seçenek


def split_combined_questions(text: str, max_length: int = 1500) -> List[str]:
    """Birleşik soruları ayırır."""
    if len(text) <= max_length:
        return [text]
    
    # Soru numarası pattern'lerine göre böl
    parts = re.split(r'(\d+)[\.\)\-\s]+', text)
    
    questions = []
    current_question = ""
    
    for i, part in enumerate(parts):
        if re.match(r'^\d+$', part):
            # Soru numarası bulundu
            if current_question and len(current_question.strip()) > 50:
                questions.append(current_question.strip())
            current_question = part + " "
        else:
            current_question += part
    
    # Son soruyu ekle
    if current_question and len(current_question.strip()) > 50:
        questions.append(current_question.strip())
    
    return questions if questions else [text]


def improve_question_quality(question: Dict) -> Dict:
    """Bir sorunun kalitesini iyileştirir."""
    q = question.copy()
    
    # 0. OCR versiyonunu tercih et (genelde daha temiz)
    ocr_text = q.get("raw_text_ocr") or q.get("full_text_ocr", "")
    if ocr_text and len(ocr_text.strip()) > 50:
        # OCR metni genelde daha temiz (encoding sorunu yok)
        current_text = q.get("raw_text", "")
        # OCR versiyonu daha temizse kullan
        if "(cid:" not in ocr_text or (current_text and ocr_text.count("(cid:") < current_text.count("(cid:")):
            q["raw_text"] = ocr_text
            q["question_text"] = ocr_text
            q["has_encoding_issues"] = False
            # OCR seçeneklerini de kullan
            if q.get("options_ocr") and len(q.get("options_ocr", [])) > len(q.get("options", [])):
                q["options"] = q.get("options_ocr", [])
    
    # 1. Encoding temizleme (daha iyi)
    raw_text = q.get("raw_text", "")
    if raw_text and "(cid:" in raw_text:
        cleaned = clean_encoding_better(raw_text)
        # Eğer temizlenmiş versiyon anlamlıysa kullan
        if cleaned and len(cleaned.strip()) > 30:  # En az 30 karakter
            q["raw_text_cleaned"] = cleaned
            # Temizlenmiş versiyon daha iyiyse kullan
            if not q.get("question_text") or len(q.get("question_text", "")) < len(cleaned):
                q["question_text"] = cleaned
            # Encoding sorunu çözüldü mü kontrol et
            if "(cid:" not in cleaned:
                q["has_encoding_issues"] = False
    
    # 2. Seçenek çıkarma (eğer yoksa veya azsa)
    current_options = q.get("options", [])
    if not current_options or len(current_options) < 4:
        # Tüm metin kaynaklarını dene
        text_sources = [
            q.get("full_text", ""),
            q.get("raw_text", ""),
            q.get("raw_text_ocr", ""),
            q.get("full_text_ocr", ""),
            q.get("question_text", "")
        ]
        
        best_options = []
        for text_source in text_sources:
            if text_source:
                options = extract_options_from_text(text_source)
                if len(options) > len(best_options):
                    best_options = options
        
        if best_options:
            q["options"] = best_options
            if len(best_options) > len(current_options):
                print(f"[green]✓[/green] Soru #{q.get('question_number')}: {len(best_options)} seçenek bulundu")
    
    # 3. Birleşik soruları tespit et ve uyarı ver
    raw_text = q.get("raw_text", "")
    full_text = q.get("full_text", raw_text)
    
    if len(full_text) > 2000:
        # Birleşik olabilir - soru numaralarına göre kontrol et
        question_numbers_in_text = re.findall(r'\b(\d+)[\.\)\-\s]+', full_text)
        unique_numbers = set(question_numbers_in_text)
        
        if len(unique_numbers) > 2:  # Birden fazla soru numarası varsa birleşik
            q["is_combined"] = True
            q["warning"] = f"Birleşik soru - {len(unique_numbers)} farklı soru numarası tespit edildi"
            # İlk soruyu ayırmayı dene (basit yaklaşım)
            # Ama şimdilik sadece uyarı ver, manuel kontrol gerekebilir
    
    # 4. Soru metni standardizasyonu (en iyi versiyonu seç)
    # Öncelik sırası: OCR > temizlenmiş > ham (ama encoding temizlenmiş)
    current_question_text = q.get("question_text", "")
    
    # Eğer mevcut question_text çok kısa veya yoksa, daha iyi versiyon ara
    if not current_question_text or len(current_question_text.strip()) < 50:
        best_text = None
        best_score = 0
        
        # Her versiyonu değerlendir (uzunluk + temizlik)
        candidates = [
            (q.get("raw_text_ocr", ""), 100),  # OCR en yüksek öncelik
            (q.get("full_text_ocr", ""), 95),
            (q.get("raw_text_cleaned", ""), 80),
            (clean_encoding_better(q.get("raw_text", "")), 70),
            (q.get("raw_text", ""), 50),
        ]
        
        for text, base_score in candidates:
            if not text or len(text.strip()) < 20:
                continue
            
            # Skor hesapla
            score = base_score
            length_bonus = min(len(text) / 10, 20)  # Uzunluk bonusu (max 20)
            
            # Encoding cezası
            if "(cid:" in text:
                encoding_penalty = min(text.count("(cid:") * 2, 30)
                score -= encoding_penalty
            
            # Final skor
            final_score = score + length_bonus
            
            if final_score > best_score:
                best_text = text
                best_score = final_score
        
        if best_text and len(best_text.strip()) > 20:
            q["question_text"] = best_text.strip()
            # Encoding sorunu yoksa işaretle
            if "(cid:" not in best_text:
                q["has_encoding_issues"] = False
    else:
        # Mevcut question_text yeterli, ama encoding temizle
        if "(cid:" in current_question_text:
            cleaned = clean_encoding_better(current_question_text)
            if cleaned and len(cleaned.strip()) > 20:  # En az 20 karakter kaldıysa
                q["question_text"] = cleaned
                if "(cid:" not in cleaned:
                    q["has_encoding_issues"] = False
    
    return q


def improve_dataset(input_path: Path, output_path: Path) -> None:
    """Veri setinin kalitesini iyileştirir."""
    console = Console()
    
    print(f"\n[bold cyan]🔧 Veri Kalitesi İyileştirme[/bold cyan]")
    print("=" * 60)
    
    # Veriyi yükle
    data = read_json(input_path)
    if isinstance(data, list):
        questions = data
    elif isinstance(data, dict) and "questions" in data:
        questions = data["questions"]
    else:
        questions = [data]
    
    print(f"\n[green]Yüklenen soru sayısı:[/green] {len(questions)}")
    
    # İyileştirme istatistikleri
    improved_encoding = 0
    improved_options = 0
    improved_text = 0
    
    # Her soruyu iyileştir
    print("\n[dim]Sorular iyileştiriliyor...[/dim]")
    improved_questions = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("İyileştirme...", total=len(questions))
        
        for q in questions:
            original = q.copy()
            improved = improve_question_quality(q)
            
            # İyileştirme sayıları
            if original.get("has_encoding_issues") and not improved.get("has_encoding_issues"):
                improved_encoding += 1
            if (not original.get("options") or len(original.get("options", [])) == 0) and \
               improved.get("options") and len(improved.get("options", [])) > 0:
                improved_options += 1
            if (not original.get("question_text") or len(original.get("question_text", "")) < 20) and \
               improved.get("question_text") and len(improved.get("question_text", "")) >= 20:
                improved_text += 1
            
            improved_questions.append(improved)
            progress.update(task, advance=1)
    
    # İyileştirme raporu
    print(f"\n[bold green]✅ İyileştirme Tamamlandı![/bold green]")
    print(f"\n[bold]📊 İyileştirme İstatistikleri:[/bold]")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("İyileştirme", style="cyan")
    table.add_column("Sayı", style="green")
    
    table.add_row("Encoding sorunları düzeltildi", str(improved_encoding))
    table.add_row("Seçenekler eklendi", str(improved_options))
    table.add_row("Soru metni iyileştirildi", str(improved_text))
    
    console.print(table)
    
    # Kalite kontrolü (iyileştirme sonrası)
    from src.data.quality_check import validate_all_questions
    validation = validate_all_questions(improved_questions)
    
    print(f"\n[bold]📈 Kalite Puanı:[/bold]")
    print(f"  Önceki: ~72.5/100")
    print(f"  Sonrası: {validation['average_score']:.1f}/100")
    print(f"  [green]İyileşme:[/green] +{validation['average_score'] - 72.5:.1f} puan")
    
    # Kaydet
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(improved_questions, output_path)
    
    print(f"\n[green]✅ Kaydedildi:[/green] {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Veri kalitesini iyileştir")
    parser.add_argument(
        "--input",
        default="data/interim/karekok_questions.json",
        help="Girdi dosyası"
    )
    parser.add_argument(
        "--output",
        default="data/interim/karekok_questions_improved.json",
        help="Çıktı dosyası"
    )
    
    args = parser.parse_args()
    improve_dataset(Path(args.input), Path(args.output))


if __name__ == "__main__":
    main()

