"""
FILE: validate_changed_files.py
STATUS: Active
RESPONSIBILITY: Validates Python file documentation headers and comment hygiene
LAST MAJOR UPDATE: 2026-02-06
MAINTAINER: Shahu
"""

import ast
import re
import subprocess
import sys
from pathlib import Path

# Required header fields
REQUIRED_FIELDS = ["FILE:", "STATUS:", "RESPONSIBILITY:", "LAST MAJOR UPDATE:", "MAINTAINER:"]
VALID_STATUSES = ["Active", "Deprecated", "Experimental"]

# Directories to scan
SCAN_DIRS = ["src", "scripts", "tests"]
EXCLUDE_DIRS = {"_archived", "global_policy", "__pycache__", ".venv", "venv"}

# Comment hygiene patterns
CODE_PATTERNS = re.compile(
    r"^\s*#\s*(def |class |import |from |if |for |while |return |raise |try:|except |with )"
)
TODO_PATTERN = re.compile(r"#\s*(TODO|FIXME)(?!\()")
TODO_VALID_PATTERN = re.compile(r"#\s*(TODO|FIXME)\(\S+\)")
STALE_COMMENT_WORDS = ["old", "previous", "used to", "was previously", "before refactor"]


def get_staged_files() -> list[Path]:
    """Get list of staged Python files from git."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True,
        text=True,
    )
    files = []
    for line in result.stdout.strip().split("\n"):
        if line.strip() and line.endswith(".py"):
            path = Path(line.strip())
            if path.exists():
                files.append(path)
    return files


def get_all_python_files() -> list[Path]:
    """Get all Python files in scan directories."""
    root = Path(".")
    files = []
    for scan_dir in SCAN_DIRS:
        dir_path = root / scan_dir
        if dir_path.exists():
            for py_file in dir_path.rglob("*.py"):
                if not any(part in EXCLUDE_DIRS for part in py_file.parts):
                    files.append(py_file)
    return files


def validate_header(filepath: Path) -> list[str]:
    """Validate documentation header of a Python file.

    Args:
        filepath: Path to the Python file

    Returns:
        List of error messages (empty if valid)
    """
    errors = []

    # Skip __init__.py files
    if filepath.name == "__init__.py":
        return errors

    content = filepath.read_text(encoding="utf-8", errors="replace")

    # Check for module docstring
    try:
        tree = ast.parse(content)
        docstring = ast.get_docstring(tree)
    except SyntaxError:
        errors.append(f"  Syntax error - cannot parse file")
        return errors

    if not docstring:
        errors.append(f"  Missing module docstring with documentation header")
        return errors

    # Check required fields
    for field in REQUIRED_FIELDS:
        if field not in docstring:
            errors.append(f"  Missing required field: {field}")

    # Validate FILE field matches filename
    file_match = re.search(r"FILE:\s*(.+)", docstring)
    if file_match:
        file_value = file_match.group(1).strip()
        if file_value != filepath.name:
            errors.append(f"  FILE field '{file_value}' doesn't match filename '{filepath.name}'")

    # Validate STATUS field
    status_match = re.search(r"STATUS:\s*(.+)", docstring)
    if status_match:
        status_value = status_match.group(1).strip()
        if status_value not in VALID_STATUSES:
            errors.append(
                f"  STATUS '{status_value}' invalid (must be {', '.join(VALID_STATUSES)})"
            )

    # Validate RESPONSIBILITY length
    resp_match = re.search(r"RESPONSIBILITY:\s*(.+)", docstring)
    if resp_match:
        resp_value = resp_match.group(1).strip()
        if len(resp_value) > 200:
            errors.append(f"  RESPONSIBILITY too long ({len(resp_value)} chars, max 200)")

    # Validate LAST MAJOR UPDATE format
    date_match = re.search(r"LAST MAJOR UPDATE:\s*(.+)", docstring)
    if date_match:
        date_value = date_match.group(1).strip()
        if not re.match(r"\d{4}-\d{2}-\d{2}", date_value):
            errors.append(f"  LAST MAJOR UPDATE '{date_value}' not in YYYY-MM-DD format")

    return errors


def validate_comments(filepath: Path) -> list[str]:
    """Validate comment hygiene in a Python file.

    Args:
        filepath: Path to the Python file

    Returns:
        List of error/warning messages
    """
    errors = []

    try:
        lines = filepath.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return errors

    # Check for commented-out code blocks (3+ consecutive)
    consecutive_comments = 0
    code_comment_start = 0

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("#") and CODE_PATTERNS.match(stripped):
            if consecutive_comments == 0:
                code_comment_start = i
            consecutive_comments += 1
        else:
            if consecutive_comments >= 3:
                errors.append(
                    f"  Line {code_comment_start}-{i - 1}: Commented-out code block "
                    f"({consecutive_comments} lines) - use git history instead"
                )
            consecutive_comments = 0

    if consecutive_comments >= 3:
        errors.append(
            f"  Line {code_comment_start}-{len(lines)}: Commented-out code block "
            f"({consecutive_comments} lines) - use git history instead"
        )

    # Check for TODO/FIXME without dates
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if TODO_PATTERN.search(stripped) and not TODO_VALID_PATTERN.search(stripped):
            errors.append(f"  Line {i}: TODO/FIXME without date/name: {stripped[:80]}")

    return errors


def main():
    """Run validation on Python files."""
    staged_only = "--staged-only" in sys.argv

    if staged_only:
        files = get_staged_files()
        mode = "staged"
    else:
        files = get_all_python_files()
        mode = "all"

    if not files:
        print(f"No {mode} Python files to validate.")
        sys.exit(0)

    print(f"Validating {len(files)} {mode} Python file(s)...")
    print()

    total_errors = 0
    files_with_errors = 0

    for filepath in sorted(files):
        header_errors = validate_header(filepath)
        comment_errors = validate_comments(filepath)
        all_errors = header_errors + comment_errors

        if all_errors:
            files_with_errors += 1
            total_errors += len(all_errors)
            print(f"FAIL {filepath}")
            for error in all_errors:
                print(error)
            print()

    if total_errors > 0:
        print(f"{'=' * 60}")
        print(f"FAILED: {total_errors} error(s) in {files_with_errors} file(s)")
        print(f"{'=' * 60}")
        sys.exit(1)
    else:
        print(f"PASSED: All {len(files)} file(s) valid")
        sys.exit(0)


if __name__ == "__main__":
    main()
