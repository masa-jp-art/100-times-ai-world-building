#!/usr/bin/env python3
"""
Example Run Script
Demonstrates how to use the pipeline from Python code
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src import Pipeline, setup_logging

# ---------------------------------------------------------------------------
# Local model options
# ---------------------------------------------------------------------------
LOCAL_MODELS = [
    {
        "name": "gpt-oss:20b",
        "label": "gpt-oss:20b (standard – recommended)",
        "description": "Full-precision 20B model. Best quality for most machines with ≥32 GB RAM or ≥16 GB VRAM.",
    },
    {
        "name": "gpt-oss:20b-q8",
        "label": "gpt-oss:20b-q8 (8-bit quantized)",
        "description": "8-bit quantized 20B model. Balanced quality / memory trade-off (16–24 GB VRAM).",
    },
    {
        "name": "gpt-oss:20b-q4",
        "label": "gpt-oss:20b-q4 (4-bit quantized)",
        "description": "4-bit quantized 20B model. Lowest memory footprint (8–16 GB VRAM).",
    },
    {
        "name": "gpt-oss:120b",
        "label": "gpt-oss:120b (high-end – powerful machines only)",
        "description": "120B model. Highest generation quality. Requires ≥60 GB VRAM or very large RAM.",
    },
]


def select_model() -> str:
    """Interactive model selection menu.

    Returns the chosen model name string.
    """
    print("\n--- Model Selection ---")
    for i, m in enumerate(LOCAL_MODELS, 1):
        print(f"{i}. {m['label']}")
        print(f"   {m['description']}")
    print()

    while True:
        try:
            raw = input("Select model [1]: ").strip()
            if raw == "":
                return LOCAL_MODELS[0]["name"]
            idx = int(raw) - 1
            if 0 <= idx < len(LOCAL_MODELS):
                return LOCAL_MODELS[idx]["name"]
        except ValueError:
            pass
        print(f"Please enter a number between 1 and {len(LOCAL_MODELS)}.")


def run_phase1_only():
    """Run only Phase 1 (100x expansion) for quick testing"""
    print("=" * 60)
    print("Running Phase 1 (100x Expansion) Only")
    print("=" * 60)

    # Model selection
    model = select_model()

    # Setup logging
    setup_logging(log_level="INFO", console=True)

    # Initialize pipeline (a new run_id is generated automatically)
    pipeline = Pipeline(model=model)

    # Check prerequisites
    if not pipeline.check_prerequisites():
        print("\n✗ Prerequisites not met. Please check the errors above.")
        return 1

    # User context (example)
    user_context = """
context:
  theme: "未来都市での人間と人工知能の共存"
  mood: "希望と不安が交錯する"
  setting: "2080年代の東京"
  key_elements:
    - "完全自動化された社会"
    - "失われつつある人間性"
    - "新しい形のコミュニケーション"
  protagonist_idea: "AIと対話できる特殊能力を持つ若者"
"""

    # Run Phase 1
    print("\nStarting Phase 1...")
    results = pipeline.run_phase1_expansion(user_context)

    print("\n" + "=" * 60)
    print("Phase 1 Complete!")
    print("=" * 60)
    print(f"Generated {len(results)} outputs:")
    for key in results.keys():
        print(f"  - {key}")

    print(f"\nOutputs saved to: {pipeline.base_dir}/intermediate/")
    print(f"Run ID: {pipeline.run_id}")
    return 0


def run_full_pipeline():
    """Run the complete pipeline (WARNING: Takes several hours)"""
    print("=" * 60)
    print("Running Full Pipeline")
    print("WARNING: This will take 1.5-8 hours depending on your hardware")
    print("=" * 60)

    response = input("\nAre you sure you want to continue? (yes/no): ")
    if response.lower() != "yes":
        print("Cancelled.")
        return 0

    # Model selection
    model = select_model()

    # Setup logging
    setup_logging(
        log_level="INFO",
        log_file="./logs/full_pipeline.log",
        console=True
    )

    # Initialize pipeline (a new run_id is generated automatically)
    pipeline = Pipeline(model=model)

    # Check prerequisites
    if not pipeline.check_prerequisites():
        print("\n✗ Prerequisites not met. Please check the errors above.")
        return 1

    # User context
    user_context = """
context:
  theme: "未来都市での人間と人工知能の共存"
  mood: "希望と不安が交錯する"
  setting: "2080年代の東京"
  key_elements:
    - "完全自動化された社会"
    - "失われつつある人間性"
    - "新しい形のコミュニケーション"
  protagonist_idea: "AIと対話できる特殊能力を持つ若者"
"""

    # Run full pipeline
    print("\nStarting full pipeline...")
    results = pipeline.run_full_pipeline(user_context)

    print("\n" + "=" * 60)
    print("Full Pipeline Complete!")
    print("=" * 60)
    print(f"\nRun ID: {pipeline.run_id}")
    print(f"Generated outputs (all under {pipeline.base_dir}/):")
    print(f"  - Novels:            {pipeline.base_dir}/novels/")
    print(f"  - References:        {pipeline.base_dir}/references/")
    print(f"  - Intermediate data: {pipeline.base_dir}/intermediate/")
    print(f"  - Checkpoints:       {pipeline.base_dir}/checkpoints/")

    return 0


def resume_from_phase():
    """Resume from a specific phase"""
    print("=" * 60)
    print("Resume from Checkpoint")
    print("=" * 60)

    # Model selection
    model = select_model()

    # Setup logging
    setup_logging(log_level="INFO", console=True)

    # Initialize pipeline (a new run_id is generated automatically)
    pipeline = Pipeline(model=model)

    # List available checkpoints
    checkpoints = pipeline.checkpoint_manager.list_checkpoints()

    if not checkpoints:
        print("\n✗ No checkpoints found.")
        return 1

    print("\nAvailable checkpoints:")
    for i, cp in enumerate(checkpoints[:10], 1):
        print(f"{i}. {Path(cp).name}")

    # Get phase name from user
    phase_name = input("\nEnter phase name to resume from (e.g., phase1_expansion): ")

    if pipeline.resume_from_checkpoint(phase_name):
        print(f"\n✓ Successfully resumed from {phase_name}")
        print("\nYou can now continue the pipeline from this point.")
        return 0
    else:
        print(f"\n✗ Failed to resume from {phase_name}")
        return 1


def main():
    """Main entry point"""
    print("\n100 TIMES AI WORLD BUILDING - Example Run\n")
    print("Select an option:")
    print("1. Run Phase 1 only (quick test, ~5-25 min)")
    print("2. Run full pipeline (complete generation, ~1.5-8 hours)")
    print("3. Resume from checkpoint")
    print("4. Exit")

    try:
        choice = input("\nEnter your choice (1-4): ").strip()

        if choice == "1":
            return run_phase1_only()
        elif choice == "2":
            return run_full_pipeline()
        elif choice == "3":
            return resume_from_phase()
        elif choice == "4":
            print("Goodbye!")
            return 0
        else:
            print("Invalid choice.")
            return 1

    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        return 1
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
