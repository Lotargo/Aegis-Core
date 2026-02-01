# Architecture & MTD Implementation

## Overview

Aegis Core is a security gateway designed around the principle of **Moving Target Defense (MTD)**. Instead of relying on static defenses, it constantly changes the attack surface to invalidate attacker reconnaissance.

## Component Interaction

### 1. The Secure Channel (Proteus Protocol)

The communication between Core A (Client) and Core B (Server) is not standard HTTP. It is a custom gRPC tunnel where:
*   **Transport Layer:** gRPC / HTTP2
*   **Encryption:** AES-256-GCM with per-session keys.
*   **Integrity:** HMAC-SHA256 signatures.

### 2. Path Obfuscation (The "Invisible API")

In a standard API call:
`GET /api/v1/users/123`

In Aegis Core:
1.  Core A receives the request.
2.  It takes the method (`GET`) and path (`/api/v1/users/123`), puts them into a JSON object, and **encrypts** them.
3.  The outer gRPC request is sent with a generic metadata trace ID: `Trace-ID: <random-uuid>`.
4.  **Wire Result:** An attacker sniffing the network sees a gRPC packet going to `AegisGateway/Process`. They have zero visibility into which REST endpoint is actually being called.

### 3. Cyber Deception (The "Lying Server")

To disrupt automated scanners, Core B implements a **Deception Engine**:
1.  Core B processes the request successfully and gets a `200 OK` from the backend.
2.  It encrypts the real response.
3.  It generates a **Fake Status Code** for the outer envelope.
    *   Example: It wraps the `200 OK` payload inside a `503 Service Unavailable` gRPC response.
4.  **Network View:** The attacker sees a `503` error and assumes the exploit failed.
5.  **Client View:** Core A ignores the `503`, decrypts the payload, finds the real `200 OK`, and returns it to the application.

### 4. Session Management (Key Rotation)

*   **Handshake:** ECDH (Elliptic-curve Diffie–Hellman) is used to establish a shared secret.
*   **TTL (Time-To-Live):** Every session in Core B has a strict lifetime (defined by `SESSION_TTL`, default 10 mins).
*   **Auto-Renewal:** When a key expires, Core B returns an `UNAUTHENTICATED` error. Core A catches this, instantly performs a new handshake, and retries the original request. This happens transparently to the user.
