"""
DOM-Tracking + LangExtract 集成测试（支持 YAML 配置）

使用方法:
    # 使用默认测试数据
    python dom_tracking_langextract_test.py
    
    # 使用 YAML 配置文件（与主程序同款格式）
    python dom_tracking_langextract_test.py -c services/profiles/example_profile.yaml --md-file test.md
    
    # 直接输入 Markdown 文本
    python dom_tracking_langextract_test.py -c example_profile.yaml --text "你的 Markdown"
    
    # 输出 HTML 到文件
    python dom_tracking_langextract_test.py -c example_profile.yaml --md-file test.md --output-html result.html
"""

import os
import sys
import json
import argparse
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from dotenv import load_dotenv

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import langextract as lx
from langextract.data import Extraction, ExampleData
from langextract.factory import ModelConfig
from langextract.providers.openai import OpenAILanguageModel 
from langextract import visualize
from bs4 import BeautifulSoup
import markdown
import yaml

# 从生产代码导入 DOM-Tracking 相关类
from services.utils.renderer import HighlightEntity, DOMTracker, DOMTrackingRenderer

# 加载环境变量
_ENV_PATH = Path(__file__).parent.parent / ".env"
if _ENV_PATH.exists():
    load_dotenv(_ENV_PATH)
else:
    load_dotenv()


def load_config_from_yaml(config_path: str) -> dict:
    """从 YAML 加载配置（兼容主程序格式）"""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config


def parse_examples_from_config(config: dict) -> List[ExampleData]:
    """从配置解析 examples"""
    examples = []
    
    # 支持两种配置结构:
    # 1. 扁平结构（example_profile.yaml）
    # 2. highlight_config 嵌套结构（omdia_smartphone_report.yaml）
    
    raw_examples = None
    if 'examples' in config:
        raw_examples = config['examples']
    elif 'highlight_config' in config and 'examples' in config['highlight_config']:
        raw_examples = config['highlight_config']['examples']
    
    if not raw_examples:
        return []
    
    for ex in raw_examples:
        text = ex.get('text', '')
        extractions = []
        
        for ext in ex.get('extractions', []):
            extraction_class = ext.get('class') or ext.get('extraction_class')
            extraction_text = ext.get('text') or ext.get('extraction_text')
            if extraction_class and extraction_text:
                extractions.append(Extraction(
                    extraction_class=extraction_class,
                    extraction_text=extraction_text
                ))
        
        if text and extractions:
            examples.append(ExampleData(text=text, extractions=extractions))
    
    return examples


def parse_prompt_from_config(config: dict) -> str:
    """从配置解析 prompt"""
    if 'extraction_prompt' in config:
        return config['extraction_prompt']
    elif 'highlight_config' in config and 'extraction_prompt' in config['highlight_config']:
        return config['highlight_config']['extraction_prompt']
    return ""


def parse_model_config_from_config(config: dict) -> ModelConfig:
    """从配置解析模型配置"""
    model_cfg = {}
    
    if 'model_config' in config:
        model_cfg = config['model_config']
    elif 'highlight_config' in config and 'model_config' in config['highlight_config']:
        model_cfg = config['highlight_config']['model_config']
    
    # 获取 API 配置
    api_key = os.getenv(model_cfg.get('api_key_env', 'DS_API_KEY'))
    base_url = os.getenv(model_cfg.get('base_url_env', 'DS_API_BASE_URL'))
    
    # 构建 provider_kwargs
    provider_kwargs = model_cfg.get('provider_kwargs', {})
    provider_kwargs['api_key'] = api_key
    provider_kwargs['base_url'] = base_url
    
    return ModelConfig(
        model_id=model_cfg.get('model_id', 'deepseek-chat'),
        provider=model_cfg.get('provider', 'OpenAILanguageModel'),
        provider_kwargs=provider_kwargs
    )


