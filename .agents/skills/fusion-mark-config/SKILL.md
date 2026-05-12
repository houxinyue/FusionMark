---
name: fusion-mark-config
description: Generate and manage fusion-mark profile YAML files for the PDF parsing and highlighting pipeline. Use when Codex needs to create, update, validate, or explain profile YAML covering MinerU extraction settings, LangExtract prompts, few-shot examples, model provider settings, category colors, and rendering/output options.
---

# Fusion-Mark Config

Create profile YAML for the current `FullPipelineConfig` schema. A profile controls:

`MinerU document parsing -> LangExtract entity extraction -> Markdown/PDF highlighting`

Use the bundled YAML files in `assets/` as starting points:

- `assets/config-template.yaml`: generic current-schema template.
- `assets/market-report-example.yaml`: market/table report profile.
- `assets/financial-report-example.yaml`: financial report profile.
- `assets/legal-contract-example.yaml`: legal contract profile.

## Current YAML Shape

Generate full pipeline profiles, not the old flat `MDHighlightConfig` shape. Valid profile files use these top-level keys:

```yaml
description: "Human-readable profile purpose"

mineru_api_key: ""
mineru_base_url: "https://mineru.net/api/v4/extract"
mineru_client_mode: "open_sdk"
mineru_sdk_base_url: "https://mineru.net/api/v4"
mineru_sdk_token_env: "MINERU_API_KEY"
mineru_sdk_token: ""
mineru_sdk_extra_formats: []
mineru_enable_storage_input: true
mineru_enable_local_input: true
mineru_output_dir: "mineru_output"
mineru_model: "vlm"
mineru_enable_ocr: true
mineru_enable_formula: true
mineru_enable_table: true
mineru_language: "ch"
mineru_poll_interval: 3
mineru_max_retries: 60

highlight_config:
  extraction_prompt: |
    ...
  examples:
    - text: |
        ...
      extractions:
        - class: category_name
          text: "Exact source text"
  model_config:
    model_id: "deepseek-chat"
    provider: "OpenAILanguageModel"
    api_key_env: "DS_API_KEY"
    base_url_env: "DS_API_BASE_URL"
    provider_kwargs: {}
  category_colors:
    - name: category_name
      color: "#3498db"
      description: "Human-readable label"
  mineru_output_dir: "mineru_output"
  output_dir: "highlight_output"
  default_title: "Document Analysis Report"
  page_header: "Automatic Document Analysis"
  renderer: "dom_tracking"

final_output_dir: "highlight_output"
```

Important compatibility rules:

- Keep LangExtract fields under `highlight_config`; do not emit old top-level `extraction_prompt`, `examples`, `model_config`, or `category_colors`.
- `description` is metadata. The backend filters it before constructing `FullPipelineConfig`.
- `mineru_client_mode` must be `open_sdk`; legacy v4 is removed.
- `mineru_model` should be one of `pipeline`, `vlm`, or `MinerU-HTML`; default to `vlm` unless speed is more important than accuracy.
- `final_output_dir` overrides `highlight_config.output_dir` at runtime.
- Top-level `mineru_output_dir` is the pipeline MinerU output location; keep nested `highlight_config.mineru_output_dir` only for direct highlight-service compatibility.
- Use `renderer: "dom_tracking"` for new profiles; use `legacy` only as a compatibility fallback.
- Do not put secrets in YAML. Prefer `mineru_sdk_token_env`, `api_key_env`, and `base_url_env`.

## Generation Workflow

1. Identify document type, language, and extraction goal.
2. Choose MinerU settings: OCR, formula, table extraction, language, and model.
3. Define semantic extraction categories. Category names must match both `examples[*].extractions[*].class` and `category_colors[*].name`.
4. Write `extraction_prompt` with exact extraction rules, exclusions, table/column guidance, and sign/format handling.
5. Add 1-3 few-shot examples using exact text snippets that represent real document structure.
6. Assign distinct hex colors with meaningful descriptions.
7. Output complete profile YAML using the current schema.
8. If editing files in the repo, validate by loading with `FullPipelineConfig.from_yaml()`.

## Category Design

- Use stable snake_case names, for example `company_name`, `revenue_amount`, `contract_end_date`.
- Separate values that need different colors or business meaning, for example `growth_rate` and `decline_rate`.
- Include source/citation categories when the user needs traceability.
- For tables, instruct the model which columns to read and which rows to ignore.
- Ask for exact source text preservation. Highlighting depends on matching text back to the rendered document.

## Model Config

Default DeepSeek/OpenAI-compatible config:

```yaml
highlight_config:
  model_config:
    model_id: "deepseek-chat"
    provider: "OpenAILanguageModel"
    api_key_env: "DS_API_KEY"
    base_url_env: "DS_API_BASE_URL"
    provider_kwargs:
      temperature: 0.1
      max_tokens: 4000
```

For OpenAI, use:

```yaml
highlight_config:
  model_config:
    model_id: "gpt-4.1-mini"
    provider: "OpenAILanguageModel"
    api_key_env: "OPENAI_API_KEY"
    base_url_env: "OPENAI_BASE_URL"
    provider_kwargs:
      temperature: 0.1
```

## Color Defaults

Use these defaults unless the user specifies a domain palette:

| Meaning | Hex |
| --- | --- |
| Title/header | `#e67e22` |
| Organization/person | `#2ecc71` |
| Numeric value | `#3498db` |
| Percentage/rate | `#9b59b6` |
| Positive/growth | `#27ae60` |
| Negative/risk | `#e74c3c` |
| Date/time | `#f1c40f` |
| Source/citation | `#95a5a6` |
| Legal clause | `#6c5ce7` |
| Money/amount | `#00cec9` |

## Validation

For files in this repo, validate generated YAML with:

```powershell
uv run python -c "from services.core.full_pipeline import FullPipelineConfig; FullPipelineConfig.from_yaml(r'<path-to-yaml>'); print('ok')"
```

Validation catches schema errors such as obsolete flat keys, unknown fields, invalid nested objects, and malformed examples.
