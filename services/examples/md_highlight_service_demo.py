"""
MD 高亮渲染服务使用示例
展示如何使用可配置的服务
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from md_highlight_service import (
    MDHighlightService, 
    MDHighlightConfig,
    LangExtractExample,
    CategoryColor,
    ModelProviderConfig
)


def demo_basic_usage():
    """示例 1: 基本使用（默认配置）"""
    print("=" * 60)
    print("示例 1: 基本使用（默认配置）")
    print("=" * 60)
    
    # 使用默认配置创建服务
    service = MDHighlightService()
    
    # 处理任务
    result = service.process(
        task_id="513f81dc-4fca-42b3-a4a9-0d58d99db2d2",
        output_filename="demo_default.pdf"
    )
    
    if result.success:
        print(f"✅ 成功生成: {result.output_path}")
    else:
        print(f"❌ 失败: {result.message}")


def demo_custom_config_code():
    """示例 2: 通过代码自定义配置"""
    print("\n" + "=" * 60)
    print("示例 2: 通过代码自定义配置")
    print("=" * 60)
    
    # 创建自定义配置
    config = MDHighlightConfig(
        # 自定义提取提示词（例如：提取药品说明书信息）
        extraction_prompt="""
        从药品说明书中提取以下信息：
        
        1. drug_name: 药品名称
        2. ingredient: 主要成分
        3. dosage: 用法用量
        4. side_effect: 不良反应
        5. contraindication: 禁忌
        6. manufacturer: 生产厂家
        
        提取规则：
        - 使用原文中的精确文本
        - 每个成分单独提取
        """,
        
        # 自定义示例数据
        examples=[
            LangExtractExample(
                text="""
                阿莫西林胶囊
                【成分】本品主要成分为阿莫西林
                【用法用量】成人一次0.5g，每6-8小时1次
                【不良反应】恶心、呕吐、腹泻
                【禁忌】青霉素过敏者禁用
                【生产企业】华北制药股份有限公司
                """,
                extractions=[
                    {"class": "drug_name", "text": "阿莫西林胶囊"},
                    {"class": "ingredient", "text": "阿莫西林"},
                    {"class": "dosage", "text": "成人一次0.5g，每6-8小时1次"},
                    {"class": "side_effect", "text": "恶心、呕吐、腹泻"},
                    {"class": "contraindication", "text": "青霉素过敏者禁用"},
                    {"class": "manufacturer", "text": "华北制药股份有限公司"},
                ]
            )
        ],
        
        # 自定义颜色
        category_colors=[
            CategoryColor("drug_name", "#e74c3c", "药品名称"),
            CategoryColor("ingredient", "#3498db", "主要成分"),
            CategoryColor("dosage", "#2ecc71", "用法用量"),
            CategoryColor("side_effect", "#f39c12", "不良反应"),
            CategoryColor("contraindication", "#9b59b6", "禁忌"),
            CategoryColor("manufacturer", "#95a5a6", "生产厂家"),
        ],
        
        # 自定义路径
        output_dir="highlight_output_drug"
    )
    
    # 使用自定义配置创建服务
    service = MDHighlightService(config)
    
    # 处理 Markdown 文本
    md_text = """
    # 药品说明书
    
    ## 布洛芬缓释胶囊
    
    **【成分】** 本品每粒含主要成份布洛芬 0.3 克
    
    **【用法用量】** 口服。成人一次 1 粒，一日 2 次（早晚各一次）
    
    **【不良反应】** 少数病人可能出现恶心、呕吐、胃烧灼感
    
    **【禁忌】** 对本品及其他非甾体抗炎药过敏者禁用
    
    **【生产企业】** 上海强生制药有限公司
    """
    
    result = service.process_text(
        md_text=md_text,
        output_filename="demo_drug.pdf"
    )
    
    if result.success:
        print(f"✅ 成功生成: {result.output_path}")
    else:
        print(f"❌ 失败: {result.message}")


def demo_config_file():
    """示例 3: 从配置文件加载"""
    print("\n" + "=" * 60)
    print("示例 3: 从配置文件加载")
    print("=" * 60)
    
    # 方式 1: 从 YAML 文件加载
    # service = MDHighlightService.from_config("config_example.yaml")
    
    # 方式 2: 从 JSON 文件加载
    # service = MDHighlightService.from_config("config_example.json")
    
    # 方式 3: 先导出默认配置，再修改使用
    service = MDHighlightService()
    service.export_default_config("my_config.yaml", format="yaml")
    
    print("✅ 默认配置已导出到 my_config.yaml")
    print("   您可以编辑此文件后使用: MDHighlightService.from_config('my_config.yaml')")


def demo_text_mode():
    """示例 4: 直接处理 Markdown 文本（无需 MinerU 输出）"""
    print("\n" + "=" * 60)
    print("示例 4: 直接处理 Markdown 文本")
    print("=" * 60)
    
    service = MDHighlightService()
    
    # 直接传入 Markdown 文本
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
    
    result = service.process_text(
        md_text=md_text,
        output_filename="demo_text_mode.pdf"
    )
    
    if result.success:
        print(f"✅ 成功生成: {result.output_path}")
        print(f"   提取实体数: {result.extraction_count}")
        print(f"   高亮次数: {result.highlight_count}")
    else:
        print(f"❌ 失败: {result.message}")


def demo_override_prompt():
    """示例 5: 运行时覆盖提示词"""
    print("\n" + "=" * 60)
    print("示例 5: 运行时覆盖提示词")
    print("=" * 60)
    
    service = MDHighlightService()
    
    # 使用默认配置，但临时覆盖提示词
    custom_prompt = """
    从财务报告中提取以下信息：
    
    1. revenue: 营收金额
    2. profit: 利润
    3. expense: 费用
    4. growth_rate: 增长率
    """
    
    md_text = """
    # 2025年度财务报告
    
    本年度公司营收达到 1000 万元，同比增长 25%。
    净利润为 200 万元，运营费用控制在 600 万元。
    """
    
    result = service.process_text(
        md_text=md_text,
        custom_prompt=custom_prompt,
        output_filename="demo_override.pdf"
    )
    
    if result.success:
        print(f"✅ 成功生成: {result.output_path}")
        print(f"   类别分布: {result.details.get('category_counts', {})}")
    else:
        print(f"❌ 失败: {result.message}")


def demo_api_style():
    """示例 6: API 风格调用（适合 Web 服务封装）"""
    print("\n" + "=" * 60)
    print("示例 6: API 风格调用")
    print("=" * 60)
    
    # 初始化服务（通常在应用启动时）
    service = MDHighlightService.from_config("config_example.yaml")
    
    # API 请求模拟
    api_request = {
        "task_id": "513f81dc-4fca-42b3-a4a9-0d58d99db2d2",
        # 或者使用 "md_text": "...",
        "output_filename": "api_result.pdf",
        "custom_prompt": None,  # 可选，覆盖默认提示词
        "custom_title": "我的分析报告"  # 可选
    }
    
    # 处理请求
    result = service.process(
        task_id=api_request["task_id"],
        output_filename=api_request["output_filename"],
        custom_title=api_request["custom_title"]
    )
    
    # 返回 API 响应
    api_response = {
        "success": result.success,
        "output_path": str(result.output_path) if result.output_path else None,
        "extraction_count": result.extraction_count,
        "highlight_count": result.highlight_count,
        "message": result.message,
        "details": result.details
    }
    
    print(f"API 响应: {api_response}")


def main():
    """运行所有示例"""
    print("\n" + "=" * 70)
    print("MD 高亮渲染服务 - 使用示例")
    print("=" * 70)
    
    # 选择要运行的示例
    demos = [
        # ("基本使用", demo_basic_usage),
        # ("自定义配置", demo_custom_config_code),
        ("导出配置文件", demo_config_file),
        # ("文本模式", demo_text_mode),
        # ("覆盖提示词", demo_override_prompt),
        # ("API 风格", demo_api_api_style),
    ]
    
    for name, demo_func in demos:
        try:
            demo_func()
        except Exception as e:
            print(f"❌ {name} 失败: {e}")
    
    print("\n" + "=" * 70)
    print("提示: 取消注释 demos 列表中的行来运行其他示例")
    print("=" * 70)


if __name__ == "__main__":
    main()
