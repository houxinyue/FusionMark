---
name: fusion-mark-config
description: Generate and manage configuration files for fusion-mark PDF intelligent parsing and highlighting system. Use when user needs to create or modify config.yaml/json for extraction prompts, category colors, model settings, or examples for few-shot learning in PDF text extraction and highlighting workflows.
---

# Fusion-Mark Configuration Helper

This skill helps generate and manage configuration files for the fusion-mark PDF intelligent parsing and highlighting system.

## Configuration Structure

A valid fusion-mark config contains these sections:

1. **extraction_prompt** - Instructions for LLM to extract entities from text
2. **examples** - Few-shot learning examples (text + extractions)
3. **model_config** - LLM provider and API settings
4. **category_colors** - Color mapping for each extraction category
5. **mineru_output_dir** - MinerU output directory
6. **output_dir** - Highlighted PDF output directory
7. **default_title** - Default document title
8. **page_header** - Page header text

## Quick Start

To create a new config for a specific business scenario:

1. Ask user about their document type and extraction needs
2. Design extraction categories based on business requirements
3. Generate config using `assets/config-template.yaml` as base
4. Provide both YAML and JSON formats

## Color Palette Reference

Common highlight colors:

| Category Type | Color | Hex |
|--------------|-------|-----|
| Title/Header | Orange | `#e67e22` |
| Organization | Green | `#2ecc71` |
| Numeric Value | Blue | `#3498db` |
| Percentage | Purple | `#9b59b6` |
| Positive Growth | Pink | `#e84393` |
| Negative Growth | Red | `#e74c3c` |
| Source/Citation | Gray | `#95a5a6` |
| Date/Time | Yellow | `#f1c40f` |
| Location | Cyan | `#00cec9` |
| Status | Indigo | `#6c5ce7` |

## Extraction Category Design

When designing categories, follow these principles:

1. **Use semantic names** - e.g., `company_name` not `field_1`
2. **Separate value types** - e.g., `shipment_value` vs `market_share`
3. **Distinguish positive/negative** - e.g., `yoy_change` vs `negative_change`
4. **Include source citations** - always add `data_source` category

## Example Patterns

### Market Report Pattern
```yaml
category_colors:
  - name: report_title
    color: "#e67e22"
    description: "报告标题"
  - name: company_name
    color: "#2ecc71" 
    description: "公司名称"
  - name: metric_value
    color: "#3498db"
    description: "指标数值"
  - name: data_source
    color: "#95a5a6"
    description: "数据来源"
```

### Financial Report Pattern
```yaml
category_colors:
  - name: revenue
    color: "#2ecc71"
    description: "收入"
  - name: expense
    color: "#e74c3c"
    description: "支出"
  - name: profit
    color: "#3498db"
    description: "利润"
  - name: date_period
    color: "#f1c40f"
    description: "会计期间"
```

### Legal Document Pattern
```yaml
category_colors:
  - name: party_name
    color: "#6c5ce7"
    description: "当事方"
  - name: key_date
    color: "#f1c40f"
    description: "关键日期"
  - name: monetary_amount
    color: "#00cec9"
    description: "金额"
  - name: clause_reference
    color: "#e67e22"
    description: "条款引用"
```

## Model Configuration

Default uses DeepSeek via OpenAI-compatible API:

```yaml
model_config:
  model_id: "deepseek-chat"
  provider: "OpenAILanguageModel"
  api_key_env: "DS_API_KEY"
  base_url_env: "DS_API_BASE_URL"
  provider_kwargs: {}
```

Alternative providers:
- OpenAI: `model_id: "gpt-4"`, `api_key_env: "OPENAI_API_KEY"`
- Azure: Add `azure_endpoint_env`, `api_version`
- Local: `provider: "CustomLanguageModel"` with custom base_url

## Usage Workflow

1. **Identify document type** - market report, financial statement, legal contract, etc.
2. **Define extraction categories** - what entities need to be highlighted
3. **Assign colors** - use semantic color coding
4. **Draft extraction prompt** - clear instructions with extraction rules
5. **Create examples** - 1-3 few-shot examples for complex extractions
6. **Output config** - provide both YAML and JSON formats

## Output Files

When generating config, create:
- `config.yaml` - Primary YAML configuration
- `config.json` - JSON alternative (same content)

Both formats are functionally equivalent; YAML is preferred for human editing.
