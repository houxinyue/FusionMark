"""
PyMuPDF vs MinerU 方案对比测试
================================
比较两种文字坐标提取方案的差异
"""

import json
import fitz
from pathlib import Path
from typing import Dict, List, Any
from pymupdf_text_extractor import PyMuPDFTextExtractor


def compare_granularity(pdf_path: str):
    """
    对比两种方案的粒度差异
    """
    print("\n" + "="*70)
    print("PyMuPDF vs MinerU 方案对比")
    print("="*70)
    
    # PyMuPDF 方案
    print("\n📊 PyMuPDF 方案:")
    with PyMuPDFTextExtractor(pdf_path) as extractor:
        # 不同粒度
        spans = extractor.extract_spans(page_idx=0)
        words = extractor.extract_words(page_idx=0)
        
        print(f"   Span 级别: {len(spans)} 个片段")
        print(f"   Word 级别: {len(words)} 个单词")
        
        # 示例
        print("\n   Span 示例 (前3个):")
        for s in spans[:3]:
            print(f"      '{s.text[:40]}' bbox={s.bbox}")
        
        print("\n   Word 示例 (前10个):")
        for w in words[:10]:
            print(f"      '{w.text}' bbox={w.bbox}")
    
    # MinerU 方案（如果存在）
    print("\n📊 MinerU 方案（如果存在）:")
    mineru_layout = None
    for layout_path in Path("mineru_output").rglob("layout.json"):
        with open(layout_path, "r", encoding="utf-8") as f:
            mineru_layout = json.load(f)
        break
    
    if mineru_layout:
        # 统计 MinerU 的粒度
        total_blocks = 0
        total_lines = 0
        total_spans = 0
        
        for page in mineru_layout.get("layout_dtls", []):
            for block in page.get("blocks", []):
                total_blocks += 1
                for line in block.get("lines", []):
                    total_lines += 1
                    total_spans += len(line.get("spans", []))
        
        print(f"   Block 级别: {total_blocks} 个块")
        print(f"   Line 级别: {total_lines} 行")
        print(f"   Span 级别: {total_spans} 个片段")
    else:
        print("   未找到 MinerU layout.json")
    
    print("\n" + "="*70)


def verify_coordinates(pdf_path: str):
    """
    验证 PyMuPDF 提取的坐标精度
    """
    print("\n" + "="*70)
    print("坐标精度验证")
    print("="*70)
    
    with PyMuPDFTextExtractor(pdf_path) as extractor:
        words = extractor.extract_words(page_idx=0)
        
        # 打开 PDF 验证
        doc = fitz.open(pdf_path)
        page = doc[0]
        
        # 选取几个单词，绘制 bbox 验证
        test_words = words[:5]
        
        print(f"\n🔍 验证 {len(test_words)} 个单词的坐标:")
        for w in test_words:
            print(f"\n   单词: '{w.text}'")
            print(f"   坐标: {w.bbox}")
            
            # 使用 PyMuPDF 在这个区域搜索文本
            rect = fitz.Rect(w.bbox)
            found = page.get_textbox(rect).strip()
            print(f"   区域提取: '{found}'")
            print(f"   匹配: {'✅' if w.text in found or found in w.text else '❌'}")
        
        doc.close()
    
    print("\n" + "="*70)


def export_comparison_json(pdf_path: str):
    """
    导出两种方案的 JSON 对比
    """
    print("\n" + "="*70)
    print("导出 JSON 对比")
    print("="*70)
    
    output_dir = Path("pymupdf_output")
    output_dir.mkdir(exist_ok=True)
    
    # PyMuPDF JSON
    with PyMuPDFTextExtractor(pdf_path) as extractor:
        pymupdf_json = extractor.export_to_json(str(output_dir / "pymupdf_coordinates.json"))
        print(f"✅ PyMuPDF JSON 已导出: {output_dir / 'pymupdf_coordinates.json'}")
        print(f"   页数: {pymupdf_json['page_count']}")
        print(f"   第1页 blocks: {len(pymupdf_json['pages'][0]['blocks'])}")
    
    # MinerU JSON（复制一份做对比）
    for layout_path in Path("mineru_output").rglob("layout.json"):
        with open(layout_path, "r", encoding="utf-8") as f:
            mineru_json = json.load(f)
        
        output_path = output_dir / "mineru_coordinates.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(mineru_json, f, ensure_ascii=False, indent=2)
        
        print(f"✅ MinerU JSON 已复制: {output_path}")
        break
    
    print("\n" + "="*70)


def main():
    """运行所有对比测试"""
    # 查找测试 PDF
    test_pdf = None
    for pattern in ["mineru_output/*/*.pdf", "*.pdf"]:
        pdfs = list(Path(".").glob(pattern))
        if pdfs:
            test_pdf = str(pdfs[0])
            break
    
    if not test_pdf:
        print("❌ 未找到测试 PDF")
        return
    
    print(f"📁 测试文件: {test_pdf}")
    
    # 运行对比
    compare_granularity(test_pdf)
    verify_coordinates(test_pdf)
    export_comparison_json(test_pdf)
    
    print("\n✅ 所有对比测试完成!")


if __name__ == "__main__":
    main()
