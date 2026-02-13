"""
完整流程服务 - PDF 智能解析与高亮
整合: MinerU API + LangExtract + MDRenderer

完整流程:
    PDF URL → MinerU API → Markdown → LangExtract → 高亮 PDF

使用方式:
    1. 简单调用: process_pdf(url)
    2. 配置文件: from_config("config.yaml") -> process_pdf(url)
    3. API 服务: 封装为 Web 接口
"""

import os
import sys
import json
import yaml
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any, Union
from dataclasses import dataclass, field, asdict
from dotenv import load_dotenv

# 导入已有模块
from mineru_client import MinerUClient, MinerUConfig, ParseResult
from md_highlight_service import (
    MDHighlightService, 
    MDHighlightConfig,
    LangExtractExample,
    CategoryColor,
    ModelProviderConfig,
    ServiceResult
)

# 加载环境变量
load_dotenv()


@dataclass
class FullPipelineConfig:
    """
    完整流程配置
    整合 MinerU + LangExtract + 渲染配置
    """
    
    # === MinerU 配置 ===
    mineru_api_key: str = field(default_factory=lambda: os.getenv("MINERU_API_KEY", ""))
    mineru_base_url: str = "https://mineru.net/api/v4/extract"
    mineru_output_dir: str = "mineru_output"
    mineru_model: str = "vlm"  # pipeline, vlm, MinerU-HTML
    mineru_enable_ocr: bool = True
    mineru_enable_formula: bool = True
    mineru_enable_table: bool = True
    mineru_language: str = "ch"
    mineru_poll_interval: int = 3
    mineru_max_retries: int = 60
    
    # === LangExtract & 渲染配置 ===
    highlight_config: MDHighlightConfig = field(default_factory=MDHighlightConfig)
    
    # === 输出配置 ===
    final_output_dir: str = "highlight_output"
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FullPipelineConfig":
        """从字典创建配置"""
        if "highlight_config" in data:
            data["highlight_config"] = MDHighlightConfig.from_dict(data["highlight_config"])
        return cls(**data)
    
    @classmethod
    def from_json(cls, path: Union[str, Path]) -> "FullPipelineConfig":
        """从 JSON 文件加载配置"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    @classmethod
    def from_yaml(cls, path: Union[str, Path]) -> "FullPipelineConfig":
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
    
    def get_mineru_config(self) -> MinerUConfig:
        """获取 MinerUConfig 实例"""
        return MinerUConfig(
            api_key=self.mineru_api_key,
            base_url=self.mineru_base_url,
            output_dir=self.mineru_output_dir,
            poll_interval=self.mineru_poll_interval,
            max_poll_retries=self.mineru_max_retries
        )


@dataclass
class PipelineResult:
    """完整流程执行结果"""
    success: bool
    task_id: Optional[str] = None
    mineru_result: Optional[ParseResult] = None
    highlight_result: Optional[ServiceResult] = None
    message: str = ""
    
    @property
    def output_path(self) -> Optional[Path]:
        """获取最终输出路径"""
        if self.highlight_result:
            return self.highlight_result.output_path
        return None
    
    @property
    def md_content(self) -> Optional[str]:
        """获取提取的 Markdown 内容"""
        if self.mineru_result:
            return self.mineru_result.content
        return None


class FullPipelineService:
    """
    完整流程服务
    
    整合 MinerU API + LangExtract + MD 高亮渲染
    """
    
    def __init__(self, config: Optional[FullPipelineConfig] = None):
        """
        初始化服务
        
        :param config: 完整流程配置，None 时使用默认配置
        """
        self.config = config or FullPipelineConfig()
        
        # 初始化 MinerU 客户端
        if not self.config.mineru_api_key:
            raise ValueError("MinerU API Key 未设置，请设置 MINERU_API_KEY 环境变量或在配置中指定")
        
        self.mineru_client = MinerUClient(self.config.get_mineru_config())
        
        # 初始化高亮服务
        # 同步输出目录
        self.config.highlight_config.output_dir = self.config.final_output_dir
        self.highlight_service = MDHighlightService(self.config.highlight_config)
    
    @classmethod
    def from_config(cls, path: Union[str, Path]) -> "FullPipelineService":
        """
        从配置文件创建服务实例
        
        :param path: 配置文件路径 (.json 或 .yaml/.yml)
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        
        if path.suffix in ['.yaml', '.yml']:
            config = FullPipelineConfig.from_yaml(path)
        elif path.suffix == '.json':
            config = FullPipelineConfig.from_json(path)
        else:
            raise ValueError(f"Unsupported config format: {path.suffix}")
        
        return cls(config)
    
    def process_pdf(
        self,
        url: str,
        output_filename: Optional[str] = None,
        custom_prompt: Optional[str] = None,
        custom_title: Optional[str] = None,
        **mineru_kwargs
    ) -> PipelineResult:
        """
        处理 PDF 完整流程
        
        流程: PDF URL → MinerU API → Markdown → LangExtract → 高亮 PDF
        
        :param url: PDF 文件 URL
        :param output_filename: 最终输出文件名
        :param custom_prompt: 自定义 LangExtract 提示词
        :param custom_title: 自定义文档标题
        :param mineru_kwargs: 传递给 MinerU 的额外参数
        :return: PipelineResult
        """
        print("\n" + "=" * 70)
        print("完整流程服务 - PDF 智能解析与高亮")
        print("=" * 70)
        print(f"PDF URL: {url}")
        print("=" * 70)
        
        # ========== Step 1: MinerU 解析 ==========
        print("\n📄 Step 1: MinerU 文档解析")
        print("-" * 60)
        
        mineru_result = self.mineru_client.process_document(
            url=url,
            model_version=self.config.mineru_model,
            is_ocr=self.config.mineru_enable_ocr,
            enable_formula=self.config.mineru_enable_formula,
            enable_table=self.config.mineru_enable_table,
            language=self.config.mineru_language,
            **mineru_kwargs
        )
        
        if not mineru_result:
            return PipelineResult(
                success=False,
                message="MinerU 解析失败"
            )
        
        if mineru_result.state == MinerUClient.STATE_FAILED:
            return PipelineResult(
                success=False,
                task_id=mineru_result.task_id,
                mineru_result=mineru_result,
                message=f"MinerU 任务失败: {mineru_result.error_msg}"
            )
        
        if not mineru_result.content:
            return PipelineResult(
                success=False,
                task_id=mineru_result.task_id,
                mineru_result=mineru_result,
                message="MinerU 未返回内容"
            )
        
        print(f"✅ MinerU 解析完成")
        print(f"   Task ID: {mineru_result.task_id}")
        print(f"   内容长度: {len(mineru_result.content)} 字符")
        
        # ========== Step 2: LangExtract + 高亮渲染 ==========
        print("\n🎨 Step 2: LangExtract 提取 & 高亮渲染")
        print("-" * 60)
        
        # 使用 task_id 作为默认输出文件名
        if output_filename is None:
            output_filename = f"{mineru_result.task_id}_highlighted.pdf"
        
        title = custom_title or f"智能分析报告 - {mineru_result.task_id}"
        
        highlight_result = self.highlight_service.process_text(
            md_text=mineru_result.content,
            output_filename=output_filename,
            custom_prompt=custom_prompt,
            custom_title=title
        )
        
        if not highlight_result.success:
            return PipelineResult(
                success=False,
                task_id=mineru_result.task_id,
                mineru_result=mineru_result,
                highlight_result=highlight_result,
                message=f"高亮渲染失败: {highlight_result.message}"
            )
        
        # ========== 完成摘要 ==========
        print("\n" + "=" * 70)
        print("✅ 完整流程执行成功")
        print("=" * 70)
        print(f"\n📊 执行摘要:")
        print(f"   Task ID: {mineru_result.task_id}")
        print(f"   Markdown 长度: {len(mineru_result.content)} 字符")
        print(f"   提取实体数: {highlight_result.extraction_count}")
        print(f"   高亮次数: {highlight_result.highlight_count}")
        print(f"\n📁 输出文件:")
        print(f"   MinerU 结果: {mineru_result.extract_dir}")
        print(f"   高亮 PDF: {highlight_result.output_path}")
        
        return PipelineResult(
            success=True,
            task_id=mineru_result.task_id,
            mineru_result=mineru_result,
            highlight_result=highlight_result,
            message="处理成功"
        )
    
    def process_md_direct(
        self,
        md_text: str,
        output_filename: Optional[str] = None,
        custom_prompt: Optional[str] = None,
        custom_title: Optional[str] = None
    ) -> PipelineResult:
        """
        直接处理 Markdown 文本（跳过 MinerU）
        
        :param md_text: Markdown 文本内容
        :param output_filename: 输出文件名
        :param custom_prompt: 自定义 LangExtract 提示词
        :param custom_title: 自定义文档标题
        :return: PipelineResult
        """
        print("\n" + "=" * 70)
        print("流程服务 - Markdown 直接处理")
        print("=" * 70)
        
        highlight_result = self.highlight_service.process_text(
            md_text=md_text,
            output_filename=output_filename,
            custom_prompt=custom_prompt,
            custom_title=custom_title
        )
        
        return PipelineResult(
            success=highlight_result.success,
            highlight_result=highlight_result,
            message=highlight_result.message
        )
    
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
    
    parser = argparse.ArgumentParser(
        description="完整流程服务 - PDF 智能解析与高亮",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 使用默认配置处理 PDF
  python full_pipeline_service.py "https://example.com/file.pdf"
  
  # 使用配置文件
  python full_pipeline_service.py "https://example.com/file.pdf" -c config.yaml
  
  # 导出默认配置
  python full_pipeline_service.py --export-config my_config.yaml
        """
    )
    
    parser.add_argument("url", nargs="?", help="PDF 文件 URL")
    parser.add_argument("-c", "--config", help="配置文件路径 (.json 或 .yaml)")
    parser.add_argument("-o", "--output", help="输出文件名")
    parser.add_argument("--export-config", metavar="PATH", help="导出默认配置文件")
    parser.add_argument("--export-format", choices=["yaml", "json"], default="yaml",
                       help="导出配置格式")
    parser.add_argument("--model", choices=["pipeline", "vlm", "MinerU-HTML"],
                       default="vlm", help="MinerU 模型版本")
    parser.add_argument("--no-ocr", action="store_true", help="禁用 OCR")
    parser.add_argument("--md-file", metavar="PATH", help="直接处理 Markdown 文件（跳过 MinerU）")
    
    args = parser.parse_args()
    
    # 导出默认配置
    if args.export_config:
        service = FullPipelineService()
        service.export_default_config(args.export_config, args.export_format)
        return
    
    # 创建服务实例
    if args.config:
        service = FullPipelineService.from_config(args.config)
    else:
        config = FullPipelineConfig()
        config.mineru_model = args.model
        config.mineru_enable_ocr = not args.no_ocr
        service = FullPipelineService(config)
    
    # 处理 Markdown 文件（跳过 MinerU）
    if args.md_file:
        with open(args.md_file, 'r', encoding='utf-8') as f:
            md_text = f.read()
        result = service.process_md_direct(
            md_text=md_text,
            output_filename=args.output
        )
    # 处理 PDF URL
    elif args.url:
        result = service.process_pdf(
            url=args.url,
            output_filename=args.output
        )
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
