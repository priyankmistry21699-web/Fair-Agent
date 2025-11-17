#!/usr/bin/env python3
"""
Django management script for FAIR-Agent Web Application
"""
import os
import sys
from pathlib import Path
import io

# === FIX FOR WINDOWS UNICODE ENCODING ERRORS ===
# Set UTF-8 mode for Python (must be done before other imports)
os.environ['PYTHONUTF8'] = '1'

# Force UTF-8 encoding for stdout/stderr to handle emoji in logs
try:
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, 
            encoding='utf-8', 
            errors='replace', 
            line_buffering=True
        )
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(
            sys.stderr.buffer, 
            encoding='utf-8', 
            errors='replace', 
            line_buffering=True
        )
except (AttributeError, io.UnsupportedOperation):
    # If stdout/stderr don't have buffer attribute or can't be wrapped, continue anyway
    pass
# === END FIX ===

if __name__ == '__main__':
    # Add the parent directory to Python path
    current_dir = Path(__file__).resolve().parent
    parent_dir = current_dir.parent
    sys.path.append(str(parent_dir))
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)