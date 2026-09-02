import os

class RAGService:
    def __init__(self, policy_dir: str = "data/policies"):
        """กำหนดตำแหน่งโฟลเดอร์นโยบาย และโหลดตัดชิ้นส่วนข้อความ (Chunks) ทันทีที่สร้าง Service"""
        self.policy_dir = policy_dir
        
        # ป้องกันปัญหา Relative Path: ตรวจสอบและถอย Path 1 ระดับหากรันคำสั่งจากโฟลเดอร์ app/
        if not os.path.exists(self.policy_dir) and os.path.exists(f"../{self.policy_dir}"):
            self.policy_dir = f"../{self.policy_dir}"
            
        # อ่านไฟล์นโยบายทั้งหมดและสับแบ่งข้อความเป็น Chunks เก็บไว้ในหน่วยความจำ
        self.chunks = self.load_and_chunk_policies()

    def load_and_chunk_policies(self, chunk_size: int = 300) -> list[dict]:
        """อ่านไฟล์ .txt ทั้งหมดใน policy_dir แล้วหั่นข้อความออกเป็นท่อนย่อยตามขนาด chunk_size"""
        chunks = []
        if not os.path.exists(self.policy_dir):
            print(f"❌ Error: Directory '{self.policy_dir}' not found.")
            return chunks

        for filename in os.listdir(self.policy_dir):
            if filename.endswith(".txt"):
                filepath = os.path.join(self.policy_dir, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                    
                # วนลูปแบ่ง content ออกเป็น Chunk ตามขนาดที่กำหนดใน chunk_size
                # range(0, len(content), chunk_size)
                # = เริ่มที่ตำแหน่ง 0 ไปจนถึงความยาวของ content
                # โดยเพิ่มตำแหน่งครั้งละ chunk_size
                for i in range(0, len(content), chunk_size):
                    
                    # ตัดข้อความตั้งแต่ตำแหน่ง i ไปจนถึง i + chunk_size
                    # .strip() ใช้ลบช่องว่างหรือขึ้นบรรทัดใหม่ที่อยู่ต้นและท้ายข้อความ
                    chunk_text = content[i:i + chunk_size].strip()
                    
                    # ตรวจสอบว่า Chunk นี้มีข้อความอยู่จริงหรือไม่
                    # ถ้าไม่ใช่ข้อความว่าง จึงนำไปเก็บใน chunks
                    if chunk_text:
                        # เก็บข้อมูลของ Chunk ในรูปแบบ Dictionary
                        chunks.append({
                            "source": filename,  # บันทึกชื่อไฟล์ต้นทางสำหรับทำ Grounding / Policy Citations
                            "text": chunk_text   # ข้อความเนื้อหาของ Chunk
                        })
        return chunks

    def search_policies(self, query: str) -> list[dict]:
        """ค้นหา Chunks ที่มีคำสำคัญ (Keyword Match) ตรงกับ Query โดยไม่สนใจตัวพิมพ์เล็ก-ใหญ่"""
        results = []
        query_lower = query.lower()
        for chunk in self.chunks:
            if query_lower in chunk["text"].lower():
                results.append(chunk)
        return results


# --- ส่วนฟังก์ชันเสริมภายนอกคลาส เพื่อรองรับโค้ดเก่าที่เรียกใช้แบบฟังก์ชันเดี่ยว (Backward Compatibility) ---

def load_and_chunk_policies(policy_dir: str = "data/policies", chunk_size: int = 300) -> list[dict]:
    """ฟังก์ชัน Wrapper สำหรับเรียกสร้าง RAGService และคืนค่ารายการ Chunks โดยตรง"""
    service = RAGService(policy_dir=policy_dir)
    return service.chunks

def search_policies(query: str, chunks: list[dict]) -> list[dict]:
    """ฟังก์ชัน Wrapper สำหรับค้นหาคำสำคัญจากรายการ Chunks ที่ส่งเข้ามา"""
    results = []
    query_lower = query.lower()
    for chunk in chunks:
        if query_lower in chunk["text"].lower():
            results.append(chunk)
    return results


# --- บล็อกทดสอบการทำงานของ RAG Ingestion และ Keyword Retrieval ผ่าน Terminal ---
if __name__ == "__main__":
    rag = RAGService()
    print(f"📂 Loaded policies from: {rag.policy_dir}")
    print(f"✅ Total Chunks Loaded: {len(rag.chunks)}")

    # ยิงทดสอบค้นหาคำว่า billing ว่าดึงข้อมูลนโยบายออกมาได้ครบถ้วนหรือไม่
    results = rag.search_policies("billing")
    print(f"\n🔍 Found {len(results)} matching chunks for 'billing':\n")
    for r in results:
        print(f"- [{r['source']}] {r['text'][:100]}...")