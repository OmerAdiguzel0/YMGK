#!/usr/bin/env python3
"""karekokcikmis.pdf ve karekok_sorular.pdf dosyalarını işlemek için özel script."""

import json
import sys
from pathlib import Path

# Proje root'unu path'e ekle
sys.path.insert(0, str(Path(__file__).parent))

from src.data.process_karekok_pdf import process_karekok_pdf
from rich import print

if __name__ == "__main__":
    raw_dir = Path("data/raw/lgs_meb_koklu")
    interim_dir = Path("data/interim")
    
    # İşlenecek PDF dosyaları
    pdf_files = [
        raw_dir / "karekokcikmis.pdf",
        raw_dir / "karekok_sorular.pdf"
    ]
    
    all_questions = []
    
    for pdf_path in pdf_files:
        if not pdf_path.exists():
            print(f"[yellow]Uyarı:[/yellow] Dosya bulunamadı: {pdf_path}")
            continue
        
        print(f"\n[bold cyan]Kareköklü İfadeler PDF İşleme:[/bold cyan] {pdf_path.name}\n")
        
        # Her dosya için ayrı output
        output_path = interim_dir / f"{pdf_path.stem}_questions.json"
        
        process_karekok_pdf(
            pdf_path=pdf_path,
            output_path=output_path,
            use_ocr=True,  # Şekilli sorular için OCR açık
            use_text_extraction=True  # Hızlı metin çıkarma da açık
        )
        
        # İşlenen soruları yükle
        if output_path.exists():
            with output_path.open("r", encoding="utf-8") as f:
                questions = json.load(f)
                all_questions.extend(questions)
                print(f"[green]✓[/green] {len(questions)} soru eklendi")
    
        # Tüm soruları birleştir ve kaydet
    if all_questions:
        final_output = interim_dir / "karekok_questions.json"
        
        # Mevcut dosya varsa birleştir (basit duplikasyon kontrolü ile)
        if final_output.exists():
            print(f"\n[bold]Mevcut veri seti ile birleştiriliyor...[/bold]")
            with final_output.open("r", encoding="utf-8") as f:
                existing_questions = json.load(f)
            
            # Duplikasyon kontrolü: soru numarası + kaynak dosya + ilk 100 karakter
            existing_signatures = set()
            for q in existing_questions:
                q_num = q.get("question_number", "")
                source = q.get("source_file", "")
                text_snippet = q.get("raw_text", q.get("question_text", ""))[:100]
                signature = f"{q_num}:{source}:{text_snippet.lower().strip()}"
                existing_signatures.add(signature)
            
            # Yeni soruları filtrele
            unique_new = []
            for q in all_questions:
                q_num = q.get("question_number", "")
                source = q.get("source_file", "")
                text_snippet = q.get("raw_text", q.get("question_text", ""))[:100]
                signature = f"{q_num}:{source}:{text_snippet.lower().strip()}"
                
                if signature not in existing_signatures:
                    unique_new.append(q)
                    existing_signatures.add(signature)
            
            print(f"[green]Yeni benzersiz soru:[/green] {len(unique_new)}")
            all_questions = existing_questions + unique_new
        
        # Kaydet
        final_output.parent.mkdir(parents=True, exist_ok=True)
        with final_output.open("w", encoding="utf-8") as f:
            json.dump(all_questions, f, ensure_ascii=False, indent=2)
        
        print(f"\n[bold green]✓ Toplam {len(all_questions)} soru kaydedildi:[/bold green] {final_output}")
    else:
        print(f"\n[red]Hata:[/red] Hiç soru bulunamadı!")
        sys.exit(1)

