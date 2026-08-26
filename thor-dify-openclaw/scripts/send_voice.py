#!/usr/bin/env python3
"""Simulate Reachy or K10 voice ingress on Thor (after local ASR)."""

from __future__ import annotations

import json
import os
import sys
import urllib.request

# Reuse the Hermes CLI parser / POST.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "hermes-skill", "ask_dify_dispatch", "scripts"))
from ask_dify import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
