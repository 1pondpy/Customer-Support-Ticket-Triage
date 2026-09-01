import json
import time
from app.schemas.ticket import TicketInput
from app.services.triage_service import triage_ticket_with_llm

def run_evaluation():
    # 1. โหลดชุดข้อมูลทองคำ
    with open("data/gold_dataset.json", "r", encoding="utf-8") as f:
        gold_data = json.load(f)

    print(f"🚀 Starting Iteration 3 Multi-Agent Evaluation on {len(gold_data)} Cases...\n")

    total_cases = len(gold_data)
    category_matches = 0
    priority_matches = 0
    queue_matches = 0
    escalation_matches = 0
    latencies = []

    for idx, item in enumerate(gold_data, 1):
        ticket = TicketInput(**item["input"])
        ground_truth = item["ground_truth"]

        start_time = time.time()
        result = triage_ticket_with_llm(ticket)
        latency = round(time.time() - start_time, 2)
        latencies.append(latency)

        # เทียบผลลัพธ์
        cat_ok = result.category.lower() == ground_truth["category"].lower()
        pri_ok = result.priority == ground_truth["priority"]
        que_ok = result.assigned_queue == ground_truth["assigned_queue"]
        esc_ok = result.escalate == ground_truth["escalate"]

        if cat_ok: category_matches += 1
        if pri_ok: priority_matches += 1
        if que_ok: queue_matches += 1
        if esc_ok: escalation_matches += 1

        print(f"[{idx}/{total_cases}] Ticket ID: {item.get('id', 'N/A')} ({ticket.subject[:40]}...)")
        print(f"   -> Result: Category={'✅' if cat_ok else '❌'} | Priority={'✅' if pri_ok else '❌'} | Queue={'✅' if que_ok else '❌'} | Escalate={'✅' if esc_ok else '❌'} ({latency}s)")
        time.sleep(6)

    # สรุป Metrics
    cat_acc = (category_matches / total_cases) * 100
    pri_acc = (priority_matches / total_cases) * 100
    que_acc = (queue_matches / total_cases) * 100
    esc_acc = (escalation_matches / total_cases) * 100
    avg_lat = round(sum(latencies) / len(latencies), 2)

    print("\n" + "="*50)
    print("📊 MULTI-AGENT EVALUATION SUMMARY")
    print(f"Total Test Cases      : {total_cases}")
    print(f"Category Accuracy     : {cat_acc:.1f}% ({category_matches}/{total_cases})")
    print(f"Priority Accuracy     : {pri_acc:.1f}% ({priority_matches}/{total_cases})")
    print(f"Queue Match Accuracy  : {que_acc:.1f}% ({queue_matches}/{total_cases})")
    print(f"Escalation Match Rate : {esc_acc:.1f}% ({escalation_matches}/{total_cases})")
    print(f"Average Latency       : {avg_lat}s")
    print("="*50)

if __name__ == "__main__":
    run_evaluation()