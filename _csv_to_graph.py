import pandas as pd
import json
import requests
import time
import re
from pathlib import Path

# --- CẤU HÌNH ---
BASE_PATH = Path("data")
INPUT_CSV = BASE_PATH / "raw" / "tuyensinh.csv"
TAGGED_CSV = BASE_PATH / "processed" / "tuyensinh_tagged.csv"
OUTPUT_JSON = BASE_PATH / "processed" / "bkfc_graph_final.json"

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2"

def normalize_tag(tag):
    """Giúp 'Tuyển sinh' và 'tuyển sinh' không bị tách thành 2 node khác nhau"""
    # Loại bỏ khoảng trắng thừa và chuyển về chữ thường để tạo ID
    tag = tag.strip()
    tag_id = re.sub(r'\s+', '_', tag).upper() # Ví dụ: "Tuyển sinh" -> "TUYỂN_SINH"
    return tag, tag_id

ALLOWED_TAGS = [
    "BK FC - Sứ mệnh & Tổ chức", # Các câu về nhiệm vụ thành viên, giai đoạn hoạt động
    "BK FC - Hoạt động & Sự kiện", # Các câu về Về trường, Vành nón xanh, BK Tour
    "Thông tin chung HCMUT",       # Lịch sử, triết lý giáo dục, số lượng khoa, kiểm định
    "Phương thức xét tuyển",       # Các câu về đối tượng, phương thức tổng hợp, ưu tiên
    "Xét tuyển tổng hợp",          # Các câu về cách tính điểm, tiêu chí đánh giá, thang điểm
    "Chỉ tiêu & Điểm chuẩn",       # Các câu về số lượng tuyển sinh, điểm chuẩn các ngành
    "Quy đổi điểm & ACT/SAT/IELTS",# Các câu về cách tính điểm ngoại ngữ, chứng chỉ quốc tế
    "Học phí & Học bổng",          # Các câu về học phí các hệ, học bổng khuyến khích
    "Chương trình PFIEV",          # Các câu riêng về hệ kỹ sư chất lượng cao Pháp
    "Chương trình Dạy & Học bằng tiếng Anh/Tiên tiến", # Các câu về tiêu chuẩn đầu vào, ngôn ngữ
    "Chương trình Tài năng",       # Các câu về điều kiện xét tuyển, cơ sở học tập của hệ tài năng
    "Chương trình Chuyển tiếp Quốc tế/Định hướng Nhật Bản", # Các câu về ngành đào tạo quốc tế
    "Khoa & Ngành đào tạo",        # Các câu hỏi về ngành này thuộc khoa nào, mã ngành
    "Cơ sở vật chất & Ký túc xá",  # Địa chỉ trường, ký túc xá, văn phòng tuyển sinh
    "Kỹ năng tư vấn",              # Lời khuyên cho học sinh, những điều nên tránh khi tư vấn
    "Khác"                         # Nhãn mặc định khi không khớp các mục trên
]

def get_tags_from_ollama(question, answer):
    """Ép Ollama chỉ được chọn từ danh sách ALLOWED_TAGS"""
    
    # Chuyển list tag thành chuỗi để đưa vào prompt
    tags_str = ", ".join(ALLOWED_TAGS)
    
    prompt = f"""
    Bạn là thành viên nòng cốt của BKFC. Nhiệm vụ của bạn là phân loại cặp QA sau vào các nhãn phù hợp.
    
    CHỈ ĐƯỢC CHỌN TỪ DANH SÁCH NHÃN SAU:
    [{tags_str}]
    
    NGUYÊN TẮC:
    1. Chọn tối đa 2-3 nhãn phù hợp nhất.
    2. Nếu không có nhãn nào phù hợp, trả về "Khác".
    3. Chỉ trả về các nhãn (TAGS) cách nhau bằng dấu phẩy. Không giải thích.

    Q: "{question}"
    A: "{answer}"
    TAGS:"""

    payload = {
        "model": "llama3.2",
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.0} # Để 0.0 để AI bám sát danh sách nhất có thể
    }
    
    try:
        res = requests.post("http://localhost:11434/api/generate", json=payload)
        tags_raw = res.json().get('response', '').strip()
        
        # Hậu kiểm: Chỉ lấy những tag thực sự nằm trong danh sách ALLOWED_TAGS
        extracted_tags = [t.strip() for t in tags_raw.split(',') if t.strip() in ALLOWED_TAGS]
        
        return ", ".join(extracted_tags) if extracted_tags else "Khác"
    except:
        return "Khác"

def step_1_tagging():
    """Đọc gốc -> Gắn thẻ -> Lưu CSV tagged"""
    print(f"🚀 [BƯỚC 1] Đang nhờ Ollama gắn thẻ dữ liệu cho culey...")
    
    if not INPUT_CSV.exists():
        print(f"❌ Lỗi: Không tìm thấy file đầu vào tại {INPUT_CSV}")
        return False

    # Đọc dữ liệu
    df = pd.read_csv(INPUT_CSV)
    total_rows = len(df)
    print(f"📋 Tìm thấy {total_rows} câu hỏi cần xử lý.")

    tags_list = []
    start_time = time.time()

    for i, row in df.iterrows():
        q = row['Question']
        a = row['Answer']
        
        # In để biết đang xử lý đến đâu
        print(f"🔄 [{i+1}/{total_rows}] Đang phân loại: {q[:50]}...", end=" ", flush=True)
        
        # Gọi hàm xử lý
        tag_result = get_tags_from_ollama(q, a)
        tags_list.append(tag_result)
        
        # In kết quả tag để debug
        print(f"✅ Tags: [{tag_result}]")

    # Gán vào dataframe
    df['Tags'] = tags_list
    
    # Lưu file
    df.to_csv(TAGGED_CSV, index=False, encoding='utf-8-sig')
    
    end_time = time.time()
    duration = end_time - start_time
    print(f"\n✨ Hoàn thành!")
    print(f"⏱️ Tổng thời gian: {duration:.2f} giây (Trung bình: {duration/total_rows:.2f}s/câu)")
    print(f"💾 Đã lưu file trung gian: {TAGGED_CSV}")
    
    return True

def step_2_convert_to_json():
    """Đọc tagged -> Chuyển sang JSON Graph"""
    print(f"🚀 [BƯỚC 2] Đang tạo Graph cho BKFC...")
    df = pd.read_csv(TAGGED_CSV)
    nodes, links, unique_tags = [], [], {}

    for _, row in df.iterrows():
        qa_id = f"QA_{row['ID']}"
        nodes.append({"id": qa_id, "user": str(row['Question']), "desc": str(row['Answer']), "type": "QA_Pair"})

        tag_list = [t.strip() for t in str(row['Tags']).split(',') if t.strip()]
        for tag_name in tag_list:
            display_name, tag_id = normalize_tag(tag_name)
            tag_key = f"TAG_{tag_id}"

            if tag_key not in unique_tags:
                unique_tags[tag_key] = {
                    "id": tag_key, 
                    "user": display_name, 
                    "desc": f"Thông tin về {display_name} tại Bách Khoa.", 
                    "type": "Keyword"
                }
            links.append({"source": qa_id, "target": tag_key, "label": "LIÊN_QUAN"})

    nodes.extend(list(unique_tags.values()))
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump({"nodes": nodes, "links": links}, f, ensure_ascii=False, indent=2)
    print(f"🎉 Xong! File JSON sẵn sàng tại {OUTPUT_JSON}")

if __name__ == "__main__":
    if step_1_tagging(): step_2_convert_to_json()