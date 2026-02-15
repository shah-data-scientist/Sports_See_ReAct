"""
FILE: validate_headers.py
STATUS: Active
RESPONSIBILITY: Validates and auto-fixes file headers and comments per GLOBAL_POLICY.md
LAST MAJOR UPDATE: 2026-02-15
MAINTAINER: Global Policy Enforcement

Validates:
1. File headers (FILE, STATUS, RESPONSIBILITY, LAST MAJOR UPDATE, MAINTAINER)
2. Comment hygiene (TODOs with dates, no commented-out code blocks)
3. Comment accuracy after code changes

Usage:
    python scripts/global_policy/validate_headers.py              # Check all files
    python scripts/global_policy/validate_headers.py --fix        # Auto-fix issues
    python scripts/global_policy/validate_headers.py --staged-only  # Pre-commit hook mode
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path
from datetime import datetime


def get_staged_python_files() -> list[Path]:
    """Get list of staged Python files."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            capture_output=True,
            text=True,
            check=True
        )
        files = [
            Path(f) for f in result.stdout.strip().split('\n')
            if f and f.endswith('.py') and not f.endswith('__init__.py')
        ]
        return files
    except subprocess.CalledProcessError:
        return []


def get_all_python_files(root_dir: Path) -> list[Path]:
    """Get all Python files in src/, tests/, scripts/ excluding __init__.py"""
    patterns = ["src/**/*.py", "tests/**/*.py", "scripts/**/*.py"]
    files = []
    for pattern in patterns:
        files.extend([
            f for f in root_dir.glob(pattern)
            if f.name != '__init__.py'
        ])
    return files


def validate_header(file_path: Path, content: str) -> tuple[bool, list[str]]:
    """Validate file has correct header format."""
    issues = []

    # Check if file starts with docstring
    if not content.strip().startswith('"""'):
        issues.append("Missing file docstring header")
        return False, issues

    # Extract first docstring
    docstring_match = re.match(r'"""(.*?)"""', content, re.DOTALL)
    if not docstring_match:
        issues.append("Malformed docstring")
        return False, issues

    header = docstring_match.group(1)

    # Required fields
    required_fields = {
        "FILE:": file_path.name,
        "STATUS:": ["Active", "Deprecated", "Experimental"],
        "RESPONSIBILITY:": None,  # Any value OK
        "LAST MAJOR UPDATE:": r'\d{4}-\d{2}-\d{2}',  # Date format
        "MAINTAINER:": None  # Any value OK
    }

    for field, expected in required_fields.items():
        if field not in header:
            issues.append(f"Missing required field: {field}")
        elif field == "FILE:" and file_path.name not in header:
            issues.append(f"{field} should be '{file_path.name}'")
        elif field == "STATUS:" and isinstance(expected, list):
            if not any(status in header for status in expected):
                issues.append(f"{field} must be one of {expected}")
        elif field == "LAST MAJOR UPDATE:" and expected:
            if not re.search(expected, header):
                issues.append(f"{field} must be in YYYY-MM-DD format")

    return len(issues) == 0, issues


def validate_comments(content: str) -> tuple[bool, list[str]]:
    """Validate comment hygiene."""
    issues = []
    lines = content.split('\n')

    # Check for commented-out code blocks (3+ consecutive commented lines)
    consecutive_comments = 0
    block_start = 0

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('#') and not stripped.startswith('# '):
            # Likely commented-out code (no space after #)
            if consecutive_comments == 0:
                block_start = i + 1
            consecutive_comments += 1
        else:
            if consecutive_comments >= 3:
                issues.append(f"Commented-out code block found at lines {block_start}-{block_start + consecutive_comments - 1}")
            consecutive_comments = 0

    # Check final block
    if consecutive_comments >= 3:
        issues.append(f"Commented-out code block found at lines {block_start}-{len(lines)}")

    # Check for TODO/FIXME without dates
    for i, line in enumerate(lines):
        if re.search(r'#\s*(TODO|FIXME)', line, re.IGNORECASE):
            if not re.search(r'\d{4}-\d{2}-\d{2}', line):
                issues.append(f"TODO/FIXME without date at line {i + 1}: {line.strip()}")

    return len(issues) == 0, issues


