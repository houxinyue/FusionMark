"""
DOM-Tracking 方案验证 Demo

验证目标:
1. 纯文本预处理是否能减少 Token 并提升 LangExtract 速度
2. 基于位置的高亮是否能避免伪阳性问题
3. 节点级映射的准确性和鲁棒性

对比:
- 当前方案: 正则全局匹配，容易跨节点误匹配
- DOM-Tracking: 基于 char_interval 精准定位到具体节点
"""

import markdown
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from bs4 import BeautifulSoup, NavigableString


@dataclass
class HighlightEntity:
    """高亮实体 - 支持基于位置的定位"""
    text: str
    category: str
    color: Optional[str] = None
    # 新增: 位置信息（来自 LangExtract）
    char_start: Optional[int] = None
    char_end: Optional[int] = None


@dataclass
class TextNodeMapping:
    """文本节点映射信息"""
    node_id: str
    start: int  # 在纯文本中的起始位置
    end: int    # 在纯文本中的结束位置
    tag_name: str  # HTML 标签名


class DOMTracker:
    """
    DOM 追踪映射器
    负责: Markdown → HTML → 纯文本 的坐标映射
    """
    
    def __init__(self, md_content: str):
        self.md_content = md_content
        self.html_content = None
        self.soup = None
        self.plain_text = ""
        self.node_mappings: List[TextNodeMapping] = []
        self._build_mapping()
    
    def _build_mapping(self):
        """构建 DOM 节点到纯文本的映射"""
        # 1. Markdown → HTML
        self.html_content = markdown.markdown(
            self.md_content,
            extensions=['extra', 'tables', 'admonition', 'fenced_code']
        )
        
        # 2. 解析 HTML
        self.soup = BeautifulSoup(self.html_content, 'html.parser')
        
        # 3. 遍历文本节点，构建映射
        # 只处理包含实际文本的块级/叶子节点
        text_bearing_tags = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 
                            'li', 'td', 'th', 'blockquote']
        
        current_offset = 0
        node_counter = 0
        
        for tag in self.soup.find_all(text_bearing_tags):
            # 跳过嵌套标签（只处理最直接的文本容器）
            # 例如 <td> 里面的 <p>，只处理 <p>
            if tag.find_parent(text_bearing_tags) and tag.name != 'td':
                continue
            
            # 提取纯文本（不包含内部 HTML 标签）
            text_content = tag.get_text(separator="", strip=False)
            text_len = len(text_content)
            
            if text_len == 0:
                continue
            
            # 生成节点 ID
            node_id = f"fusion_node_{node_counter}"
            tag['data-node-id'] = node_id
            
            # 记录映射
            self.node_mappings.append(TextNodeMapping(
                node_id=node_id,
                start=current_offset,
                end=current_offset + text_len,
                tag_name=tag.name
            ))
            
            # 拼接纯文本（用换行分隔，保持段落结构）
            self.plain_text += text_content + "\n"
            current_offset += text_len + 1
            node_counter += 1
    
    def get_plain_text(self) -> str:
        """获取给 LangExtract 的纯文本"""
        return self.plain_text
    
    def find_node_by_position(self, char_start: int, char_end: int) -> Optional[TextNodeMapping]:
        """
        根据字符位置找到对应的 HTML 节点
        
        Args:
            char_start: 实体在纯文本中的起始位置
            char_end: 实体在纯文本中的结束位置
        
        Returns:
            TextNodeMapping 或 None（如果跨节点或找不到）
        """
        for mapping in self.node_mappings:
            # 检查实体是否完全包含在该节点内
            if mapping.start <= char_start and char_end <= mapping.end:
                return mapping
        
        # 实体可能跨多个节点，记录警告
        return None
    
    def get_node_relative_position(self, mapping: TextNodeMapping, 
                                   char_start: int, char_end: int) -> Tuple[int, int]:
        """
        计算实体在节点内部的相对位置
        
        Returns:
            (relative_start, relative_end)
        """
        relative_start = char_start - mapping.start
        relative_end = char_end - mapping.start
        return relative_start, relative_end
    
    def debug_info(self) -> str:
        """打印调试信息"""
        info = []
        info.append("=" * 60)
        info.append("DOM-Tracking 映射信息")
        info.append("=" * 60)
        info.append(f"原始 Markdown 长度: {len(self.md_content)}")
        info.append(f"纯文本长度: {len(self.plain_text)}")
        info.append(f"文本节点数: {len(self.node_mappings)}")
        info.append("")
        info.append("节点映射表（前10个）:")
        for i, m in enumerate(self.node_mappings[:10]):
            preview = self.plain_text[m.start:m.end][:30].replace('\n', '\\n')
            info.append(f"  {m.node_id} [{m.tag_name}]: "
                       f"[{m.start:4d}:{m.end:4d}] {preview}...")
        if len(self.node_mappings) > 10:
            info.append(f"  ... 还有 {len(self.node_mappings) - 10} 个节点")
        info.append("")
        info.append("纯文本预览（前200字符）:")
        info.append(self.plain_text[:200].replace('\n', '\\n'))
        return "\n".join(info)


