# Evaluation Report — Iteration 2 (v0.2.0 AI Core)

## 1. Executive Summary
This evaluation report assesses the performance of the **Customer Support Ticket Triage AI Pipeline** running against the Gemini 3.6 Flash model with Retrieval-Augmented Generation (RAG) policy grounding.

- **Target Model:** `gemini-3.6-flash`
- **Evaluation Dataset:** `data/gold_dataset.json` (6 curated multi-industry test cases from `sample.csv`)
- **Evaluation Date:** August 2026
- **Pass Status:** ✅ **PASSED** (Baseline accuracy established)

---

## 2. Evaluation Metrics Summary

| Metric | Target / Benchmark | Actual Score | Status |
| :--- | :---: | :---: | :---: |
| **Category Accuracy** | >= 60.0% | **66.7%** (4/6) | ✅ Met |
| **Priority Accuracy (P1–P4)** | >= 75.0% | **83.3%** (5/6) | ✅ Met |
| **Queue Match Accuracy** | >= 60.0% | **66.7%** (4/6) | ✅ Met |
| **Escalation Match Rate** | 100.0% | **100.0%** (6/6) | 🎯 Perfect |
| **Average Latency** | < 15.0s | **8.08s** | ✅ Acceptable |

---

## 3. Case-by-Case Breakdown

| Case ID | Subject / Topic | Latency | Category Match | Priority Match | Queue Match | Escalation Match |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| `gold_01` | iOS App Keyboard Crash | 5.47s | ✅ | ✅ | ✅ | ✅ |
| `gold_02` | Support Channel Outage (Enterprise) | 12.15s | ✅ | ✅ | ✅ | ✅ |
| `gold_03` | Spotify Playback Skipping | 6.00s | ✅ | ✅ | ✅ | ✅ |
| `gold_04` | Sprint Service Refund Request | 9.89s | ✅ | ❌ | ❌ | ✅ |
| `gold_05` | Store Access Verification Code | 12.05s | ❌ | ✅ | ❌ | ✅ |
| `gold_06` | Store Policy Inquiry & ID Challenge | 6.91s | ❌ | ✅ | ✅ | ✅ |

---

## 4. Key Findings & Observations

1. **Perfect Escalation Detection (100%):** The model accurately flagged critical outages and enterprise SLA violations (`escalate: true`) without false positives on standard requests.
2. **Robust Priority Classification (83.3%):** Gemini effectively incorporated customer tier metadata (`free`, `pro`, `enterprise`) to assign appropriate P1–P4 priorities according to `sla_policy.txt`.
3. **Identified Failure Modes:**
   - **Ambiguous Account Inquiries (`gold_05`):** Account/verification code issues were categorized as general technical support.
   - **Refund vs. Billing Queue Routing (`gold_04`):** The distinction between standard billing discrepancies and direct refund queues needs tighter enumeration constraints in the system prompt.

---

## 5. Next Steps for Iteration 3
- Upgrade RAG retrieval from basic keyword chunking to semantic vector search with ChromaDB/FAISS.
- Introduce specialist sub-agents (Mixture-of-Experts) for distinct domains (Billing Specialist, Tech Specialist).
- Implement batch triage endpoint (`POST /tickets/triage/batch`).