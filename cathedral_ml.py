#!/usr/bin/env python3
"""
cathedral_ml.py – Lightweight ML using TF‑IDF + Logistic Regression.
No torch, no transformers – runs on any CPU.
"""

import json
import numpy as np
from pathlib import Path
from typing import List, Dict

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
import joblib

class HybridThreatDetector:
    def __init__(self, model_dir: str = "ml_models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(exist_ok=True)
        self.vectorizer = None
        self.classifier = None
        self._load_or_train()

    def _load_or_train(self):
        vec_path = self.model_dir / "vectorizer.pkl"
        clf_path = self.model_dir / "threat_classifier.pkl"
        if vec_path.exists() and clf_path.exists():
            self.vectorizer = joblib.load(vec_path)
            self.classifier = joblib.load(clf_path)
            print("✅ Loaded existing ML model")
        else:
            print("⚠️ No trained model found. Train with train_from_history()")

    def train(self, texts: List[str], labels: List[int]):
        if len(texts) < 10:
            print("⚠️ Need at least 10 samples for training.")
            return

        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 2),
            stop_words='english'
        )
        X = self.vectorizer.fit_transform(texts)
        clf = LogisticRegression(class_weight='balanced', max_iter=1000)
        clf.fit(X, labels)

        calibrated_clf = CalibratedClassifierCV(clf, cv=3)
        calibrated_clf.fit(X, labels)

        self.classifier = calibrated_clf
        joblib.dump(self.vectorizer, self.model_dir / "vectorizer.pkl")
        joblib.dump(self.classifier, self.model_dir / "threat_classifier.pkl")
        print(f"✅ Trained on {len(texts)} samples.")

    def compute_likelihood_ratio(self, text: str) -> float:
        if self.vectorizer is None or self.classifier is None:
            return 1.0
        X = self.vectorizer.transform([text])
        prob = self.classifier.predict_proba(X)[0][1]
        lr = prob / (1 - prob + 1e-6)
        return float(lr)

# ------------------------------------------------------------
# Integration functions
# ------------------------------------------------------------

def get_ml_likelihoods(threats: List[Dict]) -> Dict[str, float]:
    detector = HybridThreatDetector()
    if detector.classifier is None:
        print("⚠️ ML model not trained – returning neutral LRs (1.0)")
        return {t['id']: 1.0 for t in threats if t.get('id')}

    lrs = {}
    for t in threats:
        tid = t.get('id')
        text = t.get('description', '') or t.get('name', '')
        if tid and text:
            lrs[tid] = detector.compute_likelihood_ratio(text)
    return lrs

def train_from_history():
    """Train the ML model using prediction descriptions (no need for threat matching)."""
    try:
        with open('predictions.json') as f:
            preds = json.load(f)
    except FileNotFoundError:
        print("❌ predictions.json not found.")
        return

    confirmed = preds.get('confirmed', [])
    falsified = preds.get('falsified', [])

    texts = []
    labels = []

    for p in confirmed:
        desc = p.get('description', '')
        if desc:
            texts.append(desc)
            labels.append(1)

    for p in falsified:
        desc = p.get('description', '')
        if desc:
            texts.append(desc)
            labels.append(0)

    if len(texts) < 10:
        print(f"⚠️ Only {len(texts)} prediction texts with descriptions – need at least 10.")
        return

    print(f"📊 Training with {len(texts)} samples ({sum(labels)} confirmed, {len(labels)-sum(labels)} falsified)")

    detector = HybridThreatDetector()
    detector.train(texts, labels)