class DOMTrackingRenderer:
    """
    基于 DOM-Tracking 的高亮渲染器
    
    特点:
    - 基于位置而非内容匹配
    - 节点级精准定位
    - 保留原有 HTML 格式
    """
    
    # 默认颜色配置
    DEFAULT_COLORS = {
        "report_title": "#e67e22",      # 🟠 橙色
        "company_name": "#2ecc71",      # 🟢 绿色
        "shipment_value": "#3498db",    # 🔵 蓝色
        "market_share": "#9b59b6",      # 🟣 紫色
        "yoy_change": "#e84393",        # 🩷 粉色
        "negative_change": "#e74c3c",   # 🔴 红色
        "data_source": "#95a5a6",       # ⚪ 灰色
        "default": "#ffeb3b",           # 黄色
    }
    
    def __init__(self, colors: Optional[Dict[str, str]] = None):
        self.colors = {**self.DEFAULT_COLORS, **(colors or {})}
    
    def render(self, md_content: str, entities: List[HighlightEntity]) -> str:
        """
        渲染带高亮的 HTML
        
        Args:
            md_content: Markdown 原文
            entities: 带位置信息的实体列表
        
        Returns:
            带高亮标签的 HTML 字符串
        """
        # 1. 构建 DOM 追踪映射
        tracker = DOMTracker(md_content)
        print(tracker.debug_info())
        
        # 2. 获取 soup（已经打过 data-node-id）
        soup = tracker.soup
        
        # 3. 按位置倒序处理（避免插入标签后位置偏移）
        # 过滤掉没有位置信息的实体
        positioned_entities = [
            e for e in entities 
            if e.char_start is not None and e.char_end is not None
        ]
        positioned_entities.sort(key=lambda e: e.char_start, reverse=True)
        
        # 4. 处理每个实体
        success_count = 0
        fail_count = 0
        fail_reasons = []
        
        for entity in positioned_entities:
            mapping = tracker.find_node_by_position(entity.char_start, entity.char_end)
            
            if not mapping:
                fail_count += 1
                fail_reasons.append(f"  - '{entity.text}' 跨节点或找不到对应节点")
                continue
            
            # 计算节点内相对位置
            rel_start, rel_end = tracker.get_node_relative_position(
                mapping, entity.char_start, entity.char_end
            )
            
            # 找到目标节点
            target_tag = soup.find(attrs={"data-node-id": mapping.node_id})
            if not target_tag:
                fail_count += 1
                fail_reasons.append(f"  - '{entity.text}' 找不到目标标签")
                continue
            
            # 在节点内插入高亮
            if self._highlight_in_node(target_tag, rel_start, rel_end, entity):
                success_count += 1
            else:
                fail_count += 1
                fail_reasons.append(f"  - '{entity.text}' 节点内高亮失败")
        
        # 5. 输出处理统计
        print("\n" + "=" * 60)
        print("高亮处理统计")
        print("=" * 60)
        print(f"成功: {success_count}")
        print(f"失败: {fail_count}")
        if fail_reasons:
            print("\n失败原因:")
            for reason in fail_reasons[:5]:  # 只显示前5个
                print(reason)
            if len(fail_reasons) > 5:
                print(f"  ... 还有 {len(fail_reasons) - 5} 个")
        
        # 6. 清理 data-node-id 属性
        for tag in soup.find_all(attrs={"data-node-id": True}):
            del tag['data-node-id']
        
        return str(soup)
    
    def _highlight_in_node(self, tag, rel_start: int, rel_end: int, 
                           entity: HighlightEntity) -> bool:
        """
        在指定节点内插入高亮标签
        
        Args:
            tag: BeautifulSoup Tag
            rel_start: 节点内相对起始位置
            rel_end: 节点内相对结束位置
            entity: 实体信息
        
        Returns:
            是否成功
        """
        # 获取节点的纯文本
        node_text = tag.get_text(separator="", strip=False)
        
        # 验证位置是否有效
        if rel_start < 0 or rel_end > len(node_text) or rel_start >= rel_end:
            return False
        
        # 提取要替换的文本
        target_text = node_text[rel_start:rel_end]
        
        # 验证文本是否匹配（防御性检查）
        if target_text.strip() != entity.text.strip():
            print(f"  ⚠️ 文本不匹配: 期望 '{entity.text}', 实际 '{target_text}'")
        
        # 创建高亮标签
        color = self.colors.get(entity.category, self.colors["default"])
        soup = BeautifulSoup("", "html.parser")
        mark_tag = soup.new_tag("mark", 
                               attrs={"class": f"highlight-{entity.category}",
                                      "style": f"background-color: {color};"})
        mark_tag.string = target_text
        
        # 处理节点内容替换
        # 策略: 找到包含目标文本的文本节点，进行替换
        
        # 简单情况: 节点只有一个文本子节点
        if len(tag.contents) == 1 and isinstance(tag.contents[0], NavigableString):
            original_text = str(tag.contents[0])
            
            # 构建新内容: 前缀 + mark + 后缀
            new_contents = []
            if rel_start > 0:
                new_contents.append(NavigableString(original_text[:rel_start]))
            new_contents.append(mark_tag)
            if rel_end < len(original_text):
                new_contents.append(NavigableString(original_text[rel_end:]))
            
            tag.clear()
            for content in new_contents:
                tag.append(content)
            return True
        
        # 复杂情况: 节点有多个子节点（包含内联标签如 <strong>）
        # 使用递归方式处理
        return self._highlight_in_complex_node(tag, rel_start, rel_end, mark_tag)
    
    def _highlight_in_complex_node(self, tag, rel_start: int, rel_end: int,
                                   mark_tag) -> bool:
        """
        在复杂节点（包含多个子节点）中插入高亮
        
        策略: 遍历所有文本碎片，找到覆盖目标范围的位置
        """
        # 收集所有文本碎片及其累积位置
        text_fragments = []
        current_pos = 0
        
        for text_node in tag.find_all(string=True, recursive=True):
            if text_node.parent is tag or text_node.parent.name in ['strong', 'em', 'b', 'i', 'span']:
                text_len = len(str(text_node))
                text_fragments.append({
                    'node': text_node,
                    'start': current_pos,
                    'end': current_pos + text_len
                })
                current_pos += text_len
        
        # 找到覆盖目标范围的文本碎片
        target_start_frag = None
        target_end_frag = None
        
        for frag in text_fragments:
            if frag['start'] <= rel_start < frag['end']:
                target_start_frag = frag
            if frag['start'] < rel_end <= frag['end']:
                target_end_frag = frag
        
        if not target_start_frag or not target_end_frag:
            return False
        
        # 简化处理: 如果完全在同一个文本碎片内
        if target_start_frag == target_end_frag:
            text_node = target_start_frag['node']
            text = str(text_node)
            
            frag_start = target_start_frag['start']
            local_start = rel_start - frag_start
            local_end = rel_end - frag_start
            
            # 构建新内容
            new_html = f"{text[:local_start]}{str(mark_tag)}{text[local_end:]}"
            text_node.replace_with(BeautifulSoup(new_html, 'html.parser'))
            return True
        
        # 跨多个文本碎片的情况（较复杂，暂时标记为待处理）
        # 可以后续增强：拆分 mark 标签跨多个碎片
        print(f"  ⚠️ 实体跨越多个内联标签，简化处理")
        return False


