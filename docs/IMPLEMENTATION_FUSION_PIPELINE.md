# MinerU + LangExtract 融合实现文档

## 文档信息

- **版本**: 1.0
- **日期**: 2026-02-05
- **状态**: 实现完成，待测试
- **相关文件**: `mineru_langextract_fusion_demo.py`

---

## 1. 实现概述

本实现完成了 **MinerU** 与 **LangExtract** 的融合管道，实现了从 PDF 解析、信息提取到高亮标注的完整流程。

### 1.1 解决的问题

| 问题 | 解决方案 |
|------|----------|
| LangExtract 只有文本，没有位置 | 通过 MinerU layout.json 建立位置索引 |
| 文本匹配困难 | 三级匹配策略（精确→包含→模糊） |
| 多粒度位置选择 | 使用 span 级精确匹配 |
| 可视化展示 | PyMuPDF 渲染彩色边框高亮 |

### 1.2 核心流程

```
PDF + MinerU 解析
    │
    ├──→ layout.json (位置数据)
    │       └── 构建 span 索引
    │
    └──→ full.md (文本数据)
            └── LangExtract 提取
                    │
                    ▼
            提取实体列表
                    │
                    ▼
            文本匹配引擎
            (精确/包含/模糊)
                    │
                    ▼
            带位置的提取结果
                    │
                    ▼
            PyMuPDF 渲染
                    │
                    ▼
            高亮 PDF 输出
```

---

## 2. 核心组件

### 2.1 数据结构

```python
@dataclass
class PositionMatch:
    """匹配结果"""
    page: int                      # 页码
    bbox: Tuple[float, float, float, float]  # 位置 [x0, y0, x1, y1]
    text: str                      # 匹配的原文
    confidence: float              # 置信度 0-1

@dataclass
class HighlightBox:
    """高亮框（最终渲染用）"""
    page: int
    bbox: Tuple[float, float, float, float]
    color: Tuple[float, float, float]  # RGB
    category: str                  # 提取类别
    text: str                      # 提取文本
```

### 2.2 模块职责

| 函数/类 | 职责 | 输入 | 输出 |
|---------|------|------|------|
| `run_langextract()` | LLM 信息提取 | Markdown 文本 | `List[Extraction]` |
| `build_span_index()` | 构建位置索引 | layout.json | `Dict[str, List[PositionMatch]]` |
| `fuzzy_match()` | 文本位置匹配 | 提取文本 + 索引 | `List[PositionMatch]` |
| `match_extractions()` | 批量匹配 | 提取列表 + 索引 | `List[HighlightBox]` |
| `render_highlights()` | PDF 渲染 | 高亮列表 + PDF | 高亮 PDF |

---

## 3. 关键算法

### 3.1 位置索引构建

```python
def build_span_index(layout: dict) -> Dict[str, List[PositionMatch]]:
    """
    遍历 layout.json 的所有层级，建立文本→位置的倒排索引
    
    遍历路径: pdf_info → para_blocks → lines → spans
    """
    index = {}
    
    for page_info in layout["pdf_info"]:
        for para_block in page_info["para_blocks"]:
            for line in para_block["lines"]:
                for span in line["spans"]:
                    content = span["content"].strip()
                    if content:
                        if content not in index:
                            index[content] = []
                        index[content].append(PositionMatch(
                            page=page_info["page_idx"],
                            bbox=tuple(span["bbox"]),
                            text=content,
                            confidence=1.0
                        ))
    return index
```

**设计要点：**
- 使用 span 级粒度（最精确）
- 保留重复文本（同一文本可能出现多次）
- 索引 key 为清洗后的文本内容

### 3.2 三级匹配策略

```python
def fuzzy_match(text: str, index: dict, threshold: float = 0.85):
    """
    三级匹配策略：
    
    Level 1: 精确匹配 (O(1))
        - 直接字典查找
        - 置信度: 1.0
        
    Level 2: 包含匹配 (O(n))
        - 检查 text 是否是某个 span 的子串
        - 置信度: 0.95
        
    Level 3: 模糊匹配 (O(n) + 计算)
        - 使用 difflib.SequenceMatcher 计算相似度
        - 阈值: 0.85
        - 置信度: similarity_score
    """
    # Level 1: 精确匹配
    if text in index:
        return index[text]
    
    # Level 2: 包含匹配
    for content, positions in index.items():
        if text in content:
            return positions
    
    # Level 3: 模糊匹配
    results = []
    for content, positions in index.items():
        similarity = SequenceMatcher(None, text, content).ratio()
        if similarity >= threshold:
            results.extend(positions)
    
    return sorted(results, key=lambda x: x.confidence, reverse=True)
```

**设计理由：**
- 精确匹配最快，处理完全一致的文本
- 包含匹配处理 LangExtract 清洗导致的差异（如 "Apple" vs "1. Apple"）
- 模糊匹配处理 OCR 误差或格式变化

### 3.3 颜色编码方案

```python
HIGHLIGHT_COLORS = {
    "report_title":   (1.0, 0.5, 0.0),   # 🟠 橙色
    "company_name":   (0.0, 0.8, 0.0),   # 🟢 绿色  
    "shipment_value": (0.0, 0.5, 1.0),   # 🔵 蓝色
    "market_share":   (0.8, 0.0, 1.0),   # 🟣 紫色
    "yoy_change":     (1.0, 0.0, 0.5),   # 🩷 粉色
    "data_source":    (0.5, 0.5, 0.5),   # ⚪ 灰色
}
```

---

## 4. 渲染实现

### 4.1 渲染效果

