"""Veri çıkarma sonuçlarını doğrulama ve raporlama modülü."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict

from rich import print
from rich.console import Console
from rich.table import Table

from src.utils.io import read_json


def validate_extraction(
    extracted_file: Path,
    expected_count: int = None,
    source_file: str = None
) -> Dict[str, any]:
    """Çıkarılan soruları doğrular ve raporlar."""
    console = Console()
    
    print(f"\n[bold cyan]🔍 Veri Çıkarma Doğrulama[/bold cyan]")
    print("=" * 60)
    
    # Veriyi yükle
    if not extracted_file.exists():
        print(f"[red]❌ Hata:[/red] Dosya bulunamadı: {extracted_file}")
        return {
            "valid": False,
            "error": "Dosya bulunamadı"
        }
    
    data = read_json(extracted_file)
    if isinstance(data, list):
        questions = data
    elif isinstance(data, dict) and "questions" in data:
        questions = data["questions"]
    else:
        questions = [data]
    
    actual_count = len(questions)
    
    # Rapor tablosu
    table = Table(title="📊 Çıkarma Sonuçları", show_header=True, header_style="bold magenta")
    table.add_column("Özellik", style="cyan")
    table.add_column("Değer", style="green")
    
    table.add_row("Kaynak Dosya", source_file or extracted_file.name)
    table.add_row("Bulunan Soru Sayısı", str(actual_count))
    
    if expected_count is not None:
        table.add_row("Beklenen Soru Sayısı", str(expected_count))
        difference = actual_count - expected_count
        if difference == 0:
            table.add_row("Durum", "[green]✅ TAM EŞLEŞME[/green]")
        elif difference > 0:
            table.add_row("Durum", f"[yellow]⚠️  {difference} fazla soru bulundu[/yellow]")
        else:
            table.add_row("Durum", f"[red]❌ {abs(difference)} soru eksik[/red]")
    else:
        table.add_row("Beklenen", "[dim]Belirtilmemiş[/dim]")
    
    console.print(table)
    
    # Soru detayları
    print(f"\n[bold]📝 Soru Detayları:[/bold]")
    
    # Soru numaraları
    question_numbers = []
    for q in questions:
        q_num = q.get("question_number", "?")
        if q_num.isdigit():
            question_numbers.append(int(q_num))
        elif q_num != "?":
            question_numbers.append(q_num)
    
    if question_numbers:
        nums_str = ", ".join(map(str, sorted(set(question_numbers))[:20]))
        if len(set(question_numbers)) > 20:
            nums_str += f" ... (toplam {len(set(question_numbers))} benzersiz numara)"
        print(f"  • Soru numaraları: {nums_str}")
    
    # Çıkarma yöntemleri
    methods = {}
    for q in questions:
        method = q.get("extraction_method", "unknown")
        methods[method] = methods.get(method, 0) + 1
    
    if methods:
        print(f"  • Çıkarma yöntemleri:")
        for method, count in methods.items():
            print(f"    - {method}: {count} soru")
    
    # Soru özellikleri
    has_image = sum(1 for q in questions if q.get("has_image"))
    has_table = sum(1 for q in questions if q.get("has_table"))
    high_complexity = sum(1 for q in questions if q.get("complexity") == "yüksek")
    
    if has_image or has_table or high_complexity:
        print(f"  • Özellikler:")
        if has_image:
            print(f"    - Görsel içerikli: {has_image} soru")
        if has_table:
            print(f"    - Tablo içerikli: {has_table} soru")
        if high_complexity:
            print(f"    - Yüksek karmaşıklık: {high_complexity} soru")
    
    # Örnek sorular
    print(f"\n[bold]📋 Örnek Sorular (ilk 3):[/bold]")
    for i, q in enumerate(questions[:3], 1):
        q_num = q.get("question_number", "?")
        raw_text = q.get("raw_text", q.get("question_text", ""))[:80]
        method = q.get("extraction_method", "?")
        print(f"  {i}. Soru #{q_num} ({method}): {raw_text}...")
    
    # Doğrulama sonucu
    is_valid = True
    warnings = []
    errors = []
    
    if expected_count is not None:
        if actual_count < expected_count:
            is_valid = False
            errors.append(f"{expected_count - actual_count} soru eksik!")
        elif actual_count > expected_count:
            warnings.append(f"{actual_count - expected_count} fazla soru bulundu (duplikasyon olabilir)")
    
    # Boş sorular kontrolü
    empty_questions = [q for q in questions if not q.get("raw_text", q.get("question_text", "")).strip()]
    if empty_questions:
        warnings.append(f"{len(empty_questions)} boş soru metni var")
    
    # Encoding sorunları
    encoding_issues = sum(1 for q in questions if q.get("has_encoding_issues"))
    if encoding_issues:
        warnings.append(f"{encoding_issues} soruda encoding sorunu var (cid:... karakterleri)")
    
    # Uyarılar ve hatalar
    if warnings:
        print(f"\n[yellow]⚠️  Uyarılar:[/yellow]")
        for warning in warnings:
            print(f"  • {warning}")
    
    if errors:
        print(f"\n[red]❌ Hatalar:[/red]")
        for error in errors:
            print(f"  • {error}")
    
    # Sonuç
    print(f"\n[bold]Sonuç:[/bold]")
    if is_valid and not errors:
        print("[green]✅ Doğrulama başarılı! Veriler eklenebilir.[/green]")
    elif errors:
        print("[red]❌ Doğrulama başarısız! Lütfen kontrol edin.[/red]")
    else:
        print("[yellow]⚠️  Doğrulama tamamlandı, ancak uyarılar var.[/yellow]")
    
    return {
        "valid": is_valid and not errors,
        "actual_count": actual_count,
        "expected_count": expected_count,
        "warnings": warnings,
        "errors": errors,
        "questions": questions
    }


def prompt_user_confirmation(message: str = "Devam etmek istiyor musunuz?") -> bool:
    """Kullanıcıdan onay alır."""
    print(f"\n[bold yellow]❓ {message}[/bold yellow]")
    response = input("  (E/h): ").strip().lower()
    return response in ["e", "evet", "y", "yes", ""]


def main():
    """Komut satırı arayüzü."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Veri çıkarma sonuçlarını doğrula")
    parser.add_argument("--file", required=True, help="Çıkarılan veri dosyası")
    parser.add_argument("--expected", type=int, help="Beklenen soru sayısı")
    parser.add_argument("--source", help="Kaynak dosya adı")
    parser.add_argument("--auto-confirm", action="store_true", help="Otomatik onay (soru sorma)")
    
    args = parser.parse_args()
    
    result = validate_extraction(
        Path(args.file),
        expected_count=args.expected,
        source_file=args.source
    )
    
    if not args.auto_confirm:
        if result["valid"]:
            if prompt_user_confirmation("Bu verileri mevcut veri setine eklemek istiyor musunuz?"):
                print("[green]✅ Onaylandı! Veriler eklenebilir.[/green]")
                return 0
            else:
                print("[yellow]⚠️  İşlem iptal edildi.[/yellow]")
                return 1
        else:
            print("[red]❌ Doğrulama başarısız olduğu için ekleme yapılamaz.[/red]")
            return 1
    
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    exit(main())

