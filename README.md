# Aegis Core

![Aegis Core Logo](docs/logo.svg)

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Poetry](https://img.shields.io/badge/poetry-managed-blueviolet)

**Aegis Core** is a paradigm shift in API security. Unlike traditional WAFs that react to known threats, Aegis Core implements **Moving Target Defense (MTD)** and **Cyber Deception** to make your API infrastructure invisible and unpredictable to attackers.

By deploying as a transparent "man-in-the-middle" gateway, it dynamically encrypts endpoints, obfuscates traffic, and actively misleads scanners, all without requiring a single line of code change in your protected applications.

---

## 🛡️ Core Philosophy

### 1. Moving Target Defense (MTD)
Traditional APIs are static targets (e.g., `/api/v1/login`). Aegis Core eliminates this vulnerability by **encrypting the entire request structure**, including URL paths and methods, inside a binary payload.
*   **Path Obfuscation:** The external observer sees only opaque UUID-based trace IDs. The real API structure is invisible on the wire.
*   **Session Rotation:** Session keys automatically expire (default: 10 mins), forcing frequent, seamless re-authentication. This significantly reduces the window of opportunity for key theft.

### 2. Cyber Deception & Camouflage
The system actively lies to unauthorized observers.
*   **Protocol Camouflage:** A successful `200 OK` response carrying sensitive data can be wrapped in a fake `503 Service Unavailable`, `404 Not Found`, or `500 Internal Server Error` envelope.
*   **Chaos Mode:** Core B randomly selects these fake statuses, causing automated scanners (like Burp Suite or ZAP) to produce thousands of false negatives and positives, effectively blinding the attacker.

---

## 🎛️ Aegis Control Center (Dashboard)

Aegis Core comes with a GUI dashboard to generate secure deployment configurations effortlessly.

![Aegis Dashboard Preview](docs/dashboard_preview.png)

### Running the Dashboard
```bash
# Build and run with Docker
cd aegis_dashboard
docker build -t aegis-dashboard .
docker run -p 8080:8080 aegis-dashboard
```
Open [http://localhost:8080](http://localhost:8080) in your browser.

---

## 🏗️ Architecture

The system operates as a pair of proxies protecting the channel between a Client Application and a Server Application.

```mermaid
graph LR
    subgraph Client_Side
        AppA[Client App]
        CoreA[Aegis Core A]
    end

    subgraph Server_Side
        CoreB[Aegis Core B]
        AppB[Server App]
    end

    AppA -- HTTP/1.1 --> CoreA
    CoreA -- "Proteus Protocol (Encrypted gRPC)" --> CoreB
    CoreB -- HTTP/1.1 --> AppB

    %% Стили для Core (Светлый фон, Темный текст)
    style CoreA fill:#E1BEE7,stroke:#8E24AA,stroke-width:2px,color:#333333
    style CoreB fill:#BBDEFB,stroke:#1976D2,stroke-width:2px,color:#333333
```

*   **Aegis Core A (Encryptor):** Sits next to the client. It intercepts standard HTTP requests, performs an **ECDH key exchange** with Core B, and wraps the request in the secure **Proteus Protocol**. It handles automatic session renewal and extracts real data from deceptive responses.
*   **Aegis Core B (Decryptor):** Sits next to the server. It decrypts the traffic, enforcing MTD policies (Path Hiding, Key Expiration, Deception).

---

## 🚀 Key Features

### 🔒 Cryptographic Core
*   **AES-256-GCM:** All payloads (headers, body, AND routing info) are authenticated and encrypted.
*   **ECDH Key Exchange:** Ephemeral session keys are generated for every connection; no master keys are ever transmitted.
*   **HMAC Signatures:** Ensures integrity for every packet.

### 🎭 Active Defense Modules
*   **Path Hiding:** Real URL paths are never transmitted in cleartext metadata.
*   **Deception Engine:** Randomized outer HTTP status codes to mislead traffic analysis.
*   **Auto-Healing Sessions:** Clients automatically reconnect when keys expire or are revoked.

### 🛡️ Zero-Trust Security (Core B)
Before any request reaches your server, it must pass a multi-layered filter:
1.  **Schema Validation:** Validates the decrypted request against your **OpenAPI 3.x** specification.
2.  **Web Application Firewall (WAF):** Scans for SQL Injection, XSS, and Command Injection patterns.
3.  **Rate Limiting:** Redis-backed rate limiter prevents Brute Force and DoS attacks.

---

## ⚙️ Configuration

Aegis Core is configured entirely via environment variables.

| Variable | Description | Default |
| :--- | :--- | :--- |
| **Common** | | |
| `LOG_LEVEL` | Logging verbosity (DEBUG, INFO, ERROR) | `INFO` |
| **Core A (Client)** | | |
| `CORE_A_HOST` | Host to bind the HTTP proxy | `0.0.0.0` |
| `CORE_A_PORT` | Port for the HTTP proxy | `8000` |
| `CORE_B_GRPC_TARGET`| Address of the remote Core B | `localhost:50051` |
| `CORE_B_HTTP_URL` | Address of Core B HTTP server for key exchange | `http://localhost:8001` |
| **Core B (Server)** | | |
| `CORE_B_GRPC_PORT` | Port to bind the gRPC listener | `50051` |
| `TARGET_APP_URL` | The real backend URL to protect | `http://localhost:8080` |
| `SESSION_TTL` | Session key lifetime in seconds | `600` |
| `REDIS_URL` | Redis connection string for Rate Limiting | `redis://localhost:6379` |

---

## ⚡ Quick Start

### Prerequisites
*   Python 3.10+
*   Poetry
*   Redis (optional, for Rate Limiting features)

### Installation

```bash
# 1. Clone the repository
git clone <repository_url>
cd aegis-core

# 2. Install dependencies
poetry install
```

### Running the System

**1. Start Aegis Core B (Server-side):**
```bash
export TARGET_APP_URL="http://your-backend-service:8080"
poetry run python -m aegis_core.core_b
```

**2. Start Aegis Core A (Client-side):**
```bash
export CORE_B_GRPC_TARGET="localhost:50051"
poetry run python -m aegis_core.core_a
```

Now, point your client application to `http://localhost:8000` instead of the real backend.

---

## 🧪 Testing

The project includes a comprehensive E2E integration test suite that verifies MTD features (encryption, path hiding, deception, session rotation).

To run the full suite:
```bash
poetry run python tests/integration/e2e_test.py
```

To run unit tests:
```bash
poetry run pytest
```

---

## 📄 License & Contact

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

**Contact:**
Telegram: [@Lotargo](https://t.me/Lotargo)
Copyright (c) 2025 Lotargo
