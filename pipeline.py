#!/usr/bin/env python3
"""Cohesive GTM pipeline entry point (alias for run_all.py)."""
import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).resolve().parent / "run_all.py"), run_name="__main__")
