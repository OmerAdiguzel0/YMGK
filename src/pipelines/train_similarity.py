"""Soru benzerliği modeli eğitimi - TF-IDF vektörleri kaydeder."""

from __future__ import annotations

import argparse
import pathlib

import joblib
import pandas as pd
from rich import print
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.utils.io import ensure_dir, read_yaml


def train_similarity_model(config_path: str) -> None:
    """Soru benzerliği için TF-IDF modeli eğitir."""
    cfg = read_yaml(config_path)
    
    # Veri yükle
    data_path = pathlib.Path(cfg["data"]["processed_path"])
    df = pd.read_csv(data_path)
    
    text_field = cfg["data"]["text_field"]
    
    # Metin alanını seç (question_text yoksa full_text veya raw_text kullan)
    if text_field not in df.columns:
        if "question_text" in df.columns:
            texts = df["question_text"].fillna("")
        elif "full_text" in df.columns:
            texts = df["full_text"].fillna("")
        else:
            texts = df["raw_text"].fillna("")
    else:
        texts = df[text_field].fillna("")
    
    print(f"[bold cyan]Toplam soru:[/bold cyan] {len(texts)}")
    print(f"[bold cyan]Boş olmayan metin:[/bold cyan] {texts.str.len().gt(0).sum()}")
    
    # Boş metinleri filtrele
    valid_mask = texts.str.len() > 10
    texts = texts[valid_mask]
    df_filtered = df[valid_mask].reset_index(drop=True)
    
    print(f"[green]Geçerli soru:[/green] {len(texts)}")
    
    # TF-IDF vektörleştirici
    vectorizer = TfidfVectorizer(
        max_features=cfg["model"]["params"]["max_features"],
        ngram_range=tuple(cfg["model"]["params"]["ngram_range"]),
        min_df=2,
        analyzer="word"
    )
    
    print("[bold]TF-IDF vektörleri oluşturuluyor...[/bold]")
    X = vectorizer.fit_transform(texts)
    
    print(f"[green]Vektör boyutu:[/green] {X.shape}")
    print(f"[green]Kelime sayısı:[/green] {len(vectorizer.vocabulary_)}")
    
    # Model kaydet
    output_dir = ensure_dir(pathlib.Path(cfg["artifacts"]["output_dir"]))
    
    # Vectorizer kaydet
    vectorizer_path = output_dir / "vectorizer.joblib"
    joblib.dump(vectorizer, vectorizer_path)
    print(f"[green]✓ Vectorizer kaydedildi:[/green] {vectorizer_path}")
    
    # Vektörleri kaydet (benzerlik hesaplama için)
    vectors_path = output_dir / "question_vectors.joblib"
    joblib.dump(X, vectors_path)
    print(f"[green]✓ Vektörler kaydedildi:[/green] {vectors_path}")
    
    # Soru metinlerini kaydet (referans için)
    questions_path = output_dir / "questions.json"
    df_filtered.to_json(questions_path, orient="records", force_ascii=False, indent=2)
    print(f"[green]✓ Sorular kaydedildi:[/green] {questions_path}")
    
    # Test: İlk soruya en benzer 5 soruyu bul
    print("\n[bold cyan]Test: İlk soruya en benzer 5 soru[/bold cyan]")
    if len(texts) > 5:
        first_vector = X[0:1]
        similarities = cosine_similarity(first_vector, X).flatten()
        top_indices = similarities.argsort()[-6:-1][::-1]  # En benzer 5 (kendisi hariç)
        
        print(f"\n[bold]Referans soru:[/bold]")
        print(f"{texts.iloc[0][:200]}...")
        print(f"\n[bold]En benzer sorular:[/bold]")
        for i, idx in enumerate(top_indices, 1):
            sim_score = similarities[idx]
            print(f"\n{i}. Benzerlik: {sim_score:.3f}")
            print(f"   {texts.iloc[idx][:200]}...")
    
    print(f"\n[bold green]✓ Model eğitimi tamamlandı![/bold green]")
    print(f"[green]Model dizini:[/green] {output_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Soru benzerliği modeli eğitimi")
    parser.add_argument("--config", required=True, help="Training YAML dosyası")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    train_similarity_model(args.config)


if __name__ == "__main__":
    main()

