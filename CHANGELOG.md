# Changelog

All notable changes to the Customer Support Ticket Triage System will be documented in this file.

## [v1.0.0] - Demo Day Release (2026-03-30)

### Added
- **Interactive Operational Dashboard:** Deployed at `/ui` supporting Single Triage, Native JSON Batch File Upload, Quick Presets, and Benchmark Reporting.
- **Automated API Benchmark (`POST /evaluate`):** Native endpoint measuring pure inference latency across the 30-case Gold Dataset.
- **Security Guardrails & Sanitization:** Pre-processor detecting adversarial prompt injection payloads and redacting sensitive PII from audit logs.
- **Prompt Versioning Registry:** Centralized semantic version tracking in `app/services/prompt_registry.py` (`v0.1.0` through `v1.0.0`).
- **Grounding Judge Agent:** Automated layer verifying citations against retrieved policy documents.

### Changed
- Scaled evaluation benchmark from 6 cases to the full 30-case Gold Dataset (`data/gold_dataset.json`).
- Transitioned inference pipeline from single LLM to Mixture-of-Experts (MoE) 8-domain delegation.

### Performance Benchmark
- Category Accuracy: **96.7%** (Pass Bar: ≥85.0%)
- Priority Accuracy (±1 Level): **96.7%** (Pass Bar: ≥80.0%)
- Escalation Recall: **100.0%** (Safety Target: 100.0%)

---

## [v0.2.0] - AI Core Release (2026-03-01)

### Added
- Live LLM routing integration using Groq inference engine.
- Keyword-based RAG chunking service in `app/services/rag_service.py`.
- Debug retrieval endpoint `GET /policies/search`.
- Initial 6-case Gold Dataset and `evaluate.py` test harness.

---

## [v0.1.0] - Walking Skeleton Release (2026-02-10)

### Added
- FastAPI service baseline with mock response endpoints.
- Pydantic schema contracts: `TicketInput` and `TriageResult`.
- Initial repository hygiene: `README.md`, `.env.example`, and directory structure.