# Technical Specification

## Protocol Definition (Proteus)

The communication is defined by `proto/aegis.proto`.

### AegisRequest
| Field | Type | Description |
| :--- | :--- | :--- |
| `encrypted_payload` | `bytes` | Contains the JSON-serialized `method`, `path`, `headers`, and `body`. Encrypted with AES-256-GCM. |
| `metadata` | `map<string, string>` | **DEPRECATED for routing.** Only contains non-sensitive tracing data (e.g., `trace_id`). |
| `public_key` | `bytes` | The client's ephemeral public key (PEM format) to identify the session. |

### AegisResponse
| Field | Type | Description |
| :--- | :--- | :--- |
| `fake_http_status` | `int32` | A randomized HTTP status code (200, 403, 404, 500, 503) used for deception. **MUST be ignored by the client.** |
| `encrypted_payload` | `bytes` | Contains the real `status_code`, `headers`, and `body`. |
| `metadata` | `map<string, string>` | Response tracing metadata. |

## Environment Variables

### Common
*   `LOG_LEVEL`: `DEBUG`, `INFO`, `WARNING`, `ERROR` (Default: `INFO`)

### Core A (Client Proxy)
*   `CORE_A_HOST`: Interface to bind (Default: `0.0.0.0`)
*   `CORE_A_PORT`: Port to listen on (Default: `8000`)
*   `CORE_B_GRPC_TARGET`: Host:Port of Core B gRPC server (Default: `localhost:50051`)
*   `CORE_B_HTTP_URL`: URL of Core B HTTP server (for initial handshake) (Default: `http://localhost:8001`)
*   `MAX_REQUEST_SIZE`: Maximum allowed request body size in bytes (Default: `10485760` / 10MB). Used for DoS protection.

### Core B (Server Gateway)
*   `CORE_B_GRPC_PORT`: gRPC listening port (Default: `50051`)
*   `CORE_B_HTTP_PORT`: HTTP listening port for handshake (Default: `8001`)
*   `TARGET_APP_URL`: The backend URL to proxy to (Default: `http://localhost:8080`)
*   `SESSION_TTL`: Session validity duration in seconds (Default: `600`)
*   `REDIS_URL`: Redis URL for Rate Limiting (Default: `redis://localhost:6379`)

## Security Constraints
1.  **Replay Attacks:** Mitigated by Session Keys and gRPC nonces.
2.  **Man-in-the-Middle:** Mitigated by ECDH. Note: The initial HTTP handshake is vulnerable if not wrapped in TLS/mTLS in production.
3.  **DoS (Application Level):** Mitigated by `MAX_REQUEST_SIZE` enforcement in Core A (Content-Length and Stream limits).
4.  **DoS (Network Level):** Mitigated by Rate Limiting (Redis required).
