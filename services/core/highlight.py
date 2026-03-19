"""
MD 高亮渲染服务
可配置的 Pipeline 服务，支持 LangExtract 参数和高亮颜色的灵活配置

使用方式:
    1. 配置文件方式: service = MDHighlightService.from_config("config.yaml")
    2. 代码方式: service = MDHighlightService(config=MDHighlightConfig(...))
    3. API 方式: service.process(task_id) / service.process_text(md_text)
"""

import os
import sys
import json
import yaml
import textwrap
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any, Union
from dataclasses import dataclass, field, asdict
from dotenv import load_dotenv

import langextract as lx
from langextract.data import Extraction, ExampleData
from langextract.factory import ModelConfig
from langextract.providers.openai import OpenAILanguageModel # 显式导入提供者
from services.utils.renderer import MDRenderer, HighlightEntity

# 加载环境变量 (从 services/ 目录)
_ENV_PATH = Path(__file__).parent.parent / ".env"
if _ENV_PATH.exists():
    load_dotenv(_ENV_PATH)
else:
    load_dotenv()


@dataclass
class LangExtractExample:
    """LangExtract 示例数据配置"""
    text: str
    extractions: List[Dict[str, str]] = field(default_factory=list)
    
    def to_example_data(self) -> ExampleData:
        """转换为 LangExtract ExampleData"""
        return ExampleData(
            text=self.text,
            extractions=[
                Extraction(extraction_class=e["class"], extraction_text=e["text"])
                for e in self.extractions
            ]
        )


@dataclass
class CategoryColor:
    """分类颜色配置"""
    name: str
    color: str
    description: str = ""


@dataclass
class ModelProviderConfig:
    """模型提供者配置"""
    model_id: str = "deepseek-chat"
    provider: str = "OpenAILanguageModel"
    api_key_env: str = "DS_API_KEY"
    base_url_env: str = "DS_API_BASE_URL"
    provider_kwargs: Dict[str, Any] = field(default_factory=dict)
    
    def get_model_config(self) -> ModelConfig:
        """获取 ModelConfig 实例"""
        kwargs = {
            "api_key": os.getenv(self.api_key_env),
            "base_url": os.getenv(self.base_url_env),
            **self.provider_kwargs
        }
        return ModelConfig(
            model_id=self.model_id,
            provider=self.provider,
            provider_kwargs=kwargs
        )


