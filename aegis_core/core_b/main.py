import os
import grpc
import httpx
import asyncio
from concurrent import futures
import json
import time
import random

from fastapi import FastAPI, Response

from .. import aegis_pb2_grpc
from .. import aegis_pb2
from ..crypto import CryptoEngine

# --- Конфигурация ---
TARGET_APP_URL = os.getenv("TARGET_APP_URL", "http://localhost:8081")
GRPC_PORT = int(os.getenv("GRPC_PORT", 50052))
SESSION_TTL = int(os.getenv("SESSION_TTL", 600))  # 10 minutes default

# --- Крипто-движок и управление сессиями ---
crypto = CryptoEngine()
session_store = {}  # { public_key_pem: { "key": key, "created_at": timestamp } }

# --- gRPC Сервис ---
class AegisGatewayServicer(aegis_pb2_grpc.AegisGatewayServicer):

    def HealthCheck(self, request, context):
        return aegis_pb2.HealthCheckResponse(status=aegis_pb2.HealthCheckResponse.ServingStatus.SERVING)

    async def Process(self, request: aegis_pb2.AegisRequest, context):
        client_pub_key_pem = request.public_key

        current_time = time.time()

        # Session Management & Expiration
        if client_pub_key_pem not in session_store:
            session_key = crypto.derive_shared_key(client_pub_key_pem)
            session_store[client_pub_key_pem] = {
                "key": session_key,
                "created_at": current_time
            }
        else:
            session_data = session_store[client_pub_key_pem]
            if current_time - session_data["created_at"] > SESSION_TTL:
                # Session Expired
                del session_store[client_pub_key_pem]
                await context.abort(grpc.StatusCode.UNAUTHENTICATED, "Session expired. Please re-handshake.")
                return
            session_key = session_data["key"]

        try:
            # We now expect associated_data to be empty or minimal,
            # as real path/method are inside the encrypted payload for obfuscation.
            # However, to keep backward compatibility or AD check, we use an empty dict or specific Context ID.
            # Let's assume AD is fixed to "{}" for now or passed from client.
            # The client sends associated_data based on what it signed.
            # If client sends metadata, we use it for AD, but NOT for routing.

            # Extract metadata for AD verification only
            ad_dict = dict(request.metadata)
            associated_data = json.dumps(ad_dict).encode()

            decrypted_payload = crypto.decrypt(session_key, request.encrypted_payload, associated_data)
            payload_data = json.loads(decrypted_payload)

            # Routing info is now INSIDE the encrypted envelope
            method = payload_data.get('method')
            path = payload_data.get('path')
            headers = payload_data.get('headers')
            body = payload_data.get('body').encode()

            if not method or not path:
                 raise ValueError("Missing routing information in encrypted payload")

        except Exception as e:
            # If decryption fails, we return a generic error or deception
            print(f"Decryption/Processing error: {e}")
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

                # Active Deception: Randomize the outer status code
                # 50% chance of being honest, 50% chance of lying
                if random.choice([True, False]):
                    fake_status = response.status_code
                else:
                    fake_status = random.choice([200, 404, 503, 403, 500])

                return aegis_pb2.AegisResponse(
                    fake_http_status=fake_status,
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
