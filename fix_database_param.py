#!/usr/bin/env python3
import os
import pathlib

# Replace dbname= with dbname= in all Python files
for py_file in pathlib.Path(".").rglob("*.py"):
    if ".venv" in str(py_file):
        continue
    
    try:
        content = py_file.read_text(encoding='utf-8')
        if 'dbname=' in content:
            new_content = content.replace('dbname=', 'dbname=')
            py_file.write_text(new_content, encoding='utf-8')
            print(f"Fixed: {py_file}")
    except Exception as e:
        print(f"Error processing {py_file}: {e}")

print("Done!")
