# MinerU + LangExtract + PyMuPDF 融合方案
## 阶段性研究文档 - Phase 2: 信息融合与PDF高亮

---

## 1. 当前进展总结

### ✅ 已完成验证

| 组件 | 状态 | 验证结果 |
|------|------|----------|
| **MinerU 解析** | ✅ 已完成 | 可准确提取PDF文本+位置（layout.json） |
| **PyMuPDF 高亮** | ✅ 已完成 | 可在PDF上绘制透明边框，位置准确 |
| **坐标系统对齐** | ✅ 已完成 | MinerU bbox 与 PyMuPDF 坐标系兼容 |

### 📁 关键文件结构确认

```
mineru_output/
└── {task_id}/
    ├── {id}_origin.pdf          # 原始PDF（高亮绘制目标）
    ├── layout.json               # 详细布局（bbox层级结构）
    ├── {id}_content_list.json    # 简化文本列表
    └── full.md                   # Markdown文本（LangExtract输入）
```

### 🎯 layout.json 层级结构（已解析）

```
pdf_info[0]
├── para_blocks[0] (title)       # 段落级
│   ├── bbox: [0, 8, 1004, 49]
│   └── lines → spans
│
├── para_blocks[1] (table)       # 表格级
│   ├── bbox: [0, 55, 1080, 324]
│   └── blocks[]                 # 嵌套块
│       ├── block[0]: table_body  # 表格主体
│       └── block[1]: table_footnote  # 注脚
│
└── page_size: [1080, 358]
```

---

## 2. 核心问题：文本匹配

### 2.1 问题描述

**输入数据：**
- **layout.json**: 包含精确的 bbox 坐标，但文本被分割成 spans/lines
- **full.md**: 连续的 Markdown 文本（LangExtract 的输入）
- **LangExtract 输出**: 提取的文本片段（如 "Apple"、"81.3"）

**核心挑战：**
```
LangExtract 提取: "Apple"
    ↓ 需要匹配到
layout.json 中的位置: 
    - span[3]: {bbox: [x, y, x, y], content: "1. Apple"}
    或
    - span[4]: {bbox: [x, y, x, y], content: "Apple"}
    或
    - 多个 spans 组合
```

### 2.2 匹配难点分析

| 难点 | 说明 | 示例 |
|------|------|------|
| **文本清洗差异** | full.md 中的文本可能经过清洗 | `"1. Apple"` vs `"Apple"` |
| **跨度分割** | 一个提取项可能跨越多个 spans | `"Top 5 Companies"` 分散在多个 spans |
| **重复文本** | 同一文本在PDF中出现多次 | 页眉/页脚重复 |
| **坐标粒度** | 选择 para_block / line / span？ | 粗粒度 vs 细粒度 |

---

## 3. 融合方案设计

### 3.1 架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                      Fusion Pipeline                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MinerU Parse   │ →  │  Text Matcher   │ →  │  PDF Renderer   │
│                 │    │                 │    │                 │
│ - layout.json   │    │ - Fuzzy Match   │    │ - PyMuPDF       │
│ - full.md       │    │ - Index Build   │    │ - Highlight     │
│ - origin.pdf    │    │ - Multi-span    │    │ - Annotation    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                      │                      │
        ▼                      ▼                      ▼
   Position Data      Matched Positions       Highlighted PDF
```

### 3.2 核心类设计

```python
class TextPositionMatcher:
    """文本位置匹配器 - 核心融合组件"""
    
    def __init__(self, layout_json: dict):
        self.layout = layout_json
        self.text_index = self._build_span_index()
    
    def _build_span_index(self) -> Dict[str, List[SpanInfo]]:
        """
        建立文本索引
        遍历所有 spans，建立 content → [bbox, page] 的映射
        """
        index = {}
        for page in self.layout["pdf_info"]:
            for para in page["para_blocks"]:
                for line in para.get("lines", []):
                    for span in line.get("spans", []):
                        content = span["content"].strip()
                        if content:
                            if content not in index:
                                index[content] = []
                            index[content].append({
                                "bbox": span["bbox"],
                                "page": page["page_idx"],
                                "type": span.get("type", "text")
                            })
        return index
    
    def match_extraction(
        self, 
        extraction: lx.data.Extraction,
        strategy: str = "fuzzy"
    ) -> List[MatchResult]:
        """
        匹配提取项到PDF位置
        
        Strategies:
        1. exact: 精确匹配
        2. fuzzy: 模糊匹配（相似度阈值）
        3. contains: 子串匹配
        4. spanning: 跨span匹配
        """
        target_text = extraction.extraction_text
        
        if strategy == "exact":
            return self._exact_match(target_text)
        elif strategy == "fuzzy":
            return self._fuzzy_match(target_text, threshold=0.85)
        elif strategy == "contains":
            return self._contains_match(target_text)
        else:
            return self._spanning_match(target_text)


