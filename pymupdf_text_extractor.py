"""
PyMuPDF 文字坐标提取器
============================
替代 MinerU 的 layout.json，直接用 PyMuPDF 生成文字坐标 JSON

特点：
- 支持 span/word/char 三种粒度
- 生成与 MinerU 兼容的坐标格式 [x0, y0, x1, y1]
- 可直接与 LangExtract 配合做高亮
"""

import fitz  # PyMuPDF
import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path


@dataclass
class TextSpan:
    """文字片段，对应 MinerU 的 span 概念"""
    text: str
    bbox: Tuple[float, float, float, float]  # (x0, y0, x1, y1)
    page_idx: int
    block_idx: int
    line_idx: int
    span_idx: int
    font: str = ""
    size: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "bbox": list(self.bbox),
            "page_idx": self.page_idx,
            "block_idx": self.block_idx,
            "line_idx": self.line_idx,
            "span_idx": self.span_idx,
            "font": self.font,
            "size": self.size,
        }


@dataclass
class TextWord:
    """单词级别，更细粒度"""
    text: str
    bbox: Tuple[float, float, float, float]
    page_idx: int
    block_idx: int
    line_idx: int
    word_idx: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "bbox": list(self.bbox),
            "page_idx": self.page_idx,
            "block_idx": self.block_idx,
            "line_idx": self.line_idx,
            "word_idx": self.word_idx,
        }


class PyMuPDFTextExtractor:
    """
    PyMuPDF 文字坐标提取器
    
    支持两种模式：
    1. span 模式 - 使用 get_text("dict")，保留字体信息
    2. word 模式 - 使用 get_text("words")，最细粒度
    """
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.doc.close()
        
    def close(self):
        self.doc.close()
    
    def extract_spans(self, page_idx: Optional[int] = None, 
                      sort_by_reading_order: bool = True) -> List[TextSpan]:
        """
        提取 span 级别的文字坐标
        
        Args:
            page_idx: 指定页面，None 表示所有页面
            sort_by_reading_order: 是否按阅读顺序排序
        """
        spans = []
        pages_to_process = [page_idx] if page_idx is not None else range(len(self.doc))
        
        for p_idx in pages_to_process:
            page = self.doc[p_idx]
            # 使用 dict 模式获取层级结构
            data = page.get_text("dict", sort=sort_by_reading_order)
            
            for b_idx, block in enumerate(data.get("blocks", [])):
                # 跳过图片块 (type == 1)
                if block.get("type") != 0:
                    continue
                    
                for l_idx, line in enumerate(block.get("lines", [])):
                    for s_idx, span in enumerate(line.get("spans", [])):
                        spans.append(TextSpan(
                            text=span["text"],
                            bbox=tuple(span["bbox"]),
                            page_idx=p_idx,
                            block_idx=b_idx,
                            line_idx=l_idx,
                            span_idx=s_idx,
                            font=span.get("font", ""),
                            size=span.get("size", 0.0),
                        ))
        
        return spans
    
    def extract_words(self, page_idx: Optional[int] = None,
                      sort_by_reading_order: bool = True) -> List[TextWord]:
        """
        提取单词级别的文字坐标
        
        Args:
            page_idx: 指定页面，None 表示所有页面
            sort_by_reading_order: 是否按阅读顺序排序
        """
        words = []
        pages_to_process = [page_idx] if page_idx is not None else range(len(self.doc))
        
        for p_idx in pages_to_process:
            page = self.doc[p_idx]
            # 使用 words 模式
            word_list = page.get_text("words", sort=sort_by_reading_order)
            
            for w_idx, w in enumerate(word_list):
                # word 格式: (x0, y0, x1, y1, "text", block_no, line_no, word_no)
                words.append(TextWord(
                    text=w[4],
                    bbox=(w[0], w[1], w[2], w[3]),
                    page_idx=p_idx,
                    block_idx=w[5],
                    line_idx=w[6],
                    word_idx=w[7] if len(w) > 7 else w_idx,
                ))
        
        return words
    
    def extract_full_text(self, sort_by_reading_order: bool = True) -> str:
        """提取完整文本（用于 LangExtract 输入）"""
        texts = []
        for page in self.doc:
            texts.append(page.get_text("text", sort=sort_by_reading_order))
        return "\n\n".join(texts)
    
    def export_to_json(self, output_path: str, mode: str = "spans",
                       sort_by_reading_order: bool = True) -> Dict[str, Any]:
        """
        导出为 JSON 格式（兼容 MinerU 风格）
        
        Args:
            output_path: 输出文件路径
            mode: "spans" 或 "words"
        """
        result = {
            "source": "PyMuPDF",
            "pdf_path": self.pdf_path,
            "page_count": len(self.doc),
            "pages": []
        }
        
        for page_idx in range(len(self.doc)):
            page = self.doc[page_idx]
            page_info = {
                "page_idx": page_idx,
                "width": page.rect.width,
                "height": page.rect.height,
                "blocks": []
            }
            
            # 使用 dict 模式获取完整结构
            data = page.get_text("dict", sort=sort_by_reading_order)
            
            for block in data.get("blocks", []):
                if block.get("type") != 0:  # 跳过非文本块
                    continue
                    
                block_info = {
                    "type": "text",
                    "bbox": block["bbox"],
                    "lines": []
                }
                
                for line in block.get("lines", []):
                    line_info = {
                        "bbox": line["bbox"],
                        "wmode": line.get("wmode", 0),
                        "dir": line.get("dir", [1.0, 0.0]),
                        "spans": []
                    }
                    
                    for span in line.get("spans", []):
                        span_info = {
                            "text": span["text"],
                            "bbox": span["bbox"],
                            "font": span.get("font", ""),
                            "size": span.get("size", 0.0),
                            "color": span.get("color", 0),
                            "origin": span.get("origin", [0, 0]),
                        }
                        line_info["spans"].append(span_info)
                    
                    block_info["lines"].append(line_info)
                
                page_info["blocks"].append(block_info)
            
            result["pages"].append(page_info)
        
        # 保存到文件
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        return result
    
    def build_span_index(self, mode: str = "spans") -> Dict[str, List[Dict]]:
        """
        构建文字索引，用于快速匹配
        
        Returns:
            Dict[text_lower, List[span_info]]
        """
        index = {}
        
        if mode == "spans":
            items = self.extract_spans()
            for span in items:
                key = span.text.lower().strip()
                if key not in index:
                    index[key] = []
                index[key].append(span.to_dict())
        else:
            items = self.extract_words()
            for word in items:
                key = word.text.lower().strip()
                if key not in index:
                    index[key] = []
                index[key].append(word.to_dict())
        
        return index


