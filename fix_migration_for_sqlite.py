#!/usr/bin/env python3
"""
Script to fix migration files for SQLite compatibility.
This script:
1. Removes CheckConstraints with regex operator (~) which SQLite doesn't support
2. Fixes autoincrement issues in composite primary keys
"""

import os
import re
from pathlib import Path

def fix_migration_file(file_path: str) -> bool:
    """
    Fix migration file for SQLite compatibility.
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
    
    # 1. Remove CheckConstraints with regex operator (~) which SQLite doesn't support
    # Pattern: sa.CheckConstraint("... ~ ...", name='...')
    check_constraint_pattern = r'sa\.CheckConstraint\([^)]*~[^)]*\),?\s*\n'
    new_content = re.sub(check_constraint_pattern, '', content)
    if new_content != content:
        content = new_content
        modified = True
        print(f"  ✓ Removed CheckConstraints with regex operator")
    
    # 2. Fix autoincrement in composite primary keys
    # Pattern: sa.Column('..._id', sa.Integer(), nullable=False, autoincrement=True) in composite primary keys
    # This is more complex - we need to check if it's part of a composite primary key
    # For now, let's just remove autoincrement from any column that might be in a composite key
    # (This is a simplified approach - you might need to adjust based on your schema)
    
    # Remove autoincrement from columns that are likely part of composite keys
    # (e.g., translation tables with composite primary keys)
    autoincrement_pattern = r"(sa\.Column\('[^']+_id',\s*sa\.(Integer|BigInteger)\(\)[^,)]*),\s*autoincrement=True\)"
    new_content = re.sub(autoincrement_pattern, r'\1)', content)
    if new_content != content:
        content = new_content
        modified = True
        print(f"  ✓ Fixed autoincrement in composite primary keys")
    
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
    """Main function to fix migration files for SQLite compatibility."""
    print("🔧 Starting migration file fixes for SQLite...")
    print("")
    
    # Find all migration files
    migrations_dir = Path("migrations/versions")
    if not migrations_dir.exists():
        print("❌ migrations/versions directory not found!")
        return
    
    migration_files = list(migrations_dir.glob("*.py"))
    if not migration_files:
        print("⚠️  No migration files found!")
        return
    
    fixed_count = 0
    
    for file_path in migration_files:
        # Skip __pycache__ and __init__.py files
        if "__pycache__" in str(file_path) or file_path.name == "__init__.py":
            continue
        
        print(f"📄 Checking: {file_path.name}")
        if fix_migration_file(str(file_path)):
            fixed_count += 1
        else:
            print(f"  ✓ No changes needed")
        print("")
    
    print(f"✅ Fixed {fixed_count} migration file(s)")
    print("🎉 Migration file fixes completed!")

if __name__ == "__main__":
    main()

