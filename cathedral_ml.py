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
    """Train the ML model from confirmed/falsified predictions."""
    try:
        with open('predictions.json') as f:
            preds = json.load(f)
        with open('threats.json') as f:
            threats_data = json.load(f)
            threats = threats_data.get('threats', [])
    except FileNotFoundError as e:
        print(f"❌ File missing: {e}")
        return

    # Build a set of confirmed and falsified IDs
    confirmed_ids = set()
    falsified_ids = set()

    # Helper to extract IDs from a list
    def extract_ids(items):
        ids = []
        for item in items:
            if isinstance(item, dict):
                # Try common keys
                tid = item.get('id') or item.get('prediction_id') or item.get('threat_id')
                if tid:
                    ids.append(tid)
                # If item has a 'status' field, we might filter later
        return ids

    # Check various structures
    if 'confirmed' in preds:
        confirmed_ids.update(extract_ids(preds['confirmed']))
    if 'falsified' in preds:
        falsified_ids.update(extract_ids(preds['falsified']))

    # If no confirmed/falsified, look in 'history' or 'pending' with status
    if not confirmed_ids and not falsified_ids:
        print("⚠️ No 'confirmed' or 'falsified' keys found. Scanning all entries...")
        # Look in 'pending' for status
        for entry in preds.get('pending', []):
            status = entry.get('status', '').lower()
            tid = entry.get('id')
            if tid:
                if status in ('confirmed', 'resolved'):
                    confirmed_ids.add(tid)
                elif status == 'falsified':
                    falsified_ids.add(tid)

        # Also check 'history' if present
        for entry in preds.get('history', []):
            # maybe history contains status changes
            pass

    print(f"📊 Found {len(confirmed_ids)} confirmed, {len(falsified_ids)} falsified predictions.")

    if not confirmed_ids and not falsified_ids:
        print("❌ No resolved predictions found. Cannot train.")
        return

    # Build training data
    texts = []
    labels = []
    for t in threats:
        tid = t.get('id')
        if tid in confirmed_ids:
            texts.append(t.get('description', '') or t.get('name', ''))
            labels.append(1)
        elif tid in falsified_ids:
            texts.append(t.get('description', '') or t.get('name', ''))
            labels.append(0)

    if len(texts) < 10:
        print(f"⚠️ Only {len(texts)} resolved threats matched in threats.json – need at least 10.")
        return

    detector = HybridThreatDetector()
    detector.train(texts, labels)
