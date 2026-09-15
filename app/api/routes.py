import json
import time
from typing import Dict, Any
from fastapi import APIRouter, Query, HTTPException
from groq import RateLimitError

from app.schemas.ticket import TicketInput
from app.schemas.triage import TriageResult, BatchTicketInput, BatchTriageResult
from app.services.triage_service import triage_ticket_with_llm
from app.services.rag_service import RAGService

router = APIRouter()

@router.post("/tickets/triage", response_model=TriageResult)
def triage(ticket: TicketInput):
    """Triage a single ticket through the Multi-Agent MoE Pipeline."""
    return triage_ticket_with_llm(ticket)

@router.post("/tickets/triage/batch", response_model=BatchTriageResult)
def triage_batch(batch_input: BatchTicketInput):
    """Process multiple incoming support tickets sequentially."""
    results = [triage_ticket_with_llm(ticket) for ticket in batch_input.tickets]
    return BatchTriageResult(
        total_processed=len(results),
        results=results
    )

@router.get("/policies/search")
def search_policies(query: str = Query(..., description="Query string to search in support policies")):
    """RAG Debug Endpoint for policy chunk inspection."""
    rag = RAGService(policy_dir="data/policies")
    results = rag.search_policies(query)
    return {
        "query": query,
        "results_found": len(results),
        "results": results
    }

@router.post("/evaluate")
def evaluate_routing() -> Dict[str, Any]:
    """
    Automated Evaluation Harness wired as an API endpoint.
    Strictly measures pure inference latency per ticket while safely pacing upstream LLM calls.
    """
    gold_path = "data/gold_dataset.json"
    try:
        with open(gold_path, "r", encoding="utf-8") as f:
            gold_data = json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Gold dataset not found at {gold_path}")

    total_cases = len(gold_data)
    if total_cases == 0:
        raise HTTPException(status_code=400, detail="Gold dataset is empty")

    category_matches = 0
    priority_matches = 0
    queue_matches = 0
    escalation_matches = 0
    pure_latencies = []

    for item in gold_data:
        ticket = TicketInput(**item["input"])
        ground_truth = item["ground_truth"]

        result = None
        max_retries = 3
        backoff_delay = 5.0

        for attempt in range(max_retries):
            try:
                # จับเวลาเฉพาะ Pure Inference Latency ของตัวระบบจริง
                ticket_start = time.time()
                result = triage_ticket_with_llm(ticket)
                ticket_duration = round(time.time() - ticket_start, 2)
                pure_latencies.append(ticket_duration)
                break
            except RateLimitError:
                if attempt < max_retries - 1:
                    time.sleep(backoff_delay)
                    backoff_delay *= 1.5
                else:
                    raise HTTPException(
                        status_code=429,
                        detail="Upstream LLM Rate limit exceeded. Please retry shortly."
                    )

        if result.category.lower() == ground_truth["category"].lower():
            category_matches += 1
        if result.priority == ground_truth["priority"]:
            priority_matches += 1
        if result.assigned_queue == ground_truth["assigned_queue"]:
            queue_matches += 1
        if result.escalate == ground_truth["escalate"]:
            escalation_matches += 1

        # ปล่อยให้ API ภายนอกคืนโควตา TPM ระหว่างชุด โดยไม่นำเวลานี้ไปคิดเป็นความช้าของระบบ
        time.sleep(1.0)

    cat_acc = round((category_matches / total_cases) * 100, 1)
    pri_acc = round((priority_matches / total_cases) * 100, 1)
    que_acc = round((queue_matches / total_cases) * 100, 1)
    esc_acc = round((escalation_matches / total_cases) * 100, 1)
    avg_pure_lat = round(sum(pure_latencies) / len(pure_latencies), 2) if pure_latencies else 0.0

    return {
        "status": "PASSED" if cat_acc >= 85.0 and pri_acc >= 80.0 and esc_acc == 100.0 else "FAILED",
        "benchmark_summary": {
            "total_cases": total_cases,
            "category_accuracy": f"{cat_acc}%",
            "priority_accuracy": f"{pri_acc}%",
            "queue_match_accuracy": f"{que_acc}%",
            "escalation_match_rate": f"{esc_acc}%",
            "average_pure_latency_seconds": avg_pure_lat
        },
        "prd_pass_thresholds": {
            "category_accuracy_threshold": ">= 85.0%",
            "priority_accuracy_threshold": ">= 80.0%",
            "escalation_recall_threshold": "100.0%"
        }
    }