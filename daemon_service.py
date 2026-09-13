"""
V-CAD Background Daemon Controller
Commands:
  python daemon_service.py start [port]
  python daemon_service.py stop
  python daemon_service.py status
  python daemon_service.py restart [port]
  python daemon_service.py logs
"""

import os
import sys
import time
import subprocess
import signal
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PID_FILE = BASE_DIR / "vcad_server.pid"
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "vcad_engine.log"

LOG_DIR.mkdir(parents=True, exist_ok=True)

def is_pid_running(pid: int) -> bool:
    if os.name == "nt":
        cmd = f'tasklist /FI "PID eq {pid}" /NH'
        out = subprocess.getoutput(cmd)
        return str(pid) in out and "python" in out.lower()
    else:
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

def get_running_pid() -> int | None:
    if not PID_FILE.exists():
        return None
    try:
        with open(PID_FILE, "r") as f:
            pid = int(f.read().strip())
        if is_pid_running(pid):
            return pid
        else:
            PID_FILE.unlink(missing_ok=True)
            return None
    except Exception:
        return None

def start_daemon(port: int = 8080):
    pid = get_running_pid()
    if pid:
        print(f"[WARN] V-CAD Server is already running in background (PID: {pid}) on port {port}")
        return

    print(f"[START] Launching V-CAD Server in background on port {port}...")
    log_fp = open(LOG_FILE, "a", encoding="utf-8")

    creation_flags = 0
    if os.name == "nt":
        # DETACHED_PROCESS flag on Windows ensures it lives independently of this terminal
        creation_flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP

    proc = subprocess.Popen(
        [sys.executable, str(BASE_DIR / "server.py"), str(port)],
        cwd=str(BASE_DIR),
        stdin=subprocess.DEVNULL,
        stdout=log_fp,
        stderr=subprocess.STDOUT,
        creationflags=creation_flags,
        close_fds=True
    )

    with open(PID_FILE, "w") as f:
        f.write(str(proc.pid))

    # Give server 1.5 seconds to initialize
    time.sleep(1.5)
    if is_pid_running(proc.pid):
        print(f"[SUCCESS] V-CAD Background Server is ACTIVE!")
        print(f"  PID: {proc.pid}")
        print(f"  URL: http://localhost:{port}")
        print(f"  Log: {LOG_FILE}")
    else:
        print(f"[ERROR] Server failed to start. Check {LOG_FILE} for details.")

def stop_daemon():
    pid = get_running_pid()
    if not pid:
        print("[INFO] No running V-CAD server found.")
        return

    print(f"[STOP] Terminating V-CAD Server (PID: {pid})...")
    if os.name == "nt":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        os.kill(pid, signal.SIGTERM)

    PID_FILE.unlink(missing_ok=True)
    time.sleep(0.5)
    print("[SUCCESS] V-CAD Background Server terminated.")

def check_status():
    pid = get_running_pid()
    if pid:
        print(f"[ONLINE] V-CAD Background Server is running (PID: {pid}).")
        print(f"  Log file: {LOG_FILE}")
    else:
        print("[OFFLINE] V-CAD Background Server is NOT running.")

def view_logs(tail_lines: int = 40):
    if not LOG_FILE.exists():
        print("[INFO] No log file created yet.")
        return
    with open(LOG_FILE, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    print("".join(lines[-tail_lines:]))

if __name__ == "__main__":
    action = sys.argv[1].lower() if len(sys.argv) > 1 else "status"
    port_arg = int(sys.argv[2]) if len(sys.argv) > 2 else 8080

    if action == "start":
        start_daemon(port_arg)
    elif action == "stop":
        stop_daemon()
    elif action == "restart":
        stop_daemon()
        time.sleep(1.0)
        start_daemon(port_arg)
    elif action == "status":
        check_status()
    elif action == "logs":
        view_logs()
    else:
        print(f"Unknown action: {action}. Use: start | stop | restart | status | logs")
