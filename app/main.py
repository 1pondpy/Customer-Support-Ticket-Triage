from fastapi import FastAPI
from app.api.routes import router

# สร้าง Instance หลักของ FastAPI พร้อมกำหนดชื่อไตเติลสำหรับแสดงบน Swagger UI (/docs)
app = FastAPI(
    title="Customer Support Ticket Triage"
)

# ลงทะเบียนเชื่อมต่อเส้นทาง API ทั้งหมดจาก routes.py เข้าสู่แอปหลัก
app.include_router(router)