import os

class RAGService:
    def __init__(self, policy_dir: str = "data/policies"):
        self.policy_dir = policy_dir
        # ปรับ Path อัตโนมัติหากเรียกจากตำแหน่งที่ต่างกัน
        if not os.path.exists(self.policy_dir) and os.path.exists(f"../{self.policy_dir}"):
            self.policy_dir = f"../{self.policy_dir}"
            
        self.chunks = self.load_and_chunk_policies()

    def load_and_chunk_policies(self, chunk_size: int = 300) -> list[dict]:
        """
        โหลดไฟล์นโยบายทั้งหมดในโฟลเดอร์ และทำการสับย่อยข้อความออกมาเป็น Chunks
        """
        chunks = []
        if not os.path.exists(self.policy_dir):
            print(f"❌ Error: Directory '{self.policy_dir}' not found.")
            return chunks

        for filename in os.listdir(self.policy_dir):
            if filename.endswith(".txt"):
                filepath = os.path.join(self.policy_dir, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                    
                # สับย่อยข้อความตามขนาด chunk_size
                for i in range(0, len(content), chunk_size):
                    chunk_text = content[i:i + chunk_size].strip()
                    if chunk_text:
                        chunks.append({
                            "source": filename,
                            "text": chunk_text
                        })
        return chunks

    def search_policies(self, query: str) -> list[dict]:
        """
        ค้นหา Chunks ที่มีคำสำคัญ (Keyword Match) ตรงกับคำค้นหา
        """
        results = []
        query_lower = query.lower()
        for chunk in self.chunks:
            if query_lower in chunk["text"].lower():
                results.append(chunk)
        return results


# 💡 ประกาศ ฟังก์ชันโดด ด้านนอกคลาสไว้ด้วย เพื่อรองรับการเรียกใช้แบบฟังก์ชันตรงๆ (Backward Compatibility)
def load_and_chunk_policies(policy_dir: str = "data/policies", chunk_size: int = 300) -> list[dict]:
    service = RAGService(policy_dir=policy_dir)
    return service.chunks

def search_policies(query: str, chunks: list[dict]) -> list[dict]:
    results = []
    query_lower = query.lower()
    for chunk in chunks:
        if query_lower in chunk["text"].lower():
            results.append(chunk)
    return results


# 🧪 บล็อกสำหรับทดสอบรันไฟล์นี้โดยตรงผ่าน Terminal
if __name__ == "__main__":
    rag = RAGService()
    print(f"📂 Loaded policies from: {rag.policy_dir}")
    print(f"✅ Total Chunks Loaded: {len(rag.chunks)}")

    # ทดสอบค้นหาคำว่า billing
    results = rag.search_policies("billing")
    print(f"\n🔍 Found {len(results)} matching chunks for 'billing':\n")
    for r in results:
        print(f"- [{r['source']}] {r['text'][:100]}...")