# MinerU + LangExtract PDF 高亮实现计划

## 1. 项目愿景

将 **MinerU** 的 PDF 解析能力（文本+位置）与 **LangExtract** 的智能信息提取能力结合，实现：
- 从 PDF 中提取结构化信息
- 将提取结果**高亮标注**在原始 PDF 上
- 生成带标注的 PDF 和可视化报告

## 2. 数据流架构

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   原始PDF   │ --> │   MinerU    │ --> │ 文本+位置   │ --> │ LangExtract │
│  (输入)     │     │   解析API   │     │ (JSON)      │     │  信息提取   │
└─────────────┘     └─────────────┘     └─────────────┘     └──────┬──────┘
                                                                    │
                                                                    ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  带标注PDF  │ <-- │  PDF绘制    │ <-- │ 位置匹配    │ <-- │  提取实体   │
│  (输出)     │     │  高亮层     │     │  引擎       │     │  (JSON)     │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

## 3. MinerU 输出格式分析

### 3.1 关键文件结构

基于实际 MinerU 输出，主要文件包括：

| 文件 | 用途 | 说明 |
|------|------|------|
| `full.md` | LangExtract 输入 | 清洗后的 Markdown 文本 |
| `content_list.json` | **位置匹配主文件** | 每段文本的 bbox + page_idx |
| `layout.json` | 备用 | 详细的段落/行/span 层级结构 |
| `*_origin.pdf` | 高亮绘制 | 原始 PDF 文件 |

### 3.2 `content_list.json` 结构（核心）

```json
[
  {
    "type": "text",
    "text": "Patrick N.J. Lane ",
    "text_level": 1,
    "bbox": [154, 267, 830, 289],
    "page_idx": 0
  },
  {
    "type": "title",
    "text": "The response of flow duration curves to afforestation ",
    "bbox": [156, 227, 829, 251],
    "page_idx": 0
  }
]
```

**关键字段：**
- `text`: 文本内容（与 full.md 对应）
- `bbox`: [x0, y0, x1, y1] 坐标（PDF 坐标系，原点左下角）
- `page_idx`: 页码（从 0 开始）
- `type`: text/title/header/image/table/equation 等

### 3.3 坐标系统

```
PDF 坐标系（MinerU 使用）:

    y^ (向上)
     |
     |    ┌──────────┐
     |    │  bbox    │  y1
     |    │ [text]   │
     |    │          │  y0
     |    └──────────┘
     |       x0   x1
     |
     +---------------> x
    (0,0)

bbox = [x0, y0, x1, y1]
- x0: 左边界
- y0: 下边界
- x1: 右边界
- y1: 上边界
```

## 4. 技术实现方案

### 4.1 文本匹配策略

**核心挑战：** LangExtract 提取的文本片段可能跨越多个 content_list 条目

**解决方案：滑动窗口匹配算法**

```python
def match_extraction_to_positions(
    extraction_text: str,
    content_list: List[ContentItem],
    similarity_threshold: float = 0.85
) -> List[PositionMatch]:
    """
    将 LangExtract 提取的文本匹配到 PDF 位置
    
    算法：
    1. 在 content_list 中搜索 extraction_text 的子串匹配
    2. 如果没有精确匹配，使用模糊相似度匹配
    3. 返回匹配的 bbox 列表（可能多个片段）
    """
    matches = []
    
    # 1. 精确子串匹配
    for item in content_list:
        if extraction_text in item.text:
            matches.append(PositionMatch(
                bbox=item.bbox,
                page=item.page_idx,
                matched_text=item.text,
                confidence=1.0
            ))
    
    # 2. 如果没有匹配，使用模糊匹配
    if not matches:
        # 使用 difflib.SequenceMatcher 或 rapidfuzz
        best_matches = fuzzy_search(extraction_text, content_list, threshold)
        matches.extend(best_matches)
    
    # 3. 处理跨段文本（提取文本跨越多个 content_list 条目）
    if not matches:
        matches = find_spanning_match(extraction_text, content_list)
    
    return matches
```

### 4.2 PDF 高亮绘制

**使用 PyMuPDF (fitz)**

