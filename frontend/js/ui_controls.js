import { askQuestion } from './api.js';
import { highlightNodes } from './app.js';

// --- 1. KHỞI TẠO CÁC PHẦN TỬ UI ---
const askBtn = document.getElementById('ask-btn');
const searchInput = document.getElementById('search-input');
const aiResponseArea = document.getElementById('ai-response-area');
const aiText = document.getElementById('ai-text');

// --- 2. HÀM XỬ LÝ CÂU HỎI ---
async function handleQuery() {
    const query = searchInput.value.trim();
    
    if (!query) {
        aiText.innerHTML = "<span style='color: #ff9800;'>Bbi ơi, nhập câu hỏi đã chứ! :33</span>";
        return;
    }

    // Trạng thái đang xử lý (Loading)
    askBtn.disabled = true;
    aiText.innerHTML = `<div class="typing-indicator"><span>.</span><span>.</span><span>.</span></div> 
                        <p style="font-size: 0.8em; color: #888;">Gemini đang lục lọi Knowledge Graph...</p>`;

    try {
        // Gọi API Backend
        const result = await askQuestion(query);

        // 1. Hiển thị câu trả lời từ Gemini
        // Dùng replace để format xuống dòng cho đẹp
        aiText.innerHTML = result.answer.replace(/\n/g, '<br>');

        // 2. Kích hoạt hiệu ứng Highlight và Fly-to trên đồ thị 3D
        if (result.relevant_nodes && result.relevant_nodes.length > 0) {
            highlightNodes(result.relevant_nodes);
        } else {
            aiText.innerHTML += "<br/><br/><small>(Lưu ý: Không tìm thấy node liên quan trực tiếp để highlight)</small>";
        }

    } catch (error) {
        console.error("UI Error:", error);
        aiText.innerHTML = "<span style='color: #ff3e3e;'>Lỗi rồi bbi ơi! Check lại Backend (uv run uvicorn) xem có đang chạy không nhé.</span>";
    } finally {
        askBtn.disabled = false;
        searchInput.value = ""; // Xóa ô input sau khi hỏi
    }
}

// --- 3. LẮNG NGHE SỰ KIỆN ---

// Click nút "Hỏi"
askBtn.addEventListener('click', handleQuery);

// Nhấn phím Enter trong ô input
searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        handleQuery();
    }
});

// Xuất hàm nếu cần dùng ở nơi khác
export { handleQuery };