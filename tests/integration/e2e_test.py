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
    print("Starting E2E Test...")

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
        print("Mock Backend Started.")

        # 2. Start Core B
        print("Starting Core B...")
        env_b = {
            "TARGET_APP_URL": "http://localhost:8081",
            "GRPC_PORT": "50052",
            "CORE_B_HTTP_PORT": "8001",
            "PYTHONUNBUFFERED": "1"
        }
        core_b = run_process(["python", "-m", "aegis_core.core_b"], env=env_b, log_file=log_b)
        if not wait_for_port(8001):
            print("Core B failed to start")
            sys.exit(1)
        print("Core B Started.")

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
        print("Core A Started.")

        print("Waiting for session establishment...")
        time.sleep(3)

        # 4. Test
        print("Sending request to Core A...")
        try:
            response = httpx.post("http://localhost:8000/test/path?q=1", json={"foo": "bar"}, headers={"X-Test": "True"}, timeout=5)
            print(f"Response Status: {response.status_code}")
            print(f"Response Body: {response.text}")

            if response.status_code != 200:
                raise Exception(f"Status code mismatch: {response.status_code}")

            data = response.json()

            if data.get("status") != "ok":
                raise Exception("Backend status mismatch")

            if data.get("path") != "/test/path":
                 raise Exception(f"Path mismatch: {data.get('path')}")

            if data.get("query") != "q=1":
                 raise Exception(f"Query mismatch: {data.get('query')}")

            sent_body = json.loads(data["body"])
            if sent_body.get("foo") != "bar":
                raise Exception("Body mismatch")

            print("SUCCESS: E2E Test Passed!")

        except Exception as e:
            print(f"Test Failed: {e}")
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
