from __future__ import annotations

import argparse
import pathlib

import joblib
from rich import print


def load_pipeline(model_path: pathlib.Path):
    vectorizer = joblib.load(model_path.parent / "vectorizer.joblib") if (model_path.parent / "vectorizer.joblib").exists() else None
    model = joblib.load(model_path)
    return vectorizer, model


def predict(question: str, model_path: str) -> None:
    vectorizer, model = load_pipeline(pathlib.Path(model_path))

    if vectorizer is None:
        print("[red]Vectorizer bulunamadı. Eğitim sürecinde kaydettiğinizden emin olun.[/red]")
        return

    features = vectorizer.transform([question])
    prediction = model.predict(features)[0]
    print(f"[bold green]Tahmin edilen kategori:[/bold green] {prediction}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Eğitilmiş modeli kullanarak soru kategorisi tahmini yap")
    parser.add_argument("--model-path", required=True, help="joblib model dosyası")
    parser.add_argument("--question", required=True, help="Tahmin edilecek soru metni")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    predict(args.question, args.model_path)


if __name__ == "__main__":
    main()

