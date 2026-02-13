"""
完整流程服务使用示例
展示如何使用 FullPipelineService 实现 PDF → 高亮 PDF 的完整流程
"""

from full_pipeline_service import (
    FullPipelineService,
    FullPipelineConfig,
    MDHighlightConfig,
    LangExtractExample,
    CategoryColor
)


def demo_basic_usage():
    """示例 1: 基本使用（默认配置）"""
    print("=" * 60)
    print("示例 1: 基本使用（默认配置）")
    print("=" * 60)
    
    # 确保环境变量已设置:
    # - MINERU_API_KEY
    # - DS_API_KEY
    
    # 使用默认配置创建服务
    service = FullPipelineService()
    
    # 处理 PDF
    result = service.process_pdf(
        url="https://example.com/sample_report.pdf",
        output_filename="demo_basic.pdf"
    )
    
    if result.success:
        print(f"✅ 成功!")
        print(f"   Task ID: {result.task_id}")
        print(f"   输出: {result.output_path}")
        print(f"   实体数: {result.highlight_result.extraction_count}")
    else:
        print(f"❌ 失败: {result.message}")


def demo_custom_config():
    """示例 2: 自定义配置（药品说明书场景）"""
    print("\n" + "=" * 60)
    print("示例 2: 自定义配置（药品说明书场景）")
    print("=" * 60)
    
    # 创建自定义配置
    highlight_config = MDHighlightConfig(
        extraction_prompt="""
        从药品说明书中提取以下信息：
        
        1. drug_name: 药品名称
        2. ingredient: 主要成分
        3. specification: 规格
        4. dosage: 用法用量
        5. side_effect: 不良反应
        6. contraindication: 禁忌
        7. precaution: 注意事项
        8. manufacturer: 生产厂家
        
        提取规则：
        - 使用原文中的精确文本
        - 多个成分分开提取
        """,
        
        examples=[
            LangExtractExample(
                text="""
                阿莫西林胶囊
                【成份】本品主要成份为阿莫西林
                【规格】0.25g
                【用法用量】口服。成人一次0.5g，每6-8小时1次
                【不良反应】恶心、呕吐、腹泻
                【禁忌】青霉素过敏者禁用
                【注意事项】用药前需做皮试
                【生产企业】华北制药股份有限公司
                """,
                extractions=[
                    {"class": "drug_name", "text": "阿莫西林胶囊"},
                    {"class": "ingredient", "text": "阿莫西林"},
                    {"class": "specification", "text": "0.25g"},
                    {"class": "dosage", "text": "口服。成人一次0.5g，每6-8小时1次"},
                    {"class": "side_effect", "text": "恶心、呕吐、腹泻"},
                    {"class": "contraindication", "text": "青霉素过敏者禁用"},
                    {"class": "precaution", "text": "用药前需做皮试"},
                    {"class": "manufacturer", "text": "华北制药股份有限公司"},
                ]
            )
        ],
        
        category_colors=[
            CategoryColor("drug_name", "#e74c3c", "药品名称"),
            CategoryColor("ingredient", "#3498db", "主要成分"),
            CategoryColor("specification", "#9b59b6", "规格"),
            CategoryColor("dosage", "#2ecc71", "用法用量"),
            CategoryColor("side_effect", "#f39c12", "不良反应"),
            CategoryColor("contraindication", "#e74c3c", "禁忌"),
            CategoryColor("precaution", "#f1c40f", "注意事项"),
            CategoryColor("manufacturer", "#95a5a6", "生产厂家"),
        ]
    )
    
    config = FullPipelineConfig(
        mineru_model="vlm",           # 使用高精度模型
        mineru_enable_ocr=True,       # 启用 OCR
        mineru_enable_table=True,     # 启用表格识别
        highlight_config=highlight_config,
        final_output_dir="drug_output"
    )
    
    service = FullPipelineService(config)
    
    result = service.process_pdf(
        url="https://example.com/drug_manual.pdf",
        output_filename="drug_highlighted.pdf"
    )
    
    if result.success:
        print(f"✅ 成功!")
        print(f"   药品名称等实体已提取并高亮")
    else:
        print(f"❌ 失败: {result.message}")


