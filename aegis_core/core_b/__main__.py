import uvicorn
import os

if __name__ == "__main__":
    # Core B runs both gRPC (in background task) and HTTP (FastAPI)
    # The FastAPI app startup event launches the gRPC server.
    # We just need to run the FastAPI app.
    # Note: CORE_B_GRPC_PORT is handled inside main.py

    # We don't have a specific HTTP port env var defined in the docs for Core B's HTTP server
    # (it defaults to 8000 in Uvicorn default), but let's assume standard 8001 to avoid conflict if on same machine.
    # Checking main.py: It uses APP_B_URL for target, but doesn't set its own port.

    port = int(os.getenv("CORE_B_HTTP_PORT", "8001"))
    uvicorn.run("aegis_core.core_b.main:app", host="0.0.0.0", port=port, reload=False)
