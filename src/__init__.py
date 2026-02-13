"""
100 TIMES AI WORLD BUILDING - Local Version
Core modules for local execution with Ollama + gpt-oss:20b
"""

__version__ = "2.0.0-local"
__author__ = "masa-jp-art"

from .ollama_client import OllamaClient
from .checkpoint_manager import CheckpointManager
from .utils import load_config, load_prompts, data_to_markdown, rich_print
from .pipeline import Pipeline

__all__ = [
    "OllamaClient",
    "CheckpointManager",
    "Pipeline",
    "load_config",
    "load_prompts",
    "data_to_markdown",
    "rich_print",
]
