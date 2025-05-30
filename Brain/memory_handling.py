# -------- memory
def strip_system_logs(text: str) -> str:
        return re.sub(r'\*[^*]+\*', '', text).strip()
    
class MemoryManager:
    def __init__(self, db: Chroma, embeddings: Embeddings, decay_half_life=21600):  # 6 hours
        self.db = db
        self.embeddings = embeddings
        self.half_life = decay_half_life

    
    def save_memory(self, content: str, score: float = 0.5, memory_type: str = "chat", tags: list = []):
        cleaned = strip_system_logs(content)
        if not cleaned:
            return  # Don't save empty memory

        metadata = {
            "timestamp": time.time(),
            "score": score,
            "type": memory_type,
            "tags": ", ".join(tags) if tags else None  # Convert list to comma-separated string
        }   
        self.db.add_texts([cleaned], metadatas=[metadata])

    def cosine_similarity(self, a, b):
        return sum(x * y for x, y in zip(a, b)) / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))

    def score_memory(self, memory: Document, query_embedding: list):
        now = time.time()
        timestamp = memory.metadata.get("timestamp", now)
        age = now - timestamp
        recency = 0.5 ** (age / self.half_life)

        try:
            memory_embedding = self.embeddings.embed_documents([memory.page_content])[0]
        except Exception as e:
            print("[Memory][EmbedError]", e)
            return 0

        similarity = self.cosine_similarity(query_embedding, memory_embedding)
        importance = memory.metadata.get("score", 0.5)

        return 0.6 * similarity + 0.3 * importance + 0.1 * recency

    def retrieve(self, query: str, top_k: int = 5):
        query_embedding = self.embeddings.embed_query(query)
        docs = self.db.similarity_search_with_score(query, k=20)

        scored = []
        for doc, _ in docs:
            try:
                score = self.score_memory(doc, query_embedding)
                scored.append((score, doc))
            except:
                continue

        return [doc for _, doc in sorted(scored, key=lambda x: x[0], reverse=True)[:top_k]]

    def reinforce(self, memory: Document, amount: float = 0.1):
        new_score = min(memory.metadata.get("score", 0.5) + amount, 1.0)
        memory.metadata["score"] = new_score
        memory.metadata["timestamp"] = time.time()
        self.db.add_texts([memory.page_content], metadatas=[memory.metadata])

    def summarize(self, memories: list, llm):
        combined = "\n".join([m.page_content for m in memories])
        prompt = f"Summarize the following memories:\n{combined}"
        summary = llm(prompt)
        self.save_memory(summary, score=0.7, memory_type="summary")
        return summary
    
