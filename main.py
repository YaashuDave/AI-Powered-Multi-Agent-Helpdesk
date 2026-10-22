"""
CORRECT MAIN.PY — STREAMS MCP + COORDINATOR OUTPUT LIVE
---------------------------------------------------------

This version:
 - Starts MCP server AND prints its logs in real time
 - Starts Coordinator AND prints its logs in real time
 - Provides clean CLI for user tickets
 - Prevents empty input
 - No background silent processes
 - Shows EVERYTHING on terminal normally
"""

import subprocess
import threading
import time
import sys


# ============================================================
# STREAM PROCESS OUTPUT LIVE
# ============================================================
def stream_output(process, prefix):
    """Stream stdout of a subprocess to the terminal live."""
    for line in iter(process.stdout.readline, b""):
        try:
            print(f"{prefix} {line.decode('utf-8', 'replace').rstrip()}")
        except:
            pass


# ============================================================
# START MCP SERVER (VISIBLE)
# ============================================================
def start_mcp_server():
    proc = subprocess.Popen(
        [sys.executable, "-u", "mcp_server/mcp_server.py"],
        stdin=subprocess.DEVNULL,   # the CLI below owns the terminal input
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    t = threading.Thread(target=stream_output, args=(proc, "[MCP]"), daemon=True)
    t.start()

    print("✔ MCP Server started.")
    return proc


# ============================================================
# START COORDINATOR (VISIBLE)
# ============================================================
def start_coordinator():
    proc = subprocess.Popen(
        [sys.executable, "-u", "coordinator/coordinator.py"],
        stdin=subprocess.DEVNULL,   # the CLI below owns the terminal input
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    t = threading.Thread(target=stream_output, args=(proc, "[COORD]"), daemon=True)
    t.start()

    print("✔ Coordinator started.")
    return proc


# ============================================================
# CLI LOOP (CLEAN, EMPTY INPUT FIXED)
# ============================================================
def cli_loop():
    print("\n=== AI-Powered Multi-Agent Helpdesk (CLI Mode) ===")
    print("Type your issue below. Type 'exit' to quit.\n")

    while True:
        try:
            issue = input("Enter issue: ").strip()
        except KeyboardInterrupt:
            print("\nShutting down...")
            break

        # exit command
        if issue.lower() == "exit":
            print("Shutting down...")
            break

        # prevent blank submissions
        if issue == "":
            print("⚠️  Empty input ignored. Please type an issue.\n")
            continue

        # write to coordinator_input file
        with open("coordinator_input.txt", "w", encoding="utf-8") as f:
            f.write(issue)

        print(f"✔ Issue submitted: \"{issue}\"")
        print("Agents processing...\n")


# ============================================================
# MAIN ENTRY
# ============================================================
def main():
    print("Starting MCP Server...")
    mcp = start_mcp_server()
    time.sleep(1)

    print("Starting Coordinator...")
    coord = start_coordinator()
    time.sleep(1)

    print("\nSystem is LIVE.")
    print("--------------------------------------------")
    print("✔ All agent threads started")
    print("✔ Live logs streaming below")
    print("✔ Submit issues via CLI")
    print("--------------------------------------------\n")

    cli_loop()

    mcp.kill()
    coord.kill()


if __name__ == "__main__":
    main()
