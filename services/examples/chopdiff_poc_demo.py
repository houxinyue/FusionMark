"""
Chopdiff 坐标映射验证 Demo
============================

验证目标：
1. 将 Markdown 转换为纯文本（Token 更少，LangExtract 更快）
2. 使用 chopdiff 建立 Markdown ↔ 纯文本 双向坐标映射
3. 将 LangExtract 返回的纯文本坐标精确映射回 Markdown 坐标
4. 验证高亮位置的准确性

使用方式:
    cd services
    python examples/chopdiff_poc_demo.py

输出:
    - 验证报告 (控制台)
    - 对比结果文件 (chopdiff_output/)
"""

import os
import sys
import re
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 导入现有服务（用于对比）
from core.highlight import MDHighlightService, MDHighlightConfig
from utils.renderer import MDRenderer, HighlightEntity

# 尝试导入 chopdiff
try:
    from chopdiff.docs import TextDoc
    from chopdiff.transforms import filtered_transform
    from chopdiff.docs.token_mapping import TokenMapping
    CHOPDIFF_AVAILABLE = True
except ImportError:
    CHOPDIFF_AVAILABLE = False
    print("⚠️  chopdiff 未安装，请先运行: pip install chopdiff")
    print("    或使用: uv add chopdiff")
    sys.exit(1)


# ============== 测试数据 ==============

TEST_MD_CONTENT = """# 2024年全球智能手机市场报告

## 市场概况

根据 **IDC** 最新发布的季度追踪数据，2024年第一季度全球智能手机出货量达到 **2.894亿部**，同比增长 **7.8%**。

### 主要厂商表现

| 排名 | 公司 | 出货量(百万部) | 市场份额 | 同比增长 |
|------|------|---------------|----------|----------|
| 1 | **Apple** | 81.3 | 24.2% | +4.9% |
| 2 | **Samsung** | 61.2 | 18.2% | +18.3% |
| 3 | **Xiaomi** | 37.8 | 11.2% | -11.4% |
| 4 | **OPPO** | 25.6 | 8.8% | -8.5% |
| 5 | **vivo** | 23.1 | 8.0% | +3.2% |

## 关键洞察

> Apple 凭借 iPhone 15 系列的强劲表现，以 **24.2%** 的市场份额重夺第一。

主要发现：
- Samsung 出货量达到 **61.2百万部**，虽然排名下滑至第二，但同比增长 **18.3%**
- Xiaomi 遭遇挑战，出货量下降至 **37.8百万部**，同比下降 **-11.4%**
- 市场整体呈现复苏态势，总出货量 **2.894亿部** 创近两年新高

*数据来源: IDC Quarterly Mobile Phone Tracker, January 2024*
"""


# ============== 配置 ==============

