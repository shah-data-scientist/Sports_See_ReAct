"""
FILE: check_clean_working_directory.py
STATUS: Active
RESPONSIBILITY: Prevents committing ignored files, test/debug files, and runtime artifacts
LAST MAJOR UPDATE: 2026-02-15
MAINTAINER: Global Policy Enforcement
"""
import re
import subprocess
import sys
from pathlib import Path


def get_staged_files():
    """Get list of files staged for commit."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            check=True
        )
        return [f for f in result.stdout.strip().split('\n') if f]
    except subprocess.CalledProcessError:
        return []


def is_ignored_by_git(file_path):
    """Check if file matches .gitignore patterns."""
    try:
        result = subprocess.run(
            ["git", "check-ignore", file_path],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except subprocess.CalledProcessError:
        return False


def check_patterns(file_path):
    """Check if file matches problematic patterns."""
    path = Path(file_path)
    
    # Skip valid test files
    if 'tests/' in file_path and path.name.startswith('test_'):
        return False, ""
    
    # Check patterns
    if path.name.startswith('_') and path.suffix == '.py':
        return True, f"Temp file: {file_path}"
    if path.name.startswith('test_') and 'tests/' not in file_path:
        return True, f"Test file outside tests/: {file_path}"
    if path.suffix in ['.db', '.log'] or path.name == '.coverage':
        return True, f"Runtime artifact: {file_path}"
    if re.search(r'_\d{8}.*\.json$', path.name):
        return True, f"Timestamped file: {file_path}"
    
    return False, ""


if __name__ == "__main__":
    staged_files = get_staged_files()
    if not staged_files:
        print("✓ No files staged")
        sys.exit(0)
    
    issues = []
    for f in staged_files:
        if is_ignored_by_git(f):
            issues.append(f"Ignored file staged: {f}")
        else:
            has_issue, msg = check_patterns(f)
            if has_issue:
                issues.append(msg)
    
    if issues:
        print("\n❌ CLEAN WORKING DIRECTORY CHECK FAILED\n")
        for issue in issues:
            print(f"  - {issue}")
        print("\nUnstage these files: git reset HEAD <file>\n")
        sys.exit(1)
    
    print(f"✓ All {len(staged_files)} staged files are clean")
    sys.exit(0)
