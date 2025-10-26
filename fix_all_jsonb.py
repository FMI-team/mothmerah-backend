#!/usr/bin/env python3
import os
import re
from pathlib import Path

def fix_file(filepath):
    """Fix JSONB references in a Python file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Fix imports - remove postgresql JSONB imports
    content = re.sub(
        r'from sqlalchemy\.dialects\.postgresql import.*\n',
        '',
        content
    )
    content = re.sub(
        r'from sqlalchemy\.dialects import postgresql.*\n',
        '',
        content
    )
    
    # Add JSON import if JSONB was used and JSON isn't imported
    if 'JSONB' in original_content and 'from sqlalchemy import' in content:
        # Add JSON to existing sqlalchemy import
        content = re.sub(
            r'from sqlalchemy import (.*)',
            lambda m: f"from sqlalchemy import {m.group(1)}, JSON" if 'JSON' not in m.group(1) else m.group(0),
            content
        )
    elif 'JSONB' in original_content and 'from sqlalchemy import' not in content:
        # Add new import line
        content = 'from sqlalchemy import JSON\n' + content
    
    # Replace JSONB with JSON
    content = re.sub(r'postgresql\.JSONB\([^)]*\)', 'JSON()', content)
    content = re.sub(r'JSONB\(\)', 'JSON()', content)
    content = re.sub(r'\bJSONB\b', 'JSON', content)
    
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

# Find and fix all Python files in src
fixed_files = []
for py_file in Path('src').rglob('*.py'):
    if fix_file(py_file):
        fixed_files.append(py_file)
        print(f"✓ Fixed: {py_file}")

if fixed_files:
    print(f"\n✅ Fixed {len(fixed_files)} files!")
    print("\nNow delete old migration and create new one:")
    print("  rm migrations/versions/*.py")
    print("  alembic revision --autogenerate -m 'Initial migration'")
    print("  alembic upgrade head")
else:
    print("No files needed fixing!")