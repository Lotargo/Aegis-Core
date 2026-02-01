# Troubleshooting Guide

## "Everything is a 404!"
If you are inspecting the network traffic between Core A and Core B (e.g., using Wireshark or a gRPC debugger) and you see a lot of `503`, `404`, or `500` errors, **DO NOT PANIC**.

This is the **Deception Engine** working as intended.
1.  Check the logs of **Core A**. If it says `200 OK`, then the request succeeded.
2.  Check the logs of **Core B**. It will show the real status code sent to the backend.

## Session Expiry Loops
If you see repeated "Session expired. Renewing key..." messages in Core A logs:
1.  Check your `SESSION_TTL` on Core B. Is it too short (e.g., < 1 second)?
2.  Check time synchronization. If Core A and Core B are on different servers with desynchronized clocks, the token might appear expired instantly.

## "Missing routing information" Error
If Core B logs `ValueError: Missing routing information in encrypted payload`:
1.  Ensure you are using a compatible version of Core A.
2.  Older versions of Core A sent routing info in gRPC metadata. Newer versions (MTD-enabled) send it in the encrypted JSON.
3.  **Upgrade Core A.**

## gRPC Connection Refused
1.  Ensure Core B is running (`ps aux | grep core_b`).
2.  Check `CORE_B_GRPC_TARGET` in Core A env vars.
3.  Ensure the port (default 50051) is exposed in Docker/Firewall.
