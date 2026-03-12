/**
 * FusionMark - PDF 智能解析与高亮
 * 前端主逻辑
 */

// ============================================
// 配置
// ============================================
const CONFIG = {
    API_BASE_URL: 'http://localhost:8000',
    WS_BASE_URL: 'ws://localhost:8000',
    PDF_JS_WORKER: 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js'
};

// 实体颜色配置（与 CSS 变量对应）
const ENTITY_COLORS = {
    report_title: { bg: '#E8D5C4', text: '#5a4a3a', label: '报告标题' },
    company_name: { bg: '#E8D5C4', text: '#5a4a3a', label: '公司' },
    shipment_value: { bg: '#B8C5D6', text: '#3a4a5a', label: '出货量' },
    market_share: { bg: '#B8C5D6', text: '#3a4a5a', label: '市场份额' },
    yoy_change: { bg: '#A8D5BA', text: '#2a5a3a', label: '同比增长' },
    negative_change: { bg: '#E8B4B4', text: '#5a3a3a', label: '下降' },
    data_source: { bg: '#C9B8D6', text: '#4a3a5a', label: '数据来源' }
};

// ============================================
// 状态管理
// ============================================
const state = {
    currentTask: null,
    pdfDocument: null,
    currentPage: 1,
    zoomLevel: 1.0,
    extractedEntities: [],
    isProcessing: false
};

// ============================================
// DOM 元素
// ============================================
const elements = {
    uploadArea: document.getElementById('uploadArea'),
    fileInput: document.getElementById('fileInput'),
    urlInput: document.querySelector('.url-input'),
    progressCard: document.getElementById('progressCard'),
    progressFill: document.getElementById('progressFill'),
    progressPercent: document.getElementById('progressPercent'),
    progressStatus: document.getElementById('progressStatus'),
    entitiesPreview: document.getElementById('entitiesPreview'),
    entityTags: document.getElementById('entityTags'),
    emptyState: document.getElementById('emptyState'),
    pdfViewer: document.getElementById('pdfViewer'),
    pdfCanvas: document.getElementById('pdfCanvas'),
    downloadBtn: document.getElementById('downloadBtn')
};

// ============================================
// 初始化
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    initEventListeners();
    initPDFJS();
});

function initPDFJS() {
    if (typeof pdfjsLib !== 'undefined') {
        pdfjsLib.GlobalWorkerOptions.workerSrc = CONFIG.PDF_JS_WORKER;
    }
}

function initEventListeners() {
    // 文件上传
    elements.uploadArea.addEventListener('click', () => elements.fileInput.click());
    elements.fileInput.addEventListener('change', handleFileSelect);
    
    // 拖放上传
    elements.uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        elements.uploadArea.classList.add('dragover');
    });
    
    elements.uploadArea.addEventListener('dragleave', () => {
        elements.uploadArea.classList.remove('dragover');
    });
    
    elements.uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        elements.uploadArea.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length > 0 && files[0].type === 'application/pdf') {
            processFile(files[0]);
        }
    });
    
    // URL 提交
    document.querySelector('.url-input-group .btn-primary').addEventListener('click', handleURLSubmit);
    
    // 下载按钮
    elements.downloadBtn.addEventListener('click', downloadResult);
}

// ============================================
// 文件处理
// ============================================
function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file && file.type === 'application/pdf') {
        processFile(file);
    }
}

function handleURLSubmit() {
    const url = elements.urlInput.value.trim();
    if (!url) {
        showNotification('请输入 PDF 链接', 'warning');
        return;
    }
    processURL(url);
}

async function processFile(file) {
    // 暂时不支持文件上传，提示用户使用 URL 方式
    showNotification('文件上传功能暂未开放，请使用 URL 方式', 'warning');
    
    // 仅本地预览 PDF，不提交处理
    const fileURL = URL.createObjectURL(file);
    elements.emptyState.style.display = 'none';
    elements.pdfViewer.style.display = 'flex';
    await loadPDF(fileURL);
}

