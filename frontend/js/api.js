const API_BASE_URL = "http://localhost:8000";

export async function fetchGraphData() {
    try {
        const response = await fetch(`${API_BASE_URL}/graph`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error("Lỗi khi lấy dữ liệu graph:", error);
        return { nodes: [], links: [] };
    }
}

export async function askQuestion(query) {
    try {
        const response = await fetch(`${API_BASE_URL}/ask`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query })
        });
        if (!response.ok) throw new Error(`AI Backend error! status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error("Lỗi khi gửi câu hỏi:", error);
        // Trả về cấu trúc mặc định để tránh lỗi crash ở UI
        return { answer: "Không thể kết nối với trí tuệ nhân tạo lúc này.", relevant_nodes: [] };
    }
}