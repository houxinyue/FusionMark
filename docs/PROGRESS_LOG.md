# MinerU + LangExtract 融合项目 - 进度记录

**项目**: PDF 智能解析与高亮标注系统  
**开始日期**: 2026-02-05  
**最后更新**: 2026-02-09  
**状态**: Phase 2 实现完成，方案1(PyMuPDF)研究完成，待对比测试  

---

## 进度概览

```
Phase 1: 调研与验证        [██████████] 100% ✓
Phase 2: 融合实现          [████████░░] 80%  (代码完成，待运行测试)
Phase 3: 优化与扩展        [░░░░░░░░░░] 0%   (待开始)
```

---

## 详细进度

### ✅ 已完成 (Completed)

#### 1. MinerU 输出格式调研
- **时间**: 2026-02-05
- **内容**: 分析 `layout.json` 和 `content_list.json` 结构
- **关键发现**:
  - `layout.json` 包含更详细的层级结构（para_blocks → lines → spans）
  - 坐标系统与 PyMuPDF 兼容（bbox: [x0, y0, x1, y1]）
  - 注脚信息在嵌套的 `blocks` 中
- **输出文档**: `PDF_HIGHLIGHT_PLAN.md`

#### 2. PyMuPDF 高亮验证
- **时间**: 2026-02-05
- **内容**: 验证 PDF 边框绘制和坐标匹配
- **关键发现**:
  - 透明边框比高亮更适合调试位置
  - 需要轻微 Y 轴偏移（-3 单位）修正位置偏差
  - `layout.json` 的坐标比 `content_list.json` 更准确
- **测试文件**: `pdf_highlight_demo.py`
- **输出示例**: 
  - `smartphone_transparent_boxes.pdf`
  - `layout_para_block_boxes.pdf`

#### 3. 融合架构设计
- **时间**: 2026-02-05
- **内容**: 设计 MinerU + LangExtract + PyMuPDF 融合方案
- **核心设计**:
  - 三级匹配策略：精确 → 包含 → 模糊
  - Span 级位置索引
  - 颜色编码方案（按类别区分）
- **输出文档**: `RESEARCH_PHASE_2_FUSION.md`

#### 4. 完整融合代码实现
- **时间**: 2026-02-05
- **内容**: 实现端到端融合管道
- **代码文件**: `mineru_langextract_fusion_demo.py`
- **功能模块**:
  | 模块 | 功能 | 状态 |
  |------|------|------|
  | `run_langextract()` | LLM 信息提取 | ✓ |
  | `build_span_index()` | 位置索引构建 | ✓ |
  | `fuzzy_match()` | 三级匹配算法 | ✓ |
  | `match_extractions()` | 批量匹配 | ✓ |
  | `render_highlights()` | PDF 渲染 | ✓ |

#### 5. 负值高亮功能
- **时间**: 2026-02-05
- **内容**: 添加对负增长数值的特殊高亮
- **实现**:
  - 新增提取类别: `negative_change`
  - 颜色: 🔴 红色 (1.0, 0.0, 0.0)
  - 示例数据包含 `-11.4%` 负值
- **业务价值**: 一眼识别负增长数据，便于分析

#### 6. 文档整理
- **时间**: 2026-02-05
- **内容**: 创建 `docs/` 目录，整理项目文档
- **文档列表**:
  - `PDF_HIGHLIGHT_PLAN.md` - 初期调研
  - `RESEARCH_PHASE_2_FUSION.md` - Phase 2 设计
  - `IMPLEMENTATION_FUSION_PIPELINE.md` - 实现说明
  - `PROGRESS_LOG.md` - 本文件

---

### 🚧 进行中 (In Progress)

#### 端到端测试
- **状态**: 代码完成，待运行
- **待验证**:
  - [ ] LangExtract API 调用正常
  - [ ] 文本匹配准确率
  - [ ] PDF 高亮渲染效果
  - [ ] 负值识别和高亮
- **阻塞项**: 需要 DeepSeek API 密钥

---

### ⏳ 待开始 (Pending)

#### Phase 3: 优化与扩展
- [ ] 匹配准确率优化（根据测试结果调整阈值）
- [ ] 性能优化（大文档索引构建速度）
- [ ] 支持更多文档类型（药品说明书、合同等）
- [ ] 批量处理多个 PDF
- [ ] 交互式可视化界面

---

## 关键决策记录

| 日期 | 决策 | 原因 | 影响 |
|------|------|------|------|
| 2026-02-05 | 使用 `layout.json` 而非 `content_list.json` | layout 包含更详细的嵌套结构（blocks） | 能提取到注脚等嵌套内容 |
| 2026-02-05 | 使用透明边框而非高亮 | 更容易看清位置是否准确 | 调试效率提升 |
| 2026-02-05 | 三级匹配策略 | 平衡准确率和召回率 | 提高匹配成功率 |
| 2026-02-05 | Span 级粒度 | 最精确的位置信息 | 可能对长文本需要跨 span 匹配 |
| 2026-02-05 | 负值单独分类高亮 | 业务需求：负增长需要醒目标识 | 增强可读性 |

---

## 技术债务

