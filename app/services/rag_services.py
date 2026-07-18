import os

class RAGService:
    def __init__(self, policy_dir: str = "data/policies"):
        self.policy_dir = policy_dir

    def load_and_split_policies(self, chunk_size: int = 200, chunk_overlap: int = 50):
        """
        ฟังก์ชันโหลดไฟล์นโยบายทั้งหมดและทำการตัดแบ่งข้อความ (Chunking) เป็นท่อนสั้นๆ
        """
        chunks = []
        
        # ตรวจสอบว่ามีโฟลเดอร์นโยบายจริงไหม
        if not os.path.exists(self.policy_dir):
            return chunks

        # วนลูปอ่านทุกไฟล์ในโฟลเดอร์ policies
        for filename in os.listdir(self.policy_dir):
            if filename.endswith(".txt"):
                file_path = os.path.join(self.policy_dir, filename)
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()
                    
                    # ทำการตัดข้อความแบบเบสิก (สามารถอัปเกรดเป็นตัวตัดคำขั้นสูงได้ในภายหลัง)
                    words = text.split()
                    for i in range(0, len(words), chunk_size - chunk_overlap):
                        chunk = " ".join(words[i:i + chunk_size])
                        if chunk:
                            chunks.append({
                                "source": filename,
                                "content": chunk
                            })
        return chunks

# ตัวอย่างทดสอบรันภายในสคริปต์
if __name__ == "__main__":
    rag = RAGService()
    result = rag.load_and_split_policies()
    print(print(f"🎉 Successfully generated {len(result)} chunks from policies."))