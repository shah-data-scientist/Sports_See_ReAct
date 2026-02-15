"""
FILE: audit_orchestrator.py
STATUS: Active
RESPONSIBILITY: Orchestrates comprehensive project audits following AUDIT_PROCEDURES.md
LAST MAJOR UPDATE: 2026-02-11
MAINTAINER: Shahu
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def run_security_audit() -> dict[str, Any]:
    """Run security audit module.

    Returns:
        Security audit results with score and findings
    """
    print("🔒 Module 1: Security & Compliance Audit")
    results = {"module": "security", "findings": [], "score": 0}

    # Run bandit
    try:
        bandit_result = subprocess.run(
            ["poetry", "run", "bandit", "-r", "src/", "-f", "json"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if bandit_result.stdout:
            bandit_data = json.loads(bandit_result.stdout)
            critical = len([i for i in bandit_data.get("results", []) if i["issue_severity"] == "HIGH"])
            high = len([i for i in bandit_data.get("results", []) if i["issue_severity"] == "MEDIUM"])
            medium = len([i for i in bandit_data.get("results", []) if i["issue_severity"] == "LOW"])

            results["findings"].append(
                {
                    "tool": "bandit",
                    "critical": critical,
                    "high": high,
                    "medium": medium,
                    "total": len(bandit_data.get("results", [])),
                }
            )
            # Calculate score: 100 - (critical×20 + high×10 + medium×5)
            results["score"] = max(0, 100 - (critical * 20 + high * 10 + medium * 5))
    except Exception as e:
        print(f"   ⚠️ Bandit scan failed: {e}")
        results["score"] = 50  # Partial score if tool fails

    # Run safety check
    try:
        safety_result = subprocess.run(
            ["poetry", "run", "safety", "check", "--json"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if safety_result.stdout and safety_result.stdout.strip():
            try:
                safety_data = json.loads(safety_result.stdout)
                vulnerabilities = len(safety_data)
                results["findings"].append({"tool": "safety", "vulnerabilities": vulnerabilities})
                # Reduce score if vulnerabilities found
                results["score"] = max(0, results["score"] - (vulnerabilities * 5))
            except json.JSONDecodeError:
                print("   ⚠️ Could not parse safety output")
    except Exception as e:
        print(f"   ⚠️ Safety check failed: {e}")

    status = "✅" if results["score"] >= 80 else "⚠️" if results["score"] >= 60 else "❌"
    print(f"   {status} Security Score: {results['score']}/100")
    return results


def run_testing_audit() -> dict[str, Any]:
    """Run testing & coverage audit module.

    Returns:
        Testing audit results with coverage and score
    """
    print("🧪 Module 5: Testing & Coverage Audit")
    results = {"module": "testing", "coverage": 0, "score": 0}

    # Run pytest with coverage
    try:
        pytest_result = subprocess.run(
            ["poetry", "run", "pytest", "tests/", "--cov=src", "--cov-report=json", "-q"],
            capture_output=True,
            text=True,
            timeout=300,
        )

        # Read coverage report
        coverage_file = Path("coverage.json")
        if coverage_file.exists():
            coverage_data = json.loads(coverage_file.read_text())
            total_coverage = coverage_data.get("totals", {}).get("percent_covered", 0)
            results["coverage"] = round(total_coverage, 2)
            results["score"] = int(total_coverage)

            # Get coverage by file
            files = coverage_data.get("files", {})
            low_coverage_files = [
                (path, data["summary"]["percent_covered"])
                for path, data in files.items()
                if data["summary"]["percent_covered"] < 70
            ]
            results["low_coverage_files"] = low_coverage_files[:5]  # Top 5

    except Exception as e:
        print(f"   ⚠️ Coverage analysis failed: {e}")
        results["score"] = 50  # Partial score

    status = "✅" if results["score"] >= 80 else "⚠️" if results["score"] >= 60 else "❌"
    print(f"   {status} Testing Score: {results['score']}/100 (Coverage: {results['coverage']}%)")
    return results


def run_documentation_audit() -> dict[str, Any]:
    """Run documentation audit module with duplication detection.

    Returns:
        Documentation audit results with duplication findings
    """
    print("📚 Module 4: Documentation Audit")
    results = {"module": "documentation", "files": 0, "duplicates": [], "score": 0}

    docs_dir = Path("docs")
    if not docs_dir.exists():
        print("   ⚠️ No docs/ directory found")
        return results

    # Count markdown files
    md_files = list(docs_dir.glob("*.md"))
    results["files"] = len(md_files)

    # Simple duplication check (content similarity)
    import difflib

    duplicates = []
    for i, file1 in enumerate(md_files):
        content1 = file1.read_text(encoding="utf-8", errors="ignore")
        for file2 in md_files[i + 1 :]:
            content2 = file2.read_text(encoding="utf-8", errors="ignore")
            similarity = difflib.SequenceMatcher(None, content1, content2).ratio()
            if similarity > 0.3:  # >30% similar
                duplicates.append(
                    {
                        "file1": file1.name,
                        "file2": file2.name,
                        "similarity": round(similarity * 100, 1),
                    }
                )

    results["duplicates"] = sorted(duplicates, key=lambda x: x["similarity"], reverse=True)

    # Calculate score based on organization and duplication
    high_duplication = len([d for d in duplicates if d["similarity"] > 70])
    results["score"] = max(0, 100 - (high_duplication * 15))

    status = "✅" if results["score"] >= 80 else "⚠️" if results["score"] >= 60 else "❌"
    print(f"   {status} Documentation Score: {results['score']}/100")
    print(f"   Found {results['files']} docs, {len(duplicates)} duplication pairs")
    return results


def run_dependency_audit() -> dict[str, Any]:
    """Run dependency audit module.

    Returns:
        Dependency audit results
    """
    print("📦 Module 7: Dependency & Configuration Audit")
    results = {"module": "dependencies", "outdated": [], "score": 100}

    # Check for outdated packages
    try:
        outdated_result = subprocess.run(
            ["poetry", "show", "--outdated"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        outdated_count = len(outdated_result.stdout.strip().split("\n")) if outdated_result.stdout.strip() else 0
        results["outdated_count"] = outdated_count
        results["score"] = max(0, 100 - (outdated_count * 2))
    except Exception as e:
        print(f"   ⚠️ Outdated check failed: {e}")

    status = "✅" if results["score"] >= 80 else "⚠️" if results["score"] >= 60 else "❌"
    print(f"   {status} Dependency Score: {results['score']}/100")
    return results


def generate_audit_report(results: dict[str, Any], output_file: Path) -> None:
    """Generate consolidated audit report.

    Args:
        results: Audit results from all modules
        output_file: Path to save report
    """
    print("\n📊 Generating Audit Report...")

    # Calculate overall score
    module_scores = [r["score"] for r in results["modules"].values()]
    overall_score = sum(module_scores) / len(module_scores) if module_scores else 0

    # Generate markdown report
    report = f"""# Project Audit Report

