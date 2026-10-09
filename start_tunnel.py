import subprocess
import re
import sys
import os
import time
import webbrowser
import urllib.request

CLOUDFLARED_PATH = r"C:\Program Files (x86)\cloudflared\cloudflared.exe"
FLASK_LOCAL_URL = "http://127.0.0.1:5000"

def is_flask_running():
    try:
        req = urllib.request.Request(FLASK_LOCAL_URL)
        with urllib.request.urlopen(req, timeout=2) as response:
            return response.status == 200
    except Exception:
        return False

def main():
    print("=" * 65)
    print("   COLLEGE EMERGENCY ASSISTANCE PORTAL - PUBLIC TUNNEL LAUNCHER")
    print("=" * 65)
    print()

    # 1. Check if Flask is running
    print("[*] Checking if local Flask server is running...")
    if not is_flask_running():
        print("[!] Flask server is not running on port 5000.")
        print("[*] Starting Flask server in background...")
        python_exe = sys.executable
        subprocess.Popen([python_exe, "app.py"], cwd=os.path.dirname(os.path.abspath(__file__)))
        # Wait up to 10 seconds for Flask to respond
        started = False
        for _ in range(10):
            time.sleep(1)
            if is_flask_running():
                started = True
                break
        if started:
            print("[+] Flask server started successfully!")
        else:
            print("[!] Flask server took longer than expected. Continuing anyway...")
    else:
        print("[+] Flask server is active and responding on http://127.0.0.1:5000!")

    # 2. Check Cloudflared executable
    if not os.path.exists(CLOUDFLARED_PATH):
        print(f"[!] Error: cloudflared not found at {CLOUDFLARED_PATH}")
        input("Press Enter to exit...")
        return

    # 3. Terminate any previous cloudflared processes
    subprocess.run(["taskkill", "/F", "/IM", "cloudflared.exe"], capture_output=True)

    print()
    print("[*] Generating new secure public HTTPS tunnel via Cloudflare...")
    print("[*] Please wait a few seconds...")

    # 4. Start cloudflared process
    proc = subprocess.Popen(
        [CLOUDFLARED_PATH, "tunnel", "--url", FLASK_LOCAL_URL],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    public_url = None
    pattern = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")

    # Read output line by line until URL is found
    for line in proc.stdout:
        match = pattern.search(line)
        if match:
            public_url = match.group(0)
            break
        if "error" in line.lower() and "failed" in line.lower():
            print(f"[DEBUG] {line.strip()}")

    if public_url:
        # Save to text file
        with open("LATEST_PUBLIC_LINK.txt", "w", encoding="utf-8") as f:
            f.write(f"PUBLIC LINK (Valid while tunnel window is open):\n{public_url}\n\n")
            f.write("Accounts to test:\n")
            f.write("  Student:   student1   / password123\n")
            f.write("  Responder: security1  / security123\n")
            f.write("  Admin:     admin      / admin123\n")

        print()
        print("=" * 65)
        print(" [SUCCESS] YOUR PUBLIC LINK IS READY & LIVE WORLDWIDE!")
        print()
        print(f" >>> {public_url} <<<")
        print()
        print(" Saved to: LATEST_PUBLIC_LINK.txt")
        print("=" * 65)
        print()
        print("Opening this link in your browser now...")
        try:
            webbrowser.open(public_url)
        except Exception:
            pass

        print()
        print("IMPORTANT: Keep this window OPEN to keep the public link active.")
        print("Press Ctrl+C to stop the public tunnel when done.")
        print("=" * 65)

        # Wait indefinitely for the cloudflared process to run
        try:
            proc.wait()
        except KeyboardInterrupt:
            print("\nShutting down tunnel...")
            proc.terminate()
    else:
        print("[!] Could not retrieve public tunnel URL. Check internet connection.")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
