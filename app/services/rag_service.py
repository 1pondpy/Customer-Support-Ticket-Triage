import os

class RAGService:
    def __init__(self, policy_dir: str = "data/policies"):
        self.policy_dir = policy_dir

    def load_and_split_policies(self, chunk_size: int = 150, chunk_overlap: int = 30):
        chunks = []
        if not os.path.exists(self.policy_dir):
            print(f"❌ Error: Policy directory '{self.policy_dir}' not found.")
            return chunks

        for filename in os.listdir(self.policy_dir):
            if filename.endswith(".txt"):
                file_path = os.path.join(self.policy_dir, filename)
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()
                    words = text.split()
                    for i in range(0, len(words), chunk_size - chunk_overlap):
                        chunk_text = " ".join(words[i:i + chunk_size])
                        if chunk_text.strip():
                            chunks.append({
                                "source_file": filename,
                                "content": chunk_text
                            })
        return chunks

    def search_policies(self, query: str):
        """
        [ฟังก์ชันเพิ่มใหม่] ค้นหา Chunks ที่เกี่ยวข้องจากคำสำคัญ (Keyword Search)
        สำหรับใช้ใน RAG Debug Endpoint
        """
        all_chunks = self.load_and_split_policies()
        results = []
        
        # วนลูปหาข้อความที่ตรงกับ Query (แบบไม่สนใจอักษรเล็ก-ใหญ่)
        for chunk in all_chunks:
            if query.lower() in chunk["content"].lower():
                results.append(chunk)
                
        return results

if __name__ == "__main__":
    # ทดสอบฟังก์ชันค้นหา
    rag = RAGService(policy_dir="../data/policies")
    # ลองค้นหาคำว่า billing
    search_res = rag.search_policies("billing")
    print(f"🔍 Found {len(search_res)} matching chunks for 'billing'.")