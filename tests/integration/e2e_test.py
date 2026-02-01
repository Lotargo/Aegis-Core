import subprocess
import time
import httpx
import os
import sys
import json

def run_process(cmd, env=None, log_file=None):
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    return subprocess.Popen(cmd, env=full_env, stdout=log_file, stderr=subprocess.STDOUT, text=True)

def wait_for_port(port, timeout=10):
    start = time.time()
    while time.time() - start < timeout:
        try:
            httpx.get(f"http://localhost:{port}/docs", timeout=1)
            return True
        except:
            time.sleep(0.5)
    return False

def main():
    print("Starting E2E MTD Test...")

    log_a = open("core_a.log", "w")
    log_b = open("core_b.log", "w")
    log_backend = open("backend.log", "w")

    try:
        # 1. Start Mock Backend
        print("Starting Mock Backend on 8081...")
        backend = run_process(["python", "tests/integration/mock_backend.py"], log_file=log_backend)
        if not wait_for_port(8081):
            print("Backend failed to start")
            sys.exit(1)

        # 2. Start Core B with short TTL for testing expiration
        print("Starting Core B (TTL=5s)...")
        env_b = {
            "TARGET_APP_URL": "http://localhost:8081",
            "GRPC_PORT": "50052",
            "CORE_B_HTTP_PORT": "8001",
            "SESSION_TTL": "5",  # 5 seconds TTL
            "PYTHONUNBUFFERED": "1"
        }
        core_b = run_process(["python", "-m", "aegis_core.core_b"], env=env_b, log_file=log_b)
        if not wait_for_port(8001):
            print("Core B failed to start")
            sys.exit(1)

        # 3. Start Core A
        print("Starting Core A...")
        env_a = {
            "CORE_B_GRPC_TARGET": "localhost:50052",
            "CORE_B_HTTP_URL": "http://localhost:8001",
            "CORE_A_PORT": "8000",
            "PYTHONUNBUFFERED": "1"
        }
        core_a = run_process(["python", "-m", "aegis_core.core_a"], env=env_a, log_file=log_a)
        if not wait_for_port(8000):
            print("Core A failed to start")
            sys.exit(1)

        print("Waiting for session establishment...")
        time.sleep(3)

        # 4. Test 1: Normal Request (Path Hiding check)
        print("\n[Test 1] Sending normal request...")
        resp1 = httpx.post("http://localhost:8000/secret/path", json={"msg": "hello"}, timeout=5)
        print(f"Resp1 Status: {resp1.status_code}")
        if resp1.status_code != 200:
             raise Exception(f"Failed normal request: {resp1.status_code}")

        data1 = resp1.json()
        if data1["path"] != "/secret/path":
             raise Exception(f"Path obfuscation failed, backend got: {data1['path']}")
        print("PASS: Path correctly delivered.")

        # 5. Test 2: Session Expiration & Auto-Reconnect
        print("\n[Test 2] Waiting 6s for session expiry...")
        time.sleep(6)

        print("Sending request with expired session...")
        resp2 = httpx.post("http://localhost:8000/retry/test", json={"msg": "retry"}, timeout=10)
        print(f"Resp2 Status: {resp2.status_code}")

        if resp2.status_code != 200:
             raise Exception(f"Auto-reconnect failed: {resp2.status_code}")

        data2 = resp2.json()
        if data2["path"] != "/retry/test":
             raise Exception("Path mismatch after reconnect")
        print("PASS: Auto-reconnection worked.")

        # 6. Test 3: Deception (Statistical Check)
        print("\n[Test 3] Sending 10 requests to check Deception consistency...")
        # Since Core A hides the fake status from us, we can't easily check the *outer* status
        # without sniffing the gRPC traffic or checking logs.
        # But we CAN check that Core A *always* gives us 200 OK, even if Core B lied.

        for i in range(10):
            resp = httpx.get(f"http://localhost:8000/spam/{i}", timeout=5)
            if resp.status_code != 200:
                raise Exception(f"Core A failed to handle deception at request {i}, got {resp.status_code}")
        print("PASS: Client consistently ignored fake statuses.")

        print("\nSUCCESS: All MTD tests passed!")

    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        # Print logs for debugging
        print("\n--- Core A Log ---")
        with open("core_a.log", "r") as f: print(f.read())
        print("\n--- Core B Log ---")
        with open("core_b.log", "r") as f: print(f.read())
        sys.exit(1)

    finally:
        print("Stopping services...")
        if 'core_a' in locals(): core_a.terminate()
        if 'core_b' in locals(): core_b.terminate()
        if 'backend' in locals(): backend.terminate()

        log_a.close()
        log_b.close()
        log_backend.close()

if __name__ == "__main__":
    main()
