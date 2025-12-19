# Technical Specification

**Version:** 1.0
**Date:** October 28, 2025

---

## 1. General Provisions

### 1.1 Project Name
Proactive API Protection System "Aegis Core".

### 1.2 Terms and Definitions
*   **Aegis Core System:** A software complex consisting of two proxy components ensuring secure network interaction.
*   **Aegis Core A (Encryptor Proxy):** Client-side component. Intercepts, encrypts, and obfuscates requests.
*   **Aegis Core B (Decryptor Proxy):** Server-side component. Decrypts, validates, and forwards requests.
*   **Proteus Protocol:** Internal secure communication protocol between Aegis Core A and B.

## 2. Goals and Objectives

### 2.1 Goals
Create a universal, high-performance security gateway implementing "Moving Target Defense" and "Cyber Deception" principles to protect APIs from modern threats without modifying target application code.

### 2.2 Objectives
1.  Develop `Aegis Core A` and `Aegis Core B` components.
2.  Implement the secure "Proteus" protocol based on gRPC and Protocol Buffers.
3.  Integrate a cryptographic core for dynamic endpoint and payload encryption.
4.  Implement protocol camouflage to mask legitimate traffic.
5.  Integrate multi-level security filters (WAF, Rate Limiting, Schema Validation) in Core B.
6.  Ensure centralized logging integrated with ELK stack.
7.  Prepare the system for containerized deployment (Docker, Kubernetes).

## 3. Functional Requirements

### 3.1 Proxy Core (FastAPI)
1.  Both components must function as asynchronous ASGI applications.
2.  `Aegis Core A` accepts standard HTTP/1.1 requests.
3.  `Aegis Core B` forwards restored requests to the target app via HTTP/1.1.
4.  Correct proxying of HTTP headers (excluding connection-specific ones).
5.  Configurable timeout logic for all external connections.

### 3.2 Proteus Protocol (gRPC + Protobuf)
1.  **Data Contract:**
    *   **AegisRequest:** Contains encrypted endpoint, payload, metadata, and HMAC signature.
    *   **AegisResponse:** Contains fake HTTP status, encrypted payload (with real response), rotor sync position, and signature.
2.  **Cryptography:**
    *   **Key Exchange:** ECDH for session key generation.
    *   **Encryption:** AES-256-GCM for all payloads.
    *   **Obfuscation:** Deterministic URL path obfuscation based on session key and internal state.
    *   **Integrity:** HMAC signature for every message.

### 3.3 Security Modules (Aegis Core B)
1.  **WAF:** Analyzes decrypted content for SQLi, XSS, Command Injection. Configurable rules (e.g., OWASP CRS).
2.  **Rate Limiter:** Limits requests based on client ID. Uses Redis backend.
3.  **Schema Validation:** Validates requests against OpenAPI 3.x spec. Rejects invalid requests with `400 Bad Request` (masked by Proteus).

### 3.4 Configuration
1.  Configurable via environment variables or YAML.
2.  Key parameters: Listen addresses, target service address, remote Aegis Core address, Redis/ELK connection, WAF rules path, Log level.

### 3.5 Logging and Monitoring
1.  Structured JSON logging to stdout.
2.  Events: `AEGIS_REQUEST_BLOCKED`, `AEGIS_DECRYPTION_FAILED`, `AEGIS_SIGNATURE_INVALID`.
3.  Prometheus metrics endpoint (`/metrics`): Request counts, latency histograms.

## 4. Non-Functional Requirements

### 4.1 Performance
1.  Overhead should not exceed **50ms** at the 95th percentile.
2.  One instance should handle at least **1000 RPS** on standard hardware (2 vCPU, 4GB RAM).

### 4.2 Reliability
1.  Target availability: **99.95%**.
2.  Automatic reconnection and secure channel re-establishment.

### 4.3 Scalability
Horizontal scaling support behind a load balancer.

### 4.4 Security
1.  No hardcoded secrets.
2.  Regular dependency scanning.
3.  Non-privileged user execution in containers.
