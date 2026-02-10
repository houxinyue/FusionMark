"""
MD 高亮渲染 Pipeline
整合: MinerU + LangExtract + MDRenderer
文本驱动的高亮方案，支持图片型PDF
"""

import os
import sys
import json
import textwrap
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from dotenv import load_dotenv

import langextract as lx
from langextract.factory import ModelConfig
from langextract.providers.openai import OpenAILanguageModel # 显式导入提供者
from md_renderer import MDRenderer, HighlightEntity

# 加载环境变量
load_dotenv()


@dataclass
class PipelineResult:
    """Pipeline 执行结果"""
    success: bool
    md_path: Optional[Path]
    output_path: Optional[Path]
    extraction_count: int
    highlight_count: int
    message: str


class MinerUOutputFinder:
    """
    智能查找 MinerU 输出文件
    支持多种目录结构
    """
    
    def __init__(self, base_dir: str = "mineru_output"):
        self.base_dir = Path(base_dir)
    
    def find_task_files(self, task_id: str) -> Dict[str, Optional[Path]]:
        """
        查找任务相关文件
        :param task_id: 任务ID 或完整路径
        :return: 文件路径字典
        """
        # 支持传入完整路径或 task_id
        task_path = Path(task_id)
        if task_path.exists() and task_path.is_dir():
            task_dir = task_path
        else:
            task_dir = self.base_dir / task_id
        
        if not task_dir.exists():
            raise FileNotFoundError(f"Task directory not found: {task_dir}")
        
        return {
            "md_path": self._find_file(task_dir, "full.md"),
            "layout_path": self._find_file(task_dir, "layout.json"),
            "origin_pdf": self._find_file(task_dir, "*origin*.pdf"),
        }
    
    def _find_file(self, task_dir: Path, pattern: str) -> Optional[Path]:
        """
        按优先级查找文件:
        1. 直接在 task 目录下
        2. 在 extracted/ 子目录下
        3. 任意一级子目录通配查找
        """
        # 1. 直接查找
        direct_matches = list(task_dir.glob(pattern))
        if direct_matches:
            return direct_matches[0]
        
        # 2. 在 extracted/ 子目录下查找
        extracted_dir = task_dir / "extracted"
        if extracted_dir.exists():
            extracted_matches = list(extracted_dir.glob(pattern))
            if extracted_matches:
                return extracted_matches[0]
        
        # 3. 任意一级子目录通配查找
        for subdir in task_dir.iterdir():
            if subdir.is_dir():
                sub_matches = list(subdir.glob(pattern))
                if sub_matches:
                    return sub_matches[0]
        
        return None