def mock_langextract_with_positions(plain_text: str) -> List[HighlightEntity]:
    """
    模拟 LangExtract 返回带位置的结果
    
    在实际场景中，LangExtract 会返回:
    extraction.char_interval.start_pos
    extraction.char_interval.end_pos
    """
    # 模拟提取结果
    mock_entities = [
        ("智能手机市场分析", "report_title"),
        ("苹果", "company_name"),
        ("240.6", "shipment_value"),
        ("三星", "company_name"),
        ("226.6", "shipment_value"),
    ]
    
    entities = []
    for text, category in mock_entities:
        # 在纯文本中查找位置
        idx = plain_text.find(text)
        if idx != -1:
            entities.append(HighlightEntity(
                text=text,
                category=category,
                char_start=idx,
                char_end=idx + len(text)
            ))
    
    return entities


def run_demo():
    """运行验证 Demo"""
    
    # 模拟 MinerU 输出的 Markdown
    test_md = """### 智能手机市场分析

根据最新财报，**苹果**公司本季度的表现极其强劲。

| 品牌 | 出货量 | 市场份额 |
|---|---|---|
| 苹果 | 240.6 百万部 | 20.1% |
| 三星 | 226.6 百万部 | 19.4% |

总结：苹果和三星主导了市场。
"""
    
    print("=" * 70)
    print("DOM-Tracking 方案验证 Demo")
    print("=" * 70)
    print("\n输入 Markdown:")
    print("-" * 40)
    print(test_md[:300])
    print("...")
    
    # 1. 构建 DOM 追踪器
    print("\n" + "=" * 70)
    print("Step 1: 构建 DOM 追踪映射")
    print("=" * 70)
    
    tracker = DOMTracker(test_md)
    print(tracker.debug_info())
    
    # 2. 模拟 LangExtract 提取（带位置）
    print("\n" + "=" * 70)
    print("Step 2: 模拟 LangExtract 提取")
    print("=" * 70)
    
    plain_text = tracker.get_plain_text()
    print(f"输入 LangExtract 的纯文本（{len(plain_text)} 字符）:")
    print("-" * 40)
    print(plain_text[:300])
    print("...")
    
    entities = mock_langextract_with_positions(plain_text)
    print(f"\n提取到 {len(entities)} 个实体:")
    for e in entities:
        print(f"  - [{e.category}] '{e.text}' @ [{e.char_start}:{e.char_end}]")
    
    # 3. 渲染高亮 HTML
    print("\n" + "=" * 70)
    print("Step 3: 渲染高亮 HTML")
    print("=" * 70)
    
    renderer = DOMTrackingRenderer()
    highlighted_html = renderer.render(test_md, entities)
    
    # 4. 输出结果
    print("\n" + "=" * 70)
    print("输出 HTML（片段）:")
    print("=" * 70)
    # 美化输出
    soup = BeautifulSoup(highlighted_html, 'html.parser')
    print(soup.prettify()[:1500])
    print("...")
    
    # 5. 关键对比说明
    print("\n" + "=" * 70)
    print("方案对比")
    print("=" * 70)
    print("""
当前方案（正则匹配）:
  ❌ 问题: 全局搜索 "苹果" 会同时匹配到：
     - "苹果" 公司（期望高亮）
     - "苹果" 表格中的品牌（期望高亮）
     - "苹果" 和三星主导了市场（期望高亮）
  ❌ 但如果是不同位置的相同文本，无法区分
  
DOM-Tracking 方案:
  ✅ 基于位置: 精确知道 "苹果" 在纯文本中的位置 [23:25]
  ✅ 节点定位: 映射回具体 HTML 节点 <p> 或 <td>
  ✅ 局部高亮: 只在目标节点内插入 <mark>
  ✅ 避免伪阳性: 不会错误匹配到其他节点的同名文本
    """)


if __name__ == "__main__":
    run_demo()
