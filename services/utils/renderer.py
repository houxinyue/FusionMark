"""
MD 高亮渲染模块
用途: 将 Markdown 文本中的指定关键词按分类高亮，并转换为 PDF
适用场景: 结合 MinerU (获取MD) + LangExtract (获取分类实体) 使用
"""

import markdown
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from bs4 import BeautifulSoup, NavigableString
from weasyprint import HTML, CSS


@dataclass
class HighlightEntity:
    """高亮实体"""
    text: str
    category: str
    color: Optional[str] = None
    # DOM-Tracking 支持：位置信息（来自 LangExtract char_interval）
    char_start: Optional[int] = None
    char_end: Optional[int] = None
    
    def has_position(self) -> bool:
        """是否有位置信息"""
        return self.char_start is not None and self.char_end is not None


@dataclass
class TextNodeMapping:
    """DOM 文本节点映射信息"""
    node_id: str
    start: int  # 在纯文本中的起始位置
    end: int    # 在纯文本中的结束位置
    tag_name: str


class MDRenderer:
    """
    Markdown 高亮渲染器
    支持分类颜色高亮，生成 PDF
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
        """
        初始化渲染器
        :param colors: 自定义颜色配置 {category: hex_color}
        """
        self.colors = {**self.DEFAULT_COLORS, **(colors or {})}
        self.css_style = self._build_css()
    
    def _build_css(self) -> str:
        """构建 CSS 样式"""
        # 基础样式
        base_css = """
        @page {
            size: A4;
            margin: 2.5cm;
            @top-center { 
                content: "文档自动分析报告"; 
                font-size: 9pt; 
                color: #888; 
                font-family: "Microsoft YaHei", "SimSun", sans-serif;
            }
            @bottom-center { 
                content: "第 " counter(page) " 页"; 
                font-size: 9pt; 
                color: #888; 
                font-family: "Microsoft YaHei", "SimSun", sans-serif;
            }
        }
        
        body {
            font-family: "Microsoft YaHei", "SimSun", "Noto Sans CJK SC", sans-serif;
            font-size: 11pt;
            line-height: 1.6;
            color: #2c3e50;
        }

        h1, h2, h3 { color: #34495e; }
        
        /* 代码块样式 */
        pre {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            padding: 15px;
            border-radius: 4px;
            overflow-x: auto;
            font-family: "Consolas", "Monaco", monospace;
        }
        
        blockquote {
            border-left: 4px solid #3498db;
            padding-left: 15px;
            color: #7f8c8d;
            background-color: #f1f9ff;
            padding: 10px;
        }
        
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
        }
        th, td {
            border: 1px solid #dfe2e5;
            padding: 6px 13px;
        }
        tr:nth-child(2n) { background-color: #f6f8fa; }
        
        img { max-width: 100%; height: auto; }
        """
        
        # 分类高亮样式
        highlight_css = ""
        for category, color in self.colors.items():
            highlight_css += f"""
        mark.highlight-{category} {{
            background-color: {color};
            color: #000;
            padding: 2px 4px;
            border-radius: 2px;
            box-decoration-break: clone;
            -webkit-box-decoration-break: clone;
        }}
        """
        
        return base_css + highlight_css
    
    def _highlight_text_node(self, text_node, pattern_map: Dict[str, str]) -> Optional[List]:
        """
        核心逻辑：处理 HTML 文本节点，按分类高亮
        :param text_node: BeautifulSoup 文本节点
        :param pattern_map: {regex_pattern: category} 映射
        :return: 新节点列表或 None
        """
        content = text_node.string
        if not content or not content.strip():
            return None
        
        # 检查是否包含任何关键词
        has_match = False
        for pattern in pattern_map.keys():
            if pattern.search(content):
                has_match = True
                break
        
        if not has_match:
            return None
        
        # 构建所有匹配位置
        matches = []
        for pattern, category in pattern_map.items():
            for match in pattern.finditer(content):
                matches.append((match.start(), match.end(), match.group(), category))
        
        if not matches:
            return None
        
        # 按起始位置排序，解决重叠问题（优先保留长匹配）
        matches.sort(key=lambda x: (x[0], -(x[1] - x[0])))
        
        # 过滤重叠匹配
        filtered_matches = []
        last_end = -1
        for start, end, text, category in matches:
            if start >= last_end:
                filtered_matches.append((start, end, text, category))
                last_end = end
        
        # 构建新节点
        new_nodes = []
        last_idx = 0
        
        for start, end, text, category in filtered_matches:
            # 插入关键词前的普通文本
            if start > last_idx:
                new_nodes.append(NavigableString(content[last_idx:start]))
            
            # 插入高亮标签
            mark_tag = BeautifulSoup("", "html.parser").new_tag(
                "mark", 
                attrs={"class": f"highlight-{category}"}
            )
            mark_tag.string = text
            new_nodes.append(mark_tag)
            
            last_idx = end
        
        # 插入剩余文本
        if last_idx < len(content):
            new_nodes.append(NavigableString(content[last_idx:]))
        
        return new_nodes
    
    def render(
        self, 
        md_content: str, 
        entities: List[HighlightEntity], 
        output_path: str = "output.pdf",
        title: str = "Document"
    ) -> Tuple[int, int]:
        """
        执行渲染流程
        :param md_content: Markdown 源码
        :param entities: 高亮实体列表
        :param output_path: 输出 PDF 路径
        :param title: 文档标题
        :return: (实体数量, 高亮次数)
        """
        print(f"[*] 开始渲染，共 {len(entities)} 个实体...")
        
        if not entities:
            print("[!] 警告: 实体列表为空")
        
        # 1. Markdown -> HTML
        html_content = markdown.markdown(
            md_content, 
            extensions=['extra', 'tables', 'admonition', 'fenced_code']
        )
        
        # 2. 解析 HTML DOM
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 3. 构建关键词映射 {编译后正则: category}
        # 按实体文本长度降序，确保长词优先匹配
        sorted_entities = sorted(entities, key=lambda e: len(e.text), reverse=True)
        
        pattern_map = {}
        for entity in sorted_entities:
            # 转义特殊字符，忽略大小写
            escaped = re.escape(entity.text)
            pattern = re.compile(escaped, re.IGNORECASE)
            pattern_map[pattern] = entity.category
        
        # 4. 遍历并高亮
        ignore_tags = ['script', 'style', 'pre', 'code', 'noscript']
        
        text_nodes = [
            t for t in soup.find_all(text=True) 
            if t.parent.name not in ignore_tags
        ]
        
        highlight_count = 0
        for node in text_nodes:
            new_nodes = self._highlight_text_node(node, pattern_map)
            if new_nodes:
                node.replace_with(*new_nodes)
                highlight_count += 1
        
        print(f"[*] 已处理 {highlight_count} 个文本节点")
        
        # 5. 生成 PDF
        print("[*] 正在渲染 PDF (WeasyPrint)...")
        
        full_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
</head>
<body>
    {str(soup)}
</body>
</html>"""
        
        try:
            HTML(string=full_html, base_url=".").write_pdf(
                output_path, 
                stylesheets=[CSS(string=self.css_style)]
            )
            print(f"[+] 成功! PDF 已保存至: {output_path}")
        except Exception as e:
            print(f"[-] 生成 PDF 失败: {e}")
            print("提示: Windows 需安装 GTK3 运行时")
            print("提示: 中文显示方框请检查 CSS font-family")
            raise
        
        return len(entities), highlight_count


# 兼容旧接口的简单封装
def render_highlighted_pdf(
    md_content: str, 
    keywords: List[str], 
    output_path: str = "output.pdf",
    title: str = "Document"
) -> Tuple[int, int]:
    """
    简单高亮接口（所有关键词使用默认颜色）
    :param keywords: 关键词列表
    """
    entities = [HighlightEntity(text=k, category="default") for k in keywords]
    renderer = MDRenderer()
    return renderer.render(md_content, entities, output_path, title)


if __name__ == "__main__":
    # 测试
    test_md = """
# 测试文档

这是 **MinerU** 和 LangExtract 的测试。

## 数据
- 公司: Apple
- 出货量: 81.3 百万台
- 增长率: -11.4%

```python
# 这行代码中的 Apple 不应被高亮
print("Apple")
```
"""
    
    test_entities = [
        HighlightEntity("MinerU", "company_name"),
        HighlightEntity("Apple", "company_name"),
        HighlightEntity("81.3", "shipment_value"),
        HighlightEntity("-11.4%", "negative_change"),
    ]
    
    renderer = MDRenderer()
    renderer.render(test_md, test_entities, "test_output.pdf")


class DOMTrackingRenderer:
    """
    DOM-Tracking 高亮渲染器（基于位置精准高亮）
    
    特点:
    - 基于 char_interval 位置信息定位，非正则匹配
    - 节点级精准高亮，避免伪阳性
    - 支持纯文本预处理，减少 Token 消耗
    
    使用场景:
    - 当 LangExtract 返回 char_interval 时使用
    - 需要精准高亮、避免跨节点误匹配时使用
    """
    
    DEFAULT_COLORS = {
        "report_title": "#e67e22",
        "company_name": "#2ecc71",
        "shipment_value": "#3498db",
        "market_share": "#9b59b6",
        "yoy_change": "#e84393",
        "negative_change": "#e74c3c",
        "data_source": "#95a5a6",
        "default": "#ffeb3b",
    }
    
    def __init__(self, colors: Optional[Dict[str, str]] = None):
        self.colors = {**self.DEFAULT_COLORS, **(colors or {})}
    
    def build_dom_tracker(self, md_content: str) -> 'DOMTracker':
        """构建 DOM 追踪器"""
        return DOMTracker(md_content)
    
    def render(
        self, 
        md_content: str, 
        entities: List[HighlightEntity], 
        output_path: str = "output.pdf",
        title: str = "Document"
    ) -> Tuple[int, int, Dict]:
        """
        执行 DOM-Tracking 渲染
        
        :param md_content: Markdown 源码
        :param entities: 带位置信息的高亮实体列表
        :param output_path: 输出 PDF 路径
        :param title: 文档标题
        :return: (实体数量, 高亮次数, 统计信息)
        """
        print(f"[*] DOM-Tracking 渲染，共 {len(entities)} 个实体...")
        
        # 1. 构建 DOM 追踪
        tracker = self.build_dom_tracker(md_content)
        plain_text = tracker.get_plain_text()
        print(f"[*] Markdown {len(md_content)} 字符 → 纯文本 {len(plain_text)} 字符 "
              f"(减少 {(1-len(plain_text)/len(md_content))*100:.1f}%)")
        
        # 2. 过滤并排序有位置的实体
        positioned = [e for e in entities if e.has_position()]
        positioned.sort(key=lambda e: e.char_start, reverse=True)
        
        print(f"[*] 有位置信息的实体: {len(positioned)}/{len(entities)}")
        
        # 3. 执行高亮
        soup = tracker.soup
        stats = {"success": 0, "fail": 0, "cross_node": 0, "no_position": len(entities) - len(positioned)}
        
        for entity in positioned:
            mapping = tracker.find_node_by_position(entity.char_start, entity.char_end)
            
            if not mapping:
                stats["cross_node"] += 1
                stats["fail"] += 1
                continue
            
            rel_start, rel_end = tracker.get_node_relative_position(
                mapping, entity.char_start, entity.char_end
            )
            
            target_tag = soup.find(attrs={"data-node-id": mapping.node_id})
            if not target_tag:
                stats["fail"] += 1
                continue
            
            if self._insert_mark(target_tag, rel_start, rel_end, entity):
                stats["success"] += 1
            else:
                stats["fail"] += 1
        
        # 4. 清理临时属性
        for tag in soup.find_all(attrs={"data-node-id": True}):
            del tag['data-node-id']
        
        # 5. 生成 PDF
        print(f"[*] 高亮成功: {stats['success']}, 失败: {stats['fail']}, 跨节点: {stats['cross_node']}")
        print(f"[*] 正在渲染 PDF (WeasyPrint)...")
        
        css_style = self._build_css()
        full_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
</head>
<body>
    {str(soup)}
</body>
</html>"""
        
        try:
            HTML(string=full_html, base_url=".").write_pdf(
                output_path, 
                stylesheets=[CSS(string=css_style)]
            )
            print(f"[+] 成功! PDF 已保存至: {output_path}")
        except Exception as e:
            print(f"[-] 生成 PDF 失败: {e}")
            raise
        
        return len(entities), stats["success"], stats
    
    def _build_css(self) -> str:
        """构建 CSS"""
        base_css = """
        @page {
            size: A4;
            margin: 2.5cm;
            @top-center { 
                content: "文档自动分析报告"; 
                font-size: 9pt; 
                color: #888; 
                font-family: "Microsoft YaHei", "SimSun", sans-serif;
            }
            @bottom-center { 
                content: "第 " counter(page) " 页"; 
                font-size: 9pt; 
                color: #888; 
                font-family: "Microsoft YaHei", "SimSun", sans-serif;
            }
        }
        body {
            font-family: "Microsoft YaHei", "SimSun", "Noto Sans CJK SC", sans-serif;
            font-size: 11pt;
            line-height: 1.6;
            color: #2c3e50;
        }
        h1, h2, h3 { color: #34495e; }
        pre {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            padding: 15px;
            border-radius: 4px;
            overflow-x: auto;
            font-family: "Consolas", "Monaco", monospace;
        }
        blockquote {
            border-left: 4px solid #3498db;
            padding-left: 15px;
            color: #7f8c8d;
            background-color: #f1f9ff;
            padding: 10px;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
        }
        th, td {
            border: 1px solid #dfe2e5;
            padding: 6px 13px;
        }
        tr:nth-child(2n) { background-color: #f6f8fa; }
        img { max-width: 100%; height: auto; }
        """
        
        highlight_css = ""
        for category, color in self.colors.items():
            highlight_css += f"""
        mark.highlight-{category} {{
            background-color: {color};
            color: #000;
            padding: 2px 4px;
            border-radius: 2px;
            box-decoration-break: clone;
            -webkit-box-decoration-break: clone;
        }}
        """
        
        return base_css + highlight_css
    
    def _insert_mark(self, tag, rel_start: int, rel_end: int, entity: HighlightEntity) -> bool:
        """在节点内插入 mark 标签"""
        node_text = tag.get_text(separator="", strip=False)
        
        if rel_start < 0 or rel_end > len(node_text) or rel_start >= rel_end:
            return False
        
        target_text = node_text[rel_start:rel_end]
        
        # 防御性检查
        if target_text.strip() != entity.text.strip():
            print(f"  ⚠️ 文本不匹配: 期望 '{entity.text}', 实际 '{target_text}'")
        
        color = self.colors.get(entity.category, self.colors["default"])
        soup_temp = BeautifulSoup("", "html.parser")
        mark_tag = soup_temp.new_tag("mark", 
                                     attrs={"class": f"highlight-{entity.category}"})
        mark_tag.string = target_text
        
        # 简单情况：单文本子节点
        if len(tag.contents) == 1 and isinstance(tag.contents[0], NavigableString):
            original = str(tag.contents[0])
            new_contents = []
            
            if rel_start > 0:
                new_contents.append(NavigableString(original[:rel_start]))
            new_contents.append(mark_tag)
            if rel_end < len(original):
                new_contents.append(NavigableString(original[rel_end:]))
            
            tag.clear()
            for content in new_contents:
                tag.append(content)
            return True
        
        # 复杂情况（含内联标签）
        return self._handle_complex_node(tag, rel_start, rel_end, mark_tag)
    
    def _handle_complex_node(self, tag, rel_start: int, rel_end: int, mark_tag) -> bool:
        """处理复杂节点"""
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
        
        target_frag = None
        for frag in text_fragments:
            if frag['start'] <= rel_start < frag['end']:
                target_frag = frag
                break
        
        if not target_frag:
            return False
        
        text_node = target_frag['node']
        text = str(text_node)
        frag_start = target_frag['start']
        local_start = rel_start - frag_start
        local_end = rel_end - frag_start
        
        new_html = f"{text[:local_start]}{str(mark_tag)}{text[local_end:]}"
        text_node.replace_with(BeautifulSoup(new_html, 'html.parser'))
        return True


class DOMTracker:
    """
    DOM 追踪映射器
    负责 Markdown → HTML → 纯文本 的双向坐标映射
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
        self.html_content = markdown.markdown(
            self.md_content,
            extensions=['extra', 'tables', 'admonition', 'fenced_code']
        )
        self.soup = BeautifulSoup(self.html_content, 'html.parser')
        
        text_bearing_tags = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 
                            'li', 'td', 'th', 'blockquote']
        
        current_offset = 0
        node_counter = 0
        
        for tag in self.soup.find_all(text_bearing_tags):
            if tag.find_parent(text_bearing_tags) and tag.name != 'td':
                continue
            
            text_content = tag.get_text(separator="", strip=False)
            text_len = len(text_content)
            
            if text_len == 0:
                continue
            
            node_id = f"fusion_node_{node_counter}"
            tag['data-node-id'] = node_id
            
            self.node_mappings.append(TextNodeMapping(
                node_id=node_id,
                start=current_offset,
                end=current_offset + text_len,
                tag_name=tag.name
            ))
            
            self.plain_text += text_content + "\n"
            current_offset += text_len + 1
            node_counter += 1
    
    def get_plain_text(self) -> str:
        """获取给 LangExtract 的纯文本"""
        return self.plain_text
    
    def find_node_by_position(self, char_start: int, char_end: int) -> Optional[TextNodeMapping]:
        """根据字符位置找到对应的 HTML 节点"""
        for mapping in self.node_mappings:
            if mapping.start <= char_start and char_end <= mapping.end:
                return mapping
        return None
    
    def get_node_relative_position(self, mapping: TextNodeMapping, 
                                   char_start: int, char_end: int) -> Tuple[int, int]:
        """计算实体在节点内部的相对位置"""
        return char_start - mapping.start, char_end - mapping.start


# 兼容旧接口的简单封装
def render_highlighted_pdf(
    md_content: str, 
    keywords: List[str], 
    output_path: str = "output.pdf",
    title: str = "Document"
) -> Tuple[int, int]:
    """
    简单高亮接口（所有关键词使用默认颜色）
    :param keywords: 关键词列表
    """
    entities = [HighlightEntity(text=k, category="default") for k in keywords]
    renderer = MDRenderer()
    return renderer.render(md_content, entities, output_path, title)


if __name__ == "__main__":
    # 测试
    test_md = """
# 测试文档

这是 **MinerU** 和 LangExtract 的测试。

## 数据
- 公司: Apple
- 出货量: 81.3 百万台
- 增长率: -11.4%

```python
# 这行代码中的 Apple 不应被高亮
print("Apple")
```
"""
    
    test_entities = [
        HighlightEntity("MinerU", "company_name"),
        HighlightEntity("Apple", "company_name"),
        HighlightEntity("81.3", "shipment_value"),
        HighlightEntity("-11.4%", "negative_change"),
    ]
    
    renderer = MDRenderer()
    renderer.render(test_md, test_entities, "test_output.pdf")
