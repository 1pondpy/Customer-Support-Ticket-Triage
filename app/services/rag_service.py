import os
from typing import List, Dict, Any

POLICY_DIR = os.path.join(os.path.dirname(__file__), "../../data/policies")

class RAGService:
    def __init__(self, policy_dir: str = POLICY_DIR):
        self.policy_dir = policy_dir
        self.chunks: List[Dict[str, str]] = []
        self.load_and_chunk_policies()

    def load_and_chunk_policies(self):
        """โหลดไฟล์ .txt ทั้งหมดใน data/policies แล้วทำ chunking"""
        self.chunks = []
        if not os.path.exists(self.policy_dir):
            return

        for filename in os.listdir(self.policy_dir):
            if filename.endswith(".txt"):
                file_path = os.path.join(self.policy_dir, filename)
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    lines = [line.strip() for line in content.split("\n") if line.strip()]
                    current_chunk = []
                    current_len = 0
                    for line in lines:
                        current_chunk.append(line)
                        current_len += len(line)
                        if current_len >= 250:
                            self.chunks.append({
                                "source": filename,
                                "text": "\n".join(current_chunk)
                            })
                            current_chunk = []
                            current_len = 0
                    if current_chunk:
                        self.chunks.append({
                            "source": filename,
                            "text": "\n".join(current_chunk)
                        })

    def search_policies(self, query: str, top_k: int = 3) -> List[Dict[str, str]]:
        """ค้นหาชิ้นส่วนนโยบายที่ตรงกับคำค้นหา"""
        if not self.chunks:
            self.load_and_chunk_policies()

        tokens = [t.lower() for t in query.split() if len(t) > 2]
        scored_chunks = []

        for chunk in self.chunks:
            score = 0
            text_lower = chunk["text"].lower()
            for token in tokens:
                if token in text_lower:
                    score += 1
            if score > 0:
                scored_chunks.append((score, chunk))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        results = [item[1] for item in scored_chunks[:top_k]]

        # ถ้าไม่พบคีย์เวิร์ด ให้ fallback ดึงก้อนตั้งต้นจาก routing และ sla
        if not results:
            fallback = [c for c in self.chunks if c["source"] in ["routing_policy.txt", "sla_policy.txt"]]
            return fallback[:top_k]

        return results

rag_service = RAGService()