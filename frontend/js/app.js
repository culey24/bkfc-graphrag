import { fetchGraphData } from './api.js';

// --- 1. KHỞI TẠO CÁC THÀNH PHẦN GIAO DIỆN ---
const videoElement = document.querySelector('#webcam');
const canvasElement = document.querySelector('#output_canvas');
const canvasCtx = canvasElement.getContext('2d');
const handStatus = document.getElementById('hand-status');

// Khởi tạo đồ thị 3D trước để MediaPipe có thể tương tác
const Graph = ForceGraph3D()(document.getElementById('3d-graph'));

// --- 2. CẤU HÌNH MEDIAPIPE HANDS ---
const hands = new Hands({
    locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`
});

hands.setOptions({
    maxNumHands: 1,
    modelComplexity: 1,
    minDetectionConfidence: 0.7,
    minTrackingConfidence: 0.7
});

// --- BIẾN TOÀN CỤC ĐỂ LÀM MƯỢT (Đặt ngoài hàm onResults) ---
// --- BIẾN TOÀN CỤC (Đặt ngoài hàm onResults) ---
let currentCam = { x: 0, y: 0, z: 1000 };
let lastActiveNode = null; // Lưu node vừa mới chạm để tránh cập nhật liên tục

const lerpFactor = 0.15; 
const proximityThreshold = 100; // Khoảng cách để "kích hoạt" hiện thông tin (bbi tùy chỉnh nhé)

const neutralDist = 0.15; 
const zoomInPower = 1000; 
const zoomOutPower = 1000;
const minZ = 150;
const maxZ = 4000;

hands.onResults((results) => {
    canvasCtx.save();
    canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
    
    if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
        handStatus.innerText = "Active";
        const landmarks = results.multiHandLandmarks[0];
        
        drawConnectors(canvasCtx, landmarks, HAND_CONNECTIONS, {color: '#00FF00', lineWidth: 5});
        drawLandmarks(canvasCtx, landmarks, {color: '#FF0000', lineWidth: 2});

        const thumb = landmarks[4];
        const index = landmarks[8];
        const wrist = landmarks[0];

        // 1. TÍNH TOÁN TARGET (Giữ nguyên logic "bay" mượt của bbi)
        const fingerDist = Math.hypot(index.x - thumb.x, index.y - thumb.y);
        const deltaZoom = fingerDist - neutralDist;

        const targetX = (index.x - 0.5) * 600 + (wrist.x - 0.5) * 200;
        const targetY = -(index.y - 0.5) * 600; 
        
        let targetZ = currentCam.z;
        if (Math.abs(deltaZoom) > 0.02) {
            const power = deltaZoom > 0 ? zoomInPower : zoomOutPower;
            targetZ -= deltaZoom * power;
        }
        targetZ = Math.max(minZ, Math.min(maxZ, targetZ));

        // 2. LERP (Làm mượt chuyển động)
        currentCam.x += (targetX - currentCam.x) * lerpFactor;
        currentCam.y += (targetY - currentCam.y) * lerpFactor;
        currentCam.z += (targetZ - currentCam.z) * lerpFactor;

        // 3. CẬP NHẬT CAMERA
        Graph.cameraPosition({ x: currentCam.x, y: currentCam.y, z: currentCam.z }, null, 0);

        // 4. LOGIC PHÁT HIỆN NODE Ở GẦN (PROXIMITY)
        const { nodes } = Graph.graphData();
        let closestNode = null;
        let minD = proximityThreshold;

        nodes.forEach(node => {
            // Khoảng cách Euclid 3D từ Camera tới Node
            const d = Math.hypot(
                node.x - currentCam.x,
                node.y - currentCam.y,
                node.z - currentCam.z
            );
            if (d < minD) {
                minD = d;
                closestNode = node;
            }
        });

        // 5. HIỂN THỊ THÔNG TIN TỰ ĐỘNG
        if (closestNode) {
            if (lastActiveNode !== closestNode.id) {
                lastActiveNode = closestNode.id;
                
                const responseArea = document.getElementById('ai-text');
                responseArea.innerHTML = `
                    <div style="border-left: 4px solid #007bff; padding-left: 10px; background: rgba(0,123,255,0.05);">
                        <h3 style="color: #007bff; margin: 0;">📍 ${closestNode.user}</h3>
                        <p style="margin: 5px 0; color: #333;">${closestNode.desc}</p>
                    </div>
                `;
                
                // Highlight node bằng màu xanh dương đậm
                Graph.nodeColor(n => n.id === closestNode.id ? '#007bff' : n.color);
            }
        }

        // Cập nhật status cho bbi dễ nhìn
        if (deltaZoom > 0.02) handStatus.innerText = "Zooming In 🚀";
        else if (deltaZoom < -0.02) handStatus.innerText = "Zooming Out 🛸";
        else if (closestNode) handStatus.innerText = `Focus: ${closestNode.user} ✨`;
        else handStatus.innerText = "Floating... 🌌";

    } else {
        handStatus.innerText = "Off";
    }
    canvasCtx.restore();
});

// Khởi động Camera
const camera = new Camera(videoElement, {
    onFrame: async () => {
        await hands.send({image: videoElement});
    },
    width: 640,
    height: 480
});
camera.start();

// --- 3. KHỞI TẠO VÀ CẤU HÌNH ĐỒ THỊ 3D ---
export async function initGraph() {
    const data = await fetchGraphData();

    Graph.graphData(data)
        .backgroundColor('#ffffff') // ĐỔI SANG NỀN TRẮNG
        .nodeLabel(node => `<div style="color: #000; background: #fff; padding: 5px; border-radius: 5px; border: 1px solid #ddd;">
                            <b>${node.user}</b><br/>${node.desc}</div>`)
        .nodeAutoColorBy('type')
        .nodeRelSize(7)
        // ĐỔI MÀU LINK SANG MÀU TỐI (Xám hoặc xanh nhạt)
        .linkColor(() => 'rgba(0, 0, 0, 0.15)') 
        .linkDirectionalParticles(2)
        .linkDirectionalParticleSpeed(0.005)
        .linkWidth(1)
        // Hiệu ứng khi lại gần node
        .nodeCanvasObjectMode(() => 'after');

    // Cập nhật lực kéo để đồ thị giãn ra đẹp hơn trên nền sáng
    Graph.d3Force('charge').strength(-200);
}

// --- 4. HÀM HIGHLIGHT KHI AI TRẢ LỜI (FLY-TO) ---
export function highlightNodes(nodeIds) {
    if (!nodeIds || nodeIds.length === 0) return;

    const { nodes } = Graph.graphData();
    const targetNode = nodes.find(n => nodeIds.includes(n.id));
    
    // 1. Hiệu ứng Fly-to: Bay camera đến node liên quan
    if (targetNode) {
        const distance = 150; // Khoảng cách dừng của camera
        const distRatio = 1 + distance / Math.hypot(targetNode.x, targetNode.y, targetNode.z);

        Graph.cameraPosition(
            { 
                x: targetNode.x * distRatio, 
                y: targetNode.y * distRatio, 
                z: targetNode.z * distRatio 
            },
            targetNode, // Look at target
            2000 // Thời gian bay (ms)
        );
    }

    // 2. Làm mờ các node không liên quan
    Graph.nodeOpacity(node => nodeIds.includes(node.id) ? 1 : 0.15);
    Graph.nodeColor(node => nodeIds.includes(node.id) ? '#ff3e3e' : node.color);
    Graph.linkOpacity(link => nodeIds.includes(link.source.id) ? 0.8 : 0.05);

    // Sau 10 giây thì khôi phục độ mờ bình thường
    setTimeout(() => {
        Graph.nodeOpacity(0.9);
        Graph.linkOpacity(0.2);
    }, 10000);
}

// Chạy khởi tạo
initGraph();