"""
ControlPlane.ai — Audit Trail & Feedback Loop
Generates a structured, explainable record behind every non-ALLOW decision
(Round 2 brief: "governed policy layer... with a clear audit trail behind
every decision"), and provides a minimal feedback mechanism: when a human
reviewer confirms or overrides a flag, that verdict is logged and rolled
into a running false-positive estimate — the seed of the "feedback loops
that improve detection quality over time" the brief calls for. A full
retraining pipeline is out of scope for a Round 2 prototype, but the
capture point it would learn from is real and wired up.
"""

import datetime
import random
from policy_engine import get_response_action_label


def generate_flag_report(row):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    flag_id = f"FLAG-{random.randint(10000, 99999)}"

    reasons = []
    if row.get("performance_flag"):
        reasons.append(
            f"Performance: confidence {row['confidence_score']:.0f} vs. grounding "
            f"{row['retrieval_overlap']:.0f} — possible confidently-wrong response "
            f"(risk {row['performance_risk_score']:.0f}/100)"
        )
    if row.get("cost_flag"):
        reasons.append(
            f"Cost: {row['token_count']} tokens, {row['retries']} retries, "
            f"{row['latency_ms']}ms latency — above learned baseline for "
            f"'{row['use_case']}' (risk {row['cost_risk_score']:.0f}/100)"
        )
    if row.get("responsibility_flag"):
        pii_note = " [rule-based PII/secret hit]" if row.get("pii_rule_hit") else " [classifier flagged]"
        reasons.append(
            f"Responsibility: bias/unsafe/PII-leak risk {row['responsibility_risk_score']:.0f}/100"
            f"{pii_note}"
        )
    if not reasons:
        reasons.append("Composite score crossed threshold without a single dominant dimension.")

    report = (
        f"═══ CONTROLPLANE FLAG REPORT ═══\n"
        f"Flag ID        : {flag_id}\n"
        f"Timestamp      : {ts}\n"
        f"Use Case       : {row['use_case']}   Geography: {row['geography']}\n"
        f"Session        : {row.get('session_id', 'N/A')}\n"
        f"───────────────────────────────\n"
        f"Performance    : {row['performance_risk_score']:.1f}/100\n"
        f"Cost           : {row['cost_risk_score']:.1f}/100\n"
        f"Responsibility : {row['responsibility_risk_score']:.1f}/100\n"
        f"Composite      : {row['composite_risk_score']:.1f}/100\n"
        f"───────────────────────────────\n"
        f"Decision       : {row['decision']} ({row['decision_confidence']:.0f}% confident)\n"
        f"Action Taken   : {get_response_action_label(row['decision'])}\n"
        f"───────────────────────────────\n"
        f"Rationale:\n  - " + "\n  - ".join(reasons) + "\n"
        f"═════════════════════════════════\n"
    )
    return flag_id, report


def process_flags(df):
    """Return a list of flag dicts for every response that wasn't a plain ALLOW."""
    flags = []
    for _, row in df.iterrows():
        if row["decision"] != "ALLOW":
            flag_id, report = generate_flag_report(row)
            flags.append({
                "flag_id": flag_id,
                "timestamp": row.get("timestamp", datetime.datetime.now().isoformat()),
                "use_case": row["use_case"],
                "geography": row["geography"],
                "decision": row["decision"],
                "composite_risk_score": row["composite_risk_score"],
                "decision_confidence": row["decision_confidence"],
                "report": report,
                "reviewer_verdict": None,   # "confirmed" | "false_positive" — set via feedback
                "gt_hallucinated": row.get("gt_hallucinated", 0),
                "gt_responsibility_violation": row.get("gt_responsibility_violation", 0),
                "gt_cost_anomaly": row.get("gt_cost_anomaly", 0),
            })
    return flags


def record_feedback(flags, flag_id, verdict):
    """Log a human reviewer's verdict on a flag in place. verdict: 'confirmed' | 'false_positive'."""
    for f in flags:
        if f["flag_id"] == flag_id:
            f["reviewer_verdict"] = verdict
            break
    return flags


def feedback_summary(flags):
    """Roll up reviewer feedback into a running false-positive estimate."""
    reviewed = [f for f in flags if f["reviewer_verdict"] is not None]
    if not reviewed:
        return {"reviewed": 0, "confirmed": 0, "false_positive": 0, "fp_rate_pct": None}
    confirmed = sum(1 for f in reviewed if f["reviewer_verdict"] == "confirmed")
    false_pos = sum(1 for f in reviewed if f["reviewer_verdict"] == "false_positive")
    return {
        "reviewed": len(reviewed),
        "confirmed": confirmed,
        "false_positive": false_pos,
        "fp_rate_pct": round(100 * false_pos / len(reviewed), 1),
    }
