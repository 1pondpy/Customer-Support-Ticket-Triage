import os
from dotenv import load_dotenv

# โหลดตัวแปรสภาพแวดล้อมจากไฟล์ .env เข้าสู่ระบบ
load_dotenv()

class Settings:
    # การตั้งค่าแอปพลิเคชันพื้นฐาน (ชื่อแอป, สภาพแวดล้อม, พอร์ตสำหรับรัน) พร้อมค่าเริ่มต้นสำรอง
    APP_NAME: str = os.getenv("APP_NAME", "Customer Support Ticket Triage")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    APP_PORT: int = int(os.getenv("APP_PORT", 8000))
    
    # การตั้งค่าเชื่อมต่อ Google Gemini API (API Key และชื่อโมเดลหลัก)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gemini-3.6-flash")

    @property
    def has_gemini(self) -> bool:
        """ตรวจสอบว่ามีการกำหนดค่า Gemini API Key ที่ไม่ใช่ค่าว่างหรือ Placeholder ตัวอย่าง"""
        return bool(self.GEMINI_API_KEY and not self.GEMINI_API_KEY.startswith("AIzaSyxxxx"))

# สร้าง Instance การตั้งค่ากลางสำหรับแจกจ่ายให้โมดูลอื่นในโปรเจกต์เรียกใช้
settings = Settings()