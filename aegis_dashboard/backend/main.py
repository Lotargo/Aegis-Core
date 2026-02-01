from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import zipfile
import io
import yaml
import os

app = FastAPI(title="Aegis Dashboard API")

# Allow CORS for development (React dev server)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConfigRequest(BaseModel):
    backend_url: str = Field(..., example="http://my-backend:8080")
    core_a_port: int = Field(8000, example=8000)
    core_b_grpc_port: int = Field(50051, example=50051)
    core_b_http_port: int = Field(8001, example=8001)
    session_ttl: int = Field(600, example=600)
    use_redis: bool = Field(False)
    redis_url: str = Field("redis://redis:6379", example="redis://redis:6379")

@app.post("/api/generate-config")
async def generate_config(config: ConfigRequest):
    try:
        # 1. Generate docker-compose.yml content
        docker_compose = {
            "version": "3.8",
            "services": {
                "aegis-core-b": {
                    "image": "aegis-core:latest", # Assuming user will build or pull this
                    "command": "python -m aegis_core.core_b",
                    "ports": [
                        f"{config.core_b_grpc_port}:{config.core_b_grpc_port}",
                        f"{config.core_b_http_port}:{config.core_b_http_port}"
                    ],
                    "environment": {
                        "TARGET_APP_URL": config.backend_url,
                        "GRPC_PORT": str(config.core_b_grpc_port),
                        "CORE_B_HTTP_PORT": str(config.core_b_http_port),
                        "SESSION_TTL": str(config.session_ttl),
                        "REDIS_URL": config.redis_url
                    },
                    "networks": ["aegis-net"]
                },
                "aegis-core-a": {
                    "image": "aegis-core:latest",
                    "command": "python -m aegis_core.core_a",
                    "ports": [
                        f"{config.core_a_port}:8000"
                    ],
                    "environment": {
                        "CORE_B_GRPC_TARGET": f"aegis-core-b:{config.core_b_grpc_port}",
                        "CORE_B_HTTP_URL": f"http://aegis-core-b:{config.core_b_http_port}",
                        "CORE_A_PORT": "8000"
                    },
                    "depends_on": ["aegis-core-b"],
                    "networks": ["aegis-net"]
                }
            },
            "networks": {
                "aegis-net": {
                    "driver": "bridge"
                }
            }
        }

        if config.use_redis:
            docker_compose["services"]["redis"] = {
                "image": "redis:alpine",
                "ports": ["6379:6379"],
                "networks": ["aegis-net"]
            }

        docker_compose_yaml = yaml.dump(docker_compose, sort_keys=False)

        # 2. Generate .env files (optional, but good practice to separate secrets)
        # For simplicity in this Wizard, we put env vars directly in compose,
        # but we also provide a README.

        readme_content = f"""# Aegis Deployment

1. Ensure you have Docker and Docker Compose installed.
2. Build the base image if you haven't:
   `docker build -t aegis-core:latest .` (from the root of the aegis-core repo)
3. Run the stack:
   `docker-compose up -d`

Your Aegis Core A is listening on port {config.core_a_port}.
It forwards traffic securely to Core B, which sends it to {config.backend_url}.
"""

        # 3. Create ZIP
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr("docker-compose.yml", docker_compose_yaml)
            zip_file.writestr("README.txt", readme_content)

        zip_buffer.seek(0)

        return Response(
            content=zip_buffer.getvalue(),
            media_type="application/zip",
            headers={"Content-Disposition": "attachment; filename=aegis_config.zip"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Serve Frontend Static Files (Must be last to avoid overriding API routes)
if os.path.exists("/app/static"):
    app.mount("/", StaticFiles(directory="/app/static", html=True), name="static")