| 问题 | 优先级 | 解决方案 | 预计工作量 |
|------|--------|----------|-----------|
| 跨 Span 文本匹配 | 高 | 实现滑动窗口合并匹配 | 1-2 天 |
| 大文档性能优化 | 中 | 使用 Trie 树加速索引 | 1 天 |
| 坐标微调参数化 | 低 | 添加配置项支持用户调整 | 0.5 天 |

---

## 运行记录

### 测试运行 1
- **时间**: 待记录
- **输入**: 智能手机出货量报告
- **结果**: 待记录
- **问题**: 待记录

---

## 下一步行动计划

### 立即执行（今天）
1. [ ] 配置 DeepSeek API 环境变量
2. [ ] 运行 `mineru_langextract_fusion_demo.py`
3. [ ] 检查提取结果和高亮效果
4. [ ] 记录运行结果到本文件

### 短期（本周）
1. [ ] 根据测试结果调整匹配阈值
2. [ ] 优化负值匹配准确率
3. [ ] 使用药品说明书进行第二次测试

### 中期（本月）
1. [ ] 封装为可复用的 Python 库
2. [ ] 添加命令行接口
3. [ ] 编写用户使用文档

---

## 资源链接

| 资源 | 路径 | 说明 |
|------|------|------|
| 融合代码 | `mineru_langextract_fusion_demo.py` | 主程序 |
| 测试数据 | `mineru_output/513f81dc-4fca-42b3-a4a9-0d58d99db2d2/extracted/` | 智能手机报告 |
| 高亮测试 | `pdf_highlight_demo.py` | PyMuPDF 高亮测试 |
| 设计文档 | `docs/RESEARCH_PHASE_2_FUSION.md` | 架构设计 |
| 实现文档 | `docs/IMPLEMENTATION_FUSION_PIPELINE.md` | 代码说明 |

---

## 备注

- **数据集**: 使用 IDC 智能手机出货量报告（Q4 2025）作为测试数据
- **关键数据点**: Apple 81.3M (+4.9%), Samsung 61.2M (+18.3%), Xiaomi 37.8M (**-11.4%** 负值)
- **目标场景**: 财报分析、药品说明书标注、合同审查等结构化文档处理

---

## 2026-02-09 更新: 重要发现 - PDF高亮方案存在局限性

### ❌ 问题发现
**PDF 高亮这条路走不通！**

**原因**: 部分 PDF 扫描完成后，文字是以**图片形式**存在的，不是可选择的文本层。

**验证结果**:
- PyMuPDF 无法提取图片中的文字坐标
- LangExtract 也无法从图片中提取实体
- 整个 PDF 高亮方案在这种场景下失效

**影响的文件**:
- `pymupdf_text_extractor.py` - 对图片型 PDF 无效
- `pymupdf_langextract_fusion.py` - 对图片型 PDF 无效
- 所有依赖文字坐标提取的方案都受影响

### 可能的解决方案
1. **OCR 预处理** - 先用 OCR 识别图片文字并创建文本层
2. **截图高亮** - 直接在图片上绘制高亮框
3. **改用其他方案** - 如网页版高亮、导出为其他格式等

### 状态
需要进一步讨论方案方向

---

## 2026-02-09 更新: PyMuPDF 替代方案研究

### 新方案: PyMuPDF 直接提取文字坐标（方案1）

**背景**: 发现 MinerU 生成的 layout.json 粒度不够细，考虑用 PyMuPDF 直接替代

**研究内容**:
1. **PyMuPDF 文字坐标提取能力调研**
   - `page.get_text("dict")` - span 级别，含字体信息
   - `page.get_text("words")` - 单词级别，适合匹配
   - `page.get_text("rawdict")` - 字符级别，最细粒度
   - 坐标格式 `[x0, y0, x1, y1]` 与 MinerU 兼容

2. **实现代码**
   - `pymupdf_text_extractor.py` - 文字坐标提取器
     - 支持 span/word 两种粒度
     - 生成 MinerU 兼容的 JSON 格式
     - 构建文字索引用于快速匹配
   
   - `pymupdf_langextract_fusion.py` - 融合 Pipeline
     - 完整流程: PyMuPDF 提取 → LangExtract → 匹配 → 高亮
     - TextMatcher 三级匹配策略（精确→包含→模糊）
     - 直接使用 PyMuPDF 渲染高亮
   
   - `pymupdf_vs_mineru_comparison.py` - 对比测试
     - 粒度对比（span/word vs block/line/span）
     - 坐标精度验证
     - JSON 格式对比

**方案对比**:

| 特性 | MinerU 方案 | PyMuPDF 方案 |
|------|------------|-------------|
| 依赖 | 需要 MinerU API | 仅 PyMuPDF |
| 粒度 | span 级别 | span/word/char 可选 |
| 速度 | 慢（API 调用）| 快（本地处理）|
| 准确性 | 高（ML 布局分析）| 中（基于 PDF 结构）|
| 成本 | 有 API 费用 | 免费 |
| 离线可用 | 否 | 是 |

**下一步**:
- [ ] 运行对比测试，验证坐标精度
- [ ] 对比两种方案的匹配准确率
- [ ] 决定是否采用 PyMuPDF 作为默认方案

---

**记录人**: AI Assistant  
**审核状态**: 待审核  
**下次更新**: 对比测试后
