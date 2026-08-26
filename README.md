# AI Adaptive XDR – Civic Cyber Shield

## Municipal Extended Detection & Response System

### Problem Statement

Municipal governments are increasingly targeted by sophisticated cyber threats — ransomware, phishing campaigns, credential stuffing, and insider threats — yet most lack the budget and personnel for enterprise-grade Security Operations Centers (SOC). City services like water utilities, public safety dispatch, and financial systems are critical infrastructure that demand continuous protection.

**Civic Cyber Shield** is an AI-powered Extended Detection and Response (XDR) prototype designed specifically for municipal cyber defense. It provides automated threat detection, risk correlation, and incident response simulation — giving small IT teams the situational awareness of a full SOC.

### System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Streamlit Dashboard                     │
│  ┌──────┐ ┌──────────┐ ┌──────────┐ ┌───────────────┐  │
│  │ KPIs │ │Risk Gauge│ │Trend Line│ │ Alert Table    │  │
│  └──────┘ └──────────┘ └──────────┘ └───────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │         Attack Simulation Console                  │  │
│  └───────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Anomaly    │ │   Phishing   │ │     Risk     │
│  Detection   │ │  Detection   │ │ Correlation  │
│(Isol. Forest)│ │(TF-IDF + LR) │ │   Engine     │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       └────────────────┼────────────────┘
                        ▼
              ┌──────────────────┐
              │    Incident      │
              │   Response       │
              │   Simulation     │
              └──────────────────┘
                        ▲
                        │
              ┌──────────────────┐
              │   Synthetic Log  │
              │    Generator     │
              └──────────────────┘
```

### ML Models

| Model | Algorithm | Purpose |
|-------|-----------|---------|
| Anomaly Detector | Isolation Forest | Detects unusual login patterns, off-hours access, high failed attempts |
| Phishing Classifier | TF-IDF + Logistic Regression | Classifies emails as phishing or legitimate |
| Risk Engine | Weighted scoring formula | Combines anomaly, phishing, and IP risk into unified score |

**Risk Formula:**
```
risk_score = 0.5 × anomaly_score + 0.3 × phishing_probability + 0.2 × ip_risk_score
```

### How to Run

```bash
# 1. Clone / navigate to the project
cd adaptive-xdr

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch the dashboard
streamlit run app.py
```

The dashboard opens at `http://localhost:8501`. Click the simulation buttons to inject attack scenarios and watch the system respond in real time.

### Features

- **Real-time KPI Dashboard** — Active threats, average risk score, incident count
- **AI Anomaly Detection** — Isolation Forest trained on baseline municipal telemetry
- **Phishing Detection** — NLP-based email classification with probability scoring
- **Risk Correlation** — Multi-signal fusion into LOW/MEDIUM/HIGH/CRITICAL levels
- **Automated Response** — Simulated account locks, device isolation, alert generation
- **Attack Simulation** — One-click phishing, credential breach, and insider threat scenarios
- **Incident Reports** — Detailed AI-generated incident summaries

### Future Scope

- **Real SIEM Integration** — Ingest logs from Splunk, Elastic, or Microsoft Sentinel
- **SOAR Playbooks** — Automated response orchestration with real containment actions
- **Threat Intelligence Feeds** — Live IOC correlation from MISP, VirusTotal, AbuseIPDB
- **Network Traffic Analysis** — Deep packet inspection and lateral movement detection
- **User Behavior Analytics (UBA)** — Long-term behavioral profiling with LSTM models
- **Multi-tenant Support** — Dashboard per department with role-based access
- **Compliance Reporting** — Automated NIST CSF and CIS Controls mapping
- **Mobile Alerting** — Push notifications to on-call responders

---

# ControlPlane.ai — Round 2 Extension ("AIRAVAT for AI")

## Accenture Innovation Challenge 2026 — Problem Track 1

### Recap

Round 1 proposed a simple idea: a "confidently wrong" AI response is *structurally*
an anomaly, the same way malicious traffic is an anomaly on a network — so the same
detection engine behind **AIRAVAT XDR** (above) could be re-pointed from network
telemetry at AI response streams. This folder is that re-pointing, built out into a
working prototype.

### System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                 Streamlit Dashboard (controlplane_app.py)         │
│  ┌──────┐ ┌───────────┐ ┌────────────┐ ┌──────────────────────┐ │
│  │ KPIs │ │ Per-Dim   │ │ Composite  │ │ Decision Ledger +     │ │
│  │      │ │ Risk Bars │ │ Risk Trend │ │ Audit Trail/Feedback  │ │
│  └──────┘ └───────────┘ └────────────┘ └──────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │        Governance Panel (use case / geography / sensitivity)│ │
│  └────────────────────────────────────────────────────────────┘ │
└───────────────────────────┬────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌───────────────┐  ┌─────────────────┐  ┌──────────────────────┐
│  Performance  │  │       Cost       │  │    Responsibility     │
│   Detector    │  │     Monitor      │  │      Detector          │
│(Isol. Forest  │  │ (use-case-aware  │  │ (TF-IDF+LR classifier  │
│ on confidence/│  │  baseline vs.    │  │  + rule-based PII/     │
│ grounding gap)│  │  token/latency)  │  │  secret regex scanner) │
└───────┬───────┘  └────────┬─────────┘  └───────────┬───────────┘
        └───────────────────┼────────────────────────┘
                            ▼
              ┌──────────────────────────┐
              │   Policy Engine           │
              │ (weighted by use case +   │
              │  geography → tiered       │
              │  ALLOW/EDIT/FLAG/BLOCK)   │
              └─────────────┬─────────────┘
                            ▼
              ┌──────────────────────────┐
              │  Audit Trail + Feedback   │
              │  Loop (flag reports,      │
              │  reviewer verdicts)       │
              └─────────────┬─────────────┘
                            ▲
                            │
              ┌──────────────────────────┐
              │  AI Response Simulator    │
              │ (3 use cases, hidden      │
              │  ground-truth labels)     │
              └──────────────────────────┘
