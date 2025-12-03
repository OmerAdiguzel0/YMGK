"""Encoding sorunlu soruları yüksek kaliteli OCR ile yeniden işle."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List

from rich import print
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.data.pdf_ocr_extractor import extract_pages_as_images, ocr_page_image
from src.data.pdf_extractor import find_math_questions
from src.utils.io import read_json, write_json


def find_question_in_ocr_text(ocr_text: str, question_number: str) -> str:
    """OCR metninde belirli bir soruyu bulur."""
    lines = ocr_text.split('\n')
    question_lines = []
    in_question = False
    
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue
        
        # Soru numarasını bul
        if re.match(rf'^\s*{question_number}[\.\)\-\s]+', line_stripped):
            in_question = True
            question_lines = [line_stripped]
            continue
        
        if in_question:
            # Bir sonraki soru numarasına kadar devam et
            next_q_match = re.match(r'^\s*(\d+)[\.\)\-\s]+', line_stripped)
            if next_q_match and next_q_match.group(1) != question_number:
                break
            question_lines.append(line_stripped)
    
    return '\n'.join(question_lines)


def reprocess_encoding_issues(
    questions_path: Path,
    pdf_path: Path,
    output_path: Path
) -> None:
    """Encoding sorunlu soruları yüksek kaliteli OCR ile yeniden işle."""
    console = Console()
    
    print(f"\n[bold cyan]🔄 Encoding Sorunlu Soruları Yeniden İşleme[/bold cyan]")
    print("=" * 60)
    
    # Soruları yükle
    questions = read_json(questions_path)
    if isinstance(questions, dict) and "questions" in questions:
        questions = questions["questions"]
    
    # Encoding sorunlu soruları bul
    encoding_issues = [
        q for q in questions 
        if q.get("has_encoding_issues") and "(cid:" in q.get("raw_text", "")
    ]
    
    print(f"\n[green]Encoding sorunlu soru sayısı:[/green] {len(encoding_issues)}")
    
    if not encoding_issues:
        print("[yellow]⚠️  Encoding sorunlu soru bulunamadı.[/yellow]")
        return
    
    # PDF sayfalarını yüksek kaliteli görsel olarak çıkar
    print(f"\n[dim]PDF sayfaları yüksek kalitede çıkarılıyor (DPI: 400)...[/dim]")
    page_images = extract_pages_as_images(pdf_path, dpi=400)
    
    if not page_images:
        print("[red]Hata:[/red] PDF sayfaları çıkarılamadı.")
        return
    
    print(f"[green]✓[/green] {len(page_images)} sayfa çıkarıldı")
    
    # Her sayfayı OCR ile işle
    print(f"\n[dim]Sayfalar OCR ile işleniyor...[/dim]")
    all_ocr_texts = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("OCR işleme...", total=len(page_images))
        
        for page_num, image in enumerate(page_images, 1):
            ocr_text = ocr_page_image(image, lang="tur", use_preprocessing=True)
            if ocr_text:
                all_ocr_texts.append((page_num, ocr_text))
            progress.update(task, advance=1)
    
    print(f"[green]✓[/green] {len(all_ocr_texts)} sayfa OCR ile işlendi")
    
    # Her encoding sorunlu soruyu yeniden işle
    print(f"\n[dim]Encoding sorunlu sorular yeniden işleniyor...[/dim]")
    improved_count = 0
    
    question_map = {q.get("question_number"): q for q in questions}
    
    for q in encoding_issues:
        q_num = q.get("question_number", "")
        if not q_num:
            continue
        
        # OCR metinlerinde bu soruyu ara
        best_ocr_text = None
        best_length = 0
        
        for page_num, ocr_text in all_ocr_texts:
            # Soru numarasını ara
            question_text = find_question_in_ocr_text(ocr_text, q_num)
            
            if question_text and len(question_text) > best_length:
                # Encoding sorunu yoksa ve yeterince uzunsa kullan
                if "(cid:" not in question_text and len(question_text) > 50:
                    best_ocr_text = question_text
                    best_length = len(question_text)
        
        if best_ocr_text:
            # Soruyu güncelle
            q["raw_text_ocr_high_quality"] = best_ocr_text
            q["raw_text"] = best_ocr_text  # En iyi versiyonu kullan
            q["question_text"] = best_ocr_text
            q["has_encoding_issues"] = False
            q["extraction_method"] = "ocr_high_quality"
            improved_count += 1
            print(f"[green]✓[/green] Soru #{q_num}: Encoding sorunu çözüldü")
    
    print(f"\n[bold green]✅ Yeniden İşleme Tamamlandı![/bold green]")
    print(f"[green]İyileştirilen soru sayısı:[/green] {improved_count}/{len(encoding_issues)}")
    
    # Güncellenmiş soruları kaydet
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(questions, output_path)
    
    print(f"\n[green]✅ Kaydedildi:[/green] {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Encoding sorunlu soruları yeniden işle")
    parser.add_argument(
        "--questions",
        default="data/interim/karekok_questions.json",
        help="Soru dosyası"
    )
    parser.add_argument(
        "--pdf",
        default="data/raw/lgs_meb_koklu/karekokcikmis.pdf",
        help="PDF dosyası"
    )
    parser.add_argument(
        "--output",
        default="data/interim/karekok_questions_reprocessed.json",
        help="Çıktı dosyası"
    )
    
    args = parser.parse_args()
    reprocess_encoding_issues(
        Path(args.questions),
        Path(args.pdf),
        Path(args.output)
    )


if __name__ == "__main__":
    main()

