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

# Sample Requests & Responses

The following examples demonstrate how the API processes different customer support scenarios and returns structured triage results.

---

## Example 1 — Technical Bug Report

### Request (`TicketInput`)

```json
{
  "subject": "App Interaction & Keyboard Bug",
  "body": "@AppleSupport causing the reply to be disregarded and the tapped notification under the keyboard is opened😡😡😡",
  "customer_tier": "free",
  "metadata": {
    "tweet_id": "119237",
    "author_id": "105834",
    "inbound": "TRUE",
    "created_at": "Wed Oct 11 06:55:44 +0000 2017",
    "response_tweet_id": "119236",
    "in_response_to_tweet_id": ""
  }
}
```

### Response (`TriageResult`)

```json
{
  "category": "technical",
  "sub_intent": "app_crash_bug",
  "priority": "P3",
  "assigned_queue": "tech_support_queue",
  "suggested_macro_id": "macro_ios_keyboard_troubleshoot",
  "internal_notes": "User experiencing UI overlay bug with keyboard notifications. Route to Tier 1 Technical Support.",
  "policy_citations": [
    "TECH-POLICY-V1-BUG-REPORT"
  ],
  "confidence": 0.92,
  "escalate": false
}
```

---

## Example 2 — Customer Support Channel Failure

### Request (`TicketInput`)

```json
{
  "subject": "Live Chat Error & Unresponsive Support Line",
  "body": "@VirginTrains I still haven't heard & the number I'm directed to by phone is a dead end & the live chat doesn't work. Can someone call me?",
  "customer_tier": "pro",
  "metadata": {
    "tweet_id": "119242",
    "author_id": "105836",
    "inbound": "TRUE",
    "created_at": "Tue Oct 10 15:09:00 +0000 2017",
    "response_tweet_id": "119240",
    "in_response_to_tweet_id": "119246"
  }
}
```

### Response (`TriageResult`)

```json
{
  "category": "technical",
  "sub_intent": "service_channel_down",
  "priority": "P2",
  "assigned_queue": "tech_support_queue",
  "suggested_macro_id": "macro_callback_request_pro",
  "internal_notes": "Pro user unable to reach support via phone/live chat. High risk of customer dissatisfaction.",
  "policy_citations": [
    "SLA-POLICY-SEC2-PRO-CALLBACK"
  ],
  "confidence": 0.94,
  "escalate": false
}
```

---

## Verification Highlights

Both examples demonstrate that:

- Input payloads are successfully validated by the `TicketInput` schema.
- The API returns responses conforming to the `TriageResult` schema.
- Different ticket types are routed to the appropriate support queue.
- Customer tier affects priority and macro selection.
- The API contract remains consistent across multiple support scenarios.

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