```

### New Modules (this round)

| Module | Purpose |
|---|---|
| `ai_response_simulator.py` | Synthetic enterprise AI interactions across 3 use cases (customer support, internal copilot, decision support) with hidden ground-truth labels, used only to *measure* detector accuracy — never fed to the detectors |
| `performance_detector.py` | Isolation Forest — the same algorithm as AIRAVAT XDR's network anomaly detector — re-pointed at confidence/grounding features to catch "confidently wrong" responses |
| `cost_monitor.py` | Learns a separate baseline **per use case**, since a customer bot and a decision-support tool have different latency/cost budgets |
| `responsibility_detector.py` | TF-IDF + Logistic Regression (same pattern as the phishing classifier), retrained on biased/unsafe/PII-leaking text, combined with a rule-based PII/secret regex scanner as a hard floor |
| `policy_engine.py` | Governance layer: weights differ by use case, a geography multiplier tightens the Responsibility threshold for stricter regimes (e.g. EU), tiered decisions (ALLOW/AUTO_EDIT/FLAG_FOR_REVIEW/BLOCK), and a single sensitivity dial exposing the alert-fatigue-vs-liability tradeoff |
| `audit_trail.py` | Structured, explainable flag reports behind every non-ALLOW decision, plus a minimal reviewer-feedback capture point (confirmed / false positive) — the seed of a real feedback loop |
| `metrics.py` | Measures actual false-positive/false-negative rates against the simulator's hidden ground truth — not a claimed number |
| `controlplane_app.py` | The Streamlit dashboard tying it all together |

### How to Run

```bash
pip install -r requirements.txt
streamlit run controlplane_app.py
```

Opens at `http://localhost:8501`. Use the "Inject Test Responses" console to fire a
confidently-wrong response, a cost spike, or a bias/PII leak, and watch the Governance
Panel, Decision Ledger, and Audit Trail react live.

### How This Maps to the Round 2 Brief

| Brief asks about... | Where it's addressed |
|---|---|
| Different use cases have different risk/latency tolerance | `cost_monitor.py` learns a baseline **per use case**; `policy_engine.py` weights dimensions differently per use case |
| Bias/hallucination/privacy risks overlap | `responsibility_detector.py`'s rule-based PII scanner and ML classifier can co-fire independently of the performance detector on the same response |
| No reliable real-time ground truth to check claims against | Performance detection uses a *proxy* (confidence vs. self-consistency vs. retrieval-grounding gap), not a claim of verified truth — the dashboard reports this as a risk score, not a fact-check |
| Over-flagging vs under-flagging tradeoff | The sensitivity slider in the Governance Panel directly exposes this tradeoff, and `metrics.py` reports the real FP/FN rate at the current setting |
| Regulatory expectations differ by geography | `GEOGRAPHY_RESPONSIBILITY_MULTIPLIER` in `policy_engine.py` — EU responses are held to a stricter Responsibility threshold than US/IN |
| Enterprises consume models via API, not full internals | Every detector works purely on input/output text + response metadata — no model-internals access assumed anywhere in the pipeline |
| Governance / configurable policy layer with audit trail | `policy_engine.py` + `audit_trail.py` — every flag has a structured, reviewable rationale |
| Feedback loops | `audit_trail.record_feedback()` + `feedback_summary()` — reviewer verdicts are captured and rolled into a live FP-rate estimate (full retraining loop noted as future scope, not faked here) |
| Metrics & monitoring, FP/FN rates | `metrics.py` — real numbers computed against the simulator's hidden ground truth, shown live in the KPI row |

### Honest Limitations (stated, not hidden)

- The Performance detector currently favors **recall over precision** (it catches every
  injected hallucination in testing, at the cost of flagging some genuinely fine
  responses too) — this is the over-flagging/under-flagging tradeoff the brief asks
  teams to tune deliberately, and it's exactly why the sensitivity dial exists rather
  than a single hardcoded threshold.
- Added-latency figures are a stated assumption (lightweight feature math + a small
  forest + a linear classifier), not a benchmarked production number — flagged as such
  in `metrics.py` rather than presented as a measured result.
- The feedback loop captures reviewer verdicts and reports a live false-positive rate
  from them, but does not yet retrain the detectors — that's future scope, not glossed
  over as done.

### Future Scope (Round 2 → beyond)

- Feed reviewer-confirmed/false-positive verdicts back into detector retraining
- Replace the synthetic response generator with a real LLM call wrapper (OpenAI/Anthropic/local model) so the checker sits inline in an actual request path
- Add an "AI-as-judge" secondary check for borderline FLAG_FOR_REVIEW cases
- Real latency benchmarking under production-like load