```python
import fitz

def draw_highlights_on_pdf(
    input_pdf: str,
    highlights: List[HighlightInfo],
    output_pdf: str
):
    """
    在 PDF 上绘制高亮
    
    Args:
        highlights: [{
            "page": 1,
            "bbox": [x0, y0, x1, y1],
            "color": "yellow",
            "extraction_class": "name",
            "text": "提取的文本"
        }]
    """
    doc = fitz.open(input_pdf)
    
    for hl in highlights:
        page = doc[hl["page"]]  # page_idx 从 0 开始
        rect = fitz.Rect(hl["bbox"])
        
        # 添加高亮注释
        annot = page.add_highlight_annot(rect)
        annot.set_colors(stroke=fitz.utils.getColor(hl["color"]))
        annot.update()
        
        # 添加弹出注释（显示类别和文本）
        popup_text = f"[{hl['extraction_class']}]\n{hl['text'][:200]}"
        page.add_text_annot(rect.tl, popup_text)
    
    doc.save(output_pdf)
```

### 4.3 颜色配置

```python
CATEGORY_COLORS = {
    # 药品信息提取专用
    "name": (1.0, 1.0, 0.0),           # 黄色 - 药品名称
    "pinyin": (0.5, 1.0, 0.5),         # 浅绿 - 拼音
    "medicine_type": (0.0, 1.0, 0.0),  # 绿色 - 药品类型
    "ingredient": (1.0, 0.65, 0.0),    # 橙色 - 成分
    "efficacy": (0.0, 1.0, 1.0),       # 青色 - 功效
    "indication": (1.0, 0.0, 1.0),     # 品红 - 适应症
    "dosage": (1.0, 0.0, 0.0),         # 红色 - 用法用量
    "precaution": (1.0, 0.75, 0.8),    # 粉色 - 注意事项
    "adverse_reaction": (0.5, 0.5, 0.5), # 灰色 - 不良反应
    "contraindication": (0.8, 0.0, 0.0), # 深红 - 禁忌
    "storage": (0.0, 0.5, 1.0),        # 蓝色 - 贮藏
    "validity": (0.5, 0.0, 1.0),       # 紫色 - 有效期
    "standard": (0.8, 0.8, 0.8),       # 浅灰 - 执行标准
    # 通用
    "default": (1.0, 1.0, 0.0),        # 默认黄色
}
```

## 5. 核心类设计

```python
from dataclasses import dataclass
from typing import List, Tuple, Optional
import langextract as lx


@dataclass
class TextPosition:
    """PDF 中的文本位置"""
    page: int                      # 页码（从0开始）
    bbox: Tuple[float, float, float, float]  # [x0, y0, x1, y1]
    text: str                      # 匹配的原文
    confidence: float              # 匹配置信度 0-1


@dataclass
class HighlightMatch:
    """高亮匹配结果"""
    extraction: lx.data.Extraction  # LangExtract 提取结果
    positions: List[TextPosition]   # 对应的 PDF 位置（可能多个）
    color: Tuple[float, float, float]  # RGB 颜色


@dataclass
class ContentItem:
    """MinerU content_list.json 中的条目"""
    type: str                      # text/title/header/table/image/equation
    text: str                      # 文本内容
    bbox: Tuple[float, float, float, float]
    page_idx: int
    text_level: Optional[int] = None


class PDFPositionMatcher:
    """PDF 位置匹配器"""
    
    def __init__(self, content_list_path: str):
        """
        Args:
            content_list_path: content_list.json 文件路径
        """
        self.content_items = self._load_content_list(content_list_path)
        # 建立文本索引加速搜索
        self.text_index = self._build_index()
    
    def _load_content_list(self, path: str) -> List[ContentItem]:
        """加载并解析 content_list.json"""
        pass
    
    def _build_index(self) -> Dict[str, List[int]]:
        """建立文本到索引位置的倒排索引"""
        pass
    
    def match_extraction(
        self, 
        extraction: lx.data.Extraction,
        similarity_threshold: float = 0.85
    ) -> List[TextPosition]:
        """
        将单个提取结果匹配到 PDF 位置
        
        Returns:
            可能多个位置（如果文本在 PDF 中重复出现）
        """
        extraction_text = extraction.extraction_text
        
        # 1. 尝试精确匹配
        positions = self._exact_match(extraction_text)
        if positions:
            return positions
        
        # 2. 尝试模糊匹配
        positions = self._fuzzy_match(extraction_text, threshold=similarity_threshold)
        if positions:
            return positions
        
        # 3. 尝试分段匹配（处理跨段落文本）
        return self._spanning_match(extraction_text)
    
    def match_all(
        self, 
        extractions: List[lx.data.Extraction]
    ) -> List[HighlightMatch]:
        """批量匹配所有提取结果"""
        pass


class PDFHighlightDrawer:
    """PDF 高亮绘制器"""
    
    def __init__(self, color_scheme: Optional[Dict] = None):
        self.color_scheme = color_scheme or CATEGORY_COLORS
    
    def draw(
        self, 
        input_pdf: str,
        matches: List[HighlightMatch],
        output_pdf: str,
        add_popup: bool = True
    ):
        """绘制高亮到 PDF"""
        pass
    
    def generate_report(
        self, 
        matches: List[HighlightMatch],
        output_html: str
    ):
        """生成高亮统计报告 HTML"""
        pass


class MinerULangExtractPipeline:
    """MinerU + LangExtract 完整流程管道"""
    
    def __init__(
        self,
        mineru_client: MinerUClient,
        langextract_config: ModelConfig,
        color_scheme: Optional[Dict] = None
    ):
        self.mineru = mineru_client
        self.lx_config = langextract_config
        self.color_scheme = color_scheme or CATEGORY_COLORS
    
    def process(
        self,
        pdf_path: str,
        prompt: str,
        examples: List[lx.data.ExampleData],
        output_dir: str = "./output"
    ) -> PipelineResult:
        """
        执行完整流程
        
        Args:
            pdf_path: 输入 PDF 路径
            prompt: LangExtract prompt
            examples: LangExtract examples
            output_dir: 输出目录
            
        Returns:
            PipelineResult 包含：
            - highlighted_pdf: 带高亮的 PDF 路径
            - extraction_json: 提取结果 JSON
            - report_html: 可视化报告
            - statistics: 统计信息
        """
        # 1. MinerU 解析 PDF
        # 2. LangExtract 提取信息
        # 3. 位置匹配
        # 4. 绘制高亮
        # 5. 生成报告
        pass
```

