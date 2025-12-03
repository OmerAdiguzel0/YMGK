"""Soru kalitesi kontrolü ve doğrulama modülü."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import List, Dict

from rich import print
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.utils.io import read_json


def check_question_quality(question: Dict) -> Dict[str, any]:
    """Bir sorunun kalitesini kontrol eder."""
    issues = []
    warnings = []
    score = 100  # Başlangıç puanı
    
    raw_text = question.get("raw_text", "")
    question_text = question.get("question_text", raw_text)
    options = question.get("options", [])
    q_num = question.get("question_number", "")
    
    # 1. Soru metni kontrolü
    if not question_text or len(question_text.strip()) < 20:
        issues.append("Soru metni çok kısa veya boş")
        score -= 30
    
    if len(question_text) > 5000:
        warnings.append("Soru metni çok uzun (muhtemelen birleşik)")
        score -= 10
    
    # 2. Encoding sorunları
    if "(cid:" in question_text:
        # Eğer temizlenmiş versiyon kullanılıyorsa sorun yok
        if question.get("raw_text_cleaned") and question_text == question.get("raw_text_cleaned"):
            # Temizlenmiş versiyon kullanılıyor, sorun yok
            pass
        elif question.get("raw_text_ocr") and "(cid:" not in question.get("raw_text_ocr", ""):
            # OCR versiyonu temiz, sorun yok
            pass
        else:
            issues.append("Encoding sorunu var (cid:... karakterleri)")
            score -= 20
            if question.get("raw_text_cleaned") or question.get("raw_text_ocr"):
                warnings.append("Temizlenmiş versiyon mevcut")
                score += 10  # Kısmi iyileştirme
    
    # 3. Seçenek kontrolü (daha esnek)
    if len(options) == 0:
        # Seçenek yoksa, metinde seçenek var mı kontrol et
        if any(opt in question_text for opt in ["A)", "B)", "C)", "D)"]):
            warnings.append("Seçenekler parse edilememiş (metinde var)")
            score -= 3  # Daha az ceza
        else:
            warnings.append("Seçenek yok (açık uçlu olabilir)")
            score -= 5
    elif len(options) < 4:
        # 1-3 seçenek varsa kısmi başarı
        if len(options) >= 2:
            warnings.append(f"{len(options)} seçenek var (normalde 4 olmalı)")
            score -= 3  # Daha az ceza
        else:
            warnings.append(f"Sadece {len(options)} seçenek var")
            score -= 5
    elif len(options) > 4:
        warnings.append(f"{len(options)} seçenek var (normalde 4 olmalı)")
        score -= 2  # Daha az ceza
    
    # 4. Soru işareti kontrolü
    if "?" not in question_text and "kaçtır" not in question_text.lower() and "nedir" not in question_text.lower():
        warnings.append("Soru işareti yok (soru formatı şüpheli)")
        score -= 5
    
    # 5. Soru numarası kontrolü
    if not q_num or q_num == "0" or q_num == "?":
        warnings.append("Soru numarası geçersiz veya eksik")
        score -= 5
    
    # 6. Matematik sembolleri kontrolü (kareköklü ifadeler için)
    has_sqrt = "√" in question_text or "kök" in question_text.lower() or "kareköklü" in question_text.lower()
    if not has_sqrt:
        warnings.append("Kareköklü ifade bulunamadı (konu filtresi şüpheli)")
        score -= 10
    
    # 7. Anlamsız karakterler
    if question_text.count("(cid:") > 10:
        issues.append("Çok fazla encoding hatası")
        score -= 15
    
    # 8. Yarım kalmış metin kontrolü
    if question_text.endswith("...") or question_text.endswith("---"):
        issues.append("Metin yarım kalmış gibi görünüyor")
        score -= 20
    
    # 9. Tekrarlanan kelimeler (parse hatası olabilir)
    words = question_text.split()
    if len(words) > 0:
        unique_ratio = len(set(words)) / len(words)
        if unique_ratio < 0.3:
            warnings.append("Çok fazla tekrarlanan kelime (parse hatası olabilir)")
            score -= 10
    
    return {
        "score": max(0, score),
        "issues": issues,
        "warnings": warnings,
        "quality": "excellent" if score >= 90 else "good" if score >= 70 else "fair" if score >= 50 else "poor"
    }


def validate_all_questions(questions: List[Dict]) -> Dict[str, any]:
    """Tüm soruları kontrol eder."""
    results = []
    
    for i, q in enumerate(questions, 1):
        quality = check_question_quality(q)
        results.append({
            "question_index": i,
            "question_number": q.get("question_number", "?"),
            "quality": quality
        })
    
    # İstatistikler
    excellent = sum(1 for r in results if r["quality"]["quality"] == "excellent")
    good = sum(1 for r in results if r["quality"]["quality"] == "good")
    fair = sum(1 for r in results if r["quality"]["quality"] == "fair")
    poor = sum(1 for r in results if r["quality"]["quality"] == "poor")
    
    avg_score = sum(r["quality"]["score"] for r in results) / len(results) if results else 0
    
    total_issues = sum(len(r["quality"]["issues"]) for r in results)
    total_warnings = sum(len(r["quality"]["warnings"]) for r in results)
    
    return {
        "total_questions": len(questions),
        "excellent": excellent,
        "good": good,
        "fair": fair,
        "poor": poor,
        "average_score": avg_score,
        "total_issues": total_issues,
        "total_warnings": total_warnings,
        "results": results
    }


def print_quality_report(validation_result: Dict, show_details: bool = False):
    """Kalite raporunu yazdırır."""
    console = Console()
    
    print("\n[bold cyan]📊 SORU KALİTE RAPORU[/bold cyan]")
    print("=" * 60)
    
    # Özet tablo
    table = Table(title="Özet", show_header=True, header_style="bold magenta")
    table.add_column("Kategori", style="cyan")
    table.add_column("Sayı", style="green")
    table.add_column("Yüzde", style="yellow")
    
    total = validation_result["total_questions"]
    table.add_row("Toplam Soru", str(total), "100%")
    table.add_row("Mükemmel (90+)", str(validation_result["excellent"]), f"{validation_result['excellent']/total*100:.1f}%")
    table.add_row("İyi (70-89)", str(validation_result["good"]), f"{validation_result['good']/total*100:.1f}%")
    table.add_row("Orta (50-69)", str(validation_result["fair"]), f"{validation_result['fair']/total*100:.1f}%")
    table.add_row("Zayıf (<50)", str(validation_result["poor"]), f"{validation_result['poor']/total*100:.1f}%")
    
    console.print(table)
    
    # Ortalama puan
    print(f"\n[bold]Ortalama Kalite Puanı:[/bold] {validation_result['average_score']:.1f}/100")
    
    # Sorunlar
    if validation_result["total_issues"] > 0:
        print(f"\n[red]❌ Toplam Sorun:[/red] {validation_result['total_issues']}")
    if validation_result["total_warnings"] > 0:
        print(f"[yellow]⚠️  Toplam Uyarı:[/yellow] {validation_result['total_warnings']}")
    
    # Problemli sorular
    problem_questions = [r for r in validation_result["results"] if r["quality"]["quality"] in ["fair", "poor"]]
    if problem_questions:
        print(f"\n[bold red]⚠️  Problemli Sorular ({len(problem_questions)} adet):[/bold red]")
        for r in problem_questions[:10]:  # İlk 10'unu göster
            q_num = r["question_number"]
            score = r["quality"]["score"]
            issues = r["quality"]["issues"]
            print(f"  • Soru #{q_num}: {score}/100 - {', '.join(issues[:2])}")
        if len(problem_questions) > 10:
            print(f"  ... ve {len(problem_questions) - 10} soru daha")
    
    # Detaylı görünüm
    if show_details:
        print("\n[bold]📋 Detaylı Soru Listesi:[/bold]")
        for r in validation_result["results"][:5]:  # İlk 5'i göster
            q_num = r["question_number"]
            quality = r["quality"]
            print(f"\n  Soru #{q_num} - {quality['quality'].upper()} ({quality['score']}/100)")
            if quality["issues"]:
                print(f"    [red]Sorunlar:[/red] {', '.join(quality['issues'])}")
            if quality["warnings"]:
                print(f"    [yellow]Uyarılar:[/yellow] {', '.join(quality['warnings'][:2])}")


def interactive_review(questions: List[Dict], validation_result: Dict):
    """İnteraktif soru inceleme."""
    console = Console()
    
    problem_questions = [r for r in validation_result["results"] if r["quality"]["quality"] in ["fair", "poor"]]
    
    if not problem_questions:
        print("\n[green]✅ Tüm sorular kaliteli görünüyor![/green]")
        return
    
    print(f"\n[bold yellow]🔍 Problemli Sorular İnceleniyor ({len(problem_questions)} adet)[/bold yellow]")
    print("Her soruyu gözden geçirip onaylayabilirsin.\n")
    
    for r in problem_questions:
        idx = r["question_index"] - 1
        q = questions[idx]
        q_num = q.get("question_number", "?")
        quality = r["quality"]
        
        # Soruyu göster
        panel_content = f"[bold]Soru #{q_num}[/bold]\n\n"
        panel_content += f"[dim]Kalite: {quality['score']}/100 ({quality['quality']})[/dim]\n\n"
        
        raw_text = q.get("raw_text", q.get("question_text", ""))[:300]
        panel_content += f"[cyan]Metin:[/cyan]\n{raw_text}...\n\n"
        
        options = q.get("options", [])
        if options:
            panel_content += f"[green]Seçenekler:[/green]\n"
            for opt in options[:4]:
                panel_content += f"  {opt}\n"
        
        if quality["issues"]:
            panel_content += f"\n[red]Sorunlar:[/red] {', '.join(quality['issues'])}"
        
        console.print(Panel(panel_content, title=f"Soru #{q_num}", border_style="yellow"))
        
        # Kullanıcı onayı
        response = input("\nBu soru doğru mu? (E/h/ç=çıkış): ").strip().lower()
        if response == "ç":
            break
        elif response in ["h", "hayır"]:
            print(f"[red]❌ Soru #{q_num} işaretlendi: DÜZELTİLMELİ[/red]\n")
        else:
            print(f"[green]✅ Soru #{q_num} onaylandı[/green]\n")


def main():
    parser = argparse.ArgumentParser(description="Soru kalitesi kontrolü")
    parser.add_argument("--file", required=True, help="Soru dosyası (JSON)")
    parser.add_argument("--interactive", action="store_true", help="İnteraktif inceleme")
    parser.add_argument("--details", action="store_true", help="Detaylı rapor")
    
    args = parser.parse_args()
    
    # Veriyi yükle
    data = read_json(Path(args.file))
    if isinstance(data, list):
        questions = data
    elif isinstance(data, dict) and "questions" in data:
        questions = data["questions"]
    else:
        questions = [data]
    
    # Kontrol et
    result = validate_all_questions(questions)
    
    # Rapor yazdır
    print_quality_report(result, show_details=args.details)
    
    # İnteraktif inceleme
    if args.interactive:
        interactive_review(questions, result)
    
    # Çıkış kodu
    if result["poor"] > result["total_questions"] * 0.2:  # %20'den fazla zayıf soru varsa
        print("\n[red]❌ UYARI: Çok fazla düşük kaliteli soru var![/red]")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