@dataclass
class ExtractionPrompt:
    """提取提示词配置"""
    prompt: str = """从智能手机市场报告中提取以下信息：

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
"""

    examples: List[Dict] = field(default_factory=lambda: [
        {
            "text": """Top 5 Companies, Worldwide Smartphone Shipments
                1. Apple 81.3 24.2% 77.5 23.6% 4.9%
                2. Samsung 61.2 18.2% 51.7 15.7% 18.3%
                3. Xiaomi 37.8 11.2% 42.7 13.0% -11.4%
                Source: IDC Quarterly Mobile Phone Tracker""",
            "extractions": [
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
        }
    ])


# ============== Chopdiff 坐标映射器 ==============

class ChopdiffOffsetMapper:
    """
    基于 chopdiff 的 Markdown ↔ 纯文本 双向坐标映射器
    
    核心功能:
    1. 将 Markdown 转换为纯文本（去除标记，保留语义）
    2. 建立字符级坐标映射
    3. 将纯文本坐标映射回 Markdown 坐标
    """
    
    def __init__(self, original_md: str):
        """
        初始化映射器
        
        :param original_md: 原始 Markdown 文本
        """
        self.original_md = original_md
        self.md_doc = TextDoc.from_text(original_md)
        
        # 生成纯文本（保留段落结构，去除格式标记）
        self.plain_text = self._md_to_plain_text(original_md)
        self.plain_doc = TextDoc.from_text(self.plain_text)
        
        # 构建 token 映射（核心）
        self.mapping = self._build_mapping()
        
        # 统计信息
        self.stats = {
            "md_length": len(original_md),
            "plain_length": len(self.plain_text),
            "reduction": len(original_md) - len(self.plain_text),
            "reduction_pct": (len(original_md) - len(self.plain_text)) / len(original_md) * 100 if original_md else 0
        }
    
    def _md_to_plain_text(self, md: str) -> str:
        """
        将 Markdown 转换为纯文本
        
        策略:
        1. 保留所有实际文本内容
        2. 去除格式标记 (#, **, *, `, 等)
        3. 保留表格结构（转换为文本表示）
        4. 保留段落分隔
        """
        text = md
        
        # 1. 代码块 -> 保留内容但去除 ```
        text = re.sub(r'```[\s\S]*?```', lambda m: m.group().strip('`').strip(), text)
        
        # 2. 行内代码 -> 保留内容
        text = re.sub(r'`([^`]+)`', r'\1', text)
        
        # 3. 标题标记 -> 去除 # 但保留换行结构
        text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
        
        # 4. 加粗/斜体标记
        text = re.sub(r'\*\*\*|___', '', text)  # 粗斜体
        text = re.sub(r'\*\*|__', '', text)     # 粗体
        text = re.sub(r'\*|_', '', text)        # 斜体
        
        # 5. 链接 -> 保留文本，去除 URL
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        
        # 6. 图片 -> 保留 alt 文本
        text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'\1', text)
        
        # 7. 引用标记 >
        text = re.sub(r'^>\s?', '', text, flags=re.MULTILINE)
        
        # 8. 列表标记
        text = re.sub(r'^[\s]*[-*+]\s', '', text, flags=re.MULTILINE)
        text = re.sub(r'^[\s]*\d+\.\s', '', text, flags=re.MULTILINE)
        
        # 9. 表格分隔线 |---|---|
        text = re.sub(r'\|[-:\s|]+\|', '', text)
        text = re.sub(r'\|', ' ', text)  # 表格单元格分隔符 -> 空格
        
        # 10. HTML 标签
        text = re.sub(r'<[^>]+>', '', text)
        
        # 11. 多余空行规范化
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    def _build_mapping(self) -> TokenMapping:
        """
        构建 Markdown 和纯文本之间的 token 映射
        
        使用 chopdiff 的 TokenMapping 功能建立双向映射
        """
        # chopdiff 会自动处理两个文档之间的对应关系
        return self.md_doc.get_token_mapping(self.plain_doc)
    
    def get_plain_text(self) -> str:
        """获取转换后的纯文本（用于 LangExtract 输入）"""
        return self.plain_text
    
    def map_to_markdown(self, plain_start: int, plain_end: int) -> Tuple[int, int]:
        """
        将纯文本坐标映射回 Markdown 坐标
        
        :param plain_start: 纯文本中的起始位置
        :param plain_end: 纯文本中的结束位置
        :return: (md_start, md_end) Markdown 中的坐标
        """
        try:
            # 使用 chopdiff 的映射功能
            md_start = self.mapping.map_offset(plain_start, "md")
            md_end = self.mapping.map_offset(plain_end, "md")
            return (md_start, md_end)
        except Exception as e:
            # 如果映射失败，返回原始坐标（降级）
            print(f"    ⚠️  坐标映射失败: {e}, 使用原始坐标")
            return (plain_start, plain_end)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取转换统计信息"""
        return self.stats
    
    def visualize_mapping(self, max_chars: int = 200) -> str:
        """
        可视化坐标映射（用于调试）
        
        :param max_chars: 最大显示字符数
        :return: 可视化字符串
        """
        md_preview = self.original_md[:max_chars].replace('\n', '↵')
        plain_preview = self.plain_text[:max_chars].replace('\n', '↵')
        
        return f"""
=== 坐标映射可视化 (前 {max_chars} 字符) ===

[Markdown 原文]
{md_preview}

[纯文本转换]
{plain_preview}

