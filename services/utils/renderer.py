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
