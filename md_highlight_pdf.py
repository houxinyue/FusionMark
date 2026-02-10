"""
文件名: md_highlight_pdf.py
用途: 将 Markdown 文本中的指定关键词高亮，并转换为 PDF
适用场景: 结合 MinerU (获取MD) + LangExtract (获取关键词) 使用
作者: Gemini
日期: 2026-02-10
"""

import markdown
import re
import sys
from bs4 import BeautifulSoup, NavigableString
from weasyprint import HTML, CSS

# ================= 配置区域 =================
# 1. 依赖安装命令:
# pip install markdown beautifulsoup4 weasyprint
#
# 2. 系统级依赖 (WeasyPrint 需要):
# - Windows: 需要安装 GTK3 (https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer)
# - Linux (Ubuntu): sudo apt-get install python3-pip python3-cffi python3-brotli libpango-1.0-0 libpangoft2-1.0-0
# - MacOS: brew install weasyprint
# ===========================================

class MDHighlightSystem:
    def __init__(self):
        # CSS 样式配置
        # 注意: font-family 必须匹配系统已安装的中文字体，否则中文会显示为方框
        self.css_style = """
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
        
        /* 高亮样式 - 模拟荧光笔 */
        mark.highlight {
            background-color: #ffeb3b; /* 亮黄色 */
            color: #000;
            padding: 2px 4px;
            border-radius: 2px;
            box-decoration-break: clone; /* 跨行保持样式 */
            -webkit-box-decoration-break: clone;
        }

        /* 避免代码块内部被高亮，同时美化代码块 */
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

    def _highlight_text_node(self, text_node, pattern):
        """
        核心逻辑：仅处理 HTML 文本节点，安全替换，不破坏 HTML 标签结构
        """
        content = text_node.string
        if not content or not content.strip():
            return None

        # 如果当前文本节点不包含任何关键词，直接返回
        if not pattern.search(content):
            return None

        new_nodes = []
        last_idx = 0
        
        # 遍历所有匹配项
        for match in pattern.finditer(content):
            start, end = match.span()
            
            # 1. 插入关键词前的普通文本
            if start > last_idx:
                new_nodes.append(NavigableString(content[last_idx:start]))
            
            # 2. 插入高亮标签 (mark)
            # 使用 BeautifulSoup 创建新标签
            mark_tag = BeautifulSoup("<b></b>", "html.parser").new_tag("mark", attrs={"class": "highlight"})
            mark_tag.string = match.group() # 保持原文大小写
            new_nodes.append(mark_tag)
            
            last_idx = end
            
        # 3. 插入剩余文本
        if last_idx < len(content):
            new_nodes.append(NavigableString(content[last_idx:]))
            
        return new_nodes

    def process(self, md_content, keywords, output_path="output.pdf"):
        """
        执行转换流程
        :param md_content: Markdown 源码字符串
        :param keywords: 需要高亮的关键词列表 ['词1', '词2']
        :param output_path: 输出 PDF 路径
        """
        print(f"[*] 开始处理，共 {len(keywords)} 个关键词...")
        
        # 1. Markdown -> HTML
        # extensions: extra(支持表格等), codehilite(代码高亮支持)
        html_content = markdown.markdown(md_content, extensions=['extra', 'tables', 'admonition'])
        
        # 2. 解析 HTML DOM
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 3. 准备正则 (预编译以提升性能)
        # re.escape 确保关键词中的特殊符号(如 C++, .net) 被当作普通字符处理
        # 按长度降序排列，确保 "人工智能技术" 优先于 "人工智能" 被匹配
        sorted_keywords = sorted(keywords, key=len, reverse=True)
        if not sorted_keywords:
            print("[!] 警告: 关键词列表为空")
            pattern = None
        else:
            pattern = re.compile('|'.join(re.escape(k) for k in sorted_keywords), re.IGNORECASE)

        # 4. 遍历并高亮
        if pattern:
            # 获取所有文本节点
            # 过滤策略: 不处理 script, style, pre, code 标签内的文本
            # 这样可以防止代码块中的关键字被错误高亮
            ignore_tags = ['script', 'style', 'pre', 'code', 'noscript']
            
            text_nodes = [
                t for t in soup.find_all(text=True) 
                if t.parent.name not in ignore_tags
            ]

            count = 0
            for node in text_nodes:
                new_nodes = self._highlight_text_node(node, pattern)
                if new_nodes:
                    node.replace_with(*new_nodes)
                    count += 1
            print(f"[*] 已完成 DOM 注入，处理了 {count} 个文本节点")

        # 5. 生成 PDF
        print("[*] 正在渲染 PDF (WeasyPrint)...")
        
        full_html = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <title>Document</title>
        </head>
        <body>
            {str(soup)}
        </body>
        </html>
        """
        
        try:
            HTML(string=full_html, base_url=".").write_pdf(
                output_path, 
                stylesheets=[CSS(string=self.css_style)]
            )
            print(f"[+] 成功! PDF 已保存至: {output_path}")
        except Exception as e:
            print(f"[-] 生成 PDF 失败: {e}")
            print("提示: 如果是 Windows，请检查是否安装了 GTK3 运行时。")
            print("提示: 如果中文显示方框，请检查 CSS 中的 font-family 是否包含系统已安装字体。")

# ================= 模拟 MinerU + LangExtract 的调用 =================

if __name__ == "__main__":
    # 1. 模拟 MinerU 提取的 Markdown
    mock_md_content = """
# 智能文档处理系统技术方案

## 1. 项目概述
本方案旨在利用 **OCR技术** 和 **NLP算法** 对非结构化文档进行解析。
系统核心组件包括 MinerU 和 LangExtract。

## 2. 风险提示
> 警告：数据安全是重中之重，严禁在公网传输**明文密码**。

## 3. 关键代码实现
请注意，下面的代码中 `print` 不应该被高亮，因为它在代码块里。

```python
def secure_transfer(data):
    # 这是一个处理数据的函数
    print("正在传输数据...") 
    return data.encrypt()
    ```python
def secure_transfer(data):
    # 这是一个处理数据的函数
    print("正在传输数据...") 
    return data.encrypt()
4. 表格数据组件名称功能描述状态MinerUPDF解析与提取已部署LangExtract关键词抽取测试中点击访问 MinerU 仓库
# 2. 模拟 LangExtract 提取的关键词
mock_keywords = [
    "MinerU", 
    "OCR技术", 
    "数据安全", 
    "print",  # 测试是否会误伤代码块（预期：正文高亮，代码块不高亮）
    "明文密码"
]
# 3. 运行转换
converter = MDHighlightSystem()
converter.process(mock_md_content, mock_keywords, "demo_report.pdf")
```
"""