class MDHighlightPipeline:
    """
    MD 高亮渲染 Pipeline
    整合文件发现、实体提取、PDF渲染
    """
    
    # 分类颜色配置
    CATEGORY_COLORS = {
        "report_title": "#e67e22",      # 🟠 橙色
        "company_name": "#2ecc71",      # 🟢 绿色
        "shipment_value": "#3498db",    # 🔵 蓝色
        "market_share": "#9b59b6",      # 🟣 紫色
        "yoy_change": "#e84393",        # 🩷 粉色
        "negative_change": "#e74c3c",   # 🔴 红色
        "data_source": "#95a5a6",       # ⚪ 灰色
    }
    
    def __init__(
        self, 
        mineru_output_dir: str = "mineru_output",
        output_dir: str = "highlight_output"
    ):
        self.finder = MinerUOutputFinder(mineru_output_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.renderer = MDRenderer(colors=self.CATEGORY_COLORS)
    
    def _run_langextract(self, md_text: str, prompt: Optional[str] = None) -> List[lx.data.Extraction]:
        """
        使用 LangExtract 提取实体
        """
        print("=" * 60)
        print("Step 1: LangExtract 信息提取")
        print("=" * 60)
        
        # 默认提取提示词
        if prompt is None:
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
        
        # 示例数据
        examples = [
            lx.data.ExampleData(
                text="""Top 5 Companies, Worldwide Smartphone Shipments
                1. Apple 81.3 24.2% 77.5 23.6% 4.9%
                2. Samsung 61.2 18.2% 51.7 15.7% 18.3%
                3. Xiaomi 37.8 11.2% 42.7 13.0% -11.4%
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
                    lx.data.Extraction(extraction_class="negative_change", extraction_text="-11.4%"),
                    lx.data.Extraction(extraction_class="data_source", extraction_text="Source: IDC Quarterly Mobile Phone Tracker"),
                ]
            )
        ]
        
        print("🤖 调用 LangExtract...")
        
        result = lx.extract(
            examples=examples,
            text_or_documents=md_text,
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
    
    def _convert_to_highlight_entities(
        self, 
        extractions: List[lx.data.Extraction]
    ) -> List[HighlightEntity]:
        """
        将 LangExtract 结果转换为 HighlightEntity
        """
        entities = []
        for ext in extractions:
            category = ext.extraction_class
            color = self.CATEGORY_COLORS.get(category)
            entities.append(HighlightEntity(
                text=ext.extraction_text,
                category=category,
                color=color
            ))
        return entities
    
    def process(
        self,
        task_id: str,
        output_filename: Optional[str] = None,
        custom_prompt: Optional[str] = None
    ) -> PipelineResult:
        """
        执行完整 Pipeline
        
        :param task_id: MinerU 任务ID 或目录路径
        :param output_filename: 输出文件名（默认: {task_id}_highlighted.pdf）
        :param custom_prompt: 自定义 LangExtract 提示词
        :return: PipelineResult
        """
        print("\n" + "=" * 70)
        print("MD 高亮渲染 Pipeline")
        print("=" * 70)
        
        # Step 0: 查找文件
        print("\n" + "=" * 60)
        print("Step 0: 智能文件发现")
        print("=" * 60)
        
        try:
            files = self.finder.find_task_files(task_id)
        except FileNotFoundError as e:
            return PipelineResult(
                success=False,
                md_path=None,
                output_path=None,
                extraction_count=0,
                highlight_count=0,
                message=str(e)
            )
        
        md_path = files.get("md_path")
        if not md_path or not md_path.exists():
            return PipelineResult(
                success=False,
                md_path=None,
                output_path=None,
                extraction_count=0,
                highlight_count=0,
                message=f"未找到 full.md，请检查 MinerU 输出结构"
            )
        
        print(f"✅ 找到 Markdown: {md_path}")
        if files.get("layout_path"):
            print(f"   layout.json: {files['layout_path']}")
        if files.get("origin_pdf"):
            print(f"   origin.pdf: {files['origin_pdf']}")
        
        # Step 1: 读取 Markdown
        print(f"\n📖 读取 Markdown...")
        with open(md_path, 'r', encoding='utf-8') as f:
            md_text = f.read()
        print(f"   共 {len(md_text)} 字符")
        
        # Step 2: LangExtract 提取
        try:
            extractions = self._run_langextract(md_text, custom_prompt)
        except Exception as e:
            return PipelineResult(
                success=False,
                md_path=md_path,
                output_path=None,
                extraction_count=0,
                highlight_count=0,
                message=f"LangExtract 提取失败: {e}"
            )
        
        if not extractions:
            return PipelineResult(
                success=False,
                md_path=md_path,
                output_path=None,
                extraction_count=0,
                highlight_count=0,
                message="没有提取到任何实体"
            )
        
        # Step 3: 转换为 HighlightEntity
        entities = self._convert_to_highlight_entities(extractions)
        
        # Step 4: 渲染 PDF
        print("\n" + "=" * 60)
        print("Step 2: MD 高亮渲染")
        print("=" * 60)
        
        if output_filename is None:
            output_filename = f"{Path(task_id).name}_highlighted.pdf"
        
        output_path = self.output_dir / output_filename
        
        try:
            entity_count, highlight_count = self.renderer.render(
                md_content=md_text,
                entities=entities,
                output_path=str(output_path),
                title=f"分析报告 - {task_id}"
            )
        except Exception as e:
            return PipelineResult(
                success=False,
                md_path=md_path,
                output_path=None,
                extraction_count=len(extractions),
                highlight_count=0,
                message=f"PDF 渲染失败: {e}"
            )
        
        # 完成摘要
        print("\n" + "=" * 70)
        print("完成摘要")
        print("=" * 70)
        print(f"\n✅ 输入 MD: {md_path}")
        print(f"✅ 输出 PDF: {output_path}")
        print(f"\n📊 统计:")
        print(f"   - 提取实体: {len(extractions)}")
        print(f"   - 高亮次数: {highlight_count}")
        
        # 按类别统计
        category_counts = {}
        for ext in extractions:
            category_counts[ext.extraction_class] = category_counts.get(ext.extraction_class, 0) + 1
        print(f"\n📋 按类别分布:")
        for cat, count in sorted(category_counts.items()):
            color_emoji = {
                "report_title": "🟠",
                "company_name": "🟢",
                "shipment_value": "🔵",
                "market_share": "🟣",
                "yoy_change": "🩷",
                "negative_change": "🔴",
                "data_source": "⚪",
            }.get(cat, "⚫")
            print(f"   {color_emoji} {cat}: {count}")
        
        print("\n" + "=" * 70)
        
        return PipelineResult(
            success=True,
            md_path=md_path,
            output_path=output_path,
            extraction_count=len(extractions),
            highlight_count=highlight_count,
            message="处理成功"
        )


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="MD 高亮渲染 Pipeline")
    parser.add_argument("task_id", default="513f81dc-4fca-42b3-a4a9-0d58d99db2d2",help="MinerU 任务ID 或目录路径")
    parser.add_argument("-o", "--output", help="输出文件名")
    parser.add_argument("--mineru-dir", default="mineru_output", help="MinerU 输出目录")
    parser.add_argument("--output-dir", default="highlight_output", help="高亮输出目录")
    
    args = parser.parse_args()
    
    pipeline = MDHighlightPipeline(
        mineru_output_dir=args.mineru_dir,
        output_dir=args.output_dir
    )
    
    result = pipeline.process(
        task_id=args.task_id,
        output_filename=args.output
    )
    
    if result.success:
        print(f"\n🎉 成功! 输出: {result.output_path}")
        sys.exit(0)
    else:
        print(f"\n❌ 失败: {result.message}")
        sys.exit(1)


if __name__ == "__main__":
    main()
