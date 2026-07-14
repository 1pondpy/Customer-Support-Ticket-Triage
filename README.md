# Customer-Support-Ticket-Triage
### 🚀 Group 4 | SCI19 3914 & SCI19 3934

### ระบบคัดกรอง แยกประเภท และจัดลำดับความสำคัญของ Ticket

### Members :
#### B6722241  นางสาวลลิตา ร่มลำดวน
#### B6735036  นายพัชรพล ลาภชุ่มศรี
#### B6739324  นายเจษฎา โพธิ์ราช
#### B6739393  นางสาวนิจจารีย์ ระดาบุตร

# Customer Support Ticket Triage

## Overview

Customer Support Ticket Triage is an AI-ready backend service designed to classify customer support tickets and generate structured responses. This iteration (`v0.1.0`) implements a **Walking Skeleton**, focusing on a working API and system architecture without integrating a real Large Language Model (LLM).

---

## Agent Design

The system currently uses a **Mock Triage Agent**.

The purpose of the Mock Agent is to simulate the behavior of the future AI agent while keeping the system functional during the first iteration.

### Current Responsibilities

* Receive a support ticket request
* Validate the request using Pydantic schemas
* Execute mock classification logic
* Generate a predefined response
* Return a structured JSON response

### Current Workflow

```
Client
   │
POST /triage
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

In future iterations, the Mock Agent will be replaced by an AI-powered workflow.

```
Client
   │
FastAPI
   │
Triage Agent
   ├── Retrieve Knowledge (RAG)
   ├── Generate Response (LLM)
   └── Judge Response Quality
```

This modular design allows the backend to evolve from a simple mock implementation into a complete Retrieval-Augmented Generation (RAG) system without changing the public API.

---

## Current Features

* FastAPI backend
* Pydantic request/response schemas
* Mock ticket classification
* Structured JSON responses
* Interactive Swagger documentation (`/docs`)

---

## Current Limitations

* No real LLM integration
* No Retrieval-Augmented Generation (RAG)
* No multi-agent orchestration
* No Judge component
* Mock responses only

These components will be implemented in later iterations.
