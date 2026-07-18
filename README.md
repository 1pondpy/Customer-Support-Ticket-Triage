# Customer Support Ticket Triage

## Overview

Customer Support Ticket Triage is an AI-ready backend service designed to classify customer support tickets and generate structured responses.

This iteration (**v0.1.0 – Walking Skeleton**) focuses on delivering a working backend API, system architecture, and data validation without integrating a real Large Language Model (LLM).

---

## Agent Design

The current implementation uses a **Mock Triage Agent** to simulate future AI behavior while keeping the system functional.

### Responsibilities

- Receive customer support tickets
- Validate requests using Pydantic schemas
- Perform mock ticket classification
- Generate predefined structured responses
- Return JSON output

### Current Workflow

```text
Client
   │
POST /tickets/triage
   │
FastAPI Router
   │
Pydantic Validation
   │
Mock Triage Agent
   │
Structured JSON Response
```

### Future Architecture

The Mock Agent will later be replaced by an AI-powered workflow.

```text
Client
   │
FastAPI
   │
Triage Agent
   ├── Retrieve Knowledge (RAG)
   ├── Generate Response (LLM)
   └── Judge Response Quality
```

This modular architecture allows future AI components to be integrated without changing the public API.

---

## Features

- FastAPI backend
- Pydantic request/response schemas
- Mock ticket classification
- Structured JSON responses
- Interactive Swagger UI (`/docs`)
- RESTful API endpoint

---

## Project Structure

```text
customer-support-ticket-triage/
│
├── app/
│   ├── api/
│   ├── models/
│   ├── schemas/
│   └── main.py
│
├── data/
│   ├── sample.csv
│   └── twcs.csv
│
├── .env.example
├── requirements.txt
└── README.md
```

---

## Environment Configuration

Configuration values are isolated from the application source code.

- `.env.example` provides the required environment variable template.
- `.env` should remain local and is excluded using `.gitignore`.
- Future API keys (OpenAI, vector database, etc.) will be stored in `.env`.

---

## Repository Hygiene

The repository includes only lightweight sample datasets.

```text
data/
├── sample.csv
└── twcs.csv
```

Both datasets are trimmed to approximately the first **1,000 rows** to keep repository size manageable.

---

## Routing & Triage Design Matrix

### Priority & Escalation Logic

- **P1**
  - Premium customers
  - Critical or urgent issues
  - Automatically escalated

- **P2–P4**
  - Standard tickets
  - Routed based on detected category

### Queue Assignment

| Category | Assigned Queue |
|----------|----------------|
| Technical | `tech_support_queue` |
| Billing | `billing_default_queue` |
| General | `general_support_queue` |

---

## API Endpoint

### POST `/tickets/triage`

Accepts a customer support ticket and returns a structured triage result.

### Sample Request

```json
{
  "subject": "Urgent: Billing discrepancy on my premium account",
  "body": "I noticed an incorrect charge on my invoice this month. Please resolve this immediately.",
  "customer_tier": "premium",
  "metadata": {
    "source": "twitter",
    "browser": "chrome"
  }
}
```

### Sample Response

```json
{
  "category": "billing",
  "sub_intent": "dispute_charge",
  "priority": "P1",
  "assigned_queue": "billing_emergency_queue",
  "industry": "e-commerce",
  "suggested_macro_id": "macro_billing_premium_refund",
  "internal_notes": "Mocked: Premium customer billing conflict escalated for manual review.",
  "policy_citations": [
    "policy_billing_v2_section3"
  ],
  "confidence": 0.95,
  "escalate": true
}
```

---

## Sample Execution Test (API Contract Verification)

The following example demonstrates a successful execution of the `POST /tickets/triage` endpoint using the current mock implementation. This verifies that the API contract defined by the Pydantic schemas is correctly processed and returns the expected structured JSON response.

### Request

```json
{
  "subject": "Inbound Tweet Triage Test",
  "body": "@AppleSupport causing the reply to be disregarded and the tapped notification under the keyboard is opened",
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

### Response

**HTTP Status:** `200 OK`

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

### Verification

- Request payload successfully validated using **Pydantic**.
- The API returned **HTTP 200 OK**.
- The Mock Triage Agent generated a structured response following the `TriageResult` schema.
- The endpoint successfully demonstrates the expected API contract for future AI integration.

---

## Running the Project

### Install dependencies

```bash
pip install -r requirements.txt
```

### Start the server

```bash
uvicorn app.main:app --reload
```

### Open Swagger UI

```text
http://127.0.0.1:8000/docs
```

---

## Current Limitations

- No real LLM integration
- No Retrieval-Augmented Generation (RAG)
- No multi-agent orchestration
- No response evaluation (Judge Agent)
- Mock responses only

These features will be implemented in future iterations.

---

## Version

**v0.1.0 — Walking Skeleton**

---

## Authors

**Group 4 — SCI19 3914 & SCI19 3934**

| Student ID | Name |
|------------|------|
| B6722241 | นางสาวลลิตา ร่มลำดวน |
| B6735036 | นายพัชรพล ลาภชุ่มศรี |
| B6739324 | นายเจษฎา โพธิ์ราช |
| B6739393 | นางสาวนิจจารีย์ ระดาบุตร |