# Chopdiff 坐标映射验证套件

这个目录包含用于验证 **chopdiff** 库在 fusion-mark 项目中应用的 PoC（概念验证）脚本。

## 背景

当前项目使用 LangExtract 直接在 Markdown 上提取实体，存在以下问题：
1. **Token 浪费**：Markdown 标记（`#`, `**`, `|` 等）占用大量 Token
2. **提取干扰**：标记符号可能干扰 LLM 对文本语义的理解
3. **高亮错位**：需要在原始 Markdown 中精确定位实体位置

**解决方案**：使用 chopdiff 建立 Markdown ↔ 纯文本 双向坐标映射

## 验证脚本说明

### 1. `chopdiff_standalone_test.py` ⭐ 推荐先运行这个

**完全独立**的测试脚本，不依赖项目其他代码。

**功能：**
- 3 组测试用例（基础标题、表格内容、复杂格式）
- Markdown → 纯文本 转换验证
- 坐标映射准确性验证
- Token 节省比例计算
- JSON 格式详细报告

**运行方式：**
```bash
# 安装依赖
pip install chopdiff

# 运行测试
cd services
python examples/chopdiff_standalone_test.py
```

**预期输出：**
```
============================================================
Chopdiff 坐标映射独立验证
============================================================

测试: 基础标题测试
============================================================
📄 文本转换:
   Markdown: 187 字符
   纯文本: 142 字符
   减少: 45 字符
...

汇总报告
============================================================
📈 整体准确率: 6/6 (100.0%)

✅ 验证结论: 坐标映射方案可行，建议投入生产使用
```

### 2. `chopdiff_poc_demo.py`

与现有项目代码集成的演示脚本，展示如何在实际 pipeline 中使用 chopdiff。

**功能：**
- 使用真实的市场报告 Markdown 样本
- 模拟 LangExtract 提取流程
- 验证坐标映射到高亮的完整链路
- 生成详细的 Markdown 验证报告

**运行方式：**
```bash
cd services
python examples/chopdiff_poc_demo.py
```

**注意：** 此脚本需要项目其他模块支持，建议先确认 `chopdiff_standalone_test.py` 通过后再运行。

### 3. `chopdiff_config.yaml`

实验配置文件，定义：
- 文本转换策略
- 映射验证参数
- 测试实体定义
- 输出配置

## 验证检查清单

运行验证前，请确认：

- [ ] Python 3.8+ 环境
- [ ] 已安装 chopdiff: `pip install chopdiff`
- [ ] 有足够的磁盘空间（约 10MB 用于输出报告）

## 验证结果解读

### 准确率等级

| 准确率 | 结论 | 建议 |
|--------|------|------|
| ≥ 95% | ✅ 优秀 | 可直接投入生产 |
| 80-95% | ⚠️ 良好 | 需要针对失败案例优化 |
| 60-80% | ⚠️ 可用 | 需要增加降级/容错机制 |
| < 60% | ❌ 不可用 | 建议使用备选方案 |

### 关键指标

1. **Token 节省率**：Markdown → 纯文本 的字符减少比例
   - 预期：15-40%（取决于 Markdown 格式丰富程度）
   - 表格/代码多的文档节省更多

2. **映射准确率**：实体坐标映射的正确比例
   - 目标：≥ 95%
   - 主要失败原因：跨标记边界的实体、格式复杂的表格

3. **转换耗时**：大文档（5万字符）的处理时间
   - 预期：< 100ms
   - chopdiff 使用 C 实现的 diff 算法，性能优秀

## 常见问题

### Q: chopdiff 和 diff-match-patch 选哪个？

**chopdiff 优势：**
- 专为 LLM/文本处理场景设计
- 内置分块、滑动窗口、过滤等高级功能
- 现代 Python 代码风格，API 友好
- 维护活跃（2024年仍在更新）

**diff-match-patch 优势：**
- 18年生产验证（Google Docs 曾使用）
- 多语言支持
- Bitap 模糊匹配算法成熟
- ⚠️ 但官方项目已归档（2024年8月）

**建议**：先用 chopdiff 验证，如果准确率不达标，再考虑 diff-match-patch。

### Q: 如何处理表格中的实体？

表格是复杂场景，因为 Markdown 表格使用 `|` 分隔符。

**策略：**
1. 保留表格内容，去除 `|` 分隔符
2. 单元格内容用空格分隔
3. 如果实体跨越单元格边界，需要特殊处理

### Q: 中文文档支持如何？

chopdiff 基于字符级别的 diff，对中文支持良好。
测试显示中文实体的映射准确率与英文相当。

### Q: 如何集成到现有 pipeline？

步骤：
1. 在 `MinerU` 输出后，创建 `ChopdiffOffsetMapper`
2. 将 `mapper.get_plain_text()` 传给 LangExtract
3. LangExtract 返回的坐标用 `mapper.map_to_markdown()` 转换
4. 使用转换后的坐标进行高亮

代码示例见 `chopdiff_poc_demo.py` 中的 `ChopdiffOffsetMapper` 类。

## 输出文件

运行后会生成以下文件（在 `chopdiff_output/` 目录）：

| 文件 | 说明 |
|------|------|
| `chopdiff_verification_report.md` | 详细验证报告（Markdown） |
| `standalone_test_report.json` | 独立测试的 JSON 结果 |
| `mapping_visualization.txt` | 坐标映射可视化（调试用） |

## 下一步行动

验证通过后，建议：

1. **Code Review**：审查 `ChopdiffOffsetMapper` 实现
2. **性能测试**：使用真实大文档（10万+字符）测试
3. **边界测试**：测试表格、代码块、嵌套列表等复杂场景
4. **集成设计**：设计配置开关和降级机制
5. **A/B 测试**：与现有方案对比 Token 消耗和提取准确率

## 参考资源

- [chopdiff GitHub](https://github.com/jlevy/chopdiff)
- [diff-match-patch GitHub](https://github.com/google/diff-match-patch) (已归档)
- [Myers Diff 算法](https://blog.jcoglan.com/2017/02/12/the-myers-diff-algorithm-part-1/)

---

**验证完成？** 请根据准确率结果决定下一步：
- ≥ 95%：准备生产环境集成
- 80-95%：优化边界情况后重试
- < 80%：考虑备选方案（diff-match-patch）
