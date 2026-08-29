#!/usr/bin/env python3
"""Simulate Reachy or K10 voice ingress after local ASR."""

from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from ask_dify import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
