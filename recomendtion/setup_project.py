from pathlib import Path

ROOT = Path("app")

folders = [
    "api",
    "core",
    "database",
    "models",
    "repositories",
    "schemas",
    "services",
    "utils"
]

files = [
    "__init__.py"
]

for folder in folders:
    folder_path = ROOT / folder
    folder_path.mkdir(parents=True, exist_ok=True)

    for file in files:
        (folder_path / file).touch(exist_ok=True)

print("✅ Project structure created successfully!")