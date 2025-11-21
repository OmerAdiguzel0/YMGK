from __future__ import annotations

import pathlib

import joblib
from sklearn.linear_model import LogisticRegression


class BaselineClassifier:
    def __init__(self, C: float = 1.0, max_iter: int = 1000) -> None:
        self.model = LogisticRegression(
            C=C,
            max_iter=max_iter,
            multi_class="auto",
            n_jobs=-1,
        )

    def fit(self, X, y):
        return self.model.fit(X, y)

    def predict(self, X):
        return self.model.predict(X)

    def save(self, path: str | pathlib.Path) -> None:
        joblib.dump(self.model, str(path))

    @classmethod
    def load(cls, path: str | pathlib.Path) -> "BaselineClassifier":
        instance = cls()
        instance.model = joblib.load(str(path))
        return instance

