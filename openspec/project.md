# Project Context

## 1. Project Overview
This project is a highlighting system combining MinerU (multimodal text extraction) and LangExtract (structured data highlighting). 
- Frontend code is located in the `frontend/` directory.
- Backend services are located in the root directory, primarily developed in **Python**.

## 2. Coding Rules & Conventions
- **Architectural Style**: MUST use structured code that leans towards **Java's object-oriented style**. Avoid loose functional scripts.
- **Extensibility**: MUST prefer **plugin-style coding** that facilitates the easy splitting, upgrading, and iteration of project functionality.
- **Dependencies**: Always refer to `requirements.txt` for Python dependencies.

## 3. Tooling Constraints
- All feature planning MUST use OpenSpec.
- All atomic task tracking MUST use the `bd` (Beads) CLI. No Markdown TODOs.
