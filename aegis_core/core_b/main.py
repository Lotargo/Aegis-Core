import os
import grpc
import httpx
import asyncio
from concurrent import futures
import json

from fastapi import FastAPI, Response

from .. import aegis_pb2_grpc
from .. import aegis_pb2
from ..crypto import CryptoEngine

# --- Конфигурация ---
TARGET_APP_URL = os.getenv("TARGET_APP_URL", "http://localhost:8081")
GRPC_PORT = int(os.getenv("GRPC_PORT", 50052))

# --- Крипто-движок и управление сессиями ---
crypto = CryptoEngine()
session_keys = {}

# --- gRPC Сервис ---
class AegisGatewayServicer(aegis_pb2_grpc.AegisGatewayServicer):

    def HealthCheck(self, request, context):
        return aegis_pb2.HealthCheckResponse(status=aegis_pb2.HealthCheckResponse.ServingStatus.SERVING)

    async def Process(self, request: aegis_pb2.AegisRequest, context):
        client_pub_key_pem = request.public_key

        if client_pub_key_pem not in session_keys:
            session_key = crypto.derive_shared_key(client_pub_key_pem)
            session_keys[client_pub_key_pem] = session_key
        else:
            session_key = session_keys[client_pub_key_pem]

        try:
            method = request.metadata.get("method")
            path = request.metadata.get("path")
            associated_data = json.dumps({ "method": method, "path": path }).encode()

            decrypted_payload = crypto.decrypt(session_key, request.encrypted_payload, associated_data)

            payload_data = json.loads(decrypted_payload)
            headers = payload_data['headers']
            body = payload_data['body'].encode()

        except Exception as e:
            return aegis_pb2.AegisResponse(fake_http_status=400)

        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(method=method, url=f"{TARGET_APP_URL}{path}", content=body, headers=headers)

                response_payload = {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "body": response.text,
                }
                response_payload_bytes = json.dumps(response_payload).encode()

                response_metadata = {"status": str(response.status_code)}
                response_ad = json.dumps(response_metadata).encode()

                encrypted_response = crypto.encrypt(session_key, response_payload_bytes, response_ad)

                return aegis_pb2.AegisResponse(
                    fake_http_status=200,
                    encrypted_payload=encrypted_response,
                    metadata=response_metadata
                )

            except httpx.RequestError as e:
                return aegis_pb2.AegisResponse(fake_http_status=500, encrypted_payload=str(e).encode())

# --- Приложение FastAPI ---
app = FastAPI(title="Aegis Core B")

@app.get("/public-key")
def get_public_key():
    return Response(content=crypto.public_key_bytes, media_type="application/x-pem-file")

async def serve_grpc():
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    aegis_pb2_grpc.add_AegisGatewayServicer_to_server(AegisGatewayServicer(), server)
    listen_addr = f'[::]:{GRPC_PORT}'
    server.add_insecure_port(listen_addr)
    await server.start()
    await server.wait_for_termination()

@app.on_event("startup")
async def startup_event():
    global grpc_server_task
    grpc_server_task = asyncio.create_task(serve_grpc())

@app.on_event("shutdown")
async def shutdown_event():
    if grpc_server_task:
        grpc_server_task.cancel()
        try:
            await grpc_server_task
        except asyncio.CancelledError:
            pass

@app.get("/health")
def health_check():
    return {"status": "ok"}
