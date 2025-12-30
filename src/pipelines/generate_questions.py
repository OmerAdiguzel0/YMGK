"""Soru üretim pipeline'ı."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
from rich import print
from rich.console import Console
from rich.table import Table

from src.models.question_generator import QuestionGenerator, train_generator
from src.utils.io import ensure_dir


def generate_questions_cli(
    num_questions: int,
    method: str,
    model_dir: str,
    output_path: str,
    questions_path: str = None
):
    """Soru üretim CLI."""
    console = Console()
    model_dir = Path(model_dir)
    output_path = Path(output_path)
    
    console.print(f"[bold cyan]Soru Üretimi Başlatılıyor[/bold cyan]\n")
    
    # Generator oluştur
    generator = QuestionGenerator()
    
    # Şablonları yükle veya çıkar
    templates_path = model_dir / "templates.json"
    if templates_path.exists():
        generator.load_templates(templates_path)
    elif questions_path:
        # Şablonları çıkar
        questions_file = Path(questions_path)
        if questions_file.suffix == ".json":
            with questions_file.open("r", encoding="utf-8") as f:
                seed_questions = json.load(f)
        else:
            df = pd.read_csv(questions_file)
            seed_questions = df.to_dict("records")
        
        console.print("[bold]Şablonlar çıkarılıyor...[/bold]")
        generator.templates = generator.extract_templates(seed_questions)
        console.print(f"[green]✓ {len(generator.templates)} şablon bulundu[/green]")
    else:
        console.print("[red]Hata:[/red] Şablonlar veya soru dosyası bulunamadı!")
        return
    
    # Soruları üret
    console.print(f"\n[bold]Soru üretiliyor... (Yöntem: {method})[/bold]")
    generated = generator.generate_questions(
        num_questions=num_questions,
        method=method,
        seed_questions=None
    )
    
    # Sonuçları göster
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Sıra", style="dim", width=6)
    table.add_column("Üretilen Soru", width=100)
    table.add_column("Yöntem", width=15)
    
    for i, q in enumerate(generated, 1):
        table.add_row(
            str(i),
            q["question_text"][:200] + "..." if len(q["question_text"]) > 200 else q["question_text"],
            q["generation_method"]
        )
    
    console.print(table)
    
    # Kaydet
    ensure_dir(output_path.parent)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(generated, f, ensure_ascii=False, indent=2)
    
    console.print(f"\n[bold green]✓ {len(generated)} soru üretildi![/bold green]")
    console.print(f"[green]Kaydedildi:[/green] {output_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Soru üretim modeli")
    parser.add_argument(
        "--num-questions",
        type=int,
        default=5,
        help="Üretilecek soru sayısı"
    )
    parser.add_argument(
        "--method",
        choices=["template", "llm", "hybrid"],
        default="template",
        help="Üretim yöntemi"
    )
    parser.add_argument(
        "--model-dir",
        default="models/baseline",
        help="Model dizini"
    )
    parser.add_argument(
        "--output",
        default="data/generated/generated_questions.json",
        help="Çıktı dosyası"
    )
    parser.add_argument(
        "--questions",
        help="Şablon çıkarma için soru dosyası (opsiyonel)"
    )
    parser.add_argument(
        "--train",
        action="store_true",
        help="Modeli eğit (şablon çıkarma)"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    
    if args.train:
        # Model eğitimi
        questions_path = Path(args.questions) if args.questions else Path("models/baseline/questions.json")
        model_dir = Path(args.model_dir)
        
        if not questions_path.exists():
            print(f"[red]Hata:[/red] Soru dosyası bulunamadı: {questions_path}")
            return
        
        train_generator(questions_path, model_dir)
    else:
        # Soru üretimi
        generate_questions_cli(
            num_questions=args.num_questions,
            method=args.method,
            model_dir=args.model_dir,
            output_path=args.output,
            questions_path=args.questions
        )


if __name__ == "__main__":
    main()

