"""
ControlPlane.ai — Metrics & Monitoring
Round 2 brief explicitly asks: "how would you define, measure, and report
false positive/negative rates and overall system trustworthiness to a
skeptical stakeholder?" Because the simulator carries hidden ground-truth
labels, we can actually answer that with real numbers instead of a claim —
these labels are used here ONLY for measurement, never fed to the detectors.
"""

import numpy as np
import pandas as pd


def _binary_confusion(y_true, y_pred):
    y_true = np.array(y_true).astype(int)
    y_pred = np.array(y_pred).astype(int)
    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    total_pos = tp + fn
    total_neg = tn + fp
    return {
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "false_positive_rate_pct": round(100 * fp / total_neg, 1) if total_neg else 0.0,
        "false_negative_rate_pct": round(100 * fn / total_pos, 1) if total_pos else 0.0,
        "precision_pct": round(100 * tp / (tp + fp), 1) if (tp + fp) else None,
        "recall_pct": round(100 * tp / (tp + fn), 1) if (tp + fn) else None,
    }


def compute_detector_accuracy(df):
    """
    Per-dimension accuracy against hidden ground truth, plus an overall
    "any non-ALLOW decision on a genuinely risky response" view.
    """
    perf = _binary_confusion(df["gt_hallucinated"], df["performance_flag"])
    cost = _binary_confusion(df["gt_cost_anomaly"], df["cost_flag"])
    resp = _binary_confusion(df["gt_responsibility_violation"], df["responsibility_flag"])

    any_risk_gt = (
        (df["gt_hallucinated"] == 1)
        | (df["gt_cost_anomaly"] == 1)
        | (df["gt_responsibility_violation"] == 1)
    ).astype(int)
    any_flagged = (df["decision"] != "ALLOW").astype(int)
    overall = _binary_confusion(any_risk_gt, any_flagged)

    return {"performance": perf, "cost": cost, "responsibility": resp, "overall": overall}


def compute_latency_overhead(df, assumed_check_ms=45):
    """
    Estimated added latency from running the three checks. In this prototype
    the checks are lightweight (feature math + a linear classifier + a small
    forest), so we report a conservative assumed per-check cost rather than
    a real production measurement — a working prototype should not overclaim
    a benchmark it wasn't actually run under.
    """
    return {
        "assumed_ms_per_response": assumed_check_ms,
        "responses_processed": len(df),
        "total_added_latency_ms": assumed_check_ms * len(df),
    }