async function processURL(url) {
    showProgress();
    updateProgress(5, '正在提交任务...');
    
    try {
        // 提交任务
        const taskId = await submitTask(url);
        updateProgress(10, '任务已提交，等待处理...');
        
        // 连接 WebSocket 获取实时进度
        connectWebSocket(taskId);
    } catch (error) {
        updateProgress(0, '任务提交失败');
        state.isProcessing = false;
    }
}

// ============================================
// 模拟处理（用于演示）
// ============================================
async function simulateProcessing() {
    state.isProcessing = true;
    
    // 步骤 1: MinerU 解析
    await delay(800);
    updateStep('mineru', 'active');
    for (let i = 15; i <= 40; i += 5) {
        updateProgress(i, 'MinerU 解析文档结构...');
        await delay(200);
    }
    updateStep('mineru', 'completed');
    
    // 步骤 2: 实体提取
    await delay(500);
    updateStep('extract', 'active');
    for (let i = 45; i <= 70; i += 5) {
        updateProgress(i, 'AI 提取关键实体...');
        await delay(200);
    }
    
    // 添加示例实体
    addSampleEntities();
    updateStep('extract', 'completed');
    
    // 步骤 3: 高亮渲染
    await delay(500);
    updateStep('highlight', 'active');
    for (let i = 75; i <= 100; i += 5) {
        updateProgress(i, '渲染高亮 PDF...');
        await delay(150);
    }
    updateStep('highlight', 'completed');
    
    // 完成
    updateProgress(100, '处理完成！');
    elements.downloadBtn.style.display = 'inline-flex';
    state.isProcessing = false;
}

function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// ============================================
// 进度控制
// ============================================
function showProgress() {
    elements.progressCard.style.display = 'block';
    elements.emptyState.style.display = 'none';
    elements.entitiesPreview.style.display = 'block';
}

function updateProgress(percent, status) {
    elements.progressFill.style.width = `${percent}%`;
    elements.progressPercent.textContent = `${percent}%`;
    elements.progressStatus.textContent = status;
}

function updateStep(stepName, status) {
    const step = document.querySelector(`[data-step="${stepName}"]`);
    if (step) {
        step.classList.remove('active', 'completed');
        step.classList.add(status);
    }
}

// ============================================
// 实体展示
// ============================================
function addSampleEntities() {
    const sampleEntities = [
        { text: 'IDC 全球智能手机跟踪报告', type: 'report_title' },
        { text: 'Apple', type: 'company_name' },
        { text: 'Samsung', type: 'company_name' },
        { text: 'Xiaomi', type: 'company_name' },
        { text: '7,860 万台', type: 'shipment_value' },
        { text: '23.2%', type: 'market_share' },
        { text: '+4.9%', type: 'yoy_change' },
        { text: '-11.4%', type: 'negative_change' },
        { text: 'IDC', type: 'data_source' }
    ];
    
    state.extractedEntities = sampleEntities;
    renderEntityTags();
}

function renderEntityTags() {
    elements.entityTags.innerHTML = state.extractedEntities.map(entity => {
        const config = ENTITY_COLORS[entity.type] || ENTITY_COLORS.data_source;
        const className = entity.type.includes('company') ? 'company' :
                         entity.type.includes('value') || entity.type.includes('share') ? 'value' :
                         entity.type.includes('yoy') || entity.type.includes('positive') ? 'positive' :
                         entity.type.includes('negative') ? 'negative' : 'other';
        
        return `
            <span class="entity-tag ${className}" title="${config.label}">
                ${entity.text}
            </span>
        `;
    }).join('');
}

function renderEntitiesFromResult(result) {
    // 从后端返回的分类计数生成实体展示
    const categoryCounts = result.category_counts || {};
    const entities = [];
    
    // 这里简化展示，实际应该从后端获取详细的提取实体列表
    // 目前只展示分类统计
    for (const [category, count] of Object.entries(categoryCounts)) {
        entities.push({
            text: `${category}: ${count}个`,
            type: category
        });
    }
    
    if (entities.length > 0) {
        state.extractedEntities = entities;
        renderEntityTags();
    }
}

