import uvicorn
import os

if __name__ == "__main__":
    host = os.getenv("CORE_A_HOST", "0.0.0.0")
    port = int(os.getenv("CORE_A_PORT", "8000"))
    uvicorn.run("aegis_core.core_a.main:app", host=host, port=port, reload=False)
