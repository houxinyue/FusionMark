"""
MD 高亮渲染 Pipeline
整合: MinerU + LangExtract + MDRenderer
文本驱动的高亮方案，支持图片型PDF

注意: 此模块已升级为基于 MDHighlightService 的包装器
推荐使用 services/core/highlight.py 中的新服务
"""

import sys
from pathlib import Path
from typing import Optional

# 导入新的服务
from services.core.highlight import (
    MDHighlightService,
    MDHighlightConfig,
    ServiceResult
)


# 为向后兼容保留 PipelineResult 别名
PipelineResult = ServiceResult


class MDHighlightPipeline:
    """
    MD 高亮渲染 Pipeline
    
    注意: 此 Pipeline 现在是 MDHighlightService 的包装器，
    使用默认配置运行。如需更灵活的配置，请直接使用 MDHighlightService。
    
    示例:
        # 旧方式（仍然支持）
        pipeline = MDHighlightPipeline()
        result = pipeline.process(task_id="xxx")
        
        # 新方式（推荐）
        from services.core.highlight import MDHighlightService
        service = MDHighlightService.from_config("config.yaml")
        result = service.process(task_id="xxx")
    """
    
    # 分类颜色配置（保留以兼容旧代码）
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
        """
        初始化 Pipeline
        
        :param mineru_output_dir: MinerU 输出目录
        :param output_dir: 高亮输出目录
        """
        # 使用默认配置创建服务
        config = MDHighlightConfig(
            mineru_output_dir=mineru_output_dir,
            output_dir=output_dir
        )
        self._service = MDHighlightService(config)
    
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
        print("MD 高亮渲染 Pipeline (基于 MDHighlightService)")
        print("=" * 70)
        print("提示: 如需更多配置选项，请直接使用 MDHighlightService")
        print("      参见: services/core/highlight.py 和 md_highlight_service_demo.py")
        print("=" * 70)
        
        return self._service.process(
            task_id=task_id,
            output_filename=output_filename,
            custom_prompt=custom_prompt
        )


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="MD 高亮渲染 Pipeline")
    parser.add_argument("task_id", default="513f81dc-4fca-42b3-a4a9-0d58d99db2d2", help="MinerU 任务ID 或目录路径")
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

