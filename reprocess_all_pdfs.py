#!/usr/bin/env python3
"""Tüm PDF'leri yeniden işle - geliştirilmiş algoritma ile."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.data.improved_pdf_extractor import reprocess_pdf
from rich import print

if __name__ == "__main__":
    raw_dir = Path("data/raw/lgs_meb_koklu")
    output_dir = Path("data/interim/reprocessed")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Tüm PDF dosyalarını bul
    pdf_files = list(raw_dir.glob("*.pdf"))
    
    print(f"[bold cyan]Yeniden İşleme Başlatılıyor[/bold cyan]\n")
    print(f"[dim]Bulunan PDF:[/dim] {len(pdf_files)}\n")
    
    all_questions = []
    
    for pdf_path in pdf_files:
        print(f"\n{'='*60}")
        print(f"[bold]İşleniyor:[/bold] {pdf_path.name}")
        print(f"{'='*60}\n")
        
        output_path = output_dir / f"{pdf_path.stem}_reprocessed.json"
        
        reprocess_pdf(pdf_path, output_path, save_images=True)
        
        # Sonuçları yükle
        import json
        with output_path.open("r", encoding="utf-8") as f:
            questions = json.load(f)
            all_questions.extend(questions)
    
    # Tüm soruları birleştir
    final_output = output_dir / "all_questions_reprocessed.json"
    with final_output.open("w", encoding="utf-8") as f:
        json.dump(all_questions, f, ensure_ascii=False, indent=2)
    
    print(f"\n[bold green]✓ Tamamlandı![/bold green]")
    print(f"[green]Toplam soru:[/green] {len(all_questions)}")
    print(f"[green]Final dosya:[/green] {final_output}")

