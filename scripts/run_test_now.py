#!/usr/bin/env python
"""
Quick test runner - capture and display logs while you test the UI
Run this and follow the instructions
"""

import subprocess
import time
import sys
import os

def main():
    print("\n" + "="*70)
    print("STREAMLIT UI HANGING DEBUG TEST")
    print("="*70)

    print("""
WHAT TO DO:
-----------

1. Open your browser to: http://localhost:8501

2. In the chat input box, type this EXACTLY:
   high in the chart

3. Press ENTER to submit

4. Watch the logs below - they will update in REAL TIME

5. Note where the logs STOP (if they do) and tell me

6. When done, close this terminal

LOG OUTPUT (Streaming from Streamlit):
--------------------------------------
""")

    # Clear old log file or start fresh
    log_file = "streamlit_debug.log"
    if os.path.exists(log_file):
        # Get current file size to skip old logs
        skip_size = os.path.getsize(log_file)
    else:
        skip_size = 0

    print("Waiting for new logs...\n")

    # Monitor logs
    try:
        last_pos = skip_size
        while True:
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    f.seek(last_pos)
                    new_lines = f.readlines()
                    last_pos = f.tell()

                    for line in new_lines:
                        # Only show UI-DEBUG, ERROR, and Exception lines
                        if any(marker in line for marker in ['UI-DEBUG', 'ERROR', 'Exception', 'Traceback']):
                            # Remove timestamp for cleaner display
                            if ' - ' in line:
                                parts = line.split(' - ', 1)
                                if len(parts) > 1:
                                    print(f"  {parts[1].rstrip()}")
                                else:
                                    print(f"  {line.rstrip()}")
                            else:
                                print(f"  {line.rstrip()}")

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n\n" + "="*70)
        print("TEST STOPPED BY USER")
        print("="*70)
        print("\nREAD THE LOGS ABOVE:")
        print("- Where did the [UI-DEBUG] messages stop?")
        print("- Were there any ERROR or Exception messages?")
        print("- What did the UI display?")
        print("\nShare this information so I can provide the exact fix!")
        sys.exit(0)

if __name__ == "__main__":
    main()
