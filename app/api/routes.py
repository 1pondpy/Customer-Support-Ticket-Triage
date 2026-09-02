from fastapi import APIRouter, Query
from app.schemas.ticket import TicketInput
from app.schemas.triage import TriageResult, BatchTicketInput, BatchTriageResult
from app.services.triage_service import triage_ticket_with_llm
from app.services.rag_service import RAGService

router = APIRouter()

## POST ส่ง, GET รับ

## ตั๋วปกติ รับอ็อบเจกต์ตั๋ว 1 ใบเดี่ยวๆ เช่น {"subject": "...", "body": "..."} , 1 Request = 1 Problem
@router.post("/tickets/triage", response_model=TriageResult) ## ให้ FastAPI ยึดโครงสร้างของข้อมูลขากลับ ให้ตรงตาม Class ที่เราระบุไว้ คลาส TriageResult
def triage(ticket: TicketInput): ## ticket เป็นตัวแปรของ ticketinput
    return triage_ticket_with_llm(ticket) ## คำสั่งเรียกฟังก์ชันจาก triage_service.py

@router.post("/tickets/triage/batch", response_model=BatchTriageResult) ## Batch คือ รับก้อน Array ที่หุ้มด้วยคีย์ tickets เช่น {"tickets": [ {ใบที่ 1}, {ใบที่ 2} ]} , 1 Request ต่อ หลายตั๋ว
def triage_batch(batch_input: BatchTicketInput): ## ให้ fastapi ยึดโครงสร้างของข้อมูลขาเข้า ให้ตรงตาม Class ที่เราระบุไว้ คลาส BatchTicketInput
    results = [triage_ticket_with_llm(ticket) for ticket in batch_input.tickets] ## ใช้ List Comprehension วนลูปประมวลผลตั๋วทุกใบในชุด Batch ทีละรายการแบบเรียงลำดับ
    return BatchTriageResult(
        total_processed=len(results), ## นับจำนวนข้อมูลในลิสต์ results ว่ารอบนี้ประมวลผลตั๋วสำเร็จไปทั้งหมดกี่ใบ
        results=results ## นำลิสต์ที่เก็บผลลัพธ์การคัดแยกตั๋ว (results ซึ่งข้างในคืออ็อบเจกต์ TriageResult ของแต่ละใบ) ผูกเข้ากับคีย์ results ของตัว Model
    )


## รับคำค้นหาผ่าน Query String เพื่อทดสอบการสืบค้น Chunks ก่อนส่งให้ AI ใน Rag Service
@router.get("/policies/search")
def search_policies(query: str = Query(..., description="คำสำคัญที่ต้องการทดสอบค้นหาในคลังนโยบาย")): ## กำหนดให้เอนด์พอยต์นี้รับพารามิเตอร์แบบ Query String เช่น ?query=billing , ข้อมูลต้องเป็นข้อความและ required field
    rag = RAGService(policy_dir="data/policies") ## ชี้โฟลเดอร์ ให้อ่านไฟล์ policies
    results = rag.search_policies(query) # ค้นหา Chunks ที่มี Keyword ตรงกับคำค้นหา
    return { ## ส่งข้อมูลกลับออกไปเป็น Dictionary ซึ่ง FastAPI จะแปลงเป็น JSON Response
        "query": query, ## สะท้อนคำค้นหาที่ส่งเข้ามา
        "results_found": len(results), ## นับจำนวน Chunk ที่ค้นเจอทั้งหมดด้วยคำสั่ง len(results)
        "results": results ##รายการ Chunks ที่ค้นพบ ซึ่งข้างในจะระบุชื่อไฟล์ต้นทาง (source) และเนื้อหานโยบายท่อนนั้น (text)
    }

## Stub Endpoint: โครงร่างสำหรับเชื่อมต่อสคริปต์ประเมินความแม่นยำ (Evaluation) กับชุดข้อมูล Gold Dataset
@router.post("/evaluate")
def evaluate_routing():
    pass