# Simplified Dockerfile since we can't run multi-stage properly in this environment
# We assume the frontend is already built in ./dist

FROM python:3.10-slim

WORKDIR /app

# Install backend dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy PRE-BUILT frontend assets
COPY dist/ /app/static/

# Environment setup
ENV PYTHONPATH=/app

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