def parse_colors_from_config(config: dict) -> Dict[str, str]:
    """从配置解析颜色"""
    colors = {}
    
    color_list = None
    if 'category_colors' in config:
        color_list = config['category_colors']
    elif 'highlight_config' in config and 'category_colors' in config['highlight_config']:
        color_list = config['highlight_config']['category_colors']
    
    if color_list:
        for item in color_list:
            name = item.get('name') or item.get('category')
            color = item.get('color')
            if name and color:
                colors[name] = color
    
    return colors


def run_langextract(plain_text: str, prompt: str, examples: List[ExampleData], 
                    model_config: ModelConfig) -> lx.data.AnnotatedDocument:
    """调用 LangExtract，返回完整结果对象（用于后续 JSON/HTML 导出）"""
    result = lx.extract(
        examples=examples,
        text_or_documents=plain_text,
        prompt_description=prompt,
        config=model_config
    )
    return result


def convert_to_entities(extractions: List[Extraction], colors: Dict[str, str]) -> List[HighlightEntity]:
    """将 LangExtract 结果转换为 HighlightEntity"""
    entities = []
    
    for ext in extractions:
        char_start = None
        char_end = None
        alignment = None
        
        # 提取 char_interval
        if hasattr(ext, 'char_interval') and ext.char_interval:
            char_start = ext.char_interval.start_pos
            char_end = ext.char_interval.end_pos
        
        # 提取对齐状态
        if hasattr(ext, 'alignment'):
            alignment = str(ext.alignment)
        
        entities.append(HighlightEntity(
            text=ext.extraction_text,
            category=ext.extraction_class,
            color=colors.get(ext.extraction_class),
            char_start=char_start,
            char_end=char_end,
            alignment_status=alignment
        ))
    
    return entities


def export_extraction_jsonl(result: lx.data.AnnotatedDocument, output_dir: str, output_name: str = "extractions"):
    """导出 LangExtract 原始结果为 JSONL"""
    try:
        output_file_name = output_name if output_name.endswith(".jsonl") else f"{output_name}.jsonl"
        lx.io.save_annotated_documents(
            annotated_documents=iter([result]),
            output_name=output_file_name,
            output_dir=output_dir
        )
        print(f"  ✅ JSONL 已导出: {Path(output_dir) / output_file_name}")
    except Exception as e:
        print(f"  ❌ JSONL 导出失败: {e}")


def export_langextract_html(result: lx.data.AnnotatedDocument, output_path: str):
    """使用 LangExtract 内置 visualize 生成官方 HTML 可视化"""
    try:
        html = visualize(result)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"  ✅ LangExtract HTML 可视化已导出: {output_path}")
    except Exception as e:
        print(f"  ❌ HTML 导出失败: {e}")


def print_extraction_results(entities: List[HighlightEntity]):
    """打印提取结果"""
    print("\n" + "=" * 70)
    print("提取结果详情")
    print("=" * 70)
    
    has_position = sum(1 for e in entities if e.char_start is not None)
    no_position = len(entities) - has_position
    
    print(f"\n总计: {len(entities)} 个实体")
    print(f"  有位置信息: {has_position}")
    print(f"  无位置信息: {no_position}")
    
    print("\n实体列表:")
    for i, e in enumerate(entities, 1):
        pos_info = f"[{e.char_start}:{e.char_end}]" if e.char_start is not None else "[无位置]"
        align_info = f" ({e.alignment_status})" if e.alignment_status else ""
        print(f"  {i}. [{e.category}] '{e.text}' {pos_info}{align_info}")


