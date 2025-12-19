# Setup and Installation

## Prerequisites

*   Python 3.10+
*   Poetry (for dependency management)
*   Redis (for Rate Limiting)
*   ELK Stack (optional, for logging)

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd aegis-core
    ```

2.  **Install dependencies:**
    ```bash
    poetry install
    ```

## Configuration

Aegis Core is configured using environment variables.

### Common Configuration
*   `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR). Default: `INFO`.

### Aegis Core A (Client Side)
*   `CORE_A_HOST`: Host to bind the Core A HTTP server (e.g., `0.0.0.0`).
*   `CORE_A_PORT`: Port for Core A HTTP server (e.g., `8000`).
*   `CORE_B_GRPC_TARGET`: Address of the Core B gRPC server (e.g., `localhost:50051`).

### Aegis Core B (Server Side)
*   `CORE_B_GRPC_PORT`: Port to bind the Core B gRPC server (e.g., `50051`).
*   `TARGET_APP_URL`: URL of the protected backend application (e.g., `http://localhost:8080`).
*   `REDIS_URL`: Connection string for Redis (e.g., `redis://localhost:6379`).

## Running the Services

### Core A
```bash
poetry run python -m aegis_core.core_a
```

### Core B
```bash
poetry run python -m aegis_core.core_b
```

## Running Tests

To run the unit tests:

```bash
poetry run pytest
```

**Note:** Integration tests are currently disabled. The test suite primarily covers unit tests for the cryptographic core and platform logic.
