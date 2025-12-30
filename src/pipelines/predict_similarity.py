"""Soru benzerliği modeli ile benzer soruları bulma."""

from __future__ import annotations

import argparse
import json
import pathlib

import joblib
import pandas as pd
from rich import print
from rich.table import Table
from sklearn.metrics.pairwise import cosine_similarity


def find_similar_questions(
    question: str,
    model_dir: pathlib.Path,
    top_k: int = 5
) -> None:
    """Verilen soruya en benzer soruları bulur."""
    
    # Model dosyalarını yükle
    vectorizer_path = model_dir / "vectorizer.joblib"
    vectors_path = model_dir / "question_vectors.joblib"
    questions_path = model_dir / "questions.json"
    
    if not vectorizer_path.exists():
        print(f"[red]Hata:[/red] Vectorizer bulunamadı: {vectorizer_path}")
        return
    
    if not vectors_path.exists():
        print(f"[red]Hata:[/red] Vektörler bulunamadı: {vectors_path}")
        return
    
    if not questions_path.exists():
        print(f"[red]Hata:[/red] Sorular bulunamadı: {questions_path}")
        return
    
    print("[bold cyan]Model yükleniyor...[/bold cyan]")
    vectorizer = joblib.load(vectorizer_path)
    question_vectors = joblib.load(vectors_path)
    
    with questions_path.open("r", encoding="utf-8") as f:
        questions = json.load(f)
    
    # Soruyu vektörleştir
    question_vector = vectorizer.transform([question])
    
    # Benzerlik hesapla
    similarities = cosine_similarity(question_vector, question_vectors).flatten()
    
    # En benzer soruları bul
    top_indices = similarities.argsort()[-top_k:][::-1]
    
    # Sonuçları göster
    print(f"\n[bold green]Soru:[/bold green] {question[:200]}...")
    print(f"\n[bold cyan]En benzer {top_k} soru:[/bold cyan]\n")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Sıra", style="dim", width=6)
    table.add_column("Benzerlik", width=10)
    table.add_column("Soru Metni", width=80)
    table.add_column("Kaynak", width=20)
    
    for i, idx in enumerate(top_indices, 1):
        sim_score = similarities[idx]
        q = questions[idx]
        question_text = q.get("full_text", q.get("raw_text", ""))[:150]
        source = q.get("source_file", "unknown")
        
        table.add_row(
            str(i),
            f"{sim_score:.3f}",
            question_text + "..." if len(question_text) >= 150 else question_text,
            source
        )
    
    print(table)
    
    # En benzer soruyu detaylı göster
    if len(top_indices) > 0:
        best_idx = top_indices[0]
        best_q = questions[best_idx]
        print(f"\n[bold green]En benzer soru (Benzerlik: {similarities[best_idx]:.3f}):[/bold green]")
        print(f"[cyan]Kaynak:[/cyan] {best_q.get('source_file', 'unknown')}")
        print(f"[cyan]Soru numarası:[/cyan] {best_q.get('question_number', 'N/A')}")
        print(f"[cyan]Metin:[/cyan] {best_q.get('full_text', best_q.get('raw_text', ''))[:500]}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Soru benzerliği modeli ile benzer soruları bul")
    parser.add_argument(
        "--model-dir",
        default="models/baseline",
        help="Model dizini"
    )
    parser.add_argument(
        "--question",
        required=True,
        help="Benzer soruları bulunacak soru metni"
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Gösterilecek en benzer soru sayısı (varsayılan: 5)"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model_dir = pathlib.Path(args.model_dir)
    
    if not model_dir.exists():
        print(f"[red]Hata:[/red] Model dizini bulunamadı: {model_dir}")
        return
    
    find_similar_questions(
        question=args.question,
        model_dir=model_dir,
        top_k=args.top_k
    )


if __name__ == "__main__":
    main()

