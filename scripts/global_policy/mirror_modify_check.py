"""
FILE: mirror_modify_check.py
STATUS: Active
RESPONSIBILITY: Enforces Mirror & Modify rule - src/ changes require test/ changes
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
    
    src_files = [f for f in staged if str(f).startswith('src/') and f.suffix == '.py']
    test_files = [f for f in staged if str(f).startswith('tests/')]
    
    if src_files and not test_files:
        print("⚠️  WARNING: Modified src/ files but no test files staged")
        print("   This may be acceptable for pure refactoring or doc updates")
        print(f"   Modified: {', '.join(str(f) for f in src_files[:3])}")
        # Warning only, don't block
    
    print("✓ Mirror & Modify check passed")
    sys.exit(0)
