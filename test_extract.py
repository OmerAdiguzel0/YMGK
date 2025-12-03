#!/usr/bin/env python3
"""Test script - Kareköklü ifadeler sorularını çıkar."""

from pathlib import Path
from src.data.pdf_extractor import extract_questions_from_pdf
from rich import print

# Test için bir PDF seç
pdf_path = Path("data/raw/lgs_meb_koklu/2023sayisal.pdf")

if not pdf_path.exists():
    print(f"[red]Dosya bulunamadı:[/red] {pdf_path}")
    exit(1)

print(f"[bold cyan]Test ediliyor:[/bold cyan] {pdf_path.name}\n")

# Soruları çıkar
questions = extract_questions_from_pdf(pdf_path, filter_keywords=True)

print(f"\n[bold green]Sonuç:[/bold green] {len(questions)} kareköklü ifadeler sorusu bulundu\n")

# İlk 5 soruyu göster
for i, q in enumerate(questions[:5], 1):
    print(f"[bold]Soru {i}:[/bold]")
    print(f"  Numara: {q.get('question_number', '?')}")
    print(f"  Metin: {q.get('raw_text', '')[:150]}...")
    print(f"  Seçenekler: {len(q.get('options', []))} adet")
    print()