async function loadResultPreview(taskId) {
    try {
        // 先尝试获取任务状态，确认结果文件路径
        const response = await fetch(`${CONFIG.API_BASE_URL}/api/v1/tasks/${taskId}`);
        if (!response.ok) throw new Error('获取任务状态失败');
        
        const taskData = await response.json();
        if (taskData.result && taskData.result.output_path) {
            // 使用下载接口加载PDF预览
            const pdfUrl = `${CONFIG.API_BASE_URL}/api/v1/tasks/${taskId}/download`;
            await loadPDF(pdfUrl);
        }
    } catch (error) {
        console.error('加载预览失败:', error);
        showNotification('PDF预览加载失败，但可正常下载', 'warning');
    }
}

// ============================================
// PDF 加载与预览
// ============================================
async function loadPDF(url) {
    try {
        const loadingTask = pdfjsLib.getDocument(url);
        state.pdfDocument = await loadingTask.promise;
        
        elements.pdfViewer.style.display = 'flex';
        await renderPage(1);
    } catch (error) {
        console.error('PDF 加载失败:', error);
        showNotification('PDF 加载失败', 'error');
    }
}

async function renderPage(pageNumber) {
    if (!state.pdfDocument) return;
    
    const page = await state.pdfDocument.getPage(pageNumber);
    const canvas = elements.pdfCanvas;
    const context = canvas.getContext('2d');
    
    const viewport = page.getViewport({ scale: state.zoomLevel });
    canvas.width = viewport.width;
    canvas.height = viewport.height;
    
    await page.render({
        canvasContext: context,
        viewport: viewport
    }).promise;
    
    state.currentPage = pageNumber;
    updatePageInfo();
}

function updatePageInfo() {
    const pageInfo = document.querySelector('.page-info input');
    const totalPages = state.pdfDocument ? state.pdfDocument.numPages : 0;
    pageInfo.value = state.currentPage;
    pageInfo.max = totalPages;
    document.querySelector('.page-info').innerHTML = 
        `第 <input type="number" value="${state.currentPage}" min="1" max="${totalPages}"> / ${totalPages} 页`;
}

