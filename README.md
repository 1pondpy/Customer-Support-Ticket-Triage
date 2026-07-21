# Customer Support Ticket Triage

> **Version:** v0.1.0 – Walking Skeleton & Base RAG

Customer Support Ticket Triage is an AI-ready backend service designed to classify customer support tickets, retrieve relevant Knowledge Base policies, and generate structured triage responses.

This first iteration delivers a functional backend API with request validation, modular architecture, environment configuration, and a Retrieval-Augmented Generation (RAG) policy chunking service.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Project Structure](#project-structure)
- [Workflow](#workflow)
- [Environment Configuration](#environment-configuration)
- [Repository Hygiene](#repository-hygiene)
- [Routing & Triage Design](#routing--triage-design)
- [API Endpoint](#api-endpoint)
- [Running the Project](#running-the-project)
- [Current Limitations](#current-limitations)
- [Version](#version)
- [Authors](#authors)

---

# Overview

The system is designed as a modular backend that can later integrate Large Language Models (LLMs) without changing the public API.

Current implementation includes:

- FastAPI REST API
- Pydantic validation
- Mock Triage Agent
- Policy Chunking Service
- Environment configuration
- Swagger documentation

---

# Architecture

## Current Architecture

```
Client
   │
POST /tickets/triage
   │
FastAPI Router
   │
Pydantic Validation (TicketInput)
   │
Mock Triage Service
        +
RAG Policy Chunking Service
   │
Structured JSON Response (TriageResult)
```

---

## Future Architecture

The current Mock Triage Agent will be replaced by an AI-powered multi-agent workflow.

```
Client
   │
FastAPI
   │
Triage Agent
   ├── Retrieve Knowledge (RAG / Vector DB)
   ├── Generate Response (LLM)
   └── Judge Response Quality (LLM-as-a-Judge)
```

This architecture enables future AI components to be integrated without changing the API contract.

---

# Features

- FastAPI asynchronous backend
- REST API endpoint
- Pydantic request/response validation
- Environment configuration using `python-dotenv`
- Secure API key management
- Policy ingestion service
- Text chunking for RAG
- Prompt template with delimiters
- Interactive Swagger UI
- Verified API contract
- Modular service architecture

---

# Project Structure

```
customer-support-ticket-triage/
│
├── app/
│   ├── api/
│   │   └── routes.py
│   │
│   ├── services/
│   │   ├── triage_service.py
│   │   └── rag_service.py
│   │
│   ├── schemas.py
│   ├── config.py
│   └── main.py
│
├── data/
│   ├── policies/
│   │   ├── routing_policy.txt
│   │   ├── sla_policy.txt
│   │   ├── billing_policy.txt
│   │   └── technical_policy.txt
│   │
│   ├── prompt_template.txt
│   └── sample.csv
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

# Workflow

Current processing pipeline:

```
Receive Ticket
        │
        ▼
Validate Request
(Pydantic)
        │
        ▼
Policy Chunk Retrieval
(RAG Service)
        │
        ▼
Mock Ticket Classification
        │
        ▼
Generate Structured Response
(TriageResult)
```

---

# Environment Configuration

Application configuration is isolated from the source code.

### `.env.example`

```env
OPENAI_API_KEY=
GEMINI_API_KEY=
```

### Setup

Copy:

```bash
cp .env.example .env
```

Then configure your API keys.

Configuration values are centrally loaded by:

```
app/config.py
```

---

# Repository Hygiene

The repository includes processed policy documents and sample datasets.

```
data/
├── policies/
└── sample.csv
```

The dataset has been trimmed and validated to maintain a manageable repository size while preserving compatibility with ticket metadata.

---

# Routing & Triage Design

## Priority & Escalation

| Priority | Description | Escalation |
|-----------|-------------|------------|
| P1 | Enterprise customer with outage, security issue, or critical bug | ✅ Yes |
| P2–P4 | Standard support requests | No |

---

## Queue Assignment

| Category | Queue |
|-----------|----------------------------|
| Technical | tech_support_queue |
| Billing | billing_default_queue |
| Billing (Emergency) | billing_emergency_queue |
| General | general_support_queue |

---

# API Endpoint

## POST `/tickets/triage`

Accepts a customer support ticket and returns a structured triage result.

---

## Sample Request

```json
{
  "subject": "Urgent: Billing discrepancy on my pro account",
  "body": "I noticed an incorrect charge on my invoice this month. Please resolve this immediately.",
  "customer_tier": "pro",
  "metadata": {
    "source": "twitter",
    "browser": "chrome"
  }
}
```

---

## Sample Response

```json
{
  "category": "billing",
  "sub_intent": "double_charge",
  "priority": "P2",
  "assigned_queue": "billing_default_queue",
  "suggested_macro_id": "macro_billing_refund_check",
  "internal_notes": "Mocked: Processed via Triage Service layer.",
  "policy_citations": [
    "SLA-BILLING-V1",
    "REFUND-POLICY-SEC3"
  ],
  "confidence": 0.95,
  "escalate": false
}
```

---

# API Contract Verification

The endpoint has been verified to ensure compatibility with the defined Pydantic schemas.

### Verification Results

- Request successfully validated using `TicketInput`
- Supported customer tiers:
  - `free`
  - `pro`
  - `enterprise`
- Returned **HTTP 200 OK**
- Response conforms to `TriageResult`
- Verified public API contract for future LLM integration

---

# Running the Project

## 1. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 2. Configure environment

```bash
cp .env.example .env
```

Add your API keys.

---

## 3. Start the server

```bash
uvicorn app.main:app --reload
```

---

## 4. Open Swagger UI

```
http://127.0.0.1:8000/docs
```

---

# Current Limitations

The current release uses a mock implementation for ticket classification.

Upcoming improvements include:

- Live LLM integration
- Vector database retrieval
- Semantic search embeddings
- Multi-agent orchestration
- LLM-as-a-Judge evaluation
- Automatic policy ranking

---

# Version

**v0.1.0 — Walking Skeleton & Base RAG**

---

# Authors

**Group 4 — SCI19 3914 & SCI19 3934**

| Student ID | Name |
|------------|--------------------------------|
| B6722241 | นางสาวลลิตา ร่มลำดวน |
| B6735036 | นายพัชรพล ลาภชุ่มศรี |
| B6739324 | นายเจษฎา โพธิ์ราช |
| B6739393 | นางสาวนิจจารีย์ ระดาบุตร |

---

## License

This project was developed for academic purposes as part of the SCI19 3914 & SCI19 3934 coursework.