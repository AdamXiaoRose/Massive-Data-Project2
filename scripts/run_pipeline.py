"""End-to-end pipeline entry point.

Run with:  python scripts/run_pipeline.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STAGES = [
    ("cleaning", "scripts/cleaning.py"),
    ("feature_engineering", "scripts/feature_engineering.py"),
    ("modeling", "scripts/modeling.py"),
    ("merge_external", "scripts/merge_external.py"),
    ("modeling_city", "scripts/modeling_city.py"),
    ("analysis", "scripts/analysis.py"),
]


def run(stage: str, script: str) -> None:
    print(f"\n=== {stage} ===")
    result = subprocess.run([sys.executable, script], cwd=ROOT)
    if result.returncode != 0:
        raise SystemExit(f"stage {stage} failed with exit {result.returncode}")


def main() -> None:
    for stage, script in STAGES:
        run(stage, script)


if __name__ == "__main__":
    main()
