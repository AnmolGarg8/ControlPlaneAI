"""
ControlPlane.ai — Responsibility Detector
Same TF-IDF + Logistic Regression pattern used in AIRAVAT XDR's phishing
classifier, retrained on a different corpus: biased / unsafe / PII-leaking
AI responses instead of phishing emails. Combined with a lightweight
rule-based entity scanner for the cases regex catches better than a
statistical model — dedicated PII/entity detection, as called out in the
Round 2 solutioning areas.
"""

import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from ai_response_simulator import get_responsibility_training_texts

# Rule-based patterns: these fire regardless of what the ML classifier thinks,
# since a hardcoded SSN or credit-card leak should never depend on model confidence.
PII_PATTERNS = [
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),                       # SSN-like
    re.compile(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b"),       # card-like
    re.compile(r"\b\d{2}-\d{5}[- ]?\d{5}\b"),                     # phone-like (intl format used in sim)
    re.compile(r"\b(?:password|admin password|secret key)\b.{0,15}[:\-]\s*\S+", re.IGNORECASE),
]


def _rule_based_hit(text):
    return any(p.search(text) for p in PII_PATTERNS)


class ResponsibilityDetector:
    def __init__(self):
        self.pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(max_features=500, ngram_range=(1, 2), stop_words="english")),
            ("clf", LogisticRegression(max_iter=1000, C=1.0, random_state=42)),
        ])
        self.is_trained = False

    def train(self):
        texts, labels = get_responsibility_training_texts()
        self.pipeline.fit(texts, labels)
        self.is_trained = True

    def predict(self, df):
        """Adds responsibility_risk_score (0-100) combining ML probability + rule hits."""
        if not self.is_trained:
            self.train()

        texts = df["response_text"].fillna("").tolist()
        ml_proba = self.pipeline.predict_proba(texts)[:, 1] * 100
        rule_hits = np.array([100.0 if _rule_based_hit(t) else 0.0 for t in texts])

        # A hardcoded PII/secret leak always wins, regardless of what the
        # classifier thinks — rule-based checks are a hard floor, not a vote.
        combined = np.maximum(ml_proba, rule_hits)

        result = df.copy()
        result["responsibility_risk_score"] = np.round(combined, 1)
        result["responsibility_flag"] = (combined > 50).astype(int)
        result["pii_rule_hit"] = (rule_hits > 0).astype(int)
        return result
