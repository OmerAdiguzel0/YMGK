"""Veri setini finalize etme - eksik alanları doldur, standardize et."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

import pandas as pd
from rich import print
from rich.console import Console
from rich.table import Table

from src.utils.io import read_json, write_json, ensure_dir


def standardize_question(question: Dict) -> Dict:
    """Bir soruyu standardize eder ve eksik alanları doldurur."""
    q = question.copy()
    
    # 1. Soru metni standardizasyonu
    if "question_text" not in q or not q.get("question_text"):
        # Önce temizlenmiş versiyonu dene
        if q.get("raw_text_cleaned"):
            q["question_text"] = q["raw_text_cleaned"]
        elif q.get("raw_text"):
            q["question_text"] = q["raw_text"]
        else:
            q["question_text"] = ""
    
    # 2. Soru numarası
    if not q.get("question_number") or q.get("question_number") == "?":
        # ID'den çıkar veya oluştur
        if "question_id" in q:
            q["question_number"] = q["question_id"].replace("Q", "")
        else:
            q["question_number"] = "unknown"
    
    # 3. Seçenekler standardizasyonu
    if "options" not in q:
        q["options"] = []
    elif isinstance(q["options"], str):
        # String ise parse et
        import re
        options = re.findall(r'([A-D])[\.\)]\s*(.+?)(?=[A-D][\.\)]|$)', q["options"])
        q["options"] = [f"{opt[0]}) {opt[1].strip()}" for opt in options]
    
    # 4. Kaynak bilgisi
    if "source_file" not in q:
        q["source_file"] = "unknown"
    if "source_type" not in q:
        q["source_type"] = "unknown"
    
    # 5. Kareköklü ifadeler işareti
    if "is_koklu" not in q:
        q["is_koklu"] = True  # Bu veri setinde hepsi kareköklü
    
    # 6. Soru tipi
    if "question_type" not in q:
        q["question_type"] = "yeni_nesil"
    
    # 7. Karmaşıklık (eğer yoksa hesapla)
    if "complexity" not in q:
        text_len = len(q.get("question_text", ""))
        if text_len > 500:
            q["complexity"] = "yüksek"
        elif text_len > 200:
            q["complexity"] = "orta"
        else:
            q["complexity"] = "düşük"
    
    # 8. Soru ID (eğer yoksa oluştur)
    if "question_id" not in q:
        source = q.get("source_file", "unknown").replace(".pdf", "").replace(".json", "")
        q_num = q.get("question_number", "0")
        q["question_id"] = f"{source}_Q{q_num}"
    
    return q


def finalize_dataset(input_path: Path, output_path: Path) -> None:
    """Veri setini finalize eder."""
    console = Console()
    
    print(f"\n[bold cyan]🔧 Veri Seti Finalizasyonu[/bold cyan]")
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
    
    # Her soruyu standardize et
    print("\n[dim]Sorular standardize ediliyor...[/dim]")
    standardized = []
    issues = []
    
    for i, q in enumerate(questions, 1):
        try:
            std_q = standardize_question(q)
            standardized.append(std_q)
        except Exception as e:
            issues.append(f"Soru #{i}: {str(e)}")
            print(f"[yellow]⚠️  Soru #{i} standardize edilemedi: {e}[/yellow]")
    
    print(f"[green]✓[/green] {len(standardized)} soru standardize edildi")
    
    if issues:
        print(f"\n[yellow]⚠️  {len(issues)} sorun bulundu:[/yellow]")
        for issue in issues[:5]:
            print(f"  • {issue}")
    
    # Eksik alan kontrolü
    print("\n[bold]📋 Eksik Alan Kontrolü:[/bold]")
    required_fields = ["question_text", "question_number", "source_file", "is_koklu"]
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Alan", style="cyan")
    table.add_column("Eksik", style="red")
    table.add_column("Dolu", style="green")
    
    for field in required_fields:
        missing = sum(1 for q in standardized if not q.get(field))
        filled = len(standardized) - missing
        table.add_row(field, str(missing), str(filled))
    
    console.print(table)
    
    # Seçenek kontrolü
    no_options = sum(1 for q in standardized if not q.get("options") or len(q.get("options", [])) == 0)
    if no_options > 0:
        print(f"\n[yellow]⚠️  {no_options} soruda seçenek yok[/yellow]")
    
    # Kaydet
    ensure_dir(output_path.parent)
    write_json(standardized, output_path)
    
    # CSV de oluştur (model eğitimi için)
    csv_path = output_path.with_suffix(".csv")
    df = pd.DataFrame(standardized)
    df.to_csv(csv_path, index=False, encoding="utf-8")
    
    print(f"\n[bold green]✅ Tamamlandı![/bold green]")
    print(f"[green]JSON:[/green] {output_path}")
    print(f"[green]CSV:[/green] {csv_path}")
    print(f"[green]Toplam soru:[/green] {len(standardized)}")
    
    # İstatistikler
    print(f"\n[bold]📊 İstatistikler:[/bold]")
    if standardized:
        complexities = {}
        for q in standardized:
            comp = q.get("complexity", "unknown")
            complexities[comp] = complexities.get(comp, 0) + 1
        
        for comp, count in complexities.items():
            print(f"  • {comp}: {count} soru")


def main():
    parser = argparse.ArgumentParser(description="Veri setini finalize et")
    parser.add_argument(
        "--input",
        default="data/interim/karekok_questions.json",
        help="Girdi dosyası"
    )
    parser.add_argument(
        "--output",
        default="data/processed/final_questions.json",
        help="Çıktı dosyası"
    )
    
    args = parser.parse_args()
    finalize_dataset(Path(args.input), Path(args.output))


if __name__ == "__main__":
    main()

