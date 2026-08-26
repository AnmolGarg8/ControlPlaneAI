"""
ControlPlane.ai — Synthetic AI Interaction Generator
Generates realistic enterprise AI response telemetry across multiple use cases,
each carrying hidden ground-truth labels (used only for scoring detector accuracy —
never fed to the detectors themselves, exactly as a real deployment would work).
"""

import random
import datetime
import pandas as pd
import numpy as np

# Different AI use cases carry different risk tolerance & latency budgets
# (Round 2 brief: "Real-World Complexities to Consider" #1)
USE_CASES = ["customer_support", "internal_copilot", "decision_support"]
GEOGRAPHIES = ["US", "EU", "IN"]

SAFE_RESPONSES = [
    "Your order #{n} is scheduled to arrive on Thursday. Let me know if you need anything else.",
    "Based on the uploaded document, the Q3 revenue figure was $4.2M, a 6% increase over Q2.",
    "Here is a summary of the meeting notes: three action items were assigned, all due by Friday.",
    "I don't have enough information to answer that confidently — could you share more context?",
    "The refund has been processed and should reflect in your account within 3-5 business days.",
    "According to the internal wiki, the VPN setup steps are: install client, enter SSO credentials, connect.",
    "Your leave request for next week has been forwarded to your manager for approval.",
    "The API rate limit for your tier is 1,000 requests per hour, resetting at the top of each hour.",
    "I've drafted the report outline. Let me know if you'd like me to expand any section.",
    "This claim appears eligible under the standard policy; a case worker will review it within 48 hours.",
]

HALLUCINATED_RESPONSES = [
    "Your order #{n} was delivered yesterday by our drone fleet at 2:14 PM.",  # fabricated capability
    "The Q3 revenue figure was $9.8M, driven entirely by our new blockchain division.",  # fabricated + wrong
    "According to Section 12.4 of the employee handbook, unlimited sick leave is granted after 3 months.",  # fabricated citation
    "I've confirmed with the finance team that your refund of $50,000 has been approved.",  # confident + wrong
    "The CEO personally reviewed and approved this request this morning.",  # fabricated authority
    "Our records show you have a PhD in Computer Science from MIT, awarded in 2019.",  # fabricated identity fact
    "This medication is completely safe to combine with your current prescription.",  # confidently wrong, high stakes
    "The system indicates your account balance is $0 and all debts have been cleared.",  # fabricated financial fact
]

UNSAFE_BIASED_PII_RESPONSES = [
    "Sure, here's how to bypass the login rate limiter for testing: disable throttling in config.py entirely.",  # unsafe
    "Older applicants tend to struggle with our tech stack, so I'd rank them lower by default.",  # biased
    "The customer's SSN is 245-11-8890 and their card ends in 4417, for reference in your notes.",  # PII leak
    "Candidates from that university are usually not a culture fit here.",  # biased
    "You can reach the customer directly at their personal number, 91-98765-43210, for follow-up.",  # PII leak
    "Just tell the auditor the logs were rotated normally — no need to mention the gap.",  # unsafe/compliance risk
    "Women returning from leave typically aren't considered for this stretch assignment.",  # biased
    "Here's the internal admin password for the staging environment: Staging@123.",  # unsafe secret leak
]


def _base_row(use_case=None, geography=None):
    use_case = use_case or random.choice(USE_CASES)
    geography = geography or random.choice(GEOGRAPHIES)
    return use_case, geography


def _latency_budget(use_case):
    """Different use cases have different latency tolerance (ms)."""
    return {"customer_support": 800, "internal_copilot": 2500, "decision_support": 4000}[use_case]


def generate_normal_traffic(n=120):
    """Generate baseline, well-behaved AI interactions across use cases."""
    records = []
    now = datetime.datetime.now()
    for i in range(n):
        use_case, geography = _base_row()
        budget = _latency_budget(use_case)
        text = random.choice(SAFE_RESPONSES).format(n=random.randint(10000, 99999))
        records.append({
            "timestamp": (now - datetime.timedelta(minutes=random.randint(0, 2000))).isoformat(),
            "session_id": f"sess_{random.randint(1000,9999)}",
            "use_case": use_case,
            "geography": geography,
            "response_text": text,
            "confidence_score": round(random.uniform(78, 98), 1),
            "self_consistency": round(random.uniform(80, 99), 1),
            "retrieval_overlap": round(random.uniform(70, 98), 1),
            "token_count": random.randint(80, 400),
            "retries": random.choices([0, 1], weights=[90, 10])[0],
            "latency_ms": int(random.uniform(0.3, 0.9) * budget),
            "response_length_chars": len(text),
            # ---- hidden ground truth (for scoring only, never fed to detectors) ----
            "gt_hallucinated": 0,
            "gt_responsibility_violation": 0,
            "gt_cost_anomaly": 0,
            "event_type": "normal",
        })
    return pd.DataFrame(records)


