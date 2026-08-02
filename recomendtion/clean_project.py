from pathlib import Path
import shutil


for folder in Path(".").rglob("__pycache__"):
    shutil.rmtree(folder)
    print(f"Deleted: {folder}")


for file in Path(".").rglob("*.pyc"):
    file.unlink()
    print(f"Deleted: {file}")

print("\n✅ Project cleaned successfully!")