@dataclass
class MDHighlightConfig:
    """
    MD 高亮服务配置
    
    支持从字典、JSON、YAML 加载配置
    """
    # === LangExtract 配置 ===
    # 提取提示词模板
    extraction_prompt: str = field(default_factory=lambda: textwrap.dedent("""\
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
        """))
    
    # 示例数据列表
    examples: List[LangExtractExample] = field(default_factory=lambda: [
        LangExtractExample(
            text="""Top 5 Companies, Worldwide Smartphone Shipments
                1. Apple 81.3 24.2% 77.5 23.6% 4.9%
                2. Samsung 61.2 18.2% 51.7 15.7% 18.3%
                3. Xiaomi 37.8 11.2% 42.7 13.0% -11.4%
                Source: IDC Quarterly Mobile Phone Tracker""",
            extractions=[
                {"class": "report_title", "text": "Top 5 Companies, Worldwide Smartphone Shipments"},
                {"class": "company_name", "text": "Apple"},
                {"class": "shipment_value", "text": "81.3"},
                {"class": "market_share", "text": "24.2%"},
                {"class": "yoy_change", "text": "4.9%"},
                {"class": "company_name", "text": "Samsung"},
                {"class": "shipment_value", "text": "61.2"},
                {"class": "yoy_change", "text": "18.3%"},
                {"class": "company_name", "text": "Xiaomi"},
                {"class": "shipment_value", "text": "37.8"},
                {"class": "negative_change", "text": "-11.4%"},
                {"class": "data_source", "text": "Source: IDC Quarterly Mobile Phone Tracker"},
            ]
        )
    ])
    
    # 模型配置
    model_config: ModelProviderConfig = field(default_factory=ModelProviderConfig)
    
    # === 颜色配置 ===
    category_colors: List[CategoryColor] = field(default_factory=lambda: [
        CategoryColor("report_title", "#e67e22", "报告标题"),
        CategoryColor("company_name", "#2ecc71", "公司名称"),
        CategoryColor("shipment_value", "#3498db", "出货量数值"),
        CategoryColor("market_share", "#9b59b6", "市场份额"),
        CategoryColor("yoy_change", "#e84393", "同比增长率"),
        CategoryColor("negative_change", "#e74c3c", "负增长/负值"),
        CategoryColor("data_source", "#95a5a6", "数据来源"),
    ])
    
    # === 路径配置 ===
    mineru_output_dir: str = "mineru_output"
    output_dir: str = "highlight_output"
    
    # === 渲染配置 ===
    default_title: str = "文档分析报告"
    page_header: str = "文档自动分析报告"
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MDHighlightConfig":
        """从字典创建配置"""
        # 处理嵌套对象
        if "examples" in data:
            data["examples"] = [LangExtractExample(**e) for e in data["examples"]]
        if "model_config" in data:
            data["model_config"] = ModelProviderConfig(**data["model_config"])
        if "category_colors" in data:
            data["category_colors"] = [CategoryColor(**c) for c in data["category_colors"]]
        return cls(**data)
    
    @classmethod
    def from_json(cls, path: Union[str, Path]) -> "MDHighlightConfig":
        """从 JSON 文件加载配置"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    @classmethod
    def from_yaml(cls, path: Union[str, Path]) -> "MDHighlightConfig":
        """从 YAML 文件加载配置"""
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    def to_json(self, path: Union[str, Path], indent: int = 2):
        """保存为 JSON 文件"""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=indent)
    
    def to_yaml(self, path: Union[str, Path]):
        """保存为 YAML 文件"""
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(self.to_dict(), f, allow_unicode=True, default_flow_style=False)
    
    def get_color_map(self) -> Dict[str, str]:
        """获取颜色映射字典 {category: color}"""
        return {c.name: c.color for c in self.category_colors}
    
    def get_color_emoji_map(self) -> Dict[str, str]:
        """获取颜色表情映射"""
        emoji_map = {
            "report_title": "🟠",
            "company_name": "🟢", 
            "shipment_value": "🔵",
            "market_share": "🟣",
            "yoy_change": "🩷",
            "negative_change": "🔴",
            "data_source": "⚪",
        }
        # 为自定义类别生成默认表情
        for c in self.category_colors:
            if c.name not in emoji_map:
                emoji_map[c.name] = "🔶"
        return emoji_map


@dataclass
class ServiceResult:
    """服务执行结果"""
    success: bool
    md_path: Optional[Path] = None
    output_path: Optional[Path] = None
    extraction_count: int = 0
    highlight_count: int = 0
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


class MinerUOutputFinder:
    """智能查找 MinerU 输出文件"""
    
    def __init__(self, base_dir: str = "mineru_output"):
        self.base_dir = Path(base_dir)
    
    def find_task_files(self, task_id: str) -> Dict[str, Optional[Path]]:
        """
        查找任务相关文件
        :param task_id: 任务ID 或完整路径
        :return: 文件路径字典
        """
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
        """按优先级查找文件"""
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


class MDHighlightService:
    """
    MD 高亮渲染服务
    支持完全配置的 Pipeline 服务
    """
    
    def __init__(self, config: Optional[MDHighlightConfig] = None):
        """
        初始化服务
        :param config: 服务配置，如果为 None 使用默认配置
        """
        self.config = config or MDHighlightConfig()
        self.finder = MinerUOutputFinder(self.config.mineru_output_dir)
        self.output_dir = Path(self.config.output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # 初始化渲染器
        self.renderer = MDRenderer(colors=self.config.get_color_map())
    
    @classmethod
    def from_config(cls, path: Union[str, Path]) -> "MDHighlightService":
        """
        从配置文件创建服务实例
        :param path: 配置文件路径 (.json 或 .yaml/.yml)
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        
        if path.suffix in ['.yaml', '.yml']:
            config = MDHighlightConfig.from_yaml(path)
        elif path.suffix == '.json':
            config = MDHighlightConfig.from_json(path)
        else:
            raise ValueError(f"Unsupported config format: {path.suffix}")
        
        return cls(config)
    
    def _run_extraction(self, md_text: str, custom_prompt: Optional[str] = None) -> List[Extraction]:
        """
        使用 LangExtract 提取实体
        :param md_text: Markdown 文本
        :param custom_prompt: 临时覆盖的提示词
        :return: 提取结果列表
        """
        print("=" * 60)
        print("Step 1: LangExtract 信息提取")
        print("=" * 60)
        
        prompt = custom_prompt or self.config.extraction_prompt
        examples = [e.to_example_data() for e in self.config.examples]
        
        print(f"🤖 调用 LangExtract (模型: {self.config.model_config.model_id})...")
        print(f"   使用 {len(examples)} 个示例")
        
        result = lx.extract(
            examples=examples,
            text_or_documents=md_text,
            prompt_description=prompt,
            config=self.config.model_config.get_model_config()
        )
        
        print(f"✅ 提取完成，共 {len(result.extractions)} 个实体")
        
        # 显示提取结果
        print("\n📋 提取结果:")
        for i, ext in enumerate(result.extractions, 1):
            print(f"  {i}. [{ext.extraction_class}] {ext.extraction_text}")
        
        return result.extractions
    
    def _convert_to_entities(self, extractions: List[Extraction]) -> List[HighlightEntity]:
        """
        将 LangExtract 结果转换为 HighlightEntity
        """
        color_map = self.config.get_color_map()
        entities = []
        
        for ext in extractions:
            category = ext.extraction_class
            color = color_map.get(category)
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
        custom_prompt: Optional[str] = None,
        custom_title: Optional[str] = None
    ) -> ServiceResult:
        """
        处理 MinerU 任务
        
        :param task_id: MinerU 任务ID 或目录路径
        :param output_filename: 输出文件名
        :param custom_prompt: 临时覆盖的提取提示词
        :param custom_title: 临时覆盖的文档标题
        :return: ServiceResult
        """
        print("\n" + "=" * 70)
        print("MD 高亮渲染服务")
        print("=" * 70)
        
        # Step 0: 查找文件
        print("\n" + "=" * 60)
        print("Step 0: 智能文件发现")
        print("=" * 60)
        
        try:
            files = self.finder.find_task_files(task_id)
        except FileNotFoundError as e:
            return ServiceResult(success=False, message=str(e))
        
        md_path = files.get("md_path")
        if not md_path or not md_path.exists():
            return ServiceResult(
                success=False,
                message=f"未找到 full.md，请检查 MinerU 输出结构"
            )
        
        print(f"✅ 找到 Markdown: {md_path}")
        
        # 读取 Markdown
        with open(md_path, 'r', encoding='utf-8') as f:
            md_text = f.read()
        print(f"   共 {len(md_text)} 字符")
        
        # 调用文本处理方法
        result = self.process_text(
            md_text=md_text,
            output_filename=output_filename,
            custom_prompt=custom_prompt,
            custom_title=custom_title or f"分析报告 - {Path(task_id).name}"
        )
        
        # 补充路径信息
        result.md_path = md_path
        return result
    
    def process_text(
        self,
        md_text: str,
        output_filename: Optional[str] = None,
        custom_prompt: Optional[str] = None,
        custom_title: Optional[str] = None
    ) -> ServiceResult:
        """
        直接处理 Markdown 文本
        
        :param md_text: Markdown 文本内容
        :param output_filename: 输出文件名
        :param custom_prompt: 临时覆盖的提取提示词
        :param custom_title: 临时覆盖的文档标题
        :return: ServiceResult
        """
        print("\n" + "=" * 70)
        print("MD 高亮渲染服务 (文本模式)")
        print("=" * 70)
        
        # Step 1: LangExtract 提取
        try:
            extractions = self._run_extraction(md_text, custom_prompt)
        except Exception as e:
            return ServiceResult(
                success=False,
                message=f"LangExtract 提取失败: {e}"
            )
        
        if not extractions:
            return ServiceResult(
                success=False,
                message="没有提取到任何实体"
            )
        
        # Step 2: 转换为 HighlightEntity
        entities = self._convert_to_entities(extractions)
        
        # Step 3: 渲染 PDF
        print("\n" + "=" * 60)
        print("Step 2: MD 高亮渲染")
        print("=" * 60)
        
        if output_filename is None:
            import uuid
            output_filename = f"highlighted_{uuid.uuid4().hex[:8]}.pdf"
        
        output_path = self.output_dir / output_filename
        title = custom_title or self.config.default_title
        
        try:
            entity_count, highlight_count = self.renderer.render(
                md_content=md_text,
                entities=entities,
                output_path=str(output_path),
                title=title
            )
        except Exception as e:
            return ServiceResult(
                success=False,
                message=f"PDF 渲染失败: {e}",
                extraction_count=len(extractions)
            )
        
        # 统计信息
        category_counts = {}
        for ext in extractions:
            category_counts[ext.extraction_class] = category_counts.get(ext.extraction_class, 0) + 1
        
        # 打印摘要
        self._print_summary(output_path, len(extractions), highlight_count, category_counts)
        
        return ServiceResult(
            success=True,
            output_path=output_path,
            extraction_count=len(extractions),
            highlight_count=highlight_count,
            message="处理成功",
            details={"category_counts": category_counts}
        )
    
    def _print_summary(self, output_path: Path, extraction_count: int, 
                       highlight_count: int, category_counts: Dict[str, int]):
        """打印处理摘要"""
        print("\n" + "=" * 70)
        print("完成摘要")
        print("=" * 70)
        print(f"\n✅ 输出 PDF: {output_path}")
        print(f"\n📊 统计:")
        print(f"   - 提取实体: {extraction_count}")
        print(f"   - 高亮次数: {highlight_count}")
        
        print(f"\n📋 按类别分布:")
        emoji_map = self.config.get_color_emoji_map()
        for cat, count in sorted(category_counts.items()):
            emoji = emoji_map.get(cat, "🔶")
            print(f"   {emoji} {cat}: {count}")
        
        print("\n" + "=" * 70)
    
    def export_default_config(self, path: Union[str, Path], format: str = "yaml"):
        """
        导出默认配置文件
        :param path: 输出路径
        :param format: 格式 (yaml 或 json)
        """
        path = Path(path)
        if format == "yaml":
            self.config.to_yaml(path)
        else:
            self.config.to_json(path)
        print(f"✅ 默认配置已导出到: {path}")


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="MD 高亮渲染服务")
    parser.add_argument("task_id", nargs="?", help="MinerU 任务ID 或目录路径")
    parser.add_argument("-c", "--config", help="配置文件路径 (.json 或 .yaml)")
    parser.add_argument("-o", "--output", help="输出文件名")
    parser.add_argument("--export-config", metavar="PATH", help="导出默认配置文件")
    parser.add_argument("--export-format", choices=["yaml", "json"], default="yaml",
                       help="导出配置格式")
    parser.add_argument("--mineru-dir", help="MinerU 输出目录")
    parser.add_argument("--output-dir", help="高亮输出目录")
    parser.add_argument("--text", metavar="MD_TEXT", help="直接传入 Markdown 文本")
    parser.add_argument("--text-file", metavar="PATH", help="从文件读取 Markdown 文本")
    
    args = parser.parse_args()
    
    # 导出默认配置
    if args.export_config:
        service = MDHighlightService()
        service.export_default_config(args.export_config, args.export_format)
        return
    
    # 创建服务实例
    if args.config:
        service = MDHighlightService.from_config(args.config)
    else:
        config = MDHighlightConfig()
        if args.mineru_dir:
            config.mineru_output_dir = args.mineru_dir
        if args.output_dir:
            config.output_dir = args.output_dir
        service = MDHighlightService(config)
    
    # 处理文本输入
    if args.text:
        result = service.process_text(md_text=args.text, output_filename=args.output)
    elif args.text_file:
        with open(args.text_file, 'r', encoding='utf-8') as f:
            md_text = f.read()
        result = service.process_text(md_text=md_text, output_filename=args.output)
    elif args.task_id:
        result = service.process(task_id=args.task_id, output_filename=args.output)
    else:
        parser.print_help()
        sys.exit(1)
    
    # 输出结果
    if result.success:
        print(f"\n🎉 成功! 输出: {result.output_path}")
        sys.exit(0)
    else:
        print(f"\n❌ 失败: {result.message}")
        sys.exit(1)


if __name__ == "__main__":
    main()