[统计]
- Markdown 长度: {self.stats['md_length']}
- 纯文本长度: {self.stats['plain_length']}
- 减少字符: {self.stats['reduction']} ({self.stats['reduction_pct']:.1f}%)
"""


# ============== 模拟 LangExtract 提取结果 ==============

class MockLangExtractResult:
    """
    模拟 LangExtract 提取结果
    
    为了验证坐标映射的准确性，我们使用预设的提取结果
    这些结果包含纯文本坐标 (char_interval)
    """
    
    @staticmethod
    def extract_from_plain_text(plain_text: str) -> List[Dict]:
        """
        从纯文本中提取实体（模拟 LangExtract）
        
        返回包含 char_interval 的提取结果
        """
        # 预定义的关键实体及其在纯文本中的预期位置
        # 注意：这些位置需要根据实际纯文本来计算
        entities = []
        
        # 定义要查找的模式
        patterns = [
            ("report_title", "2024年全球智能手机市场报告"),
            ("company_name", "Apple"),
            ("shipment_value", "81.3"),
            ("market_share", "24.2%"),
            ("yoy_change", "4.9%"),
            ("company_name", "Samsung"),
            ("shipment_value", "61.2"),
            ("yoy_change", "18.3%"),
            ("company_name", "Xiaomi"),
            ("shipment_value", "37.8"),
            ("negative_change", "-11.4%"),
            ("data_source", "IDC Quarterly Mobile Phone Tracker"),
        ]
        
        for category, text in patterns:
            # 在纯文本中查找位置
            idx = plain_text.find(text)
            if idx != -1:
                entities.append({
                    "class": category,
                    "text": text,
                    "char_interval": {"start_pos": idx, "end_pos": idx + len(text)}
                })
            else:
                # 模糊匹配（处理格式差异）
                # 例如 "-11.4%" 可能在文本中是 "-11.4%" 或 "(11.4%)" 等
                fuzzy_match = MockLangExtractResult._fuzzy_find(plain_text, text)
                if fuzzy_match:
                    entities.append({
                        "class": category,
                        "text": text,
                        "char_interval": {"start_pos": fuzzy_match[0], "end_pos": fuzzy_match[1]}
                    })
        
        return entities
    
    @staticmethod
    def _fuzzy_find(text: str, pattern: str) -> Optional[Tuple[int, int]]:
        """模糊查找（处理格式差异）"""
        # 去除空格后的匹配
        normalized_text = text.replace(' ', '').replace('\n', '')
        normalized_pattern = pattern.replace(' ', '').replace('\n', '')
        
        idx = normalized_text.find(normalized_pattern)
        if idx != -1:
            # 需要映射回原始坐标（简化处理）
            # 实际实现需要更复杂的映射
            return None  # 暂时返回 None
        return None


# ============== 高亮对比实验 ==============

class HighlightComparisonExperiment:
    """
    高亮对比实验
    
    对比三种方案的准确性:
    1. 现有方案: 直接在 Markdown 中字符串搜索高亮
    2. Chopdiff 方案: 纯文本提取 + 坐标映射高亮
    3. 理想方案: 直接字符级坐标插入
    """
    
    def __init__(self, output_dir: str = "chopdiff_output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # 颜色配置
        self.colors = {
            "report_title": "#e67e22",
            "company_name": "#2ecc71",
            "shipment_value": "#3498db",
            "market_share": "#9b59b6",
            "yoy_change": "#e84393",
            "negative_change": "#e74c3c",
            "data_source": "#95a5a6",
        }
    
    def run_experiment(self, md_content: str) -> Dict[str, Any]:
        """
        运行对比实验
        
        :param md_content: 原始 Markdown 内容
        :return: 实验结果
        """
        print("\n" + "=" * 70)
        print("Chopdiff 坐标映射验证实验")
        print("=" * 70)
        
        results = {
            "original_md_length": len(md_content),
            "steps": []
        }
        
        # ===== Step 1: 创建 Chopdiff 映射器 =====
        print("\n📋 Step 1: 创建 Markdown ↔ 纯文本 映射器")
        print("-" * 60)
        
        mapper = ChopdiffOffsetMapper(md_content)
        stats = mapper.get_stats()
        
        print(f"✅ 映射器创建成功")
        print(f"   Markdown 长度: {stats['md_length']}")
        print(f"   纯文本长度: {stats['plain_length']}")
        print(f"   Token 节省: {stats['reduction']} 字符 ({stats['reduction_pct']:.1f}%)")
        
        results["steps"].append({
            "name": "创建映射器",
            "stats": stats
        })
        
        # 显示映射可视化
        print(mapper.visualize_mapping(max_chars=150))
        
        # ===== Step 2: 模拟 LangExtract 提取 =====
        print("\n📋 Step 2: 模拟 LangExtract 信息提取")
        print("-" * 60)
        
        plain_text = mapper.get_plain_text()
        mock_results = MockLangExtractResult.extract_from_plain_text(plain_text)
        
        print(f"✅ 从纯文本提取到 {len(mock_results)} 个实体")
        print("\n   提取结果（纯文本坐标）:")
        for i, entity in enumerate(mock_results, 1):
            interval = entity["char_interval"]
            print(f"   {i}. [{entity['class']}] '{entity['text']}' @ [{interval['start_pos']}-{interval['end_pos']}]")
        
        results["steps"].append({
            "name": "LangExtract 提取",
            "entity_count": len(mock_results),
            "entities": mock_results
        })
        
        # ===== Step 3: 坐标映射 =====
        print("\n📋 Step 3: 纯文本坐标 → Markdown 坐标映射")
        print("-" * 60)
        
        mapped_entities = []
        for entity in mock_results:
            plain_start = entity["char_interval"]["start_pos"]
            plain_end = entity["char_interval"]["end_pos"]
            
            # 使用 chopdiff 映射
            md_start, md_end = mapper.map_to_markdown(plain_start, plain_end)
            
            # 验证映射结果
            expected_text = entity["text"]
            actual_text = md_content[md_start:md_end]
            
            mapped_entity = {
                "class": entity["class"],
                "text": expected_text,
                "plain_interval": (plain_start, plain_end),
                "md_interval": (md_start, md_end),
                "mapped_text": actual_text,
                "match": expected_text == actual_text
            }
            mapped_entities.append(mapped_entity)
            
            match_symbol = "✅" if mapped_entity["match"] else "❌"
            print(f"   {match_symbol} [{entity['class']}] '{expected_text}'")
            print(f"      纯文本: [{plain_start:4d}-{plain_end:4d}] → Markdown: [{md_start:4d}-{md_end:4d}]")
            if not mapped_entity["match"]:
                print(f"      ⚠️  文本不匹配: 期望 '{expected_text}', 实际 '{actual_text}'")
        
        results["steps"].append({
            "name": "坐标映射",
            "mapped_entities": mapped_entities
        })
        
        # ===== Step 4: 高亮效果对比 =====
        print("\n📋 Step 4: 高亮效果验证")
        print("-" * 60)
        
        # 统计映射准确性
        accurate_count = sum(1 for e in mapped_entities if e["match"])
        accuracy = accurate_count / len(mapped_entities) * 100 if mapped_entities else 0
        
        print(f"   映射准确率: {accurate_count}/{len(mapped_entities)} ({accuracy:.1f}%)")
        
        # 保存详细报告
        report_path = self._save_report(md_content, plain_text, mapped_entities, stats)
        print(f"\n📁 详细报告已保存: {report_path}")
        
        results["accuracy"] = accuracy
        results["report_path"] = str(report_path)
        
        # ===== Step 5: Token 节省分析 =====
        print("\n📋 Step 5: Token 节省分析")
        print("-" * 60)
        
        # 估算 Token 数量（简化计算：中文 ≈ 1.5 tokens/字，英文 ≈ 0.25 tokens/char）
        def estimate_tokens(text: str) -> float:
            """粗略估算 token 数量"""
            chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
            other_chars = len(text) - chinese_chars
            return chinese_chars * 1.5 + other_chars * 0.25
        
        md_tokens = estimate_tokens(md_content)
        plain_tokens = estimate_tokens(plain_text)
        token_saving = md_tokens - plain_tokens
        token_saving_pct = token_saving / md_tokens * 100 if md_tokens else 0
        
        print(f"   Markdown Token 估算: {md_tokens:.0f}")
        print(f"   纯文本 Token 估算: {plain_tokens:.0f}")
        print(f"   Token 节省: {token_saving:.0f} ({token_saving_pct:.1f}%)")
        
        results["token_analysis"] = {
            "md_tokens": md_tokens,
            "plain_tokens": plain_tokens,
            "saving": token_saving,
            "saving_pct": token_saving_pct
        }
        
        return results
    
    def _save_report(self, md_content: str, plain_text: str, 
                     mapped_entities: List[Dict], stats: Dict) -> Path:
        """保存详细验证报告"""
        report_path = self.output_dir / "chopdiff_verification_report.md"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# Chopdiff 坐标映射验证报告\n\n")
            
            f.write("## 1. 基本信息\n\n")
            f.write(f"- Markdown 长度: {stats['md_length']} 字符\n")
            f.write(f"- 纯文本长度: {stats['plain_length']} 字符\n")
            f.write(f"- 字符减少: {stats['reduction']} ({stats['reduction_pct']:.1f}%)\n\n")
            
            f.write("## 2. 坐标映射验证\n\n")
            f.write("| 类别 | 实体文本 | 纯文本坐标 | Markdown坐标 | 映射结果 |\n")
            f.write("|------|----------|-----------|-------------|----------|\n")
            
            for entity in mapped_entities:
                match_str = "✅ 匹配" if entity["match"] else "❌ 不匹配"
                f.write(f"| {entity['class']} | `{entity['text']}` | "
                       f"{entity['plain_interval']} | {entity['md_interval']} | {match_str} |\n")
            
            f.write("\n## 3. 原始 Markdown\n\n")
            f.write("```markdown\n")
            f.write(md_content)
            f.write("\n```\n\n")
            
            f.write("## 4. 纯文本转换\n\n")
            f.write("```text\n")
            f.write(plain_text)
            f.write("\n```\n\n")
        
        return report_path


# ============== 主入口 ==============

def main():
    """主入口函数"""
    
    # 检查 chopdiff 是否可用
    if not CHOPDIFF_AVAILABLE:
        print("❌ chopdiff 未安装，无法运行验证")
        print("\n安装方式:")
        print("  pip install chopdiff")
        print("  # 或")
        print("  uv add chopdiff")
        return 1
    
    # 运行实验
    experiment = HighlightComparisonExperiment()
    results = experiment.run_experiment(TEST_MD_CONTENT)
    
    # 打印最终总结
    print("\n" + "=" * 70)
    print("验证实验总结")
    print("=" * 70)
    
    accuracy = results.get("accuracy", 0)
    token_saving = results.get("token_analysis", {}).get("saving_pct", 0)
    
    if accuracy >= 95:
        verdict = "✅ 验证通过 - 坐标映射高度准确"
    elif accuracy >= 80:
        verdict = "⚠️  验证部分通过 - 需要进一步优化"
    else:
        verdict = "❌ 验证失败 - 需要重新设计映射方案"
    
    print(f"\n{verdict}")
    print(f"   映射准确率: {accuracy:.1f}%")
    print(f"   Token 节省: {token_saving:.1f}%")
    print(f"   报告文件: {results.get('report_path', 'N/A')}")
    
    print("\n" + "=" * 70)
    print("下一步建议:")
    print("=" * 70)
    
    if accuracy >= 95:
        print("""
1. ✅ 当前方案已经可以投入生产使用
2. 建议将 ChopdiffOffsetMapper 集成到现有 pipeline
3. 添加配置开关: enable_chopdiff_mapping: true/false
4. 实现降级机制: 映射失败时回退到字符串搜索
""")
    else:
        print("""
1. 需要优化纯文本转换逻辑，保留更多格式信息
2. 考虑使用 diff-match-patch 作为备选方案
3. 增加模糊匹配容错机制
4. 针对表格、代码块等特殊元素单独处理
""")
    
    return 0 if accuracy >= 80 else 1


if __name__ == "__main__":
    sys.exit(main())
