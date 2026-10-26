#!/usr/bin/env python3
"""Compatibility entrypoint: readiness is now computed by the real runtime."""
from datetime import datetime, timezone
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.forecasting.runtime import run


def main():
    run(Path(__file__).resolve().parents[1], datetime.now(timezone.utc))


if __name__ == '__main__':
    main()
