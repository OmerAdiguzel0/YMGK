from __future__ import annotations

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer


class FeatureBuilder:
    def __init__(self, max_features: int = 20000, ngram_range: tuple[int, int] = (1, 2)) -> None:
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            ngram_range=ngram_range,
            analyzer="word",
            min_df=2,
        )

    def fit_transform(self, texts: pd.Series):
        return self.vectorizer.fit_transform(texts)

    def transform(self, texts: pd.Series):
        return self.vectorizer.transform(texts)