// ============================================
// API 交互（实际使用）
// ============================================
async function submitTask(documentUrl, options = {}) {
    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/api/v1/tasks`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                document_url: documentUrl,
                model: options.model || 'vlm',
                enable_ocr: options.enable_ocr !== false,
                enable_formula: options.enable_formula !== false,
                enable_table: options.enable_table !== false,
                language: options.language || 'ch',
                output_filename: options.output_filename || null,
                custom_title: options.custom_title || null,
                custom_prompt: options.custom_prompt || null
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '提交任务失败');
        }
        
        const data = await response.json();
        state.currentTask = data.task_id;
        return data.task_id;
    } catch (error) {
        console.error('提交任务失败:', error);
        showNotification(error.message || '提交任务失败，请检查网络', 'error');
        throw error;
    }
}

function connectWebSocket(taskId) {
    console.log(`[WebSocket] 正在连接: ${CONFIG.WS_BASE_URL}/ws/${taskId}`);
    const ws = new WebSocket(`${CONFIG.WS_BASE_URL}/ws/${taskId}`);
    
    ws.onopen = () => {
        console.log('[WebSocket] 已连接');
    };
    
    ws.onmessage = (event) => {
        console.log('[WebSocket] 收到消息:', event.data);
        try {
            const data = JSON.parse(event.data);
            handleWebSocketMessage(data);
        } catch (e) {
            console.error('[WebSocket] 解析消息失败:', e);
        }
    };
    
    ws.onclose = (event) => {
        console.log('[WebSocket] 已断开:', event.code, event.reason);
    };
    
    ws.onerror = (error) => {
        console.error('[WebSocket] 错误:', error);
        showNotification('WebSocket 连接错误', 'error');
    };
    
    // 保存 WebSocket 实例以便调试
    state.ws = ws;
}

function handleWebSocketMessage(data) {
    console.log('[WebSocket] 处理消息:', data.type, data);
    
    if (data.type === 'connected') {
        console.log('[WebSocket] 初始状态:', data.data);
        const taskData = data.data;
        if (taskData.status === 'failed') {
            handleTaskFailed(taskData.message || '任务处理失败');
        }
        return;
    }
    
    if (data.type === 'heartbeat') {
        console.log('[WebSocket] 收到心跳');
        return;
    }
    
    if (data.type === 'progress') {
        const taskData = data.data;
        console.log('[WebSocket] 进度更新:', taskData);
        const { progress, status, message, result } = taskData;
        
        // 使用新的分阶段进度
        if (progress && progress.stage) {
            updateProgressByStage(progress);
        } else {
            // 兼容旧格式
            const percent = calculateProgressPercent(progress, status);
            updateProgress(percent, message || getStatusMessage(status));
            updateStepsByProgress(progress, status);
        }
        
        // 完成
        if (status === 'completed') {
            updateStep('highlight', 'completed');
            elements.downloadBtn.style.display = 'inline-flex';
            showNotification('处理完成！', 'success');
            state.isProcessing = false;
            
            if (result && result.category_counts) {
                renderEntitiesFromResult(result);
            }
            loadResultPreview(state.currentTask);
        }
        
        // 失败
        if (status === 'failed') {
            handleTaskFailed(message || '处理失败');
        }
    }
}

function updateProgressByStage(progress) {
    const stage = progress.stage;
    const stageProgress = progress.stage_progress || 0;
    const overallProgress = progress.overall_progress || 0;
    
    // 阶段名称映射
    const stageNames = {
        'pending': '准备中',
        'mineru': 'MinerU 解析',
        'extraction': '实体提取',
        'highlight': '高亮渲染',
        'completed': '处理完成',
        'failed': '处理失败'
    };
    
    // 更新总体进度条
    updateProgress(overallProgress, `${stageNames[stage] || stage}: ${stageProgress}%`);
    
    // 更新各步骤状态 - 注意后端阶段名和前端 data-step 的映射
    const stepMapping = {
        'mineru': 'mineru',
        'extraction': 'extract',  // 后端叫 extraction，前端叫 extract
        'highlight': 'highlight'
    };
    
    // 遍历所有阶段，更新状态
    for (const [backendStage, frontendStep] of Object.entries(stepMapping)) {
        const el = document.querySelector(`[data-step="${frontendStep}"]`);
        if (!el) continue;
        
        const stepData = progress[backendStage];
        if (!stepData) continue;
        
        const stepState = stepData.state;
        
        // 清除旧状态
        el.classList.remove('active', 'completed', 'failed');
        
        // 判断步骤状态
        // 如果当前阶段是此阶段或之后，且状态为 completed，则标记为完成
        // 如果当前阶段正是此阶段且状态为 running，则标记为活跃
        const stageOrder = ['mineru', 'extraction', 'highlight'];
        const currentStageIndex = stageOrder.indexOf(stage);
        const thisStageIndex = stageOrder.indexOf(backendStage);
        
        if (stepState === 'completed' || stepState === 'done') {
            el.classList.add('completed');
        } else if (stepState === 'running' || (stage === backendStage && stepState !== 'pending')) {
            el.classList.add('active');
            // 更新步骤进度文本
            const label = el.querySelector('.step-label');
            if (label && stepData.progress !== undefined) {
                const baseText = {
                    'mineru': 'MinerU 解析',
                    'extraction': '实体提取',
                    'highlight': '高亮渲染'
                }[backendStage];
                label.textContent = `${baseText} (${stepData.progress}%)`;
            }
        } else if (stepState === 'failed') {
            el.classList.add('failed');
        } else if (thisStageIndex < currentStageIndex) {
            // 当前阶段之前的阶段都标记为完成
            el.classList.add('completed');
        }
    }
}

function handleTaskFailed(message) {
    // 更新UI显示失败状态
    updateProgress(0, `失败: ${message}`);
    
    // 重置所有步骤为失败状态
    document.querySelectorAll('.step').forEach(step => {
        step.classList.remove('active', 'completed');
        step.classList.add('failed');
    });
    
    // 显示错误通知
    showNotification(message, 'error');
    
    // 重置处理状态
    state.isProcessing = false;
    
    // 隐藏下载按钮
    elements.downloadBtn.style.display = 'none';
}

function getStatusMessage(status) {
    const messages = {
        'pending': '等待处理...',
        'processing': '正在处理...',
        'completed': '处理完成！',
        'failed': '处理失败'
    };
    return messages[status] || '未知状态';
}

function updateStepsByProgress(progress, status) {
    if (!progress) return;
    
    // MinerU 解析步骤
    if (progress.mineru_state === 'pending') {
        updateStep('mineru', 'active');
    } else if (progress.mineru_state === 'running') {
        updateStep('mineru', 'active');
    } else if (progress.mineru_state === 'completed') {
        updateStep('mineru', 'completed');
        updateStep('extract', 'active');
    }
    
    // 实体提取步骤
    if (progress.extraction_count > 0) {
        updateStep('extract', 'completed');
        updateStep('highlight', 'active');
    }
    
    // 高亮渲染步骤
    if (progress.highlight_count > 0) {
        updateStep('highlight', 'completed');
    }
}

function calculateProgressPercent(progress, status) {
    if (!progress) return 0;
    
    // 如果已完成，返回100%
    if (status === 'completed') return 100;
    if (status === 'failed') return 0;
    
    let percent = 10; // 基础进度（任务已创建）
    
    // MinerU 解析阶段 (10% - 50%)
    if (progress.mineru_state === 'pending') {
        percent = 15;
    } else if (progress.mineru_state === 'running') {
        const mineruProgress = progress.mineru_total > 0 
            ? (progress.mineru_progress / progress.mineru_total) 
            : 0;
        percent = 15 + Math.round(mineruProgress * 35);
    } else if (progress.mineru_state === 'completed') {
        percent = 50;
    }
    
    // 实体提取阶段 (50% - 80%)
    if (progress.extraction_count > 0) {
        percent = Math.max(percent, 50 + Math.min(progress.extraction_count * 5, 30));
    }
    
    // 高亮渲染阶段 (80% - 100%)
    if (progress.highlight_count > 0) {
        percent = Math.max(percent, 80 + Math.min(progress.highlight_count * 2, 20));
    }
    
    return Math.min(Math.round(percent), 99); // 完成前最高99%
}

// ============================================
// 下载结果
// ============================================
async function downloadResult() {
    if (!state.currentTask) {
        showNotification('没有可下载的结果', 'warning');
        return;
    }
    
    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/api/v1/tasks/${state.currentTask}/download`);
        const blob = await response.blob();
        
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `highlighted_${state.currentTask}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        showNotification('下载成功！', 'success');
    } catch (error) {
        console.error('下载失败:', error);
        showNotification('下载失败', 'error');
    }
}

// ============================================
// 通知提示
// ============================================
function showNotification(message, type = 'info') {
    // 简单的通知实现，可以扩展为更复杂的组件
    const colors = {
        info: '#002FA7',
        success: '#A8D5BA',
        warning: '#E8D5C4',
        error: '#E8B4B4'
    };
    
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        padding: 12px 20px;
        background: ${colors[type]};
        color: ${type === 'info' ? 'white' : '#333'};
        border-radius: 8px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        z-index: 1000;
        animation: slideIn 0.3s ease;
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// 添加动画样式
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);

// ============================================
// 导出（用于调试）
// ============================================
window.FusionMark = {
    state,
    CONFIG,
    loadPDF,
    renderPage
};