def main():
    parser = argparse.ArgumentParser(description="DOM-Tracking + LangExtract 集成测试（YAML 配置）")
    parser.add_argument("-c", "--config", help="YAML 配置文件路径（与主程序同款格式）")
    parser.add_argument("--md-file", help="Markdown 文件路径")
    parser.add_argument("--text", help="直接输入 Markdown 文本")
    parser.add_argument("--output-html", help="输出 DOM-Tracking 高亮后的 HTML 文件路径")
    parser.add_argument("--output-pdf", help="输出 PDF 文件路径（需要 WeasyPrint）")
    parser.add_argument("--output-json", help="输出 LangExtract 原始 JSON 文件路径")
    parser.add_argument("--output-lx-html", help="输出 LangExtract 官方 HTML 可视化文件路径")
    
    args = parser.parse_args()
    
    # 加载配置
    config = {}
    if args.config:
        print(f"📄 加载配置: {args.config}")
        config = load_config_from_yaml(args.config)
    
    # 获取输入 Markdown
    if args.md_file:
        with open(args.md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
        print(f"📄 加载 Markdown: {args.md_file} ({len(md_content)} 字符)")
    elif args.text:
        md_content = args.text
        print(f"📝 使用命令行输入文本 ({len(md_content)} 字符)")
    else:
        # 默认测试数据
        md_content = """### 智能手机市场分析

根据最新财报，**苹果**公司本季度的表现极其强劲。

| 品牌 | 出货量 | 市场份额 |
|---|---|---|
| 苹果 | 240.6 百万部 | 20.1% |
| 三星 | 226.6 百万部 | 19.4% |

总结：苹果和三星主导了市场。
"""
        print("📝 使用默认测试数据")
    
    print("\n" + "=" * 70)
    print("DOM-Tracking + LangExtract 集成测试")
    print("=" * 70)
    
    # 解析配置
    examples = parse_examples_from_config(config)
    prompt = parse_prompt_from_config(config)
    colors = parse_colors_from_config(config)
    
    # 如果没有配置文件，使用默认值
    if not examples:
        print("⚠️ 未找到 examples，使用默认示例")
        examples = [
            lx.data.ExampleData(
                text="Top 5 Companies, Worldwide Smartphone Shipments\n1. Apple 81.3 24.2%",
                extractions=[
                    lx.data.Extraction(extraction_class="report_title", extraction_text="Top 5 Companies, Worldwide Smartphone Shipments"),
                    lx.data.Extraction(extraction_class="company_name", extraction_text="Apple"),
                    lx.data.Extraction(extraction_class="shipment_value", extraction_text="81.3"),
                ]
            )
        ]
    
    if not prompt:
        print("⚠️ 未找到 extraction_prompt，使用默认提示词")
        prompt = """从智能手机市场报告中提取以下信息：

1. report_title: 报告标题
2. company_name: 公司名称（如 Apple, Samsung, 苹果, 三星 等）
3. shipment_value: 出货量数值（如 240.6）

提取规则：
- 使用原文中的精确文本
- 每个数值单独提取
"""
    
    if not colors:
        colors = DOMTrackingHighlighter.DEFAULT_COLORS
    
    print(f"\n配置摘要:")
    print(f"  Examples: {len(examples)} 个")
    print(f"  Prompt: {len(prompt)} 字符")
    print(f"  Colors: {len(colors)} 个分类")
    
    # Step 1: 构建 DOM 追踪
    print("\n" + "-" * 70)
    print("Step 1: 构建 DOM 追踪映射")
    print("-" * 70)
    
    tracker = DOMTracker(md_content)
    plain_text = tracker.get_plain_text()
    
    print(f"  Markdown 长度: {len(md_content)} 字符")
    print(f"  纯文本长度: {len(plain_text)} 字符")
    print(f"  纯文本: {plain_text}")
    print(f"  文本节点数: {len(tracker.node_mappings)}")
    print(f"  Token 减少: ~{len(md_content) - len(plain_text)} 字符 ({(1 - len(plain_text)/len(md_content))*100:.1f}%)")
    
    # Step 2: LangExtract 提取
    print("\n" + "-" * 70)
    print("Step 2: LangExtract 提取")
    print("-" * 70)
    
    model_config = parse_model_config_from_config(config)
    print(f"  模型: {model_config.model_id}")
    print(f"  Provider: {model_config.provider}")
    
    start_time = time.time()
    try:
        lx_result = run_langextract(plain_text, prompt, examples, model_config)
        extractions = lx_result.extractions
        extract_time = time.time() - start_time
        print(f"  ✅ 提取成功，耗时: {extract_time:.2f}s")
        print(f"  提取实体数: {len(extractions)}")
    except Exception as e:
        print(f"  ❌ 提取失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 3: 导出原始结果（JSON + LangExtract HTML）
    if args.output_json:
        output_dir = str(Path(args.output_json).parent) if Path(args.output_json).parent.exists() else "."
        output_name = Path(args.output_json).stem
        export_extraction_jsonl(lx_result, output_dir, output_name)
    
    if args.output_lx_html:
        export_langextract_html(lx_result, args.output_lx_html)
    
    # Step 4: 转换为实体并打印
    entities = convert_to_entities(extractions, colors)
    print_extraction_results(entities)
    
    # Step 5: DOM-Tracking 高亮
    print("\n" + "-" * 70)
    print("Step 4: DOM-Tracking 高亮")
    print("-" * 70)
    
    renderer = DOMTrackingRenderer(colors=colors)
    highlighted_html, _, stats = renderer.highlight(tracker, entities)
    
    print(f"  高亮统计:")
    print(f"    成功: {stats['success']}")
    print(f"    失败: {stats['fail']}")
    print(f"    跨节点: {stats['cross_node']}")
    print(f"    无位置信息: {stats['no_position']}")
    
    # Step 6: 输出结果
    if args.output_html:
        # 包装成完整 HTML
        full_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>DOM-Tracking 高亮结果</title>
    <style>
        body {{
            font-family: "Microsoft YaHei", "SimSun", sans-serif;
            max-width: 900px;
            margin: 40px auto;
            padding: 20px;
            line-height: 1.6;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #f5f5f5;
        }}
    </style>
</head>
<body>
    {highlighted_html}
</body>
</html>"""
        with open(args.output_html, 'w', encoding='utf-8') as f:
            f.write(full_html)
        print(f"\n  ✅ HTML 已保存: {args.output_html}")
    
    # Step 7: 生成 PDF（如果需要）
    if args.output_pdf:
        try:
            from weasyprint import HTML, CSS
            
            css_style = """
            @page { size: A4; margin: 2cm; }
            body { font-family: "Microsoft YaHei", "SimSun", sans-serif; line-height: 1.6; }
            table { border-collapse: collapse; width: 100%; margin: 15px 0; }
            th, td { border: 1px solid #ddd; padding: 6px 13px; }
            th { background-color: #f5f5f5; }
            """
            
            for category, color in colors.items():
                css_style += f"""
            mark.highlight-{category} {{
                background-color: {color};
                padding: 2px 4px;
                border-radius: 2px;
            }}
                """
            
            full_html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head><body>{highlighted_html}</body></html>"""
            
            HTML(string=full_html, base_url=".").write_pdf(
                args.output_pdf,
                stylesheets=[CSS(string=css_style)]
            )
            print(f"  ✅ PDF 已保存: {args.output_pdf}")
        except Exception as e:
            print(f"  ❌ PDF 生成失败: {e}")
    
    # 打印对比信息
    if args.output_html or args.output_lx_html:
        print("\n" + "=" * 70)
        print("输出文件对比")
        print("=" * 70)
        if args.output_html:
            print(f"  DOM-Tracking 高亮 HTML : {args.output_html}")
        if args.output_lx_html:
            print(f"  LangExtract 官方 HTML  : {args.output_lx_html}")
        if args.output_json:
            print(f"  LangExtract 原始 JSON  : {args.output_json}")
        print("\n  💡 提示: 同时打开两个 HTML 文件，可直观对比 DOM-Tracking 与 LangExtract 原生高亮差异")
    
    # 打印 HTML 片段
    if not args.output_html:
        print("\n" + "=" * 70)
        print("高亮后 HTML（片段）:")
        print("=" * 70)
        soup = BeautifulSoup(highlighted_html, 'html.parser')
        print(soup.prettify()[:2000])
        if len(str(soup)) > 2000:
            print("...")
    
    print("\n" + "=" * 70)
    print("测试完成")
    print("=" * 70)


if __name__ == "__main__":
    main()
