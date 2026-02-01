# Aegis Control Center (Dashboard)

The **Aegis Control Center** is a visual tool designed to simplify the deployment of Aegis Core. Instead of manually editing `docker-compose.yml` or `.env` files, you can use the graphical wizard to generate a secure configuration tailored to your infrastructure.

## Features

*   **Wizard Interface:** Step-by-step configuration of backend targets, ports, and security policies.
*   **Live Metrics:** Real-time monitoring of threat levels, active sessions, and deception effectiveness.
*   **One-Click Generation:** Downloads a ready-to-use ZIP archive containing `docker-compose.yml` and deployment instructions.

## Installation & Usage

The dashboard is delivered as a containerized application containing both the frontend (React) and the backend (FastAPI).

### Prerequisites
*   Docker installed on your local machine.

### Running the Dashboard

1.  Navigate to the dashboard directory:
    ```bash
    cd aegis_dashboard
    ```

2.  Build the Docker image:
    ```bash
    docker build -t aegis-dashboard .
    ```

3.  Run the container:
    ```bash
    docker run -p 8080:8080 aegis-dashboard
    ```

4.  Open your browser and go to:
    [http://localhost:8080](http://localhost:8080)

## Configuration Fields

| Field | Description | Example |
| :--- | :--- | :--- |
| **Target Backend URL** | The URL of the application you want to protect. | `http://my-api-server:8080` |
| **Core A Port** | The port where Aegis Core A will listen for incoming traffic. | `8000` |
| **Core B gRPC Port** | The encrypted communication channel port. | `50051` |
| **Session TTL** | How often session keys should rotate (in seconds). Lower is safer. | `600` |
| **Redis Rate Limiting** | Enable if you want protection against Brute Force attacks. | `On` |

> **Note on DoS Protection:**
> The `MAX_REQUEST_SIZE` (default 10MB) is currently configured via environment variables in the generated `docker-compose.yml` but is not yet exposed in the GUI wizard. You can edit the generated file to change this limit if needed.
