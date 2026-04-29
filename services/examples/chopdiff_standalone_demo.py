"""
Chopdiff 独立验证脚本（不依赖项目其他代码）
=============================================

这个脚本完全独立，只需要安装 chopdiff 即可运行：
    pip install chopdiff
    python chopdiff_standalone_test.py

功能:
1. 纯 Markdown → 纯文本 转换测试
2. 坐标映射准确性验证
3. Token 节省比例计算
4. 生成详细的映射报告

注意: chopdiff 的 TokenMapping 是基于 wordtoks（词级别token）的映射，
      不是字符级别映射，所以需要额外的坐标转换。
"""

import re
import json
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional

# 尝试导入 chopdiff
try:
    from chopdiff.docs import TextDoc
    from chopdiff.docs.token_mapping import TokenMapping
    from chopdiff.docs.token_diffs import diff_wordtoks
    CHOPDIFF_AVAILABLE = True
except ImportError:
    CHOPDIFF_AVAILABLE = False
    print("❌ 请先安装 chopdiff: pip install chopdiff")
    exit(1)


@dataclass
class TestCase:
    """测试用例"""
    name: str
    markdown: str
    expected_entities: List[Dict]  # 期望在纯文本中找到的实体


# ============== 测试数据 ==============

TEST_CASES = [
    TestCase(
        name="基础标题测试",
        markdown="""# 2024年市场报告

## 第一部分：市场概况

根据 **IDC** 的数据，Apple 出货量为 **81.3** 百万部。

Samsung 紧随其后，出货量达到 **61.2** 百万部。
""",
        expected_entities=[
            {"text": "2024年市场报告", "type": "title"},
            {"text": "IDC", "type": "source"},
            {"text": "Apple", "type": "company"},
            {"text": "81.3", "type": "number"},
            {"text": "Samsung", "type": "company"},
            {"text": "61.2", "type": "number"},
        ]
    ),
    
    TestCase(
        name="表格内容测试",
        markdown="""| 公司 | 份额 |
|------|------|
| **Apple** | 24.2% |
| **Samsung** | 18.2% |
| **Xiaomi** | 11.2% |

总市场规模达到 **2.894亿部**。
""",
        expected_entities=[
            {"text": "Apple", "type": "company"},
            {"text": "24.2%", "type": "percentage"},
            {"text": "Samsung", "type": "company"},
            {"text": "18.2%", "type": "percentage"},
            {"text": "Xiaomi", "type": "company"},
            {"text": "11.2%", "type": "percentage"},
            {"text": "2.894亿部", "type": "volume"},
        ]
    ),
    
    TestCase(
        name="复杂格式测试",
        markdown="""> 重要发现: Apple 在2024年Q1实现了 **4.9%** 的同比增长。
> 
> 数据来源: [IDC官网](https://idc.com)

关键数字:
- 出货量: **81.3** 百万部
- 市场份额: `24.2%`
- 增长率: ***+4.9%***

~~旧数据: 77.5 百万部~~ 已更新
""",
        expected_entities=[
            {"text": "Apple", "type": "company"},
            {"text": "4.9%", "type": "percentage"},
            {"text": "81.3", "type": "number"},
            {"text": "24.2%", "type": "percentage"},
            {"text": "+4.9%", "type": "percentage"},
        ]
    ),
]


class MarkdownToPlainConverter:
    """Markdown 转纯文本（保留语义，去除标记）"""
    
    def convert(self, md: str) -> str:
        text = md
        
        # 代码块
        text = re.sub(r'```[\s\S]*?```', lambda m: m.group().strip('`').strip(), text)
        # 行内代码
        text = re.sub(r'`([^`]+)`', r'\1', text)
        # 标题
        text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
        # 加粗/斜体
        text = re.sub(r'\*\*\*|___', '', text)
        text = re.sub(r'\*\*|__', '', text)
        text = re.sub(r'\*|_', '', text)
        # 链接
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        # 图片
        text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'\1', text)
        # 引用
        text = re.sub(r'^>\s?', '', text, flags=re.MULTILINE)
        # 列表
        text = re.sub(r'^[\s]*[-*+]\s', '', text, flags=re.MULTILINE)
        text = re.sub(r'^[\s]*\d+\.\s', '', text, flags=re.MULTILINE)
        # 删除线
        text = re.sub(r'~~([^~]+)~~', r'\1', text)
        # 表格分隔线
        text = re.sub(r'\|[-:\s|]+\|', '', text)
        text = re.sub(r'\|', ' ', text)
        # HTML
        text = re.sub(r'<[^>]+>', '', text)
        # 多余空行
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()


