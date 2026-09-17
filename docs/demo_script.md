# สคริปต์นำเสนอฉบับเดี่ยว (Single Speaker)
**Customer Support Ticket Triage Architecture | v1.0.0 Demo Day**

> เวลาพูดประมาณ 7–8 นาที + Q&A ประมาณ 2–3 นาที

---

## Phase 1: Problem, Objective & Architecture Overview (0:00–1:30)

### 🖥️ Action
- เปิดสไลด์นำเสนอ (Canva หรือ PDF)
- สไลด์ 1 & 2: เปิดหน้าปกและรายชื่อสมาชิกค้างไว้ประมาณ 10–15 วินาทีตอนเริ่มทักทาย
- จากนั้นเปิด **Slide 01 — Problem & Scope**
- ตอนพูดถึง Out-of-Scope ให้ชี้หัวข้อ **Out-of-Scope**
- จากนั้นเปิด **Slide 02 — System Architecture Diagram**
- ใช้ Laser Pointer หรือ Cursor ชี้ตาม Flow ของระบบ
- เตรียม `Alt + Tab` ไป Chrome ตอนจบช่วงนี้

### 🎤 บทพูด

เรียนอาจารย์และสวัสดีทุกคนครับ วันนี้กลุ่ม 4 จะนำเสนอระบบ Customer Support Ticket Triage ในรีลีส v1.0.0 ครับ

ปัญหาหลักคือ ตั๋วแจ้งปัญหามีจำนวนมากและหลากหลาย ทำให้การคัดแยกด้วยคนเกิดความล่าช้า ส่งผิดคิว และควบคุม SLA ได้ยาก

ระบบของเราจึงพัฒนาขึ้นเพื่อจำแนกประเภทตั๋ว กำหนด Priority ตั้งแต่ P1 ถึง P4 ส่งเข้าคิวเฉพาะทาง และค้นหานโยบายที่เกี่ยวข้องโดยอัตโนมัติ โดยเน้นการคัดแยกและจัดการงานภายใน **ไม่ได้ตอบลูกค้าโดยตรงครับ**

จาก Architecture ระบบเริ่มจาก REST API ผ่าน Security Pre-Processor เพื่อป้องกัน Prompt Injection

จากนั้น Intent Router จะส่งงานไปยัง Domain Specialists โดยใช้โมเดล `openai/gpt-oss-20b` บน Groq Cloud API และดึงข้อมูลจาก Knowledge Base ที่มี Policy 5 ฉบับ

สุดท้าย Deterministic SLA Engine และ Judge Agent จะตรวจสอบ Priority และ Citation ก่อนส่งผลลัพธ์ออกมาในรูปแบบ Pydantic Schema ครับ

ต่อไปจะเป็นการสาธิตการทำงานจริงครับ

### 🖥️ Action
**กด `Alt + Tab` → Google Chrome → Dashboard**

---

# Phase 2: Live UI Demo — Security, SLA & Edge Cases (1:30–5:00)

## 1. Security Guardrails — Prompt Injection & PII

### 🖥️ Action
- อยู่ที่แท็บ **Live Single Triage**
- คลิก Preset **"1. Prompt Injection"**
- กด **"Execute MoE Triage Pipeline"**
- ชี้ผลลัพธ์ด้านขวา โดยเฉพาะ Priority ที่ยังไม่ถูกหลอกให้เป็น P1
- จากนั้นสลับไป Terminal / Console ชั่วครู่
- ชี้ Audit Log ที่แสดงเฉพาะ `ticket_id` และข้อมูล PII ถูก Redact
- สลับกลับหน้าเว็บทันที

### 🎤 บทพูด

เริ่มจาก Security Guardrails ครับ ระบบมองข้อความใน Ticket เป็น **Untrusted Input** เสมอ

เมื่อพบ Prompt Injection ที่พยายามบังคับให้ระบบกำหนด Priority เป็น P1 ระบบจะป้องกันไม่ให้คำสั่งดังกล่าวควบคุมผลการคัดแยกครับ

ส่วนการจัดการ PII ระบบยังสามารถวิเคราะห์ปัญหาได้ตามปกติ แต่ข้อมูลอ่อนไหวจะถูก **Redact ใน Audit Logs** โดยเก็บเฉพาะข้อมูลที่จำเป็น เช่น Ticket ID ครับ

---

## 2. Deterministic SLA & Hard Override

### 🖥️ Action
- คลิก Preset **"3. Enterprise Outage (P1)"**
- กด **"Execute MoE Triage Pipeline"**
- ชี้ตามลำดับ:
  - `ESCALATED`
  - `P1`
  - `tech_support_queue`
  - `macro_tech_system_outage`
  - Citation จาก `sla_policy.txt`
- จากนั้นคลิก Preset **"4. Pro Billing Dispute (P2)"**
- กด Execute
- ชี้ให้เห็น `NORMAL`, `P2` และ `billing_default_queue`

### 🎤 บทพูด

ต่อมาคือการควบคุม SLA แบบ Deterministic ครับ

ในกรณี Enterprise Outage ที่พบสัญญาณระบบขัดข้อง เช่น 500 Error ระบบจะใช้ Hard Rule กำหนดเป็น **P1** และ Escalate ไปยัง `tech_support_queue`

พร้อมแสดง Citation จากนโยบาย SLA และ Suggested Macro สำหรับให้เจ้าหน้าที่นำไปใช้งานครับ

ในทางกลับกัน เคส Pro Billing Dispute ที่ไม่เข้าเงื่อนไขระบบล่ม จะถูกจัดเป็น **P2 Normal** และส่งไปยัง `billing_default_queue` โดยไม่ Escalate เกินความจำเป็นครับ

---

