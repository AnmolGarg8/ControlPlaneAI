"""
ControlPlane.ai — Performance Detector
Same Isolation Forest engine used in AIRAVAT XDR's network anomaly detector,
re-pointed at AI response signals instead of network telemetry: a "confidently
wrong" response is structurally an anomaly — high stated confidence paired with
low grounding / low self-consistency — the same way malicious traffic deviates
from a normal baseline.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


class PerformanceDetector:
    def __init__(self, contamination=0.15):
        self.model = IsolationForest(
            n_estimators=100,
            contamination=contamination,
            random_state=42,
        )
        self.scaler = StandardScaler()
        self.is_fitted = False

    def _extract_features(self, df):
        features = pd.DataFrame()
        # The core "confidently wrong" signal: confidence high, grounding low
        features["confidence_score"] = df["confidence_score"]
        features["consistency_gap"] = df["confidence_score"] - df["self_consistency"]
        features["retrieval_overlap"] = df["retrieval_overlap"]
        features["grounding_gap"] = df["confidence_score"] - df["retrieval_overlap"]
        return features

    def fit(self, df):
        features = self._extract_features(df)
        X = self.scaler.fit_transform(features)
        self.model.fit(X)
        self.is_fitted = True

    def predict(self, df):
        """Adds performance_risk_score (0-100, higher = more likely confidently wrong)."""
        if not self.is_fitted:
            self.fit(df)

        features = self._extract_features(df)
        X = self.scaler.transform(features)

        raw_scores = self.model.decision_function(X)
        predictions = self.model.predict(X)

        min_s, max_s = raw_scores.min(), raw_scores.max()
        if max_s - min_s > 0:
            risk = 100 * (1 - (raw_scores - min_s) / (max_s - min_s))
        else:
            risk = np.where(predictions == -1, 75.0, 25.0)

        result = df.copy()
        result["performance_risk_score"] = np.round(risk, 1)
        result["performance_flag"] = (predictions == -1).astype(int)
        return result
