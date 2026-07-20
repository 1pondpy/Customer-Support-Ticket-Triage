import os
from dotenv import load_dotenv

# สั่งให้ระบบวิ่งไปอ่านค่าจากไฟล์ .env เข้าสู่หน่วยความจำของ OS
load_dotenv()

class Settings:
    # ดึงค่า API Key ออกมาจาก Environment (ถ้าไม่มีให้ตั้งเป็นค่าสตริงว่างเปล่า)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    APP_ENV: str = os.getenv("APP_ENV", "development")

    @property
    def has_openai(self) -> bool:
        return self.OPENAI_API_KEY != "" and not self.OPENAI_API_KEY.startswith("sk-")

    @property
    def has_gemini(self) -> bool:
        return self.GEMINI_API_KEY != "" and not self.GEMINI_API_KEY.startswith("AIzaSyxxxx")

# ทำการประกาศ Instance พร้อมใช้งาน
settings = Settings()

# ตัวทดสอบรันดูใน Terminal สดๆ
if __name__ == "__main__":
    print("🔒 [Config Loader Test]")
    print(f"App Environment: {settings.APP_ENV}")
    print(f"OpenAI Key Detected: {'✅ Yes' if os.getenv('OPENAI_API_KEY') else '❌ No'}")
    print(f"Gemini Key Detected: {'✅ Yes' if os.getenv('OPENAI_API_KEY') else '❌ No'}")