def demo_extract(pdf_path: str):
    """演示提取功能"""
    print(f"\n{'='*60}")
    print(f"PyMuPDF 文字坐标提取演示")
    print(f"{'='*60}")
    print(f"PDF: {pdf_path}")
    
    with PyMuPDFTextExtractor(pdf_path) as extractor:
        # 1. 显示 PDF 基本信息
        print(f"\n📄 文档信息:")
        print(f"   页数: {len(extractor.doc)}")
        print(f"   第1页尺寸: {extractor.doc[0].rect.width:.1f} x {extractor.doc[0].rect.height:.1f} pt")
        
        # 2. 提取 span 级别
        print(f"\n📝 Span 级别提取 (前5个):")
        spans = extractor.extract_spans(page_idx=0)
        for span in spans[:5]:
            print(f"   [{span.page_idx}:{span.block_idx}:{span.line_idx}:{span.span_idx}] "
                  f"'{span.text[:30]}...' "
                  f"bbox={span.bbox}")
        
        # 3. 提取 word 级别
        print(f"\n🔤 Word 级别提取 (前10个):")
        words = extractor.extract_words(page_idx=0)
        for word in words[:10]:
            print(f"   '{word.text}' bbox={word.bbox}")
        
        # 4. 导出完整 JSON
        output_path = "pymupdf_output/text_coordinates.json"
        print(f"\n💾 导出完整 JSON: {output_path}")
        result = extractor.export_to_json(output_path)
        print(f"   共 {len(result['pages'])} 页")
        
        # 5. 提取纯文本（给 LangExtract 用）
        print(f"\n📋 提取纯文本 (前200字符):")
        full_text = extractor.extract_full_text()
        print(f"   {full_text[:200]}...")
        
        # 6. 构建索引
        print(f"\n🔍 构建文字索引:")
        index = extractor.build_span_index(mode="words")
        print(f"   共 {len(index)} 个唯一词汇")
        
    print(f"\n{'='*60}")
    print(f"演示完成!")
    print(f"{'='*60}")


if __name__ == "__main__":
    import sys
    
    # 查找测试 PDF
    test_pdf = None
    for pattern in ["mineru_output/*/*.pdf", "*.pdf"]:
        pdfs = list(Path(".").glob(pattern))
        if pdfs:
            test_pdf = str(pdfs[0])
            break
    
    if test_pdf:
        demo_extract(test_pdf)
    else:
        print("请提供 PDF 文件路径: python pymupdf_text_extractor.py <pdf_path>")