def generate_header(file_path: Path, content: str) -> str:
    """Generate a basic header for files missing one."""
    # Try to extract a description from the first comment or class/function
    responsibility = "TODO: Add description"

    # Look for first function/class docstring
    func_match = re.search(r'def\s+\w+.*?:\s*"""(.*?)"""', content, re.DOTALL)
    class_match = re.search(r'class\s+\w+.*?:\s*"""(.*?)"""', content, re.DOTALL)

    if func_match:
        responsibility = func_match.group(1).strip().split('\n')[0][:100]
    elif class_match:
        responsibility = class_match.group(1).strip().split('\n')[0][:100]

    header = f'''"""
FILE: {file_path.name}
STATUS: Active
RESPONSIBILITY: {responsibility}
LAST MAJOR UPDATE: {datetime.now().strftime('%Y-%m-%d')}
MAINTAINER: Shahu
"""
'''
    return header


def fix_header(file_path: Path, content: str) -> str:
    """Fix or add file header."""
    # If no header, add one
    if not content.strip().startswith('"""'):
        header = generate_header(file_path, content)
        return header + '\n' + content

    # If header exists but incomplete, try to fix it
    docstring_match = re.match(r'(""".*?""")', content, re.DOTALL)
    if not docstring_match:
        return content

    old_header = docstring_match.group(1)
    new_header = generate_header(file_path, content)

    return content.replace(old_header, new_header, 1)


def main():
    parser = argparse.ArgumentParser(description="Validate file headers and comments")
    parser.add_argument("--fix", action="store_true", help="Auto-fix issues")
    parser.add_argument("--staged-only", action="store_true", help="Only check staged files (pre-commit mode)")
    args = parser.parse_args()

    root_dir = Path.cwd()

    # Get files to check
    if args.staged_only:
        files = get_staged_python_files()
        if not files:
            print("✓ No Python files staged for commit")
            sys.exit(0)
    else:
        files = get_all_python_files(root_dir)

    print(f"Checking {len(files)} Python files...")

    issues_found = []
    files_fixed = []

    for file_path in files:
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception as e:
            print(f"✗ Error reading {file_path}: {e}")
            continue

        # Validate header
        header_valid, header_issues = validate_header(file_path, content)

        # Validate comments
        comments_valid, comment_issues = validate_comments(content)

        if not header_valid or not comments_valid:
            all_issues = header_issues + comment_issues
            issues_found.append((file_path, all_issues))

            if args.fix:
                # Try to fix header issues
                if not header_valid:
                    fixed_content = fix_header(file_path, content)
                    file_path.write_text(fixed_content, encoding='utf-8')
                    files_fixed.append(file_path)
                    print(f"✓ Fixed header in {file_path}")
                else:
                    print(f"✗ {file_path}: {', '.join(all_issues)}")
            else:
                print(f"✗ {file_path}:")
                for issue in all_issues:
                    print(f"  - {issue}")

    # Summary
    print(f"\n{'=' * 80}")
    if not issues_found:
        print("✓ All files pass validation!")
        sys.exit(0)
    else:
        print(f"Found issues in {len(issues_found)} files")
        if args.fix:
            print(f"Fixed {len(files_fixed)} files")
            if len(files_fixed) < len(issues_found):
                print(f"\n⚠️  {len(issues_found) - len(files_fixed)} files require manual attention")
                sys.exit(1)
            else:
                print("✓ All issues fixed!")
                sys.exit(0)
        else:
            print("\nRun with --fix to auto-fix header issues")
            sys.exit(1)


if __name__ == "__main__":
    main()
