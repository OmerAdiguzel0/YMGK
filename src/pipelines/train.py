from __future__ import annotations

import argparse
import pathlib

import joblib
import pandas as pd
from rich import print
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split

from src.features.feature_builder import FeatureBuilder
from src.models.modeling import BaselineClassifier
from src.utils.io import ensure_dir, read_yaml


def train(config_path: str) -> None:
    cfg = read_yaml(config_path)

    data_path = pathlib.Path(cfg["data"]["processed_path"])
    df = pd.read_csv(data_path)

    text_field = cfg["data"]["text_field"]
    target_field = cfg["data"]["target_field"]

    X_train, X_temp, y_train, y_temp = train_test_split(
        df[text_field],
        df[target_field],
        test_size=cfg["training"]["test_size"],
        random_state=cfg["seed"],
        stratify=df[target_field] if cfg["training"].get("stratify", False) else None,
    )

    X_val, X_test, y_val, y_test = train_test_split(
        X_temp,
        y_temp,
        test_size=0.5,
        random_state=cfg["seed"],
        stratify=y_temp if cfg["training"].get("stratify", False) else None,
    )

    builder = FeatureBuilder(
        max_features=cfg["model"]["params"]["max_features"],
        ngram_range=tuple(cfg["model"]["params"]["ngram_range"]),
    )
    X_train_vec = builder.fit_transform(X_train)
    X_val_vec = builder.transform(X_val)
    X_test_vec = builder.transform(X_test)

    classifier = BaselineClassifier(C=cfg["model"]["params"]["C"])
    classifier.fit(X_train_vec, y_train)

    val_pred = classifier.predict(X_val_vec)
    test_pred = classifier.predict(X_test_vec)

    print("[bold cyan]Val F1:[/bold cyan]", f1_score(y_val, val_pred, average="macro"))
    print("[bold cyan]Test Accuracy:[/bold cyan]", accuracy_score(y_test, test_pred))
    print(classification_report(y_test, test_pred))

    output_dir = ensure_dir(pathlib.Path(cfg["artifacts"]["output_dir"]))
    classifier.save(output_dir / "baseline_classifier.joblib")
    joblib.dump(builder.vectorizer, output_dir / "vectorizer.joblib")
    print(f"[green]Model kaydedildi:[/green] {output_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Baseline TF-IDF + Logistic Regression eğitimi")
    parser.add_argument("--config", required=True, help="Training YAML dosyası")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    train(args.config)


if __name__ == "__main__":
    main()

