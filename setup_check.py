#!/usr/bin/env python3
"""
Setup Check Script
Verify that all prerequisites are met for running the local version
"""

import sys
from pathlib import Path


def check_python_version():
    """Check Python version"""
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")

    if version.major >= 3 and version.minor >= 10:
        print("✓ Python version OK (3.10+)")
        return True
    else:
        print("✗ Python version too old (required: 3.10+)")
        return False


def check_directory_structure():
    """Check if required directories exist"""
    required_dirs = [
        "config",
        "config/prompts",
        "src",
        "output",
        "output/intermediate",
        "output/checkpoints",
        "output/novels",
        "output/references",
        "tests",
        "logs",
    ]

    all_exist = True
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            print(f"✓ {dir_path}/")
        else:
            print(f"✗ {dir_path}/ (missing)")
            all_exist = False

    return all_exist


def check_required_files():
    """Check if required files exist"""
    required_files = [
        "config/ollama_config.yaml",
        "config/prompts/expansion.yaml",
        "config/prompts/world_building.yaml",
        "src/__init__.py",
        "src/ollama_client.py",
        "src/checkpoint_manager.py",
        "src/utils.py",
        "src/pipeline.py",
        "local-v2.0.ipynb",
        "README_LOCAL.md",
        "DESIGN_SPEC_LOCAL.md",
        "requirements-local.txt",
        ".gitignore",
    ]

    all_exist = True
    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} (missing)")
            all_exist = False

    return all_exist


def check_dependencies():
    """Check if required Python packages are installed"""
    required_packages = [
        "ollama",
        "yaml",
        "requests",
        "tqdm",
        "psutil",
        "loguru",
        "pytest",
        "jupyter",
    ]

    print("\nChecking Python packages...")
    all_installed = True

    for package in required_packages:
        try:
            if package == "yaml":
                __import__("yaml")
            else:
                __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} (not installed)")
            all_installed = False

    return all_installed


def check_ollama_server():
    """Check if Ollama server is accessible"""
    try:
        import requests

        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✓ Ollama server is running")
            return True
        else:
            print(f"✗ Ollama server returned status {response.status_code}")
            return False
    except ImportError:
        print("⚠ Cannot check Ollama server (requests not installed)")
        return False
    except requests.exceptions.ConnectionError:
        print("✗ Ollama server is not running")
        print("  Start it with: ollama serve")
        return False
    except Exception as e:
        print(f"✗ Error checking Ollama server: {e}")
        return False


def check_ollama_models():
    """Check if required models are available"""
    try:
        import requests

        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = data.get("models", [])
            model_names = [m.get("name", "") for m in models]

            target_models = ["gpt-oss:20b", "gpt-oss:20b-q4", "gpt-oss:20b-q8"]
            found = False

            for target in target_models:
                if target in model_names:
                    print(f"✓ Model found: {target}")
                    found = True
                    break

            if not found:
                print("✗ No required models found")
                print("  Download with: ollama pull gpt-oss:20b")
                return False

            return True
        else:
            print("✗ Cannot check models (server not responding)")
            return False
    except Exception as e:
        print(f"⚠ Cannot check models: {e}")
        return False


def main():
    """Main check routine"""
    print("=" * 60)
    print("100 TIMES AI WORLD BUILDING - Setup Check")
    print("=" * 60)
    print()

    checks = {
        "Python Version": check_python_version(),
    }

    print("\n" + "=" * 60)
    print("Directory Structure")
    print("=" * 60)
    checks["Directory Structure"] = check_directory_structure()

    print("\n" + "=" * 60)
    print("Required Files")
    print("=" * 60)
    checks["Required Files"] = check_required_files()

    print("\n" + "=" * 60)
    print("Python Dependencies")
    print("=" * 60)
    checks["Dependencies"] = check_dependencies()

    print("\n" + "=" * 60)
    print("Ollama Setup")
    print("=" * 60)
    checks["Ollama Server"] = check_ollama_server()
    checks["Ollama Models"] = check_ollama_models()

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    all_passed = True
    for check_name, passed in checks.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {check_name}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All checks passed! You're ready to start.")
        print("\nNext steps:")
        print("1. Open Jupyter Notebook: jupyter notebook")
        print("2. Open local-v2.0.ipynb")
        print("3. Run cells sequentially")
    else:
        print("✗ Some checks failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("- Install dependencies: pip install -r requirements-local.txt")
        print("- Start Ollama: ollama serve")
        print("- Download model: ollama pull gpt-oss:20b")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
