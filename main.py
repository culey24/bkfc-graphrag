from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from neo4j import GraphDatabase
from pathlib import Path
import json
import glob
from backend.core.rag_chain import GraphRAG
from backend.core.llm_engine import LLMEngine
from backend.core.embedding_engine import EmbeddingEngine

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ĐỊNH NGHĨA ĐƯỜNG DẪN Ở ĐÂY ---
# Đường dẫn tới thư mục chứa các file JSON của bbi
DATA_DIR = Path("data/processed") 

# Khởi tạo các Engine (Singleton)
llm_engine = LLMEngine(mode="ollama", model_name="llama3.2")
embedder = EmbeddingEngine()
neo4j_driver = GraphDatabase.driver("bolt://localhost:7687", auth=None)

def load_json():
    all_data = {"nodes": [], "links": []}
    
    # Quét tất cả file .json trong folder data/processed
    json_files = glob.glob(str(DATA_DIR / "*.json"))
    
    node_ids = set()
    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Tránh trùng node nếu cùng ID xuất hiện ở nhiều file
                for node in data.get('nodes', []):
                    if node['id'] not in node_ids:
                        all_data['nodes'].append(node)
                        node_ids.add(node['id'])
                all_data['links'].extend(data.get('links', []))
        except Exception as e:
            print(f"❌ Lỗi khi đọc file {file_path}: {e}")
            
    return all_data

@app.get("/graph")
async def get_graph():
    return load_json()

@app.post("/ask")
async def ask_question(data: dict):
    query = data.get("query", "")
    graph_data = load_json()
    
    rag = GraphRAG(graph_data, llm_engine, embedder, neo4j_driver)
    answer, node_ids = rag.query(query)
    
    return {"answer": answer, "relevant_nodes": node_ids}

@app.on_event("shutdown")
def shutdown_db():
    neo4j_driver.close()