class CoordinateMapper:
    """
    基于 chopdiff 的坐标映射器
    
    注意：chopdiff 的 TokenMapping 是基于 wordtoks（词级别token）的，
    不是字符级别的。我们需要将字符坐标转换为 wordtok 坐标。
    """
    
    def __init__(self, markdown: str):
        self.markdown = markdown
        self.converter = MarkdownToPlainConverter()
        self.plain_text = self.converter.convert(markdown)
        
        # chopdiff 文档
        self.md_doc = TextDoc.from_text(markdown)
        self.plain_doc = TextDoc.from_text(self.plain_text)
        
        # 获取 wordtoks
        self.md_wordtoks = list(self.md_doc.as_wordtoks())
        self.plain_wordtoks = list(self.plain_doc.as_wordtoks())
        
        # 构建映射（wordtok 级别）
        self.mapping = None
        if len(self.md_wordtoks) >= 10 and len(self.plain_wordtoks) >= 10:
            try:
                self.mapping = TokenMapping(
                    self.md_wordtoks, 
                    self.plain_wordtoks,
                    min_tokens=10,  # 降低最小token要求
                    max_diff_frac=0.4  # 允许更多差异
                )
            except ValueError as e:
                print(f"    ⚠️  TokenMapping 创建失败: {e}")
        
        # 构建字符到 wordtok 的索引（用于快速查找）
        self._build_char_to_wordtok_index()
    
    def _build_char_to_wordtok_index(self):
        """构建字符位置到 wordtok 索引的映射"""
        # Markdown 的字符索引
        self.md_char_to_wordtok = []
        char_pos = 0
        for i, tok in enumerate(self.md_wordtoks):
            for _ in range(len(tok)):
                self.md_char_to_wordtok.append(i)
            char_pos += len(tok)
        
        # 纯文本的字符索引
        self.plain_char_to_wordtok = []
        char_pos = 0
        for i, tok in enumerate(self.plain_wordtoks):
            for _ in range(len(tok)):
                self.plain_char_to_wordtok.append(i)
            char_pos += len(tok)
    
    def map_to_markdown(self, plain_start: int, plain_end: int) -> Tuple[int, int]:
        """
        将纯文本字符坐标映射回 Markdown 字符坐标
        
        策略：
        1. 将纯文本字符坐标转换为 wordtok 索引
        2. 使用 TokenMapping 映射到 Markdown 的 wordtok 索引
        3. 将 Markdown wordtok 索引转换回字符坐标
        """
        if self.mapping is None:
            # 没有映射时，直接返回原始坐标（降级）
            return (plain_start, plain_end)
        
        try:
            # 字符坐标 -> wordtok 索引
            plain_start_tok = self.plain_char_to_wordtok[plain_start] if plain_start < len(self.plain_char_to_wordtok) else 0
            plain_end_tok = self.plain_char_to_wordtok[plain_end - 1] if plain_end <= len(self.plain_char_to_wordtok) else len(self.plain_wordtoks) - 1
            
            # wordtok 映射
            md_start_tok = self.mapping.map_back(plain_start_tok)
            md_end_tok = self.mapping.map_back(plain_end_tok)
            
            # wordtok 索引 -> 字符坐标
            md_start = sum(len(self.md_wordtoks[i]) for i in range(md_start_tok))
            md_end = sum(len(self.md_wordtoks[i]) for i in range(md_end_tok + 1))
            
            return (md_start, md_end)
        except (IndexError, KeyError) as e:
            # 映射失败时返回原始坐标
            return (plain_start, plain_end)
    
    def find_entity_in_plain(self, entity_text: str) -> Optional[Tuple[int, int]]:
        """在纯文本中查找实体位置"""
        idx = self.plain_text.find(entity_text)
        if idx != -1:
            return (idx, idx + len(entity_text))
        return None


