"""
FILE: run_ui_tests.py
STATUS: Active
RESPONSIBILITY: Runner script for Playwright UI tests
LAST MAJOR UPDATE: 2026-02-11
MAINTAINER: Shahu

USAGE:
    poetry run python scripts/run_ui_tests.py
    poetry run python scripts/run_ui_tests.py --headed  # Show browser
"""

import sys
import time
import subprocess
import requests
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


def check_server(url: str, name: str, max_retries: int = 5) -> bool:
    """Check if a server is running and responding."""
    print(f"Checking {name} at {url}...")

    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                print(f"✓ {name} is running")
                return True
        except requests.exceptions.RequestException:
            if attempt < max_retries - 1:
                print(f"  Attempt {attempt + 1}/{max_retries}: Waiting for {name}...")
                time.sleep(2)

    print(f"✗ {name} is not responding")
    return False


def run_tests(headed: bool = False):
    """Run Playwright UI tests."""
    print("\n" + "=" * 80)
    print("PLAYWRIGHT UI TEST RUNNER")
    print("=" * 80)

    # Check if servers are running
    api_ok = check_server("http://localhost:8002/health", "FastAPI (port 8002)")
    streamlit_ok = check_server("http://localhost:8501", "Streamlit (port 8501)")

    if not api_ok or not streamlit_ok:
        print("\n⚠️  WARNING: One or more servers are not running!")
        print("\nPlease start the servers:")
        print("  FastAPI:   poetry run uvicorn src.api.main:app --host 0.0.0.0 --port 8002")
        print("  Streamlit: poetry run streamlit run streamlit_viz_example.py")
        return 1

    print("\n✓ All servers are running\n")
    print("=" * 80)
    print("RUNNING TESTS")
    print("=" * 80 + "\n")

    # Build pytest command
    cmd = [
        "poetry", "run", "pytest",
        "tests/ui/test_streamlit_visualization.py",
        "-v",
        "-s",
        "--tb=short",
    ]

    if headed:
        print("Running in HEADED mode (browser will be visible)\n")
    else:
        print("Running in HEADLESS mode\n")

    # Run tests
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)

    print("\n" + "=" * 80)
    if result.returncode == 0:
        print("✅ ALL TESTS PASSED")
        print("\nScreenshots saved to: test_screenshots/")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 80)

    return result.returncode


if __name__ == "__main__":
    headed = "--headed" in sys.argv or "-h" in sys.argv
    sys.exit(run_tests(headed))
