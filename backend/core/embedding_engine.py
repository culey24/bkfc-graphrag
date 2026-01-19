import faiss
import numpy as np
import os
import torch # Nhớ import torch nhé bbi
from sentence_transformers import SentenceTransformer

class EmbeddingEngine:
    def __init__(self, model_name='paraphrase-multilingual-MiniLM-L12-v2'):
        # Tự động chọn cuda nếu có GPU, không thì dùng cpu
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model = SentenceTransformer(model_name, device=self.device)
        self.index_path = "data/processed/vector.index"
        self.index = None
        
        if os.path.exists(self.index_path):
            self.load_index()
            
    def encode(self, text):
        """Hàm này đảm bảo trả về Tensor để đồng bộ với logic cũ"""
        return self.model.encode(text, convert_to_tensor=True)

    def build_index(self, embeddings):
        # Kiểm tra nếu là torch tensor thì mới cần .cpu().detach()
        if torch.is_tensor(embeddings):
            emb_np = embeddings.cpu().detach().numpy().astype('float32')
        else:
            # Nếu đã là numpy array thì chỉ cần ép kiểu
            emb_np = np.array(embeddings).astype('float32')
            
        dimension = emb_np.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(emb_np)
        
    def save_index(self):
        if self.index:
            # Đảm bảo folder tồn tại trước khi lưu
            os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
            faiss.write_index(self.index, self.index_path)
            
    def load_index(self):
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)

    def search(self, query, k=3):
        """HÀM QUAN TRỌNG: Tìm kiếm các node liên quan nhất"""
        if self.index is None:
            print("❌ Lỗi: FAISS Index chưa được khởi tạo. Bbi hãy chạy sync_data.py trước nhé!")
            return []
        
        # Encode câu hỏi sang vector
        query_vec = self.model.encode([query]).astype('float32')
        
        # Thực hiện tìm kiếm k node gần nhất
        distances, indices = self.index.search(query_vec, k)
        
        # Trả về danh sách index (số nguyên)
        return indices[0].tolist()