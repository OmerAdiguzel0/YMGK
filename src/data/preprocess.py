from __future__ import annotations

import argparse
import pathlib

import pandas as pd
from rich import print

from src.utils.io import ensure_dir


def preprocess(raw_csv: pathlib.Path, output_csv: pathlib.Path) -> None:
    print(f"[bold cyan]Ham veri yükleniyor:[/bold cyan] {raw_csv}")
    df = pd.read_csv(raw_csv)

    print("Temizlik: boş alanlar, whitespace normalize ediliyor...")
    df["question_text"] = df["question_text"].str.strip()
    df["solution_text"] = df.get("solution_text", "").fillna("").astype(str).str.strip()

    df = df.dropna(subset=["question_text"])

    ensure_dir(output_csv.parent)
    df.to_csv(output_csv, index=False)
    print(f"[green]Hazır:[/green] {output_csv} dosyasına kaydedildi.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ham LGS verilerini temizle")
    parser.add_argument("--input", required=True, help="Ham CSV yolu")
    parser.add_argument("--output", required=True, help="Çıktı CSV yolu")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    preprocess(pathlib.Path(args.input), pathlib.Path(args.output))


if __name__ == "__main__":
    main()

