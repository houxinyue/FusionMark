"""
MinerU + LangExtract 融合演示
对智能手机报告进行信息提取并在 PDF 上高亮
"""

import langextract as lx
from langextract.factory import ModelConfig
from langextract.providers.openai import OpenAILanguageModel # 显式导入提供者
import fitz
import json
import os
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional
from difflib import SequenceMatcher
import textwrap
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ============== 配置 ==============
BASE_DIR = Path("mineru_output/513f81dc-4fca-42b3-a4a9-0d58d99db2d2/extracted")
PDF_PATH = str(BASE_DIR / "9590ce5e-59c2-425c-8067-15d3657f1879_origin.pdf")
LAYOUT_PATH = str(BASE_DIR / "layout.json")
MD_PATH = str(BASE_DIR / "full.md")
OUTPUT_DIR = Path("highlight_output")


@dataclass
class PositionMatch:
    """匹配结果"""
    page: int
    bbox: Tuple[float, float, float, float]
    text: str
    confidence: float


@dataclass
class HighlightBox:
    """高亮框"""
    page: int
    bbox: Tuple[float, float, float, float]
    color: Tuple[float, float, float]
    category: str
    text: str


# ============== 1. LangExtract 提取 ==============

def run_langextract(markdown_text: str) -> List[lx.data.Extraction]:
    """
    使用 LangExtract 从 Markdown 提取信息
    """
    print("=" * 60)
    print("Step 1: LangExtract 信息提取")
    print("=" * 60)
    
    # 定义提取规则
    prompt = textwrap.dedent("""\
        从智能手机市场报告中提取以下信息：
        
        1. report_title: 报告标题
        2. company_name: 公司名称（如 Apple, Samsung, Xiaomi 等）
        3. shipment_value: 出货量数值（如 81.3）
        4. market_share: 市场份额（如 24.2%）
        5. yoy_change: 同比增长率（正值，如 4.9%）
        6. negative_change: 负增长/负值（带负号的数值，如 -11.4%）
        7. data_source: 数据来源
        
        提取规则：
        - 使用原文中的精确文本
        - 每个数值单独提取
        - 百分比保留 % 符号
        - 负值必须包含负号（-）
        - 负增长用 negative_change 类别，正值用 yoy_change 类别
        """)
    
    # 示例 - 包含负值示例
    examples = [
        lx.data.ExampleData(
            text="""Top 5 Companies, Worldwide Smartphone Shipments
            1. huwei 81.3 24.2% 77.5 23.6% 4.9%
            2. oppo 61.2 18.2% 51.7 15.7% 18.3%
            3. xxx 37.8 11.2% 42.7 13.0% -11.4%
            Source: IDC Quarterly Mobile Phone Tracker""",
            extractions=[
                lx.data.Extraction(extraction_class="report_title", extraction_text="Top 5 Companies, Worldwide Smartphone Shipments"),
                lx.data.Extraction(extraction_class="company_name", extraction_text="Apple"),
                lx.data.Extraction(extraction_class="shipment_value", extraction_text="81.3"),
                lx.data.Extraction(extraction_class="market_share", extraction_text="24.2%"),
                lx.data.Extraction(extraction_class="yoy_change", extraction_text="4.9%"),
                lx.data.Extraction(extraction_class="company_name", extraction_text="Samsung"),
                lx.data.Extraction(extraction_class="shipment_value", extraction_text="61.2"),
                lx.data.Extraction(extraction_class="yoy_change", extraction_text="18.3%"),
                lx.data.Extraction(extraction_class="company_name", extraction_text="Xiaomi"),
                lx.data.Extraction(extraction_class="shipment_value", extraction_text="37.8"),
                lx.data.Extraction(extraction_class="negative_change", extraction_text="-11.4%"),  # 负值示例
                lx.data.Extraction(extraction_class="data_source", extraction_text="Source: IDC Quarterly Mobile Phone Tracker"),
            ]
        )
    ]
    
    print("🤖 调用 LangExtract...")
    
    result = lx.extract(
        examples=examples,
        text_or_documents=markdown_text,
        prompt_description=prompt,
        config=ModelConfig(
            model_id="deepseek-chat",
            provider="OpenAILanguageModel",
            provider_kwargs={
                "api_key": os.getenv("DS_API_KEY"),
                "base_url": os.getenv("DS_API_BASE_URL")
            }
        )
    )
    
    print(f"✅ 提取完成，共 {len(result.extractions)} 个实体")
    
    # 显示提取结果
    print("\n📋 提取结果:")
    for i, ext in enumerate(result.extractions, 1):
        print(f"  {i}. [{ext.extraction_class}] {ext.extraction_text}")
    
    return result.extractions


