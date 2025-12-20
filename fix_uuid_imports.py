#!/usr/bin/env python3
"""
Script to fix UUID import issues in SQLAlchemy models.
This script:
1. Adds UUID import from sqlalchemy.dialects.postgresql if UUID is used but not imported
2. Fixes server_default=func.now() to default=uuid4 for UUID primary keys (SQLite compatibility)
"""

import os
import re
from pathlib import Path

def fix_uuid_imports(file_path: str) -> bool:
    """
    Fix UUID imports and usage in a Python file.
    Returns True if file was modified, False otherwise.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}")
        return False
    
    original_content = content
    modified = False
    
    # Check if file uses UUID
    uses_uuid = re.search(r'\bUUID\(', content) or re.search(r':\s*Mapped\[UUID\]', content)
    
    if not uses_uuid:
        return False
    
    # Check if UUID is already imported
    has_uuid_import = re.search(r'from\s+sqlalchemy\.dialects\.postgresql\s+import\s+UUID', content)
    has_uuid_from_typing = re.search(r'from\s+typing\s+import.*\bUUID\b', content)
    
    # Check if uuid4 is imported
    has_uuid4_import = re.search(r'from\s+uuid\s+import.*\buuid4\b', content)
    
    # 1. Add UUID import if needed
    if not has_uuid_import:
        # Find the sqlalchemy import block
        sqlalchemy_import_pattern = r'(from\s+sqlalchemy\s+import\s*\([^)]*\))'
        sqlalchemy_import_match = re.search(sqlalchemy_import_pattern, content, re.MULTILINE | re.DOTALL)
        
        if sqlalchemy_import_match:
            # Add UUID import after sqlalchemy imports
            sqlalchemy_import_end = sqlalchemy_import_match.end()
            # Find the end of the import block (closing parenthesis and newline)
            next_line = content.find('\n', sqlalchemy_import_end)
            if next_line != -1:
                content = content[:next_line+1] + 'from sqlalchemy.dialects.postgresql import UUID\n' + content[next_line+1:]
                modified = True
        else:
            # If no sqlalchemy import block, add after other imports
            # Find the last import statement
            import_pattern = r'^(from\s+\S+\s+import\s+.*|import\s+.*)$'
            imports = list(re.finditer(import_pattern, content, re.MULTILINE))
            if imports:
                last_import = imports[-1]
                insert_pos = content.find('\n', last_import.end())
                if insert_pos != -1:
                    content = content[:insert_pos+1] + 'from sqlalchemy.dialects.postgresql import UUID\n' + content[insert_pos+1:]
                    modified = True
    
    # 2. Add uuid4 import if UUID is used with default=uuid4 pattern
    if not has_uuid4_import and re.search(r'default\s*=\s*uuid4', content):
        # Find a good place to add the import (after other imports)
        import_pattern = r'^(from\s+\S+\s+import\s+.*|import\s+.*)$'
        imports = list(re.finditer(import_pattern, content, re.MULTILINE))
        if imports:
            last_import = imports[-1]
            insert_pos = content.find('\n', last_import.end())
            if insert_pos != -1:
                # Check if uuid import already exists
                if not re.search(r'from\s+uuid\s+import', content[:insert_pos]):
                    content = content[:insert_pos+1] + 'from uuid import uuid4\n' + content[insert_pos+1:]
                    modified = True
    
    # 3. Fix server_default=func.now() to default=uuid4 for UUID primary keys
    # Pattern: UUID primary key with server_default=func.now()
    uuid_primary_key_pattern = r'(\w+_id):\s*Mapped\[UUID\]\s*=\s*mapped_column\(UUID\(as_uuid=True\),\s*primary_key=True,\s*\)server_default=func\.now\(\)'
    
    def replace_uuid_default(match):
        field_name = match.group(1)
        return f'{field_name}: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)'
    
    new_content = re.sub(uuid_primary_key_pattern, replace_uuid_default, content)
    if new_content != content:
        content = new_content
        modified = True
    
    # Write back if modified
    if modified and content != original_content:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed: {file_path}")
            return True
        except Exception as e:
            print(f"❌ Error writing {file_path}: {e}")
            return False
    
    return False

def main():
    """Main function to fix UUID imports in all Python files."""
    print("🔧 Starting UUID import fixes...")
    print("")
    
    # Find all Python files in src directory
    src_dir = Path("src")
    if not src_dir.exists():
        print("❌ src directory not found!")
        return
    
    python_files = list(src_dir.rglob("*.py"))
    fixed_count = 0
    
    for file_path in python_files:
        # Skip __pycache__ and __init__.py files
        if "__pycache__" in str(file_path) or file_path.name == "__init__.py":
            continue
        
        if fix_uuid_imports(str(file_path)):
            fixed_count += 1
    
    print("")
    print(f"✅ Fixed {fixed_count} file(s)")
    print("🎉 UUID import fixes completed!")

if __name__ == "__main__":
    main()

