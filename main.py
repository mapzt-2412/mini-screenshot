#!/usr/bin/env python3
"""Thin CLI entry — delegates to ``mini_screenshot.cli``."""

from mini_screenshot.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