## 3. Edge Cases & Disambiguation — gold_30

### 🖥️ Action
- คลิก Preset **"7. Dual-Intent (gold_30)"**
- กด **"Execute MoE Triage Pipeline"**
- ชี้ช่อง **Category → Shipping**
- ชี้ **Priority → P2**

### 🎤 บทพูด

สำหรับ Edge Case ที่มีหลายเจตนา เช่น `gold_30` ที่ลูกค้าแจ้งพัสดุสูญหายและขอเงินคืน

ระบบจะพิจารณาตัวชี้วัดเพื่อเลือก Domain ที่เหมาะสม ซึ่งในกรณีนี้ Router จัดเป็น **Shipping** และกำหนด Priority เป็น **P2** ตามเงื่อนไข SLA ครับ

---

# Phase 3: Asynchronous Batch Processing (5:00–6:15)

### 🖥️ Action
- สลับไปแท็บ **Batch Processing Queue**
- ชี้ JSON Array ที่เตรียมไว้ 3 Ticket
- กด **"Run Batch Asynchronous Execution"**
- ชี้ตารางผลลัพธ์ทั้ง 3 แถว
- ชี้:
  - Outage → P1
  - Finance → P2
  - Shipping → P2/P3
- ชี้ **Raw JSON** ด้านล่าง

### 🎤 บทพูด

ต่อมาในส่วน Batch Processing ระบบรองรับการประมวลผลตั๋วหลายรายการผ่าน API `POST /tickets/triage/batch` ครับ

ระบบใช้ Asynchronous Processing ร่วมกับ `asyncio.gather` เพื่อประมวลผลหลายเคสพร้อมกัน

จากผลลัพธ์จะเห็นว่าแต่ละ Ticket ถูกแจกแจงทั้ง Domain, Priority, Queue และสถานะ Escalation พร้อม Raw JSON สำหรับนำไปใช้งานต่อกับระบบอื่นครับ

---

# Phase 4: Code Walkthrough & Prompt Management (6:15–7:15)

### 🖥️ Action
- กด `Alt + Tab` → VS Code
- เปิด `app/services/triage_service.py`
- ชี้ **System Prompt**
  - `<ticket_body>`
  - `<instructions>`
  - Prompt Delimiters
- เลื่อนลงไปชี้ **Regex Weighted / Collision Guards**
- เลื่อนลงไปชี้ฟังก์ชัน `_evaluate_deterministic_sla()`
- ชี้บล็อก:
  - `if tier == "enterprise" and is_outage:`
- เปิด File Explorer ด้านซ้าย
- ชี้โฟลเดอร์ `data/policies/`
- ชี้ให้เห็น Policy ทั้ง 5 ฉบับ

### 🎤 บทพูด

ในส่วนของโค้ด เราแยกการทำงานหลักไว้ใน `triage_service.py` ครับ

ตรงนี้เราใช้ **Prompt Delimiters** เพื่อแยก Ticket Body ออกจากคำสั่งของระบบ และมี Collision Guards ช่วยจัดการ Keyword ที่อาจตรงกันหลาย Domain

ส่วน SLA เราใช้ **Deterministic Engine** ตรวจสอบ Customer Tier และสัญญาณ Outage โดยใช้ Hard Rules ไม่ปล่อยให้ LLM กำหนด Priority เองทั้งหมดครับ

สำหรับ Knowledge Base เรามี Policy หลัก 5 ฉบับ รวมถึง `macro_catalog.txt` โดย In-Memory RAG จะดึง Chunk ที่เกี่ยวข้องมาใช้ Grounding ร่วมกับโมเดล `openai/gpt-oss-20b` บน Groq Cloud API ครับ

---

# Phase 5: Evaluation Benchmark & Conclusion (7:15–8:00)

### 🖥️ Action
- กด `Alt + Tab` → Chrome
- เปิดแท็บ **Evaluation & Metrics (30 Gold Cases)**
- ชี้ KPI Cards ตามลำดับที่พูด:
  1. Category Accuracy → **96.7%**
  2. Priority Accuracy → **96.7%**
  3. Average Latency → **5.27s**
  4. Escalation Recall → **100.0%**
- ชี้กราฟ Chart.js สั้น ๆ
- ชี้ In-Depth Failure Note ของ `gold_30`
- จากนั้นปล่อยหน้าจอนี้ค้างไว้สำหรับ Q&A

### 🎤 บทพูด

สุดท้ายคือผลการประเมินระบบจาก **Full Gold Dataset จำนวน 30 เคส โดยเปรียบเทียบกับ Baseline ใน Iteration 2** ครับ

Category Accuracy อยู่ที่ **96.7% หรือ 29 จาก 30 เคส** สูงกว่าเกณฑ์ 85%

Priority Accuracy Within 1-Level อยู่ที่ **96.7%** ผ่านเกณฑ์ 80%

Average Latency อยู่ที่ **5.27 วินาที**

และ Escalation Recall อยู่ที่ **100% หรือ 7 จาก 7 เคส** สามารถตรวจจับเคสฉุกเฉินในชุดทดสอบได้ครบถ้วนครับ

โดยสรุป ระบบของกลุ่ม 4 ครอบคลุมทั้งการคัดแยกตั๋ว การควบคุม SLA, Security, RAG Grounding และ Dashboard สำหรับติดตามผลครับ

ขอจบการนำเสนอและการสาธิตระบบ Customer Support Ticket Triage เพียงเท่านี้

ขอบคุณครับ ยินดีตอบคำถามจากอาจารย์ครับ

### 🖥️ Action
- หยุดพูด
- ปล่อยหน้า **Evaluation & Metrics** ค้างไว้
- เตรียมตอบ Q&A ประมาณ 2–3 นาที