| 元素 | 实现方式 | 说明 |
|------|----------|------|
| 边框 | `shape.draw_rect()` + `shape.finish()` | 2px 宽度，彩色 |
| 标签 | `page.insert_text()` | 左上角，6字符缩写 |
| 注释 | `page.add_text_annot()` | 点击显示详细信息 |

### 4.2 渲染代码

```python
def render_highlights(input_pdf: str, highlights: List[HighlightBox], output_pdf: str):
    doc = fitz.open(input_pdf)
    
    # 按页分组
    page_highlights = group_by_page(highlights)
    
    for page_num, hls in page_highlights.items():
        page = doc[page_num]
        
        for hl in hls:
            rect = fitz.Rect(hl.bbox)
            
            # 1. 绘制彩色边框
            shape = page.new_shape()
            shape.draw_rect(rect)
            shape.finish(color=hl.color, fill=None, width=2)
            shape.commit()
            
            # 2. 添加类别标签
            page.insert_text(rect.tl + (2, 10), 
                           hl.category[:6], 
                           fontsize=7, 
                           color=hl.color)
            
            # 3. 添加交互注释
            page.add_text_annot(rect.tl, 
                              f"[{hl.category}]\n{hl.text}",
                              icon="Note")
    
    doc.save(output_pdf)
```

---

## 5. 配置与输入

### 5.1 输入文件

```
mineru_output/{task_id}/
├── {id}_origin.pdf      # 原始 PDF（渲染目标）
├── layout.json          # 位置数据（构建索引）
└── full.md              # 文本数据（LangExtract 输入）
```

### 5.2 LangExtract 配置

**提取类别定义：**

| 类别 | 描述 | 示例 |
|------|------|------|
| `report_title` | 报告标题 | "Top 5 Companies..." |
| `company_name` | 公司名称 | "Apple", "Samsung" |
| `shipment_value` | 出货量数值 | "81.3" |
| `market_share` | 市场份额 | "24.2%" |
| `yoy_change` | 同比增长 | "4.9%" |
| `data_source` | 数据来源 | "Source: IDC..." |

**示例配置：**

```python
examples = [
    lx.data.ExampleData(
        text="Top 5 Companies... 1. Apple 81.3 24.2%...",
        extractions=[
            lx.data.Extraction(
                extraction_class="company_name", 
                extraction_text="Apple"
            ),
            lx.data.Extraction(
                extraction_class="shipment_value", 
                extraction_text="81.3"
            ),
            # ...
        ]
    )
]
```

---

## 6. 预期输出

### 6.1 控制台输出

```
======================================================================
MinerU + LangExtract 融合演示
======================================================================

Step 1: LangExtract 信息提取
🤖 调用 LangExtract...
✅ 提取完成，共 12 个实体

📋 提取结果:
  1. [report_title] Top 5 Companies, Worldwide Smartphone Shipments...
  2. [company_name] Apple
  3. [shipment_value] 81.3
  ...

======================================================================
Step 2: 构建位置索引
✅ 索引构建完成，共 45 个 spans
   唯一文本数: 38

======================================================================
Step 3: 文本位置匹配
  ✓ [report_title] 'Top 5 Companies...' → 1 个位置
  ✓ [company_name] 'Apple' → 1 个位置
  ✓ [shipment_value] '81.3' → 1 个位置
  ...

✅ 匹配完成: 11/12

======================================================================
Step 4: PDF 高亮渲染
🎨 共 11 个高亮，分布在 1 页
💾 保存: highlight_output/smartphone_fusion_highlighted.pdf
```

### 6.2 输出文件

```
highlight_output/
└── smartphone_fusion_highlighted.pdf
```

**PDF 效果：**
- 🟠 橙色框：报告标题
- 🟢 绿色框：公司名称（Apple、Samsung等）
- 🔵 蓝色框：出货量数值
- 🟣 紫色框：市场份额百分比
- 🩷 粉色框：同比增长率
- ⚪ 灰色框：数据来源

---

## 7. 边界情况处理

| 情况 | 处理策略 | 效果 |
|------|----------|------|
| 匹配失败 | 记录日志，跳过该提取项 | PDF 中无高亮 |
| 多位置匹配 | 高亮所有匹配位置 | 多个同色框 |
| 重复文本 | 每个出现都高亮 | 多处标注 |
| 跨行文本 | 目前按 span 匹配 | 可能匹配到部分 |

---

## 8. 待优化点

1. **匹配粒度优化**
   - 当前使用 span 级
   - 可考虑对长文本使用 line 级或 para_block 级

2. **性能优化**
   - 大文档索引构建较慢
   - 可考虑使用 trie 树加速前缀匹配

3. **准确性提升**
   - 添加上下文验证（如验证数值是否在合理范围内）
   - 支持用户反馈修正

4. **功能扩展**
   - 支持表格内单元格级高亮
   - 支持多页文档处理
   - 支持批处理多个 PDF

---

## 9. 相关文档

| 文档 | 说明 |
|------|------|
| `PDF_HIGHLIGHT_PLAN.md` | 初期调研与方案设计 |
| `RESEARCH_PHASE_2_FUSION.md` | Phase 2 融合方案详细设计 |
| `IMPLEMENTATION_FUSION_PIPELINE.md` | 本文档，实现说明 |

---

## 10. 运行方式

```bash
# 确保环境变量设置
export DS_API_KEY=your_key
export DS_API_BASE_URL=https://api.deepseek.com/v1

# 运行演示
python mineru_langextract_fusion_demo.py
```

**输出位置：** `highlight_output/smartphone_fusion_highlighted.pdf`
