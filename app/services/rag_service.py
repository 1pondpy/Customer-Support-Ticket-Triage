import os

def load_and_chunk_policies(policy_dir: str = "data/policies", chunk_size: int = 300) -> list[dict]:
    """
    โหลดไฟล์นโยบายทั้งหมดในโฟลเดอร์ และทำการสับย่อยข้อความออกมาเป็น Chunks
    """
    chunks = []
    if not os.path.exists(policy_dir):
        print(f"❌ Error: Directory '{policy_dir}' not found.")
        return chunks

    for filename in os.listdir(policy_dir):
        if filename.endswith(".txt"):
            filepath = os.path.join(policy_dir, filename)
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


def search_policies(query: str, chunks: list[dict]) -> list[dict]:
    """
    ค้นหา Chunks ที่มีคำสำคัญ (Keyword Match) ตรงกับคำค้นหา
    """
    results = []
    query_lower = query.lower()
    for chunk in chunks:
        if query_lower in chunk["text"].lower():
            results.append(chunk)
    return results


# 🧪 บล็อกสำหรับทดสอบรันไฟล์นี้โดยตรงผ่าน Terminal
if __name__ == "__main__":
    policy_dir = "data/policies"
    if not os.path.exists(policy_dir):
        policy_dir = "../data/policies"

    print(f"📂 Loading policies from: {policy_dir}")
    
    # แก้ชื่อเรียกฟังก์ชันเป็น load_and_chunk_policies ให้ถูกต้องตรงกัน
    chunks = load_and_chunk_policies(policy_dir)
    print(f"✅ Total Chunks Loaded: {len(chunks)}")

    # ทดสอบค้นหาคำว่า billing
    results = search_policies("billing", chunks)
    print(f"\n🔍 Found {len(results)} matching chunks for 'billing':\n")
    for r in results:
        print(f"- [{r['source']}] {r['text'][:100]}...")