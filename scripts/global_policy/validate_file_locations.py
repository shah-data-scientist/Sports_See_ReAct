"""
FILE: validate_file_locations.py
STATUS: Active
RESPONSIBILITY: Validates files are in correct locations per GLOBAL_POLICY.md
LAST MAJOR UPDATE: 2026-02-15
MAINTAINER: Global Policy Enforcement
"""
import subprocess
import sys
from pathlib import Path


def get_staged_files():
    try:
        result = subprocess.run(["git", "diff", "--cached", "--name-only"], capture_output=True, text=True, check=True)
        return [Path(f) for f in result.stdout.strip().split('\n') if f]
    except subprocess.CalledProcessError:
        return []


if __name__ == "__main__":
    staged = get_staged_files()
    issues = []
    
    for f in staged:
        # Check for misplaced files
        if f.name.endswith('.md') and f.parent == Path('.') and f.name not in ['README.md', 'CHANGELOG.md', 'PROJECT_MEMORY.md']:
            issues.append(f"Markdown file in root (should be in docs/): {f}")
        if f.suffix == '.py' and f.parent == Path('.') and not f.name.startswith('_'):
            issues.append(f"Script in root (should be in scripts/): {f}")
    
    if issues:
        print("❌ FILE LOCATION VIOLATIONS\n")
        for issue in issues:
            print(f"  - {issue}")
        sys.exit(1)
    
    print("✓ All files in correct locations")
    sys.exit(0)
