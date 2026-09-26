from __future__ import annotations

import csv
from pathlib import Path
from functools import lru_cache
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


DATA_DIR = Path(__file__).resolve().parents[3] / "ml"
DATASETS = [DATA_DIR / "sms_spam_uci.csv", DATA_DIR / "demo_dataset.csv"]


def load_data() -> tuple[list[str], list[int], dict[str, int]]:
    rows: list[dict] = []
    sources: dict[str, int] = {}
    for dataset in DATASETS:
        if not dataset.exists():
            continue
        with dataset.open(encoding="utf-8") as handle:
            dataset_rows = list(csv.DictReader(handle))
        sources[dataset.name] = len(dataset_rows)
        rows.extend(dataset_rows)
    unique = {row["text"].strip(): row for row in rows if row["text"].strip()}
    values = list(unique.values())
    return [row["text"] for row in values], [int(row["label"]) for row in values], sources


def build_pipeline() -> Pipeline:
    return Pipeline([
        ("tfidf", FeatureUnion([
            ("word", TfidfVectorizer(ngram_range=(1, 2), min_df=2, lowercase=True, sublinear_tf=True)),
            ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=2, lowercase=True, sublinear_tf=True)),
        ])),
        ("classifier", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)),
    ])


class ScamClassifier:
    def __init__(self) -> None:
        self.texts, self.labels, self.sources = load_data()
        train_texts, test_texts, train_labels, test_labels = train_test_split(
            self.texts,
            self.labels,
            test_size=0.20,
            stratify=self.labels,
            random_state=42,
        )
        evaluation_pipeline = build_pipeline()
        evaluation_pipeline.fit(train_texts, train_labels)
        predictions = evaluation_pipeline.predict(test_texts)
        self.metrics = {
            "model_name": "TF-IDF + Logistic Regression",
            "accuracy": round(float(accuracy_score(test_labels, predictions)), 3),
            "precision": round(float(precision_score(test_labels, predictions, zero_division=0)), 3),
            "recall": round(float(recall_score(test_labels, predictions, zero_division=0)), 3),
            "f1": round(float(f1_score(test_labels, predictions, zero_division=0)), 3),
            "sample_count": len(self.labels),
            "train_sample_count": len(train_labels),
            "test_sample_count": len(test_labels),
            "method": "Stratified 80/20 held-out test set",
            "split_random_state": 42,
            "dataset_sources": self.sources,
        }
        self.pipeline = build_pipeline()
        self.pipeline.fit(self.texts, self.labels)

    def predict(self, text: str) -> dict:
        probability = float(self.pipeline.predict_proba([text])[0][1])
        return {"scam_probability": round(probability, 4), "label": int(probability >= 0.5)}


@lru_cache
def get_classifier() -> ScamClassifier:
    return ScamClassifier()
