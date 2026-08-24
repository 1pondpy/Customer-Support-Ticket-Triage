import json
import time
from pathlib import Path
from app.schemas.ticket import TicketInput
from app.services.triage_service import triage_ticket_with_llm

def run_evaluation(gold_dataset_path: str = "data/gold_dataset.json"):
    gold_file = Path(gold_dataset_path)
    if not gold_file.exists():
        print(f"❌ Error: {gold_dataset_path} not found.")
        return

    with open(gold_file, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    print(f"🚀 Starting Evaluation Pipeline on {len(test_cases)} Gold Cases...\n")
    
    results = []
    category_matches = 0
    priority_matches = 0
    queue_matches = 0
    escalate_matches = 0

    for idx, case in enumerate(test_cases, 1):
        ticket_input = TicketInput(**case["input"])
        gt = case["ground_truth"]
        
        print(f"[{idx}/{len(test_cases)}] Evaluating Ticket ID: {case['id']} ({ticket_input.subject})...")
        
        start_time = time.time()
        try:
            prediction = triage_ticket_with_llm(ticket_input)
            latency = round(time.time() - start_time, 2)
            
            # Normalization check
            pred_cat = prediction.category.lower() if prediction.category else ""
            gt_cat = gt["category"].lower()
            cat_ok = gt_cat in pred_cat or pred_cat in gt_cat
            
            prio_ok = prediction.priority == gt["priority"]
            queue_ok = prediction.assigned_queue == gt["assigned_queue"]
            esc_ok = prediction.escalate == gt["escalate"]

            if cat_ok: category_matches += 1
            if prio_ok: priority_matches += 1
            if queue_ok: queue_matches += 1
            if esc_ok: escalate_matches += 1

            results.append({
                "id": case["id"],
                "subject": ticket_input.subject,
                "latency_sec": latency,
                "category": {"pred": prediction.category, "gt": gt["category"], "match": cat_ok},
                "priority": {"pred": prediction.priority, "gt": gt["priority"], "match": prio_ok},
                "queue": {"pred": prediction.assigned_queue, "gt": gt["assigned_queue"], "match": queue_ok},
                "escalate": {"pred": prediction.escalate, "gt": gt["escalate"], "match": esc_ok},
                "citations": prediction.policy_citations
            })
            print(f"   -> Result: Category={'✅' if cat_ok else '❌'} | Priority={'✅' if prio_ok else '❌'} | Queue={'✅' if queue_ok else '❌'} ({latency}s)")
        except Exception as e:
            print(f"   ❌ Error evaluating {case['id']}: {e}")

    total = len(test_cases)
    cat_acc = (category_matches / total) * 100
    prio_acc = (priority_matches / total) * 100
    queue_acc = (queue_matches / total) * 100
    esc_acc = (escalate_matches / total) * 100

    print("\n" + "=" * 50)
    print("📊 EVALUATION SUMMARY METRICS")
    print("=" * 50)
    print(f"Total Test Cases      : {total}")
    print(f"Category Accuracy     : {cat_acc:.1f}% ({category_matches}/{total})")
    print(f"Priority Accuracy     : {prio_acc:.1f}% ({priority_matches}/{total})")
    print(f"Queue Match Accuracy  : {queue_acc:.1f}% ({queue_matches}/{total})")
    print(f"Escalation Match Rate : {esc_acc:.1f}% ({escalate_matches}/{total})")
    print("=" * 50)

if __name__ == "__main__":
    run_evaluation()