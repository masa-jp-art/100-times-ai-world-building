# 100 TIMES AI WORLD BUILDING

## Overview

This project provides an AI-assisted world-building workflow for generating rich narrative universes.
It supports both a **cloud version** (OpenAI / Claude API) and a **local version** (Ollama, fully offline).

The project is designed for **iterative exploration**: you run it multiple times with different contexts
or models, and each run is saved to its own directory so previous results are never overwritten.

---

## Cloud Version

- **Setup**: Configure your OpenAI or Claude API key and run `20250601-100-TIMES-AI-WORLD-BUILDING-v1.2.ipynb`.
- **Usage**: Open the notebook, fill in your creative context, and execute cells in order.

---

## Local Version

> Full documentation: [README_LOCAL.md](README_LOCAL.md)

### Quick Start

```bash
# 1. Install Ollama and pull the default model
ollama pull gpt-oss:20b

# 2. Start Ollama server
ollama serve

# 3. Install Python dependencies
pip install -r requirements-local.txt

# 4. Run the interactive CLI
python example_run.py
```

### Model Options

| Model | Description | Requirement |
|-------|-------------|-------------|
| `gpt-oss:20b` | **Default** – full-precision 20B model | ≥16 GB VRAM or ≥32 GB RAM |
| `gpt-oss:20b-q8` | 8-bit quantized – balanced | 16–24 GB VRAM |
| `gpt-oss:20b-q4` | 4-bit quantized – lowest memory | 8–16 GB VRAM |
| `gpt-oss:120b` | High-end – best quality | ≥60 GB VRAM |

The CLI will prompt you to choose a model before each run.

### Per-Run Output Directories

Every execution creates a timestamped directory so repeated runs never overwrite each other:

```
output/
├── run_20260101_120000/   ← run 1
│   ├── intermediate/
│   ├── checkpoints/
│   ├── novels/
│   └── references/
├── run_20260102_093000/   ← run 2
└── run_20260103_150500/   ← run 3
```

### Python API

```python
from src import Pipeline

# Default model (gpt-oss:20b), auto-generated run_id
pipeline = Pipeline()

# Choose a quantized variant
pipeline = Pipeline(model="gpt-oss:20b-q4")

# Use the high-end model on a powerful machine
pipeline = Pipeline(model="gpt-oss:120b")

# Fix the run_id for reproducibility
pipeline = Pipeline(run_id="experiment_01")

print(pipeline.base_dir)  # ./output/run_YYYYMMDD_HHMMSS
```

---

## Running Tests

```bash
pytest tests/ -v
```