class HighlightFusionEngine:
    """高亮融合引擎 - 协调 LangExtract 和 PyMuPDF"""
    
    def __init__(
        self,
        origin_pdf: str,
        layout_json: dict,
        color_scheme: dict = None
    ):
        self.pdf_path = origin_pdf
        self.matcher = TextPositionMatcher(layout_json)
        self.colors = color_scheme or DEFAULT_COLORS
    
    def process_extractions(
        self,
        extractions: List[lx.data.Extraction]
    ) -> List[HighlightBox]:
        """
        处理所有提取项，生成高亮框
        
        Returns:
            [{bbox, page, color, category, confidence}]
        """
        highlights = []
        
        for ext in extractions:
            matches = self.matcher.match_extraction(ext)
            
            for match in matches:
                highlights.append(HighlightBox(
                    bbox=match.bbox,
                    page=match.page,
                    color=self.colors.get(ext.extraction_class, (1,1,0)),
                    category=ext.extraction_class,
                    confidence=match.confidence,
                    text=ext.extraction_text
                ))
        
        return highlights
    
    def render(self, highlights: List[HighlightBox], output_pdf: str):
        """渲染高亮到PDF"""
        renderer = PDFRenderer(self.pdf_path)
        renderer.draw_highlights(highlights, output_pdf)
```

### 3.3 匹配算法详解

#### 算法1: 精确匹配（Exact Match）
```python
def _exact_match(self, target: str) -> List[MatchResult]:
    """直接索引查找"""
    if target in self.text_index:
        return [MatchResult(**pos, confidence=1.0) 
                for pos in self.text_index[target]]
    return []
```

#### 算法2: 模糊匹配（Fuzzy Match）⭐ 推荐
```python
from difflib import SequenceMatcher

def _fuzzy_match(self, target: str, threshold: float = 0.85) -> List[MatchResult]:
    """基于相似度的匹配"""
    results = []
    
    for content, positions in self.text_index.items():
        similarity = SequenceMatcher(None, target, content).ratio()
        if similarity >= threshold:
            for pos in positions:
                results.append(MatchResult(
                    **pos, 
                    confidence=similarity
                ))
    
    return sorted(results, key=lambda x: x.confidence, reverse=True)
```

#### 算法3: 跨Span匹配（Spanning Match）
```python
def _spanning_match(self, target: str) -> List[MatchResult]:
    """
    处理跨越多个spans的文本
    使用滑动窗口在 lines 上匹配
    """
    results = []
    target_clean = self._normalize(target)
    
    for page in self.layout["pdf_info"]:
        for para in page["para_blocks"]:
            for line in para.get("lines", []):
                # 合并 line 中所有 spans 的文本
                line_text = "".join(
                    s["content"] for s in line.get("spans", [])
                )
                line_clean = self._normalize(line_text)
                
                if target_clean in line_clean:
                    # 计算 bbox（合并相关 spans）
                    bbox = self._calculate_span_bbox(
                        line["spans"], target, line_text
                    )
                    results.append(MatchResult(
                        bbox=bbox,
                        page=page["page_idx"],
                        confidence=0.9
                    ))
    
    return results
