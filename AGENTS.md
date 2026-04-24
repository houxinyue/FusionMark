# Shell
- Use PowerShell
- Use encoding utf-8

# File encoding
- Always read/write files in UTF-8


# Agent Instructions

This project is a **highlighting system**.
This project combines the core technology of **MinerU** and **LangExtract** to develop a configuration that highlights text display capabilities. MinerU is responsible for extracting multimodal text content, while **LangExtract** is responsible for highlighting structured data output from large model text. **MinerU** MD text is highlighted and converted to PDF display.

`You can read the files in the docs directory` to see the specific implementation status of the project, or you can use the **bd (beads)** command to view the specific work progress.

> 📖 **Project Overview**: If you need to understand the overall architecture, core processes, dependency instructions, and other summary information of the project, please first read the **README.md** file.

## Encoding grid
The project includes front-end pages and back-end logic
- The front-end related code is located in the **frontend** directory
- The backend related service code is located in the **services** directory, mainly developed in **Python** code. The relevant version dependencies can be viewed in the **requirements.txt** file

> 📖 **Project Structure**: See **README.md** for detailed project structure and module organization.

- `Attention: Project developers prefer structured code that leans towards Java's object-oriented style, and prefer plugin style coding that facilitates the splitting, upgrading, and iteration of project functionality`


## Workflow Requirement

For engineering workflow, task tracking, OpenSpec usage, Beads usage, quality gates, commit/push rules, and session handoff:

> Follow the `ai-agent-sop-skill`.

Do not duplicate workflow rules in this file.

## Python Execution

This project uses `uv` local virtual environment.

Use:

```powershell
uv run python path/to/script.py
uv run pytest
uv pip install <package_name>