**Date:** {results['date']}
**Audit Type:** {results['audit_type'].title()}
**Overall Score:** {overall_score:.0f}/100

---

## 📋 Executive Summary

| Module | Score | Status |
|--------|-------|--------|
"""

    for module_name, module_data in results["modules"].items():
        score = module_data["score"]
        status = "✅" if score >= 80 else "⚠️" if score >= 60 else "❌"
        report += f"| {module_name.replace('_', ' ').title()} | {score}/100 | {status} |\n"

    report += """
---

## 🔍 Detailed Findings

"""

    # Security findings
    if "security" in results["modules"]:
        security = results["modules"]["security"]
        report += "### Security & Compliance\n\n"
        for finding in security.get("findings", []):
            if finding["tool"] == "bandit":
                report += f"**Bandit Scan:** {finding['total']} issues found\n"
                report += f"- Critical: {finding['critical']}\n"
                report += f"- High: {finding['high']}\n"
                report += f"- Medium: {finding['medium']}\n\n"
            elif finding["tool"] == "safety":
                report += f"**Safety Check:** {finding['vulnerabilities']} vulnerabilities found\n\n"

    # Testing findings
    if "testing" in results["modules"]:
        testing = results["modules"]["testing"]
        report += f"### Testing & Coverage\n\n"
        report += f"**Overall Coverage:** {testing['coverage']:.1f}%\n\n"
        if testing.get("low_coverage_files"):
            report += "**Low Coverage Files:**\n"
            for filepath, coverage in testing["low_coverage_files"]:
                report += f"- {filepath}: {coverage:.1f}%\n"
            report += "\n"

    # Documentation findings
    if "documentation" in results["modules"]:
        docs = results["modules"]["documentation"]
        report += f"### Documentation\n\n"
        report += f"**Files:** {docs['files']}\n"
        report += f"**Duplication Pairs:** {len(docs['duplicates'])}\n\n"

        if docs.get("duplicates"):
            high_dup = [d for d in docs["duplicates"] if d["similarity"] > 70]
            if high_dup:
                report += "**High Duplication (>70%):**\n"
                for dup in high_dup[:3]:
                    report += f"- {dup['file1']} ↔ {dup['file2']}: {dup['similarity']}% similar\n"
                report += "\n**Recommendation:** Consider consolidating duplicate documentation.\n\n"

    # Dependencies findings
    if "dependencies" in results["modules"]:
        deps = results["modules"]["dependencies"]
        report += f"### Dependencies\n\n"
        report += f"**Outdated Packages:** {deps.get('outdated_count', 0)}\n\n"

    report += """
