import sys
import re
from pathlib import Path

def bump_version(part):
    toml_path = Path("pyproject.toml")
    if not toml_path.exists():
        print("Error: pyproject.toml not found")
        sys.exit(1)
    
    content = toml_path.read_text(encoding="utf-8")
    
    # Match version = "x.y.z"
    version_match = re.search(r'version\s*=\s*"([^"]+)"', content)
    if not version_match:
        print("Error: Could not find version in pyproject.toml")
        sys.exit(1)
    
    current_version = version_match.group(1)
    try:
        major, minor, patch = map(int, current_version.split('.'))
    except ValueError:
        print(f"Error: Current version '{current_version}' is not in x.y.z format")
        sys.exit(1)
    
    if part == "major":
        major += 1
        minor = 0
        patch = 0
    elif part == "minor":
        minor += 1
        patch = 0
    elif part == "patch":
        patch += 1
    else:
        print(f"Error: Unknown version part '{part}'. Use major, minor, or patch.")
        sys.exit(1)
    
    new_version = f"{major}.{minor}.{patch}"
    # Use count=1 to only replace the first occurrence (project version)
    new_content = re.sub(r'(^version\s*=\s*")([^"]+)(")', rf'\g<1>{new_version}\g<3>', content, flags=re.MULTILINE, count=1)
    
    toml_path.write_text(new_content, encoding="utf-8")
    print(f"Version bumped from {current_version} to {new_version}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python bump_version.py [major|minor|patch]")
        sys.exit(1)
    bump_version(sys.argv[1].lower())
