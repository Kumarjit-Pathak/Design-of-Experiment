#!/usr/bin/env python3
"""
Script to fix Streamlit deprecation warnings by replacing use_container_width with width parameter.
"""

import os
import re
from pathlib import Path

def fix_use_container_width(file_path):
    """Fix use_container_width deprecation warnings in a file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Track if changes were made
    original_content = content
    
    # Replace use_container_width=True with width="stretch"
    content = re.sub(r'use_container_width=True', 'width="stretch"', content)
    
    # Replace use_container_width=False with width="content" (if any exist)
    content = re.sub(r'use_container_width=False', 'width="content"', content)
    
    # Handle multiline cases where use_container_width is on its own line
    content = re.sub(r',\s*use_container_width=True', ', width="stretch"', content)
    content = re.sub(r',\s*use_container_width=False', ', width="content"', content)
    
    # Write back if changes were made
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Fixed {file_path}")
        return True
    return False

def main():
    """Main function to fix all Python files in the project."""
    project_root = Path("DOE_Simulator")
    
    if not project_root.exists():
        print("DOE_Simulator directory not found!")
        return
    
    # Find all Python files
    python_files = list(project_root.rglob("*.py"))
    
    print(f"Found {len(python_files)} Python files to check...")
    
    fixed_count = 0
    for file_path in python_files:
        if fix_use_container_width(file_path):
            fixed_count += 1
    
    print(f"\n🎉 Fixed {fixed_count} files!")
    print("Deprecation warnings should now be resolved.")

if __name__ == "__main__":
    main()