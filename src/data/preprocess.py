from __future__ import annotations

import argparse
import json
import pathlib

import pandas as pd
from rich import print

from src.utils.io import ensure_dir


def load_data(input_path: pathlib.Path) -> pd.DataFrame:
    """JSON veya CSV dosyasından veri yükler."""
    if input_path.suffix == ".json":
        print(f"[bold cyan]JSON dosyası yükleniyor:[/bold cyan] {input_path}")
        with input_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict) and "questions" in data:
            df = pd.DataFrame(data["questions"])
        else:
            df = pd.DataFrame([data])
    else:
        print(f"[bold cyan]CSV dosyası yükleniyor:[/bold cyan] {input_path}")
        df = pd.read_csv(input_path)
    
    return df


def preprocess(input_path: pathlib.Path, output_path: pathlib.Path) -> None:
    """Ham veriyi temizler ve yapılandırır."""
    df = load_data(input_path)
    
    print(f"[cyan]Toplam kayıt:[/cyan] {len(df)}")
    
    # Temizlik: boş alanlar, whitespace normalize
    print("Temizlik: boş alanlar, whitespace normalize ediliyor...")
    
    # Soru metni alanını bul (farklı isimler olabilir)
    # Öncelik: temizlenmiş versiyon > ham versiyon
    question_col = None
    for col in ["raw_text_cleaned", "question_text_cleaned", "question_text", "raw_text", "question", "soru"]:
        if col in df.columns:
            question_col = col
            break
    
    if question_col:
        df["question_text"] = df[question_col].astype(str).str.strip()
        
        # Eğer temizlenmiş versiyon kullanıldıysa, encoding sorunlarını işaretle
        if "cleaned" in question_col:
            print("[green]✓[/green] Temizlenmiş metin versiyonu kullanılıyor")
    else:
        print("[yellow]Uyarı:[/yellow] Soru metni sütunu bulunamadı, ilk sütun kullanılıyor.")
        df["question_text"] = df.iloc[:, 0].astype(str).str.strip()
    
    # Encoding sorunları kontrolü ve uyarı
    if "has_encoding_issues" in df.columns:
        encoding_issues = df["has_encoding_issues"].sum()
        if encoding_issues > 0:
            print(f"[yellow]⚠️  Uyarı:[/yellow] {encoding_issues} soruda encoding sorunu var")
            # Temizlenmiş versiyon yoksa uyarı ver
            if "raw_text_cleaned" not in df.columns:
                print("[yellow]  → raw_text_cleaned alanı yok, OCR ile tekrar çıkarılması önerilir[/yellow]")
            else:
                cleaned_available = df["raw_text_cleaned"].notna().sum()
                if cleaned_available < encoding_issues:
                    print(f"[yellow]  → Sadece {cleaned_available} sorunun temizlenmiş versiyonu var[/yellow]")
    
    # Çözüm metni (opsiyonel)
    solution_col = None
    for col in ["solution_text", "solution", "çözüm", "cevap_açıklama"]:
        if col in df.columns:
            solution_col = col
            break
    
    if solution_col:
        df["solution_text"] = df[solution_col].fillna("").astype(str).str.strip()
    else:
        df["solution_text"] = ""
    
    # Seçenekleri birleştir (eğer ayrı sütunlarda ise)
    if "options" in df.columns:
        # options zaten liste veya string olabilir
        if df["options"].dtype == "object":
            df["options"] = df["options"].apply(
                lambda x: ", ".join(x) if isinstance(x, list) else str(x)
            )
    
    # Boş soruları kontrol et ve çıkar (ama dikkatli)
    initial_count = len(df)
    
    # Önce encoding sorunlu ama temizlenmiş versiyonu olan soruları kontrol et
    if "raw_text_cleaned" in df.columns:
        # Temizlenmiş versiyonu olan ama question_text boş olanları düzelt
        mask = (df["question_text"].isna() | (df["question_text"].str.len() == 0)) & df["raw_text_cleaned"].notna()
        if mask.sum() > 0:
            df.loc[mask, "question_text"] = df.loc[mask, "raw_text_cleaned"]
            print(f"[green]✓[/green] {mask.sum()} soru için temizlenmiş versiyon kullanıldı")
    
    # Gerçekten boş olanları çıkar (hem question_text hem raw_text_cleaned boşsa)
    truly_empty = df["question_text"].isna() | (df["question_text"].str.len() == 0)
    if "raw_text_cleaned" in df.columns:
        truly_empty = truly_empty & (df["raw_text_cleaned"].isna() | (df["raw_text_cleaned"].str.len() == 0))
    if "raw_text" in df.columns:
        truly_empty = truly_empty & (df["raw_text"].isna() | (df["raw_text"].str.len() == 0))
    
    df = df[~truly_empty]
    removed_count = initial_count - len(df)
    
    if removed_count > 0:
        print(f"[yellow]Uyarı:[/yellow] {removed_count} tamamen boş kayıt çıkarıldı.")
    else:
        print(f"[green]✓[/green] Tüm sorular korundu ({len(df)} soru)")
    
    # Kareköklü ifadeler filtresi (opsiyonel - eğer zaten filtrelenmişse atla)
    if "has_keyword" not in df.columns:
        keywords = ["kök", "√", "kareköklü", "irrasyonel", "karekök"]
        df["has_keyword"] = df["question_text"].str.lower().apply(
            lambda x: any(kw in x for kw in keywords)
        )
        # Filtreleme yapılabilir ama şimdilik tümünü tutuyoruz
    
    print(f"[green]Temizlenmiş kayıt sayısı:[/green] {len(df)}")
    
    # Çıktıyı kaydet
    ensure_dir(output_path.parent)
    
    if output_path.suffix == ".json":
        df.to_json(output_path, orient="records", ensure_ascii=False, indent=2)
    else:
        df.to_csv(output_path, index=False, encoding="utf-8")
    
    print(f"[green]Hazır:[/green] {output_path} dosyasına kaydedildi.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ham LGS verilerini temizle")
    parser.add_argument("--input", required=True, help="Ham JSON/CSV yolu")
    parser.add_argument("--output", required=True, help="Çıktı JSON/CSV yolu")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    preprocess(pathlib.Path(args.input), pathlib.Path(args.output))


if __name__ == "__main__":
    main()

