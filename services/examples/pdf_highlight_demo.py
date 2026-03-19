"""
PyMuPDF 透明边框绘制示例 - 使用 layout.json
提取所有层级的框：para_block + 嵌套的 blocks
"""

import fitz  # PyMuPDF
import json
import os
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class BoxInfo:
    """边框信息"""
    page: int
    bbox: Tuple[float, float, float, float]
    text: str
    box_type: str  # 类型标识


def load_layout(layout_path: str) -> dict:
    """加载 MinerU 的 layout.json"""
    with open(layout_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_all_boxes(layout: dict) -> List[BoxInfo]:
    """
    从 layout.json 提取所有层级的框
    包括：para_block + 嵌套的 blocks
    """
    boxes = []
    
    for page_info in layout.get("pdf_info", []):
        page_idx = page_info.get("page_idx", 0)
        
        for para_block in page_info.get("para_blocks", []):
            para_bbox = para_block.get("bbox", [0, 0, 0, 0])
            para_type = para_block.get("type", "text")
            
            # 1. 添加段落级框
            content_preview = ""
            if para_type == "table":
                content_preview = "表格区域"
            else:
                # 提取前50字符作为预览
                for line in para_block.get("lines", [])[:1]:
                    for span in line.get("spans", []):
                        content_preview += span.get("content", "")
            
            boxes.append(BoxInfo(
                page=page_idx,
                bbox=tuple(para_bbox),
                text=content_preview[:50],
                box_type=f"para_{para_type}"
            ))
            
            # 2. 添加嵌套的 blocks（如表格的表体、脚注等）
            for block in para_block.get("blocks", []):
                block_bbox = block.get("bbox", [0, 0, 0, 0])
                block_type = block.get("type", "unknown")
                
                # 提取文本预览
                block_text = ""
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        block_text += span.get("content", "") + " "
                
                boxes.append(BoxInfo(
                    page=page_idx,
                    bbox=tuple(block_bbox),
                    text=block_text[:50],
                    box_type=f"block_{block_type}"
                ))
    
    return boxes


def draw_boxes(
    input_pdf: str,
    boxes: List[BoxInfo],
    output_pdf: str,
    y_offset: float = 0
):
    """绘制透明边框"""
    print(f"📖 打开 PDF: {input_pdf}")
    doc = fitz.open(input_pdf)
    
    # 按页分组
    page_boxes = {}
    for box in boxes:
        if box.page not in page_boxes:
            page_boxes[box.page] = []
        page_boxes[box.page].append(box)
    
    print(f"🎨 共 {len(boxes)} 个边框")
    print(f"📐 Y轴偏移: {y_offset}")
    
    # 统计类型
    type_counts = {}
    for box in boxes:
        type_counts[box.box_type] = type_counts.get(box.box_type, 0) + 1
    print("\n📊 边框类型统计:")
    for t, c in sorted(type_counts.items()):
        print(f"  • {t}: {c}")
    
    for page_num, box_list in sorted(page_boxes.items()):
        if page_num >= len(doc):
            continue
        
        page = doc[page_num]
        print(f"\n  第 {page_num + 1} 页: {len(box_list)} 个边框")
        
        for i, box in enumerate(box_list):
            # 应用偏移
            x0, y0, x1, y1 = box.bbox
            adjusted_bbox = (x0, y0 + y_offset, x1, y1 + y_offset)
            rect = fitz.Rect(adjusted_bbox)
            
            # 根据类型选择边框颜色
            if "footnote" in box.box_type:
                color = (0.8, 0.2, 0.2)  # 红色 - 脚注
            elif "table_body" in box.box_type:
                color = (0.2, 0.2, 0.8)  # 蓝色 - 表格主体
            elif "para_table" in box.box_type:
                color = (0.2, 0.6, 0.2)  # 绿色 - 整个表格区域
            elif "title" in box.box_type:
                color = (0.8, 0.6, 0.2)  # 橙色 - 标题
            else:
                color = (0.3, 0.3, 0.3)  # 灰色 - 其他
            
            # 绘制边框
            shape = page.new_shape()
            shape.draw_rect(rect)
            shape.finish(color=color, fill=None, width=1.5)
            shape.commit()
            
            # 标签
            label = box.box_type.split("_")[-1][:4]  # 缩写
            page.insert_text(
                rect.tl + (2, 8),
                label,
                fontsize=6,
                color=color
            )
    
    doc.save(output_pdf, garbage=4, deflate=True)
    doc.close()
    print(f"\n💾 保存: {output_pdf}")


def main():
    base_dir = Path("mineru_output/513f81dc-4fca-42b3-a4a9-0d58d99db2d2/extracted")
    input_pdf = str(base_dir / "9590ce5e-59c2-425c-8067-15d3657f1879_origin.pdf")
    layout_path = str(base_dir / "layout.json")
    
    output_dir = Path("highlight_output")
    output_dir.mkdir(exist_ok=True)
    
    if not os.path.exists(input_pdf):
        print(f"❌ 找不到 PDF: {input_pdf}")
        return
    
    if not os.path.exists(layout_path):
        print(f"❌ 找不到 layout.json: {layout_path}")
        return
    
    print("=" * 60)
    print("PyMuPDF 边框绘制 - 使用 layout.json (含嵌套 blocks)")
    print("=" * 60)
    
    # 加载并提取
    print(f"\n📂 加载: {layout_path}")
    layout = load_layout(layout_path)
    
    boxes = extract_all_boxes(layout)
    
    # 显示框详情
    print(f"\n📋 提取的边框详情:")
    for i, box in enumerate(boxes):
        print(f"  {i+1}. [{box.box_type}] bbox={box.bbox}")
        print(f"      text={box.text[:40]}...")
    
    # 绘制
    output_pdf = str(output_dir / "layout_all_boxes.pdf")
    draw_boxes(input_pdf, boxes, output_pdf, y_offset=0)
    
    print("\n" + "=" * 60)
    print("完成!")
    print(f"输出: {output_pdf}")
    print("\n框说明:")
    print("  🟢 绿色 para_table = 整个表格区域")
    print("  🔵 蓝色 block_table_body = 表格主体")
    print("  🔴 红色 block_table_footnote = 表格脚注（Source:...）")
    print("  🟠 橙色 para_title = 标题")
    print("=" * 60)


if __name__ == "__main__":
    main()
