# FusionMark 示例代码

本目录包含 FusionMark 的各种示例和演示代码，帮助理解系统的工作原理和使用方法。

## 文件说明

### 主线流程示例

| 文件 | 说明 |
|------|------|
| `full_pipeline_demo.py` | **完整流程演示** - 展示如何使用 `FullPipelineService` 实现 PDF → 高亮 PDF 的完整流程 |
| `md_highlight_service_demo.py` | **高亮服务演示** - 展示如何使用可配置的 `MDHighlightService` |
| `langextract_demo.py` | **LangExtract 基础演示** - 展示 LangExtract 基础用法（简历信息提取） |

### 融合方案示例

| 文件 | 说明 |
|------|------|
| `mineru_langextract_fusion_demo.py` | **MinerU + LangExtract 融合** - 早期探索版本，使用 MinerU layout.json 进行位置匹配（旧版方案） |

### 备用方案（PyMuPDF）

以下文件是 PyMuPDF 备用方案的实现，**未在主线流程中使用**，仅作为技术探索保留：

| 文件 | 说明 |
|------|------|
| `pymupdf_langextract_fusion.py` | PyMuPDF + LangExtract 融合（备用方案） |
| `pymupdf_text_extractor.py` | PyMuPDF 文本提取器 |
| `pymupdf_vs_mineru_comparison.py` | PyMuPDF 与 MinerU 方案对比测试 |
| `pdf_highlight_demo.py` | PyMuPDF PDF 高亮演示 |

## 运行示例

### 完整流程演示

```bash
cd examples
python full_pipeline_demo.py
```

### 高亮服务演示

```bash
cd examples
python md_highlight_service_demo.py
```

### LangExtract 基础演示

```bash
cd examples
python langextract_demo.py
```

## 环境要求

运行示例前，请确保：

1. 已安装依赖：`pip install -r ../requirements.txt`
2. 已配置环境变量（`.env` 文件）：
   - `MINERU_API_KEY` - MinerU API 密钥
   - `DS_API_KEY` - DeepSeek API 密钥
   - `DS_API_BASE_URL` - DeepSeek API 地址

## 主线流程 vs 备用方案

### 主线流程（推荐使用）

```
PDF → MinerU API → Markdown → LangExtract → HTML高亮 → WeasyPrint → PDF
```

**优点：**
- 纯文本处理，无需精确坐标匹配
- 使用 WeasyPrint 渲染，排版美观
- 支持页眉页脚、中文优化

### 备用方案（PyMuPDF）

```
PDF → PyMuPDF → 文本+坐标 → LangExtract → 坐标匹配 → PyMuPDF渲染 → PDF
```

**未采用原因：**
- 文本匹配复杂（需处理重复、跨行等问题）
- 坐标精度依赖 PDF 质量
- 渲染效果不如 WeasyPrint

备用方案代码保留在 `pymupdf_*.py` 文件中，供参考学习。
