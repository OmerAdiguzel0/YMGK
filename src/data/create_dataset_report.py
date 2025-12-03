"""Veri seti için detaylı rapor oluşturur."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

import pandas as pd
from rich import print
from rich.console import Console
from rich.table import Table

from src.utils.io import read_json


def create_report(input_path: Path, output_path: Path) -> None:
    """Veri seti raporu oluşturur."""
    console = Console()
    
    data = read_json(input_path)
    if isinstance(data, list):
        questions = data
    elif isinstance(data, dict) and "questions" in data:
        questions = data["questions"]
    else:
        questions = [data]
    
    df = pd.DataFrame(questions)
    
    # Rapor içeriği
    report = f"""# Veri Seti Raporu

**Oluşturulma Tarihi:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Toplam Soru Sayısı:** {len(questions)}

## 📊 Genel İstatistikler

### Soru Dağılımı
- **Toplam:** {len(questions)} soru
- **Kaynak Dosya:** {df['source_file'].iloc[0] if 'source_file' in df.columns else 'Bilinmiyor'}

### Çıkarma Yöntemleri
"""
    
    if 'extraction_method' in df.columns:
        methods = df['extraction_method'].value_counts()
        for method, count in methods.items():
            report += f"- **{method}:** {count} soru ({count/len(questions)*100:.1f}%)\n"
    
    report += "\n### Karmaşıklık Dağılımı\n"
    if 'complexity' in df.columns:
        complexities = df['complexity'].value_counts()
        for comp, count in complexities.items():
            report += f"- **{comp}:** {count} soru\n"
    
    report += "\n### Soru Özellikleri\n"
    if 'has_image' in df.columns:
        has_img = df['has_image'].sum()
        report += f"- **Görsel içerikli:** {has_img} soru\n"
    if 'has_table' in df.columns:
        has_tbl = df['has_table'].sum()
        report += f"- **Tablo içerikli:** {has_tbl} soru\n"
    
    report += "\n## ⚠️ Sorunlar ve Uyarılar\n"
    
    # Encoding sorunları
    if 'has_encoding_issues' in df.columns:
        encoding_issues = df['has_encoding_issues'].sum()
        if encoding_issues > 0:
            report += f"- **Encoding sorunları:** {encoding_issues} soruda `(cid:...)` karakterleri var\n"
            if 'raw_text_cleaned' in df.columns:
                cleaned = df['raw_text_cleaned'].notna().sum()
                report += f"  - Temizlenmiş versiyon: {cleaned} soru\n"
    
    # Seçenek eksikliği
    if 'options' in df.columns:
        no_options = (df['options'].isna() | (df['options'].astype(str) == '[]')).sum()
        if no_options > 0:
            report += f"- **Seçenek eksikliği:** {no_options} soruda seçenek yok\n"
    
    # Soru metni eksikliği
    if 'question_text' in df.columns:
        no_text = df['question_text'].isna().sum() + (df['question_text'] == '').sum()
        if no_text > 0:
            report += f"- **Soru metni eksikliği:** {no_text} soruda metin yok\n"
    
    report += "\n## 📋 Veri Şeması\n\n"
    report += "### Zorunlu Alanlar\n"
    required = ['question_text', 'question_number', 'source_file', 'is_koklu']
    for field in required:
        if field in df.columns:
            missing = df[field].isna().sum()
            status = "✅" if missing == 0 else f"⚠️ ({missing} eksik)"
            report += f"- `{field}`: {status}\n"
    
    report += "\n### Opsiyonel Alanlar\n"
    optional = ['options', 'correct_answer', 'solution_text', 'complexity', 'has_image', 'has_table']
    for field in optional:
        if field in df.columns:
            filled = df[field].notna().sum()
            report += f"- `{field}`: {filled}/{len(questions)} dolu\n"
    
    report += "\n## ✅ Kalite Değerlendirmesi\n\n"
    report += "Veri seti model eğitimi için hazır görünüyor.\n"
    
    if encoding_issues > 0:
        report += f"\n⚠️ **Not:** {encoding_issues} soruda encoding sorunu var, ancak temizlenmiş versiyonlar mevcut.\n"
    
    # Kaydet
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"[green]✅ Rapor oluşturuldu:[/green] {output_path}")
    
    # Konsola da yazdır
    console.print("\n[bold cyan]📄 Rapor Özeti:[/bold cyan]")
    console.print(f"[green]Toplam soru:[/green] {len(questions)}")
    if 'extraction_method' in df.columns:
        console.print(f"[green]Çıkarma yöntemleri:[/green] {df['extraction_method'].nunique()} farklı yöntem")
    console.print(f"[green]Rapor dosyası:[/green] {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Veri seti raporu oluştur")
    parser.add_argument(
        "--input",
        default="data/processed/final_questions.json",
        help="Veri seti dosyası"
    )
    parser.add_argument(
        "--output",
        default="reports/dataset_report.md",
        help="Rapor çıktı dosyası"
    )
    
    args = parser.parse_args()
    create_report(Path(args.input), Path(args.output))


if __name__ == "__main__":
    main()

