# สคริปต์นำเสนอฉบับเดี่ยว (Single Speaker)
**Customer Support Ticket Triage Architecture | v1.0.0 Demo Day**

> เวลาประมาณ 7–8 นาที เพื่อเหลือเวลาสำหรับ Q&A

## Phase 1: Problem, Objective & Architecture Overview (0:00–1:30)

เรียนอาจารย์และสวัสดีทุกคนครับ วันนี้กลุ่ม 4 จะนำเสนอระบบ Customer Support Ticket Triage ในรีลีส v1.0.0 ครับ

ปัญหาหลักคือ ตั๋วแจ้งปัญหามีจำนวนมากและหลากหลาย ทำให้การคัดแยกด้วยคนเกิดความล่าช้า ส่งผิดคิว และควบคุม SLA ได้ยาก

ระบบของเราจึงพัฒนาขึ้นเพื่อจำแนกประเภทตั๋ว กำหนด Priority ตั้งแต่ P1 ถึง P4 ส่งเข้าคิวเฉพาะทาง และค้นหานโยบายที่เกี่ยวข้องโดยอัตโนมัติ โดยเน้นการคัดแยกและจัดการงานภายใน ไม่ได้ตอบลูกค้าโดยตรงครับ

จาก Architecture ระบบเริ่มจาก REST API ผ่าน Security Pre-Processor เพื่อป้องกัน Prompt Injection จากนั้น Intent Router จะส่งงานไปยัง Domain Specialists โดยใช้ RAG ดึงนโยบายจาก Knowledge Base ร่วมกับ Groq API

สุดท้าย Deterministic SLA Engine และ Judge Agent จะช่วยตรวจสอบระดับความเร่งด่วนและ Citation ก่อนส่งผลลัพธ์ออกมาในรูปแบบ Pydantic Schema ครับ

ต่อไปจะเป็นการสาธิตการทำงานจริงครับ

## Phase 2: Live UI Demo — Security, SLA & Edge Cases (1:30–5:00)

### 1. Security Guardrails

เริ่มจาก Security Guardrails ครับ ระบบมองข้อความใน Ticket เป็น Untrusted Input เสมอ

เมื่อพบคำสั่ง Prompt Injection เช่น การพยายามบังคับให้ระบบกำหนด Priority เป็น P1 ระบบจะป้องกันไม่ให้คำสั่งดังกล่าวควบคุมผลการคัดแยกครับ

ส่วนการจัดการ PII เมื่อมีข้อมูลอย่างเบอร์โทรศัพท์ อีเมล หรือเลขบัตรเครดิต ระบบยังสามารถวิเคราะห์ปัญหาได้ตามปกติ แต่ข้อมูลอ่อนไหวจะถูก Redact ใน Audit Logs เพื่อปกป้องความเป็นส่วนตัวครับ

### 2. Deterministic SLA & Hard Override

ต่อมาคือการควบคุม SLA ครับ

ในกรณี Enterprise Outage ที่พบสัญญาณระบบขัดข้อง เช่น 500 Error ระบบจะใช้ Hard Rule กำหนด Priority เป็น P1 พร้อม Escalate ไปยัง `tech_support_queue` และแสดง Citation จากนโยบายที่เกี่ยวข้อง รวมถึง Suggested Macro สำหรับให้เจ้าหน้าที่นำไปใช้งานครับ

ในทางกลับกัน เคส Pro Billing Dispute ที่ไม่เข้าเงื่อนไขระบบล่ม จะถูกจัดเป็น P2 และส่งไปยัง `billing_default_queue` โดยไม่ Escalate เกินความจำเป็นครับ

### 3. Edge Cases & Disambiguation

สำหรับเคสที่มีหลายเจตนา เช่น gold_30 ที่ลูกค้าแจ้งพัสดุสูญหายและขอเงินคืน ระบบจะพิจารณาตัวชี้วัดเพื่อเลือก Domain ที่เหมาะสม

ในกรณีนี้ Router จัดเป็น Shipping และกำหนด Priority เป็น P2 โดยยังคงเป็นไปตามเงื่อนไข SLA ที่กำหนดครับ

## Phase 3: Asynchronous Batch Processing (5:00–6:15)

ในส่วน Batch Processing ระบบรองรับการประมวลผลตั๋วหลายรายการผ่าน API `POST /tickets/triage/batch` ครับ

ระบบใช้ Asynchronous Processing ร่วมกับ `asyncio.gather` เพื่อประมวลผลหลายเคสพร้อมกัน

ผลลัพธ์จะแสดงในรูปแบบตาราง ทั้ง Domain, Priority, Queue และสถานะ Escalation พร้อม Raw JSON สำหรับนำไปใช้งานต่อกับระบบอื่นครับ

## Phase 4: Code Walkthrough & Prompt Management (6:15–7:15)

ในส่วนของโค้ด เราแยกการทำงานไว้ใน `triage_service.py` ครับ

เราใช้ Prompt Delimiters เพื่อแยกข้อความที่ไม่เชื่อถือออกจากคำสั่งของระบบ และใช้ Collision Guards ช่วยจัดการ Keyword ที่อาจตรงกันหลาย Domain

ส่วน SLA จะใช้ Deterministic Engine ตรวจสอบ Customer Tier และสัญญาณ Outage โดยไม่ปล่อยให้ LLM กำหนด Priority เองทั้งหมดครับ

สำหรับ Knowledge Base เรามีเอกสารนโยบายหลัก 5 ฉบับ รวมถึง `macro_catalog.txt` โดย In-Memory RAG จะดึง Chunk ที่เกี่ยวข้องมาใช้ Grounding ร่วมกับ Groq API ครับ

## Phase 5: Evaluation Benchmark & Conclusion (7:15–8:00)

สุดท้ายคือผลการประเมินระบบจาก Full Gold Dataset จำนวน 30 เคสครับ

- Category Accuracy อยู่ที่ 96.7% หรือ 29 จาก 30 เคส สูงกว่าเกณฑ์ 85%
- Priority Accuracy Within 1-Level อยู่ที่ 96.7% ผ่านเกณฑ์ 80%
- Average Latency อยู่ที่ 5.27 วินาที
- Escalation Recall อยู่ที่ 100% หรือ 7 จาก 7 เคส สามารถตรวจจับเคสฉุกเฉินในชุดทดสอบได้ครบถ้วนครับ

โดยสรุป ระบบของกลุ่ม 4 ครอบคลุมทั้งการคัดแยกตั๋ว การควบคุม SLA, Security, RAG Grounding และ Dashboard สำหรับติดตามผลครับ

ขอจบการนำเสนอและการสาธิตระบบ Customer Support Ticket Triage เพียงเท่านี้ ขอบคุณครับ ยินดีตอบคำถามจากอาจารย์ครับ