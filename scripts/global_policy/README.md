# Global Policy Enforcement Scripts

This directory contains enforcement scripts for [GLOBAL_POLICY.md](C:\Users\shahu\Documents\coding_agent_policies\GLOBAL_POLICY.md).

## Scripts Overview

### 1. `validate_headers.py` ⭐ CRITICAL
**Purpose:** Validates and auto-fixes file headers and comment hygiene

**Checks:**
- File headers (FILE, STATUS, RESPONSIBILITY, LAST MAJOR UPDATE, MAINTAINER)
- Comment hygiene (TODOs with dates, no commented-out code blocks)
- Comment accuracy after code changes

**Usage:**
```bash
poetry run python scripts/global_policy/validate_headers.py              # Check all
poetry run python scripts/global_policy/validate_headers.py --fix        # Auto-fix
poetry run python scripts/global_policy/validate_headers.py --staged-only  # Pre-commit
```

### 2. `check_clean_working_directory.py` ⭐ CRITICAL
**Purpose:** Prevents committing ignored files, test/debug files, runtime artifacts

**Checks:**
- Files matching .gitignore patterns
- Test/debug files (_*.py, test_*.py outside tests/)
- Runtime artifacts (*.db, *.log, .coverage)
- Timestamped evaluation results

**Usage:** Runs automatically via pre-commit hook (MUST BE FIRST HOOK)

### 3. `validate_file_locations.py`
**Purpose:** Ensures files are in correct directories

**Checks:**
- Markdown files in root (only README.md, CHANGELOG.md, PROJECT_MEMORY.md allowed)
- Scripts in root (should be in scripts/)

### 4. `mirror_modify_check.py`
**Purpose:** Enforces Mirror & Modify rule

**Checks:**
- src/ modifications should have corresponding tests/ modifications
- Warnings only (doesn't block)

### 5. `check_coverage_thresholds.py`
**Purpose:** Validates coverage meets tier-based thresholds

**Configuration:** `coverage_thresholds.toml` in project root

### 6. `check_orphaned_files.py`
**Purpose:** Detects orphaned files

**Checks:**
- Unused scripts
- Old files without tests
- Warning only (doesn't block)

## Pre-Commit Hook Setup

1. **Install pre-commit:**
   ```bash
   pip install pre-commit
   pre-commit install
   ```

2. **Configuration:** Already set up in `.pre-commit-config.yaml`

3. **Hook execution order:**
   1. ✅ check-clean-working-directory (MUST BE FIRST)
   2. ✅ validate-headers (auto-fixes)
   3. ✅ validate-file-locations
   4. ⚠️  mirror-modify-check (warning)
   5. ✅ check-coverage-thresholds
   6. ⚠️  check-orphaned-files (warning)

## Coverage Configuration

**File:** `coverage_thresholds.toml` in project root

**Tiers:**
- **Tier 1** (≥90%): src/services/, src/core/, src/models/, src/api/, src/tools/
- **Tier 2** (≥70%): src/pipeline/, src/evaluation/[models, validator].py, src/utils/
- **Tier 3** (≥50%): src/ui/, src/evaluation/[evaluator, analyzer, metrics, test_data].py, scripts/
- **Overall** (≥80%): Total project coverage

## Critical Rules

### ⚠️ NEVER:
1. **Use `--no-verify`** to skip pre-commit hooks (FORBIDDEN)
2. **Use `git stash`** without explicit user permission
3. **Commit ignored files** (*.db, *.log, _*.py, test_*.py in root)
4. **Replace PROJECT_MEMORY.md** (APPEND ONLY)

### ✅ ALWAYS:
1. **Run validation before commits**
2. **Fix header issues** with `--fix` flag
3. **Archive obsolete files** to `_archived/YYYY-MM/`
4. **Update CHANGELOG.md** with code changes

## Quick Checklist Before Commit

- [ ] All tests pass
- [ ] Coverage meets tier thresholds
- [ ] File headers complete
- [ ] Comments updated with code changes
- [ ] Files in correct locations
- [ ] .gitignore updated if needed
- [ ] Working directory clean

## References

- **GLOBAL_POLICY.md:** Main policy document
- **Pre-commit config:** `.pre-commit-config.yaml`
- **Coverage config:** `coverage_thresholds.toml`
- **.gitignore:** Mandatory exclusion patterns

