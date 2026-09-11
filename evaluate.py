import json
import time
from pathlib import Path
from app.schemas.ticket import TicketInput
from app.services.triage_service import triage_ticket_with_llm

PRIORITY_LEVELS = {"P1": 1, "P2": 2, "P3": 3, "P4": 4}

def is_priority_within_one_level(pred: str, gt: str) -> bool:
    """ตรวจสอบว่าระดับ Priority คลาดเคลื่อนไม่เกิน 1 ระดับตามเกณฑ์ PRD"""
    if pred not in PRIORITY_LEVELS or gt not in PRIORITY_LEVELS:
        return False
    return abs(PRIORITY_LEVELS[pred] - PRIORITY_LEVELS[gt]) <= 1

def normalize_category(cat: str) -> str:
    """แปลงหมวดหมู่ที่มีความหมายใกล้เคียงกันให้เทียบเคียงกันได้"""
    c = cat.strip().lower()
    mapping = {
        "general": "other",
        "technical_support": "technical",
        "refund_request": "refund",
        "dispute": "billing"
    }
    return mapping.get(c, c)

def is_category_match(pred: str, gt: str) -> bool:
    """ตรวจสอบความถูกต้องของ Category พร้อมรองรับ Substring และ Normalization"""
    p = normalize_category(pred)
    g = normalize_category(gt)
    return p == g or (p in g) or (g in p)

def run_evaluation(gold_dataset_path: str = "data/gold_dataset.json"):
    gold_path = Path(gold_dataset_path)
    if not gold_path.exists():
        print(f"❌ Error: File not found at {gold_dataset_path}")
        return

    with open(gold_path, "r", encoding="utf-8") as f:
        gold_data = json.load(f)

    total_cases = len(gold_data)
    print(f"🚀 Starting Multi-Agent Evaluation on {total_cases} Gold Cases...\n")

    cat_matches = 0
    pri_exact_matches = 0
    pri_one_level_matches = 0
    que_matches = 0
    
    # Escalation Recall Metrics
    actual_escalate_count = 0  # TP + FN
    true_positive_escalate = 0 # TP
    
    latencies = []

    for idx, item in enumerate(gold_data, 1):
        ticket = TicketInput(**item["input"])
        gt = item["ground_truth"]

        start_time = time.time()
        try:
            result = triage_ticket_with_llm(ticket)
            latency = round(time.time() - start_time, 2)
            latencies.append(latency)

            # 1. Category Check
            cat_ok = is_category_match(result.category, gt["category"])

            # 2. Priority Checks
            pri_exact_ok = result.priority == gt["priority"]
            pri_one_level_ok = is_priority_within_one_level(result.priority, gt["priority"])

            # 3. Queue Match Check
            p_queue = result.assigned_queue.strip().lower()
            g_queue = gt["assigned_queue"].strip().lower()
            que_ok = (p_queue == g_queue) or (p_queue in g_queue) or (g_queue in p_queue)
            
            # 4. Escalation Recall Check
            if gt.get("escalate", False):
                actual_escalate_count += 1
                if result.escalate:
                    true_positive_escalate += 1

            if cat_ok: cat_matches += 1
            if pri_exact_ok: pri_exact_matches += 1
            if pri_one_level_ok: pri_one_level_matches += 1
            if que_ok: que_matches += 1

            status_icon = "✅" if (cat_ok and pri_one_level_ok and que_ok) else "⚠️"
            print(f"[{idx}/{total_cases}] {status_icon} Ticket ID: {item.get('id', 'N/A')} ({ticket.subject[:35]}...)")
            print(f"    -> Pred: cat={result.category}, prio={result.priority}, queue={result.assigned_queue}, esc={result.escalate}")
            print(f"    -> GT  : cat={gt['category']}, prio={gt['priority']}, queue={gt['assigned_queue']}, esc={gt['escalate']} ({latency}s)")

        except Exception as e:
            print(f"[{idx}/{total_cases}] ❌ Error processing {item.get('id', 'N/A')}: {e}")

        # หน่วงเวลาสั้นๆ 1 วินาที ป้องกันการส่งคำขอถี่เกินไป
        time.sleep(1)

    # คำนวณ Metrics สรุป
    cat_acc = (cat_matches / total_cases) * 100 if total_cases else 0.0
    pri_exact_acc = (pri_exact_matches / total_cases) * 100 if total_cases else 0.0
    pri_one_level_acc = (pri_one_level_matches / total_cases) * 100 if total_cases else 0.0
    que_acc = (que_matches / total_cases) * 100 if total_cases else 0.0
    esc_recall = (true_positive_escalate / actual_escalate_count * 100) if actual_escalate_count > 0 else 100.0
    avg_lat = round(sum(latencies) / len(latencies), 2) if latencies else 0.0

    # ประเมินเกณฑ์ PRD
    cat_pass = cat_acc >= 85.0
    pri_pass = pri_one_level_acc >= 80.0
    all_passed = cat_pass and pri_pass and (esc_recall == 100.0)

    print("\n" + "="*58)
    print("📊 PRD COMPLIANT EVALUATION SUMMARY")
    print("="*58)
    print(f"Total Test Cases               : {total_cases}")
    print(f"Category Accuracy (Pass ≥85%)  : {cat_acc:.1f}% ({cat_matches}/{total_cases}) {'✅' if cat_pass else '❌'}")
    print(f"Priority Exact Match           : {pri_exact_acc:.1f}% ({pri_exact_matches}/{total_cases})")
    print(f"Priority Within 1-Level (≥80%) : {pri_one_level_acc:.1f}% ({pri_one_level_matches}/{total_cases}) {'✅' if pri_pass else '❌'}")
    print(f"Queue Match Accuracy           : {que_acc:.1f}% ({que_matches}/{total_cases})")
    print(f"Escalation Recall (TP Target)  : {esc_recall:.1f}% ({true_positive_escalate}/{actual_escalate_count}) {'✅' if esc_recall == 100.0 else '❌'}")
    print(f"Average Latency                : {avg_lat}s")
    print(f"Overall PRD Status             : {'🏆 PASSED ALL THRESHOLDS' if all_passed else '⚠️ BELOW PASS THRESHOLD'}")
    print("="*58)

if __name__ == "__main__":
    run_evaluation()