"""
ahe-sync setup script.

Usage: python scripts/setup.py

Creates a .venv/, installs dependencies, and scaffolds .env from .env.example.
Uses only Python stdlib — no external packages required to run this script.
"""

import shutil
import subprocess
import sys
from pathlib import Path

MIN_PYTHON = (3, 10)
ROOT = Path(__file__).parent.parent


def check_python_version() -> None:
    if sys.version_info < MIN_PYTHON:
        version = ".".join(str(v) for v in sys.version_info[:2])
        required = ".".join(str(v) for v in MIN_PYTHON)
        print(f"Error: Python {required}+ required (found {version}). Please upgrade.")
        sys.exit(1)


def create_venv() -> Path:
    venv_dir = ROOT / ".venv"
    if venv_dir.exists():
        print(".venv/ already exists — skipping creation")
    else:
        print("Creating .venv/ ...")
        subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
        print(".venv/ created")
    return venv_dir


def get_pip(venv_dir: Path) -> Path:
    if sys.platform == "win32":
        return venv_dir / "Scripts" / "pip"
    return venv_dir / "bin" / "pip"


def get_python(venv_dir: Path) -> Path:
    if sys.platform == "win32":
        return venv_dir / "Scripts" / "python"
    return venv_dir / "bin" / "python"


def install_dependencies(venv_dir: Path) -> None:
    pip = get_pip(venv_dir)
    print("Installing dependencies ...")
    subprocess.run([str(pip), "install", "-e", ".", "--quiet"], cwd=ROOT, check=True)
    print("Dependencies installed")


def scaffold_env() -> None:
    env_file = ROOT / ".env"
    example_file = ROOT / ".env.example"
    if env_file.exists():
        print(".env already exists — skipping copy")
    else:
        shutil.copy(example_file, env_file)
        print(".env created from .env.example")


def print_next_steps(venv_dir: Path) -> None:
    python = get_python(venv_dir)
    if sys.platform == "win32":
        start_cmd = f".venv\\Scripts\\python -m ahe_sync"
    else:
        start_cmd = ".venv/bin/python -m ahe_sync"

    print()
    print("─" * 60)
    print("Setup complete!")
    print()
    print("Next steps:")
    print("  1. Edit .env and fill in your credentials")
    print(f"  2. Start the daemon: {start_cmd}")
    print()
    print("To remove synced events before stopping:")
    print(f"  {start_cmd} remove --source puw")
    print(f"  {start_cmd} remove --source wps")
    print("─" * 60)


def main() -> None:
    check_python_version()
    venv_dir = create_venv()
    install_dependencies(venv_dir)
    scaffold_env()
    print_next_steps(venv_dir)


if __name__ == "__main__":
    main()