# ============== 2. 加载 MinerU 位置 ==============

def load_layout(layout_path: str) -> dict:
    """加载 layout.json"""
    with open(layout_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def build_span_index(layout: dict) -> Dict[str, List[PositionMatch]]:
    """
    建立文本到位置的索引
    """
    print("\n" + "=" * 60)
    print("Step 2: 构建位置索引")
    print("=" * 60)
    
    index = {}
    span_count = 0
    
    for page_info in layout.get("pdf_info", []):
        page_idx = page_info.get("page_idx", 0)
        
        for para_block in page_info.get("para_blocks", []):
            # 遍历所有 lines 和 spans
            for line in para_block.get("lines", []):
                for span in line.get("spans", []):
                    content = span.get("content", "").strip()
                    if content:
                        span_count += 1
                        if content not in index:
                            index[content] = []
                        index[content].append(PositionMatch(
                            page=page_idx,
                            bbox=tuple(span["bbox"]),
                            text=content,
                            confidence=1.0
                        ))
    
    print(f"✅ 索引构建完成，共 {span_count} 个 spans")
    print(f"   唯一文本数: {len(index)}")
    
    return index


# ============== 3. 文本匹配 ==============

def fuzzy_match(text: str, index: Dict[str, List[PositionMatch]], threshold: float = 0.85) -> List[PositionMatch]:
    """模糊匹配"""
    results = []
    
    # 1. 精确匹配
    if text in index:
        return [PositionMatch(p.page, p.bbox, p.text, 1.0) for p in index[text]]
    
    # 2. 包含匹配
    for content, positions in index.items():
        if text in content:
            for p in positions:
                results.append(PositionMatch(p.page, p.bbox, p.text, 0.95))
    
    if results:
        return results
    
    # 3. 模糊匹配
    for content, positions in index.items():
        similarity = SequenceMatcher(None, text, content).ratio()
        if similarity >= threshold:
            for p in positions:
                results.append(PositionMatch(p.page, p.bbox, p.text, similarity))
    
    # 按置信度排序
    results.sort(key=lambda x: x.confidence, reverse=True)
    return results[:3]  # 最多返回3个


def match_extractions(
    extractions: List[lx.data.Extraction],
    index: Dict[str, List[PositionMatch]]
) -> List[HighlightBox]:
    """
    将提取结果匹配到 PDF 位置
    """
    print("\n" + "=" * 60)
    print("Step 3: 文本位置匹配")
    print("=" * 60)
    
    # 颜色配置 - 负值用醒目的红色
    colors = {
        "report_title": (1.0, 0.5, 0.0),    # 橙色
        "company_name": (0.0, 0.8, 0.0),    # 绿色
        "shipment_value": (0.0, 0.5, 1.0),  # 蓝色
        "market_share": (0.8, 0.0, 1.0),    # 紫色
        "yoy_change": (1.0, 0.0, 0.5),      # 粉色
        "negative_change": (1.0, 0.0, 0.0), # 🔴 红色 - 负值醒目提示
        "data_source": (0.5, 0.5, 0.5),     # 灰色
    }
    
    highlights = []
    match_count = 0
    
    for ext in extractions:
        target_text = ext.extraction_text
        category = ext.extraction_class
        
        matches = fuzzy_match(target_text, index)
        
        if matches:
            match_count += 1
            for match in matches:
                highlights.append(HighlightBox(
                    page=match.page,
                    bbox=match.bbox,
                    color=colors.get(category, (0.3, 0.3, 0.3)),
                    category=category,
                    text=target_text
                ))
            print(f"  ✓ [{category}] '{target_text[:30]}...' → {len(matches)} 个位置")
        else:
            print(f"  ✗ [{category}] '{target_text[:30]}...' → 未匹配")
    
    print(f"\n✅ 匹配完成: {match_count}/{len(extractions)}")
    
    return highlights


# ============== 4. PDF 高亮渲染 ==============

def render_highlights(input_pdf: str, highlights: List[HighlightBox], output_pdf: str):
    """渲染高亮到 PDF"""
    print("\n" + "=" * 60)
    print("Step 4: PDF 高亮渲染")
    print("=" * 60)
    
    doc = fitz.open(input_pdf)
    
    # 按页分组
    page_highlights = {}
    for hl in highlights:
        if hl.page not in page_highlights:
            page_highlights[hl.page] = []
        page_highlights[hl.page].append(hl)
    
    print(f"🎨 共 {len(highlights)} 个高亮，分布在 {len(page_highlights)} 页")
    
    for page_num, hls in sorted(page_highlights.items()):
        if page_num >= len(doc):
            continue
        
        page = doc[page_num]
        print(f"\n  第 {page_num + 1} 页: {len(hls)} 个高亮")
        
        for hl in hls:
            rect = fitz.Rect(hl.bbox)
            
            # 绘制彩色边框
            shape = page.new_shape()
            shape.draw_rect(rect)
            shape.finish(color=hl.color, fill=None, width=2)
            shape.commit()
            
            # 添加类别标签
            label = hl.category.replace("_", "")[:6]
            page.insert_text(
                rect.tl + (2, 10),
                label,
                fontsize=7,
                color=hl.color
            )
            
            # 添加隐形注释（点击显示详情）
            page.add_text_annot(
                rect.tl,
                f"[{hl.category}]\n{hl.text}",
                icon="Note"
            )
    
    doc.save(output_pdf, garbage=4, deflate=True)
    doc.close()
    
    print(f"\n💾 保存: {output_pdf}")


# ============== 主流程 ==============

def main():
    """完整流程演示"""
    print("\n" + "=" * 70)
    print("MinerU + LangExtract 融合演示")
    print("=" * 70)
    
    # 检查文件
    if not os.path.exists(PDF_PATH):
        print(f"❌ 找不到 PDF: {PDF_PATH}")
        return
    if not os.path.exists(MD_PATH):
        print(f"❌ 找不到 Markdown: {MD_PATH}")
        return
    if not os.path.exists(LAYOUT_PATH):
        print(f"❌ 找不到 layout: {LAYOUT_PATH}")
        return
    
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # 1. 读取 Markdown
    print(f"\n📖 读取 Markdown: {MD_PATH}")
    with open(MD_PATH, 'r', encoding='utf-8') as f:
        md_text = f.read()
    print(f"   共 {len(md_text)} 字符")
    
    # 2. LangExtract 提取
    extractions = run_langextract(md_text)
    
    if not extractions:
        print("❌ 没有提取到任何信息")
        return
    
    # 3. 加载 layout 并构建索引
    layout = load_layout(LAYOUT_PATH)
    index = build_span_index(layout)
    
    # 4. 匹配位置
    highlights = match_extractions(extractions, index)
    
    if not highlights:
        print("❌ 没有匹配到任何位置")
        return
    
    # 5. 渲染 PDF
    output_pdf = str(OUTPUT_DIR / "smartphone_fusion_highlighted.pdf")
    render_highlights(PDF_PATH, highlights, output_pdf)
    
    # 6. 完成摘要
    print("\n" + "=" * 70)
    print("完成摘要")
    print("=" * 70)
    print(f"\n✅ 原始 PDF: {PDF_PATH}")
    print(f"✅ 高亮 PDF: {output_pdf}")
    print(f"\n📊 统计:")
    print(f"   - 提取实体: {len(extractions)}")
    print(f"   - 匹配位置: {len(highlights)}")
    
    # 按类别统计
    category_counts = {}
    for hl in highlights:
        category_counts[hl.category] = category_counts.get(hl.category, 0) + 1
    print(f"\n📋 按类别分布:")
    for cat, count in sorted(category_counts.items()):
        print(f"   - {cat}: {count}")
    
    print("\n🎨 颜色说明:")
    print("   🟠 橙色 = 报告标题")
    print("   🟢 绿色 = 公司名称")
    print("   🔵 蓝色 = 出货量数值")
    print("   🟣 紫色 = 市场份额")
    print("   🩷 粉色 = 同比增长（正值）")
    print("   🔴 红色 = 负增长/负值（警示）")
    print("   ⚪ 灰色 = 数据来源")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
