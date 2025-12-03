"""Yeni veri setlerini mevcut veri setine ekleme modülü."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

from rich import print

from src.utils.io import read_json, write_json, ensure_dir


def load_existing_dataset(dataset_path: Path) -> List[dict]:
    """Mevcut veri setini yükler."""
    if not dataset_path.exists():
        print(f"[yellow]Uyarı:[/yellow] Mevcut veri seti bulunamadı, yeni oluşturuluyor.")
        return []
    
    data = read_json(dataset_path)
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and "questions" in data:
        return data["questions"]
    else:
        return [data]


def merge_datasets(
    existing_path: Path,
    new_path: Path,
    output_path: Path,
    deduplicate: bool = True
) -> None:
    """Yeni veri setini mevcut veri setine ekler."""
    print(f"[bold cyan]Veri Setleri Birleştiriliyor[/bold cyan]\n")
    
    # Mevcut veri setini yükle
    existing_data = load_existing_dataset(existing_path)
    print(f"[green]Mevcut veri:[/green] {len(existing_data)} soru")
    
    # Yeni veri setini yükle
    new_data = read_json(new_path)
    if isinstance(new_data, list):
        new_questions = new_data
    elif isinstance(new_data, dict) and "questions" in new_data:
        new_questions = new_data["questions"]
    else:
        new_questions = [new_data]
    
    print(f"[green]Yeni veri:[/green] {len(new_questions)} soru\n")
    
    # Duplikasyon kontrolü
    if deduplicate:
        print("[dim]Duplikasyon kontrolü yapılıyor...[/dim]")
        
        # Mevcut soruların imzalarını oluştur
        existing_signatures = set()
        for q in existing_data:
            # Soru numarası + kaynak dosya + ilk 100 karakter
            q_num = q.get("question_number", "")
            source = q.get("source_file", "")
            text_snippet = q.get("raw_text", q.get("question_text", ""))[:100]
            signature = f"{q_num}:{source}:{text_snippet.lower().strip()}"
            existing_signatures.add(signature)
        
        # Yeni soruları filtrele
        unique_new = []
        duplicates = 0
        
        for q in new_questions:
            q_num = q.get("question_number", "")
            source = q.get("source_file", "")
            text_snippet = q.get("raw_text", q.get("question_text", ""))[:100]
            signature = f"{q_num}:{source}:{text_snippet.lower().strip()}"
            
            if signature not in existing_signatures:
                unique_new.append(q)
                existing_signatures.add(signature)
            else:
                duplicates += 1
        
        print(f"[green]Benzersiz yeni soru:[/green] {len(unique_new)}")
        if duplicates > 0:
            print(f"[yellow]Duplikasyon:[/yellow] {duplicates} soru atlandı")
        
        new_questions = unique_new
    
    # Verileri birleştir
    merged_data = existing_data + new_questions
    
    # Soru ID'lerini güncelle (opsiyonel - sıralı ID)
    for i, q in enumerate(merged_data, 1):
        if "question_id" not in q:
            q["question_id"] = f"Q{i:04d}"
    
    # Kaydet
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(merged_data, output_path)
    
    print(f"\n[bold green]✓ Tamamlandı![/bold green]")
    print(f"[green]Toplam soru:[/green] {len(merged_data)}")
    print(f"[green]Kaydedildi:[/green] {output_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Yeni veri setini mevcut veri setine ekle"
    )
    parser.add_argument(
        "--existing",
        default="data/interim/karekok_questions.json",
        help="Mevcut veri seti yolu"
    )
    parser.add_argument(
        "--new",
        required=True,
        help="Yeni veri seti yolu (eklenecek)"
    )
    parser.add_argument(
        "--output",
        default="data/interim/karekok_questions.json",
        help="Birleştirilmiş veri seti çıktı yolu"
    )
    parser.add_argument(
        "--no-deduplicate",
        action="store_true",
        help="Duplikasyon kontrolü yapma"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    merge_datasets(
        existing_path=Path(args.existing),
        new_path=Path(args.new),
        output_path=Path(args.output),
        deduplicate=not args.no_deduplicate
    )


if __name__ == "__main__":
    main()

