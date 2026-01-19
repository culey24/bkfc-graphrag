import json
import os
import torch
import numpy as np
import glob
from neo4j import GraphDatabase
from backend.core.embedding_engine import EmbeddingEngine
from pathlib import Path

# Cấu hình đường dẫn thư mục
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "processed"
NEO4J_URI = "bolt://localhost:7687"

class DataSynchronizer:
    def __init__(self):
        self.embedder = EmbeddingEngine()
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=None)

    def close(self):
        self.driver.close()

    def load_all_json_data(self):
        """Quét toàn bộ thư mục và gộp dữ liệu từ các file JSON"""
        all_nodes = []
        all_links = []
        
        json_files = glob.glob(str(DATA_DIR / "*.json"))
        print(f"📂 Tìm thấy {len(json_files)} file JSON trong {DATA_DIR}")
        
        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                    all_nodes.extend(content.get('nodes', []))
                    all_links.extend(content.get('links', []))
            except Exception as e:
                print(f"❌ Lỗi khi đọc file {file_path}: {e}")
                
        return all_nodes, all_links

    def sync(self):
        # 1. Thu thập dữ liệu từ tất cả các file
        nodes, links = self.load_all_json_data()
        if not nodes:
            print("⚠️ Không có dữ liệu node nào để xử lý.")
            return

        # 2. Lấy ID đã có trong Neo4j để tránh encode lại
        existing_ids = set()
        with self.driver.session() as session:
            result = session.run("MATCH (n:Entity) RETURN n.id AS id")
            existing_ids = {record["id"] for record in result}

        # 3. Lọc node mới hoàn toàn
        # Lưu ý: Dùng dict để lọc trùng ID giữa các file JSON khác nhau
        unique_nodes = {n['id']: n for n in nodes}.values()
        new_nodes = [n for n in unique_nodes if n['id'] not in existing_ids]

        # 4. Xử lý FAISS (Chỉ dành cho lính mới)
        if new_nodes:
            print(f"🚀 Phát hiện {len(new_nodes)} node mới từ các file. Đang làm Embedding...")
            texts = [f"{n['user']} {n['desc']}" for n in new_nodes]
            new_embeddings = self.embedder.encode(texts)
            
            if torch.is_tensor(new_embeddings):
                new_emb_np = new_embeddings.cpu().detach().numpy().astype('float32')
            else:
                new_emb_np = np.array(new_embeddings).astype('float32')

            if self.embedder.index is None:
                self.embedder.build_index(new_emb_np)
            else:
                self.embedder.index.add(new_emb_np)
            
            self.embedder.save_index()
        else:
            print("✨ Tất cả node đều đã được đánh chỉ mục vector.")

        # 5. Đẩy toàn bộ vào Neo4j (Dùng MERGE để cập nhật nếu có thay đổi)
        print(f"🔗 Đang đồng bộ {len(unique_nodes)} nodes và {len(links)} links vào Neo4j...")
        with self.driver.session() as session:
            for node in unique_nodes:
                session.run("""
                    MERGE (e:Entity {id: $id})
                    SET e.user = $user, e.desc = $desc, e.type = $type
                """, id=node['id'], user=node['user'], desc=node['desc'], type=node.get('type', 'General'))

            for link in links:
                session.run("""
                    MATCH (a:Entity {id: $src}), (b:Entity {id: $tgt})
                    MERGE (a)-[r:RELATION {label: $label}]->(b)
                """, src=link['source'], tgt=link['target'], label=link['label'])

        print("🎊 Toàn bộ thư mục dữ liệu đã được đồng bộ hóa!")

if __name__ == "__main__":
    sync_tool = DataSynchronizer()
    sync_tool.sync()
    sync_tool.close()