```

---

## 4. 实现步骤（Roadmap）

### Phase 2.1: 基础匹配引擎（2-3天）

- [ ] 实现 `TextPositionMatcher._build_span_index()`
- [ ] 实现精确匹配（`_exact_match`）
- [ ] 实现模糊匹配（`_fuzzy_match`）
- [ ] 编写单元测试（使用示例 layout.json）

### Phase 2.2: 跨Span匹配（2天）

- [ ] 实现滑动窗口文本搜索
- [ ] 实现多span bbox 计算
- [ ] 处理重复匹配（同一文本多个位置）

### Phase 2.3: 融合引擎整合（2天）

- [ ] 实现 `HighlightFusionEngine`
- [ ] 颜色配置系统
- [ ] 批处理多个 extraction

### Phase 2.4: 端到端验证（1-2天）

- [ ] 完整流程：PDF → LangExtract → 高亮PDF
- [ ] 使用智能手机报告测试
- [ ] 使用药品说明书测试

---

## 5. 关键设计决策

### 5.1 匹配粒度选择

| 粒度 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **Span** | 最精确 | 匹配困难 | 短文本、关键词 |
| **Line** | 平衡 | 可能包含多余内容 | 句子级提取 |
| **Para Block** | 匹配简单 | 精度低 | 段落级提取 |

**建议策略：**
- 短文本（<10字符）→ Span 级
- 长文本（>50字符）→ Line 级或 Para 级
- 表格数据 → 通过表格结构匹配

### 5.2 颜色编码方案

```python
HIGHLIGHT_COLORS = {
    # 药品提取
    "name": (1.0, 0.8, 0.0),        # 金色
    "ingredient": (1.0, 0.5, 0.0),   # 橙色
    "efficacy": (0.0, 0.8, 1.0),     # 青色
    "dosage": (1.0, 0.0, 0.0),       # 红色
    
    # 通用
    "entity": (0.0, 1.0, 0.0),       # 绿色
    "value": (0.8, 0.0, 1.0),        # 紫色
    "date": (0.0, 0.5, 1.0),         # 蓝色
}
```

### 5.3 冲突处理

**问题：** 多个 extraction 匹配到同一位置

**解决方案：**
1. **置信度优先** - 保留高置信度匹配
2. **类别优先级** - 预定义类别优先级（name > text）
3. **合并显示** - 在PDF注释中列出所有类别

---

## 6. 预期输出示例

### 6.1 输入
```json
// layout.json (片段)
{
  "bbox": [100, 200, 150, 220],
  "content": "Apple"
}

// LangExtract 输出
{
  "extraction_class": "company",
  "extraction_text": "Apple"
}
```

### 6.2 输出
```json
// 融合结果
{
  "highlights": [
    {
      "page": 0,
      "bbox": [100, 200, 150, 220],
      "color": [0, 1, 0],
      "category": "company",
      "text": "Apple",
      "confidence": 1.0
    }
  ]
}
```

### 6.3 可视化PDF
- 绿色边框圈出 "Apple"
- 点击显示注释：`[company] Apple`

---

## 7. 风险与缓解

| 风险 | 影响 | 缓解策略 |
|------|------|----------|
| 文本匹配失败率高 | 高 | 多级匹配策略（精确→模糊→跨越） |
| 性能问题（大PDF） | 中 | 分页处理 + 索引优化 |
| 坐标偏差 | 中 | 支持 Y 轴微调参数 |
| LangExtract 提取不完整 | 中 | 增强 prompt + 更多示例 |

---

## 8. 下一步行动

1. **立即开始** - 实现 `TextPositionMatcher` 基础类
2. **验证匹配** - 使用智能手机报告测试匹配准确率
3. **调整策略** - 根据测试结果优化匹配算法
4. **整合渲染** - 连接 PyMuPDF 渲染器

---

## 附录：关键数据结构

```python
@dataclass
class SpanInfo:
    """layout.json 中的 span 信息"""
    bbox: Tuple[float, float, float, float]
    content: str
    page: int
    type: str  # text, inline_equation, etc.

@dataclass
class MatchResult:
    """匹配结果"""
    bbox: Tuple[float, float, float, float]
    page: int
    confidence: float  # 0-1
    matched_text: str

@dataclass
class HighlightBox:
    """高亮框（用于渲染）"""
    page: int
    bbox: Tuple[float, float, float, float]
    color: Tuple[float, float, float]
    category: str
    confidence: float
    text: str
```

---

**文档版本**: 1.0  
**创建日期**: 2026-02-05  
**状态**: Phase 2 设计完成，待开发