## 6. 实现步骤

### Phase 1: 核心匹配引擎（2-3天）

- [ ] 实现 `ContentItem` 数据类
- [ ] 实现 `PDFPositionMatcher._load_content_list()`
- [ ] 实现精确匹配 (`_exact_match`)
- [ ] 实现模糊匹配 (`_fuzzy_match`) - 使用 `difflib.SequenceMatcher`
- [ ] 实现跨段匹配 (`_spanning_match`)
- [ ] 编写单元测试

### Phase 2: PDF 高亮绘制（2天）

- [ ] 集成 PyMuPDF
- [ ] 实现 `PDFHighlightDrawer.draw()`
- [ ] 实现颜色配置系统
- [ ] 添加弹出注释功能
- [ ] 测试高亮效果

### Phase 3: 整合管道（2天）

- [ ] 实现 `MinerULangExtractPipeline`
- [ ] 整合 MinerU 调用
- [ ] 整合 LangExtract 调用
- [ ] 实现报告生成功能
- [ ] 端到端测试

### Phase 4: 优化与文档（1-2天）

- [ ] 处理边界情况（匹配失败、多页文本等）
- [ ] 性能优化（大文件处理）
- [ ] 编写使用文档
- [ ] 示例代码

## 7. 边界情况处理

| 情况 | 处理策略 |
|------|----------|
| **匹配失败** | 记录警告，跳过该提取项 |
| **跨页文本** | 分割为多个高亮区域 |
| **重复文本** | 高亮所有匹配位置 |
| **MinerU 无位置文件** | 使用 PyMuPDF 重新解析 |
| **坐标转换** | MinerU 坐标与 PyMuPDF 一致（已验证） |
| **中文编码** | 全程 UTF-8 |

## 8. 预期输出示例

### 8.1 带高亮的 PDF
- 黄色高亮：药品名称
- 橙色高亮：成分
- 红色高亮：用法用量
- 点击高亮区域显示弹出注释

### 8.2 统计报告
```json
{
  "total_extractions": 45,
  "matched": 42,
  "failed": 3,
  "by_category": {
    "name": 1,
    "ingredient": 11,
    "efficacy": 1,
    "precaution": 12,
    ...
  },
  "pages_with_highlights": [0, 1, 2],
  "output_files": {
    "highlighted_pdf": "output/guipiwan_highlighted.pdf",
    "extraction_json": "output/extractions.json",
    "report_html": "output/report.html"
  }
}
```

## 9. 下一步行动

1. **确认可行性**
   - 验证 MinerU 的 bbox 坐标与 PyMuPDF 是否一致
   - 测试文本匹配算法的准确率

2. **开始实现**
   - 先实现 `PDFPositionMatcher` 核心类
   - 用示例数据测试匹配效果

3. **逐步完善**
   - 添加 PDF 绘制功能
   - 整合完整流程

---

**需要我先开始实现哪个部分？**
- A. 核心匹配引擎 (`PDFPositionMatcher`)
- B. 完整的 Pipeline 类
- C. 先写一个原型验证可行性