def run_single_test(test_case: TestCase) -> Dict:
    """运行单个测试用例"""
    print(f"\n{'='*60}")
    print(f"测试: {test_case.name}")
    print('='*60)
    
    # 创建映射器
    mapper = CoordinateMapper(test_case.markdown)
    
    print(f"\n📄 文本转换:")
    print(f"   Markdown: {len(test_case.markdown)} 字符")
    print(f"   纯文本: {len(mapper.plain_text)} 字符")
    print(f"   减少: {len(test_case.markdown) - len(mapper.plain_text)} 字符")
    print(f"   MD wordtoks: {len(mapper.md_wordtoks)}")
    print(f"   Plain wordtoks: {len(mapper.plain_wordtoks)}")
    if mapper.mapping:
        print(f"   ✅ TokenMapping 创建成功")
    else:
        print(f"   ⚠️  TokenMapping 未创建（文档太短或差异太大）")
    
    print(f"\n📝 纯文本内容:")
    for i, line in enumerate(mapper.plain_text.split('\n')[:5], 1):
        print(f"   {i}: {line[:60]}{'...' if len(line) > 60 else ''}")
    
    # 验证每个实体
    results = []
    print(f"\n🔍 实体坐标映射验证:")
    
    for entity in test_case.expected_entities:
        entity_text = entity["text"]
        entity_type = entity["type"]
        
        # 在纯文本中查找
        plain_pos = mapper.find_entity_in_plain(entity_text)
        
        if plain_pos is None:
            results.append({
                "entity": entity_text,
                "type": entity_type,
                "found": False,
                "reason": "在纯文本中未找到"
            })
            print(f"   ❌ [{entity_type}] '{entity_text}' - 未找到")
            continue
        
        # 映射回 Markdown
        md_start, md_end = mapper.map_to_markdown(plain_pos[0], plain_pos[1])
        
        # 验证映射结果
        mapped_text = test_case.markdown[md_start:md_end]
        
        # 判断是否匹配（去除空白后比较）
        is_correct = (entity_text.strip() in mapped_text.strip()) or (mapped_text.strip() in entity_text.strip())
        
        results.append({
            "entity": entity_text,
            "type": entity_type,
            "found": True,
            "plain_pos": plain_pos,
            "md_pos": (md_start, md_end),
            "mapped_text": mapped_text,
            "correct": is_correct
        })
        
        status = "✅" if is_correct else "❌"
        print(f"   {status} [{entity_type}] '{entity_text}'")
        print(f"      纯文本@{plain_pos} → Markdown@{md_start}-{md_end}")
        if not is_correct:
            print(f"      ⚠️  实际提取: '{mapped_text}'")
    
    # 统计
    total = len(results)
    found = sum(1 for r in results if r.get("found", False))
    correct = sum(1 for r in results if r.get("correct", False))
    
    print(f"\n📊 测试结果:")
    print(f"   实体总数: {total}")
    print(f"   找到: {found} ({found/total*100:.0f}%)")
    print(f"   坐标正确: {correct} ({correct/total*100:.0f}%)")
    
    return {
        "test_name": test_case.name,
        "markdown_length": len(test_case.markdown),
        "plain_length": len(mapper.plain_text),
        "reduction": len(test_case.markdown) - len(mapper.plain_text),
        "entities": results,
        "accuracy": correct / total if total > 0 else 0
    }


def main():
    """主函数"""
    print("="*70)
    print("Chopdiff 坐标映射独立验证")
    print("="*70)
    print("\n这个测试验证以下能力:")
    print("1. Markdown → 纯文本 转换（Token 节省）")
    print("2. 纯文本坐标 → Markdown 坐标 映射准确性")
    print("3. 实体高亮位置的正确性")
    
    # 运行所有测试
    all_results = []
    for test_case in TEST_CASES:
        result = run_single_test(test_case)
        all_results.append(result)
    
    # 汇总报告
    print("\n" + "="*70)
    print("汇总报告")
    print("="*70)
    
    total_entities = sum(len(r["entities"]) for r in all_results)
    total_correct = sum(sum(1 for e in r["entities"] if e.get("correct", False)) for r in all_results)
    overall_accuracy = total_correct / total_entities if total_entities > 0 else 0
    
    print(f"\n📈 整体准确率: {total_correct}/{total_entities} ({overall_accuracy*100:.1f}%)")
    
    print(f"\n📋 各测试用例结果:")
    for r in all_results:
        accuracy = r["accuracy"] * 100
        status = "✅" if accuracy >= 90 else "⚠️" if accuracy >= 70 else "❌"
        print(f"   {status} {r['test_name']}: {accuracy:.0f}% | "
              f"Token 节省: {r['reduction']} 字符")
    
    # 保存详细报告
    output_dir = Path("chopdiff_output")
    output_dir.mkdir(exist_ok=True)
    
    report_file = output_dir / "standalone_test_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump({
            "summary": {
                "total_tests": len(all_results),
                "total_entities": total_entities,
                "total_correct": total_correct,
                "overall_accuracy": overall_accuracy
            },
            "details": all_results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n📁 详细报告已保存: {report_file}")
    
    # 最终结论
    print("\n" + "="*70)
    if overall_accuracy >= 0.9:
        print("✅ 验证结论: 坐标映射方案可行，建议投入生产使用")
    elif overall_accuracy >= 0.7:
        print("⚠️  验证结论: 坐标映射基本可用，需要优化边界情况")
    else:
        print("❌ 验证结论: 坐标映射准确率不足，建议使用备选方案")
    print("="*70)


if __name__ == "__main__":
    main()
