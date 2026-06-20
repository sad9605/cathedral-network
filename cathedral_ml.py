#!/usr/bin/env python3
"""
cathedral_ml.py – Deep Learning + Bayesian hybrid for threat detection.
Integrates with existing cascade_engine.py via likelihood ratios.
"""

import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional

# NLP
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV

# Placeholder for image models
# from torchvision import models, transforms

class HybridThreatDetector:
    def __init__(self, model_dir: str = "ml_models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(exist_ok=True)

        # Load NLP encoder (lightweight, 384-dim embeddings)
        self.nlp_encoder = SentenceTransformer('all-MiniLM-L6-v2')

        # Load or train the classifier
        self.classifier = self._load_or_train_classifier()

    def _load_or_train_classifier(self):
        # Check if we have a saved classifier
        clf_path = self.model_dir / "threat_classifier.pkl"
        if clf_path.exists():
            import joblib
            return joblib.load(clf_path)

        # If not, train on existing threats (or fallback to dummy)
        print("⚠️ No trained classifier found. Using rule‑based fallback.")
        return None

    def encode_text(self, texts: List[str]) -> np.ndarray:
        """Convert list of text strings to embeddings."""
        if not texts:
            return np.array([])
        return self.nlp_encoder.encode(texts, convert_to_numpy=True)

    def extract_features_from_sweep(self, sweep_report: Dict) -> Dict:
        """
        Process sweep_report.json and extract:
          - Threat text embeddings
          - Sentiment scores
          - Event detection scores
        """
        features = {}
        # Extract relevant text fields from sweep report
        events = sweep_report.get('events', [])
        texts = [e.get('description', '') for e in events if e.get('description')]

        if texts:
            embeddings = self.encode_text(texts)
            # For each threat ID, we might aggregate embeddings (e.g., average)
            # For now, store as list
            features['text_embeddings'] = embeddings.tolist()
            features['text_count'] = len(texts)

        # Could also compute sentiment polarity (using a separate model)
        # Placeholder:
        features['avg_sentiment'] = 0.0  # would compute from VADER or similar

        return features

    def compute_likelihood_ratio(self, threat_id: str, threat_text: str, features: Dict) -> float:
        """
        For a given threat, compute a likelihood ratio based on ML features.
        Returns LR > 1 if evidence supports escalation.
        """
        if self.classifier is None:
            # Fallback: use a simple heuristic based on sentiment and event count
            # This is a dummy – in production we'd use the classifier
            return 1.0

        # Encode the threat description
        embedding = self.encode_text([threat_text])[0]

        # Get probability from classifier
        prob = self.classifier.predict_proba([embedding])[0][1]
        # Convert to likelihood ratio: LR = P(evidence|threat) / P(evidence|no-threat)
        # For binary classifier, we use the predicted probability as P(evidence|threat)
        # and 1 - P as P(evidence|no-threat)
        lr = prob / (1 - prob + 1e-6)
        return float(lr)

    def train_classifier(self, threats: List[Dict], labels: List[int]):
        """
        Train a logistic regression classifier on threat descriptions.
        labels: 1 for threats that escalated, 0 for those that didn't (from prediction log).
        """
        texts = [t.get('description', '') or t.get('name', '') for t in threats]
        if not texts:
            print("No text data for training.")
            return

        embeddings = self.encode_text(texts)
        clf = LogisticRegression(class_weight='balanced', max_iter=1000)
        clf.fit(embeddings, labels)

        # Calibrate for better probabilities
        calibrated_clf = CalibratedClassifierCV(clf, cv=3)
        calibrated_clf.fit(embeddings, labels)

        # Save
        import joblib
        joblib.dump(calibrated_clf, self.model_dir / "threat_classifier.pkl")
        self.classifier = calibrated_clf
        print(f"✅ Classifier trained on {len(texts)} samples.")

# ------------------------------------------------------------
# Integration function for cascade_engine.py
# ------------------------------------------------------------

def get_ml_likelihoods(threats: List[Dict], sweep_data: Dict) -> Dict[str, float]:
    """
    Called from cascade_engine.py to get per‑threat likelihood ratios.
    Returns dict: {threat_id: LR}
    """
    detector = HybridThreatDetector()
    features = detector.extract_features_from_sweep(sweep_data)

    lrs = {}
    for t in threats:
        tid = t.get('id')
        text = t.get('description', '') or t.get('name', '')
        if tid and text:
            lr = detector.compute_likelihood_ratio(tid, text, features)
            lrs[tid] = lr
    return lrs

# ------------------------------------------------------------
# Training script (to be run manually after sufficient history)
# ------------------------------------------------------------

def train_from_history():
    """Load confirmed/falsified predictions and train classifier."""
    preds = json.load(open('predictions.json'))
    threats = json.load(open('threats.json')).get('threats', [])

    # Create labels: 1 if confirmed, 0 if falsified or unresolved? We'll use confirmed as positive.
    confirmed_ids = {p['id'] for p in preds.get('confirmed', [])}
    falsified_ids = {p['id'] for p in preds.get('falsified', [])}
    # Only use threats that have been resolved
    labels = []
    training_threats = []
    for t in threats:
        tid = t.get('id')
        if tid in confirmed_ids:
            training_threats.append(t)
            labels.append(1)
        elif tid in falsified_ids:
            training_threats.append(t)
            labels.append(0)
    if len(training_threats) < 10:
        print("Not enough resolved threats for training. Need more data.")
        return

    detector = HybridThreatDetector()
    detector.train_classifier(training_threats, labels)

if __name__ == "__main__":
    # Example: train from history
    train_from_history()