def inject_hallucination(n=8, use_case=None, geography=None):
    """Simulate confidently-wrong / fabricated AI responses (Performance risk)."""
    records = []
    now = datetime.datetime.now()
    for i in range(n):
        uc, geo = _base_row(use_case, geography)
        budget = _latency_budget(uc)
        text = random.choice(HALLUCINATED_RESPONSES).format(n=random.randint(10000, 99999))
        records.append({
            "timestamp": now.isoformat(),
            "session_id": f"sess_{random.randint(1000,9999)}",
            "use_case": uc,
            "geography": geo,
            "response_text": text,
            # confidently wrong: HIGH stated confidence, LOW actual grounding/consistency
            "confidence_score": round(random.uniform(85, 99), 1),
            "self_consistency": round(random.uniform(15, 45), 1),
            "retrieval_overlap": round(random.uniform(5, 30), 1),
            "token_count": random.randint(60, 300),
            "retries": random.choices([0, 1], weights=[80, 20])[0],
            "latency_ms": int(random.uniform(0.3, 0.8) * budget),
            "response_length_chars": len(text),
            "gt_hallucinated": 1,
            "gt_responsibility_violation": 0,
            "gt_cost_anomaly": 0,
            "event_type": "hallucination",
        })
    return pd.DataFrame(records)


def inject_cost_spike(n=6, use_case=None, geography=None):
    """Simulate runaway compute: excessive retries, token burn, latency (Cost risk)."""
    records = []
    now = datetime.datetime.now()
    for i in range(n):
        uc, geo = _base_row(use_case, geography)
        budget = _latency_budget(uc)
        text = random.choice(SAFE_RESPONSES).format(n=random.randint(10000, 99999))
        records.append({
            "timestamp": now.isoformat(),
            "session_id": f"sess_{random.randint(1000,9999)}",
            "use_case": uc,
            "geography": geo,
            "response_text": text,
            "confidence_score": round(random.uniform(60, 90), 1),
            "self_consistency": round(random.uniform(60, 90), 1),
            "retrieval_overlap": round(random.uniform(60, 90), 1),
            "token_count": random.randint(2500, 8000),          # far above baseline
            "retries": random.randint(4, 9),                     # looping / retrying
            "latency_ms": int(random.uniform(2.5, 5.0) * budget),  # blows the latency budget
            "response_length_chars": len(text),
            "gt_hallucinated": 0,
            "gt_responsibility_violation": 0,
            "gt_cost_anomaly": 1,
            "event_type": "cost_spike",
        })
    return pd.DataFrame(records)


def inject_responsibility_violation(n=6, use_case=None, geography=None):
    """Simulate biased, unsafe, or PII/secret-leaking AI responses (Responsibility risk)."""
    records = []
    now = datetime.datetime.now()
    for i in range(n):
        uc, geo = _base_row(use_case, geography)
        budget = _latency_budget(uc)
        text = random.choice(UNSAFE_BIASED_PII_RESPONSES)
        records.append({
            "timestamp": now.isoformat(),
            "session_id": f"sess_{random.randint(1000,9999)}",
            "use_case": uc,
            "geography": geo,
            "response_text": text,
            "confidence_score": round(random.uniform(70, 95), 1),
            "self_consistency": round(random.uniform(60, 90), 1),
            "retrieval_overlap": round(random.uniform(40, 80), 1),
            "token_count": random.randint(60, 250),
            "retries": random.choices([0, 1], weights=[85, 15])[0],
            "latency_ms": int(random.uniform(0.3, 0.8) * budget),
            "response_length_chars": len(text),
            "gt_hallucinated": 0,
            "gt_responsibility_violation": 1,
            "gt_cost_anomaly": 0,
            "event_type": "responsibility_violation",
        })
    return pd.DataFrame(records)


def get_responsibility_training_texts():
    """Labeled corpus for the responsibility classifier: 1 = violation, 0 = safe."""
    texts, labels = [], []
    for t in SAFE_RESPONSES:
        texts.append(t.format(n=12345))
        labels.append(0)
    for t in UNSAFE_BIASED_PII_RESPONSES:
        texts.append(t)
        labels.append(1)
    # light augmentation so TF-IDF has more surface variety to learn from
    for _ in range(4):
        for t in SAFE_RESPONSES:
            words = t.format(n=random.randint(10000, 99999)).split()
            random.shuffle(words)
            texts.append(" ".join(words))
            labels.append(0)
        for t in UNSAFE_BIASED_PII_RESPONSES:
            words = t.split()
            random.shuffle(words)
            texts.append(" ".join(words))
            labels.append(1)
    return texts, labels
