import os
from pathlib import Path
from neo4j import GraphDatabase

# Cấu hình đường dẫn
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "processed"
INDEX_PATH = DATA_DIR / "vector.index"
NEO4J_URI = "bolt://localhost:7687"

def nuke():
    print("☢️  Bắt đầu chiến dịch dọn dẹp hệ thống (Giữ lại JSON)...")

    # 1. DỌN DẸP NEO4J (Xóa thực thể và quan hệ trên DB)
    print("🔗 Đang xóa dữ liệu trong Neo4j...")
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=None)
        with driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        driver.close()
        print("✅ Neo4j đã trống trơn.")
    except Exception as e:
        print(f"❌ Lỗi khi dọn Neo4j: {e} (Bbi đã bật Docker chưa?)")

    # 2. XÓA FILE VECTOR INDEX (FAISS)
    # Xóa cái này để khi sync lại, script sẽ tạo embedding mới từ đầu cho chính xác
    print("🧠 Đang xóa bộ nhớ Vector (FAISS)...")
    if INDEX_PATH.exists():
        os.remove(INDEX_PATH)
        print(f"✅ Đã xóa file index: {INDEX_PATH}")
    else:
        print("ℹ️  Không tìm thấy file vector.index, bỏ qua.")

    print("\n📂 Trạng thái folder processed: Các file JSON vẫn được giữ nguyên.")
    print("✨ NHIỆM VỤ HOÀN THÀNH!")
    print("👉 Giờ bbi có thể sửa các file JSON rồi chạy sync_data.py để nạp lại nhé!")

if __name__ == "__main__":
    confirm = input("⚠️  Xác nhận dọn dẹp DB và Vector Index? (y/n): ")
    if confirm.lower() == 'y':
        nuke()
    else:
        print("❌ Đã hủy lệnh.")