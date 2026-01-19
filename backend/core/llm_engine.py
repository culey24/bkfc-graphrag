from google import genai # Thư viện mới cực gọn
import os
import requests
from dotenv import load_dotenv

load_dotenv()

class LLMEngine:
    def __init__(self, mode="gemini", model_name=None):
        """
        mode: "gemini" hoặc "ollama"
        model_name: Tên model (vd: "gemini-2.0-flash" hoặc "llama3.2")
        """
        self.mode = mode
        
        if self.mode == "gemini":
            # Khởi tạo Client theo chuẩn SDK mới
            self.model_name = model_name or "gemini-2.0-flash"
            self.client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
            print(f"--- [NEW SDK] LLM Engine: Cloud Mode ({self.model_name}) ---")
            
        elif self.mode == "ollama":
            self.model_name = model_name or "llama3.2"
            self.ollama_url = "http://localhost:11434/api/generate"
            print(f"--- LLM Engine: Local Mode ({self.model_name}) ---")

    def generate_answer(self, prompt, context):
        full_prompt = f"""
        Bạn là một trợ lý phân tích đồ thị tri thức y tế.
        Dựa trên DỮ LIỆU ĐỒ THỊ sau đây để trả lời câu hỏi:
        ---
        {context}
        ---
        CÂU HỎI: {prompt}
        """

        if self.mode == "gemini":
            try:
                # Cách gọi mới: client.models.generate_content
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=full_prompt
                )
                # SDK mới trả về kết quả trực tiếp qua .text
                return response.text
            except Exception as e:
                return f"Lỗi Gemini SDK mới: {str(e)}"

        elif self.mode == "ollama":
            payload = {
                "model": self.model_name,
                "prompt": full_prompt,
                "stream": False,
                "options": {"temperature": 0.2} # Giảm sáng tạo để trả lời chính xác dữ liệu
            }
            try:
                res = requests.post(self.ollama_url, json=payload)
                return res.json().get('response', 'Lỗi không nhận được phản hồi từ Ollama')
            except Exception as e:
                return f"Lỗi kết nối Ollama: {str(e)}"

        return "Mode không hợp lệ bbi ơi!"