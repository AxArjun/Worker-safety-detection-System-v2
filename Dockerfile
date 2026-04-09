# ──────────────────────────────────────────────────────────
# Stage 1: Build frontend
# ──────────────────────────────────────────────────────────
FROM node:20-alpine AS frontend-build
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ──────────────────────────────────────────────────────────
# Stage 2: Python backend
# ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS backend

# System deps for OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 libsm6 libxrender1 libxext6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./backend/
COPY detection/ ./detection/
COPY yolov8n.pt ./

# Copy built frontend into static serving dir
COPY --from=frontend-build /frontend/dist ./frontend/dist

# Create runtime directories
RUN mkdir -p snapshots data

# Environment defaults (override at runtime)
ENV PYTHONUNBUFFERED=1 \
    MODEL_PATH=yolov8n.pt \
    DB_URL=sqlite:///./data/safety.db \
    SNAPSHOT_DIR=snapshots

EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