def demo_config_file():
    """示例 3: 从配置文件加载"""
    print("\n" + "=" * 60)
    print("示例 3: 从配置文件加载")
    print("=" * 60)
    
    # 从 YAML 配置文件加载
    service = FullPipelineService.from_config("full_pipeline_config.yaml")
    
    result = service.process_pdf(
        url="https://example.com/report.pdf",
        output_filename="config_based.pdf"
    )
    
    if result.success:
        print(f"✅ 成功!")
    else:
        print(f"❌ 失败: {result.message}")


def demo_md_direct():
    """示例 4: 直接处理 Markdown（跳过 MinerU）"""
    print("\n" + "=" * 60)
    print("示例 4: 直接处理 Markdown（跳过 MinerU）")
    print("=" * 60)
    
    service = FullPipelineService()
    
    md_text = """
    # 2025年Q4智能手机市场报告
    
    ## 市场表现
    
    根据 IDC 的最新数据，2025年第四季度全球智能手机出货量如下：
    
    | 排名 | 公司 | 出货量(百万台) | 市场份额 | 同比增长 |
    |------|------|----------------|----------|----------|
    | 1 | Apple | 81.3 | 24.2% | +4.9% |
    | 2 | Samsung | 61.2 | 18.2% | +18.3% |
    | 3 | Xiaomi | 37.8 | 11.2% | -11.4% |
    
    **数据来源**: IDC Quarterly Mobile Phone Tracker, January 2026
    """
    
    result = service.process_md_direct(
        md_text=md_text,
        output_filename="direct_md.pdf"
    )
    
    if result.success:
        print(f"✅ 成功!")
        print(f"   输出: {result.output_path}")
    else:
        print(f"❌ 失败: {result.message}")


def demo_export_config():
    """示例 5: 导出默认配置"""
    print("\n" + "=" * 60)
    print("示例 5: 导出默认配置")
    print("=" * 60)
    
    service = FullPipelineService()
    
    # 导出为 YAML
    service.export_default_config("my_pipeline_config.yaml", format="yaml")
    
    # 导出为 JSON
    service.export_default_config("my_pipeline_config.json", format="json")
    
    print("\n💡 提示: 编辑导出的配置文件，然后使用:")
    print("   service = FullPipelineService.from_config('my_pipeline_config.yaml')")


def demo_api_style():
    """示例 6: API 风格调用（适合封装为 Web 服务）"""
    print("\n" + "=" * 60)
    print("示例 6: API 风格调用（Web 服务封装）")
    print("=" * 60)
    
    # 初始化服务（应用启动时）
    service = FullPipelineService.from_config("full_pipeline_config.yaml")
    
    # 模拟 API 请求
    api_request = {
        "pdf_url": "https://example.com/report.pdf",
        "output_filename": "api_result.pdf",
        "custom_prompt": None,  # 可选
        "custom_title": "智能分析报告",  # 可选
        # MinerU 参数
        "mineru_options": {
            "is_ocr": True,
            "enable_table": True
        }
    }
    
    # 处理请求
    result = service.process_pdf(
        url=api_request["pdf_url"],
        output_filename=api_request["output_filename"],
        custom_title=api_request["custom_title"],
        **api_request.get("mineru_options", {})
    )
    
    # 构造 API 响应
    api_response = {
        "success": result.success,
        "task_id": result.task_id,
        "output_url": f"/downloads/{result.output_path.name}" if result.output_path else None,
        "stats": {
            "md_length": len(result.md_content) if result.md_content else 0,
            "extraction_count": result.highlight_result.extraction_count if result.highlight_result else 0,
            "highlight_count": result.highlight_result.highlight_count if result.highlight_result else 0,
        },
        "message": result.message
    }
    
    print(f"API 响应:\n{api_response}")


def main():
    """运行示例"""
    print("\n" + "=" * 70)
    print("完整流程服务 - 使用示例")
    print("=" * 70)
    
    # 选择要运行的示例
    demos = [
        ("导出默认配置", demo_export_config),
        # ("基本使用", demo_basic_usage),
        # ("自定义配置", demo_custom_config),
        # ("配置文件", demo_config_file),
        # ("直接处理 MD", demo_md_direct),
        # ("API 风格", demo_api_style),
    ]
    
    for name, demo_func in demos:
        try:
            demo_func()
        except Exception as e:
            print(f"❌ {name} 失败: {e}")
    
    print("\n" + "=" * 70)
    print("提示: 取消注释 demos 列表中的行来运行其他示例")
    print("      确保已设置环境变量: MINERU_API_KEY, DS_API_KEY")
    print("=" * 70)


if __name__ == "__main__":
    main()
