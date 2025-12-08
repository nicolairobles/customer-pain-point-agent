#!/usr/bin/env python3
"""Diagnostic: print sys.path[0] and CWD to demonstrate import behavior."""
import sys
import os
import pathlib

print("cwd:", os.getcwd())
print("sys.path[0]:", repr(sys.path[0]))
sp0 = sys.path[0] or os.getcwd()
print("sys.path[0] exists:", pathlib.Path(sp0).exists())
print("items in sys.path[0]:", [p.name for p in pathlib.Path(sp0).iterdir()] if pathlib.Path(sp0).exists() else [])