---

## 📅 Recommendations

Based on audit findings:

1. **Security:** Review and address security findings from bandit scan
2. **Testing:** Increase coverage for low-coverage files (target: 80%+)
3. **Documentation:** Consolidate duplicate documentation files
4. **Dependencies:** Update outdated packages (especially security patches)

---

## 📈 Next Steps

- [ ] Review detailed findings above
- [ ] Create GitHub issues for high-priority items
- [ ] Update PROJECT_MEMORY.md with audit summary
- [ ] Schedule follow-up audit in 1 month

---

**Report Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Tool:** audit_orchestrator.py
"""

    # Save report
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(report, encoding="utf-8")
    print(f"   ✅ Report saved to: {output_file}")


def main() -> int:
    """Main orchestrator function.

    Returns:
        Exit code (0 = success)
    """
    parser = argparse.ArgumentParser(description="Project Audit Orchestrator")
    parser.add_argument(
        "--depth",
        choices=["quick", "full", "deep"],
        default="full",
        help="Audit depth (default: full)",
    )
    parser.add_argument(
        "--modules",
        help="Comma-separated list of modules to run (e.g., security,testing)",
        default=None,
    )
    parser.add_argument(
        "--output",
        help="Output file path for report",
        default=None,
    )

    args = parser.parse_args()

    print("=" * 60)
    print("🔍 PROJECT AUDIT ORCHESTRATOR")
    print("=" * 60)
    print(f"Audit Depth: {args.depth.upper()}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()

    # Determine which modules to run
    all_modules = {
        "security": run_security_audit,
        "testing": run_testing_audit,
        "documentation": run_documentation_audit,
        "dependencies": run_dependency_audit,
    }

    if args.modules:
        module_names = [m.strip() for m in args.modules.split(",")]
        modules_to_run = {k: v for k, v in all_modules.items() if k in module_names}
    else:
        modules_to_run = all_modules if args.depth == "full" else {"security": run_security_audit, "testing": run_testing_audit}

    # Execute audit modules
    results = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "audit_type": args.depth,
        "modules": {},
    }

    for module_name, module_func in modules_to_run.items():
        try:
            module_result = module_func()
            results["modules"][module_name] = module_result
        except Exception as e:
            print(f"   ❌ Module '{module_name}' failed: {e}")
            results["modules"][module_name] = {"module": module_name, "score": 0, "error": str(e)}
        print()

    # Generate report
    if args.output:
        output_file = Path(args.output)
    else:
        timestamp = datetime.now().strftime("%Y%m%d")
        output_file = Path(f"docs/audit/AUDIT_REPORT_{timestamp}.md")

    generate_audit_report(results, output_file)

    # Save JSON results
    json_file = output_file.with_suffix(".json")
    json_file.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"   ✅ JSON results saved to: {json_file}")

    print("\n" + "=" * 60)
    print("✅ AUDIT COMPLETE")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
