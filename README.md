# Worker Safety Detection System v2

> **Real-time AI-powered PPE compliance monitoring platform for industrial environments.**  
> Detects safety violations (missing helmets, missing vests) across multiple live camera feeds and delivers instant WebSocket alerts to a React dashboard.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Features](#features)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Option 1 — Docker Compose (Recommended)](#option-1--docker-compose-recommended)
  - [Option 2 — Manual Local Setup](#option-2--manual-local-setup)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Detection Pipeline](#detection-pipeline)
- [PPE Compliance Logic](#ppe-compliance-logic)
- [Alert System](#alert-system)
- [Frontend Pages](#frontend-pages)
- [Default Credentials](#default-credentials)
- [Known Limitations](#known-limitations)

---

## Overview

Worker Safety Detection System v2 is a full-stack platform that monitors CCTV/webcam feeds in real time, detects Personal Protective Equipment (PPE) compliance violations using YOLOv8, and immediately alerts supervisors via a live dashboard and optional email.

The system processes video frames through a multi-threaded camera manager, publishes events to Redis, and broadcasts them to all connected browser clients over WebSockets — all with sub-second latency.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Browser (React + Vite)                    │
│   Dashboard · Cameras · Violations · Analytics · Alerts · Login │
└────────────────────────┬────────────────────────────────────────┘
                         │  REST + WebSocket (port 8001)
┌────────────────────────▼────────────────────────────────────────┐
│                    FastAPI Backend (Python 3.11)                  │
│                                                                   │
│  ┌─────────────┐  ┌────────────────┐  ┌──────────────────────┐  │
│  │ Auth Router  │  │ Violation/Stats│  │  WebSocket Router    │  │
│  │ (JWT + OTP)  │  │    Routers     │  │  (real-time alerts)  │  │
│  └─────────────┘  └────────────────┘  └──────────────────────┘  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │               Detection Layer (detection/)                │   │
│  │                                                           │   │
│  │  CameraManager  →  CameraStream (per thread)             │   │
│  │       ↓                    ↓                              │   │
│  │  SafetyDetector       PPEDetector                        │   │
│  │  (YOLOv8 + FPS HUD)   (multi-class spatial matching)     │   │
│  │       ↓                                                   │   │
│  │  EventPublisher  →  Redis Pub/Sub                        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌──────────────────┐   ┌──────────────────┐                    │
│  │  AlertService     │   │  ViolationConsumer│                   │
│  │  (severity class) │   │  (background task)│                   │
│  └──────────────────┘   └──────────────────┘                    │
│                                                                   │
│  SQLite (violations + users)       Redis (pub/sub + frame cache) │
└─────────────────────────────────────────────────────────────────┘
```

Each camera runs in its own background thread. Detected frames are JPEG-encoded and stored in Redis (5-second TTL). Violations are published to the `violations.raw` channel, consumed by `AlertService`, enriched with severity, and broadcast over WebSocket to all browser clients.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Detection / ML | YOLOv8 (`ultralytics`), OpenCV |
| Backend API | FastAPI, Uvicorn, Pydantic v2 |
| Auth | JWT (python-jose), bcrypt (passlib), OTP |
| Database | SQLAlchemy + SQLite |
| Message Broker | Redis 7 (Pub/Sub + frame cache) |
| Frontend | React 19, TypeScript, Vite 8 |
| State / Data | TanStack Query v5, Axios |
| UI | Recharts, Lucide React, React Hot Toast |
| Routing | React Router v7 |
| Containerisation | Docker + Docker Compose |

---

## Features

- **Multi-camera live streaming** — MJPEG stream endpoint per camera; supports webcam (index), RTSP, and HTTP sources
- **Dual-model detection pipeline** — General `SafetyDetector` (YOLOv8n) with a specialised `PPEDetector` (multi-class model with spatial region matching)
- **PPE compliance classification** — Per-worker status: `FULLY_COMPLIANT`, `NO_HELMET`, `NO_VEST`, `NON_COMPLIANT`
- **Real-time alerts** — WebSocket broadcast to all dashboard tabs within milliseconds of a detection
- **Severity classification** — Violations rated `HIGH` (helmet), `MEDIUM` (vest), `LOW` (other)
- **Snapshot saving** — Annotated JPEG snapshots written to disk on every violation, served as static files
- **Cooldown-based alert throttling** — Configurable per camera+violation type to prevent alert spam
- **SMTP email alerts** — Optional async email delivery to configurable recipient list
- **JWT + OTP auth** — Password login and 6-digit OTP login; admin/viewer role separation
- **Analytics dashboard** — Violation trends by hour, by type, per-camera breakdown
- **Docker-native deployment** — Two-stage Dockerfile builds frontend then serves everything from one container

---

## Project Structure

```
Worker-safety-detection-System-v2/
├── app.py                          # Standalone Streamlit prototype (legacy, not part of main system)
├── Dockerfile                      # Multi-stage: frontend build → Python backend
├── docker-compose.yml              # Backend + Frontend (dev) + Redis
├── .env.example                    # All configurable environment variables
│
├── detection/                      # Core ML detection layer (framework-agnostic)
│   ├── engine.py                   # SafetyDetector: YOLOv8 inference, FPS tracking, snapshot saving
│   ├── camera_manager.py           # CameraManager + CameraStream (threaded per-camera capture)
│   ├── ppe_detector.py             # PPEDetector: spatial region matching for helmet/vest compliance
│   ├── event_publisher.py          # Redis publisher (violations.raw, frame cache, metrics)
│   └── alert_manager.py            # Cooldown logic + SMTP email alerts
│
├── backend/
│   └── app/
│       ├── main.py                 # FastAPI app: lifespan, camera seeding, MJPEG stream, CORS
│       ├── config.py               # Pydantic Settings (reads .env)
│       ├── core/
│       │   ├── redis_client.py     # Async Redis client wrapper
│       │   └── ws_manager.py       # WebSocket connection manager (broadcast)
│       ├── models/
│       │   ├── database.py         # SQLAlchemy models: User, Violation, Camera
│       │   └── schemas.py          # Pydantic request/response schemas
│       ├── routers/
│       │   ├── auth.py             # /api/auth/* — register, login, OTP, /me
│       │   ├── cameras.py          # /api/cameras/* — add, remove, list, info
│       │   ├── detect.py           # /api/detect — upload frame for inference
│       │   ├── violations.py       # /api/violations — CRUD + filtering
│       │   ├── stats.py            # /api/stats — aggregated metrics
│       │   ├── ppe.py              # /api/ppe — PPE-specific detection endpoint
│       │   └── websockets.py       # /ws — WebSocket upgrade
│       ├── services/
│       │   ├── detection_service.py
│       │   ├── ppe_service.py
│       │   └── alert_service.py    # Consumes violations.raw, classifies severity, broadcasts
│       └── workers/
│           └── event_consumer.py   # Background task: persists Redis events to SQLite
│
└── frontend/
    └── src/
        ├── App.tsx                 # Router + layout
        ├── api/client.ts           # Axios instance with auth interceptors
        ├── context/
        │   ├── AuthContext.tsx     # JWT storage + login state
        │   └── WebSocketContext.tsx # WS connection + incoming alert stream
        └── pages/
            ├── LoginPage.tsx       # JWT login form
            ├── DashboardPage.tsx   # Live stats + recent alerts
            ├── CamerasPage.tsx     # Add/remove cameras + live MJPEG feed
            ├── IncidentsPage.tsx   # Filterable violations table + snapshot preview
            ├── AnalyticsPage.tsx   # Recharts: violations by hour + by type
            └── AlertsPage.tsx      # Real-time incoming alert feed
```

---

## Getting Started

### Prerequisites

- Docker ≥ 24 and Docker Compose v2 **or** Python 3.11+ and Node.js 20+
- A YOLOv8n model file (`yolov8n.pt`) in the project root — downloaded automatically by `ultralytics` on first run if absent
- *(Optional)* A specialised PPE model at `backend/models/ppe.pt` — the system falls back gracefully to `yolov8n.pt` without it

---

### Option 1 — Docker Compose (Recommended)

```bash
# 1. Clone the repo
git clone https://github.com/<your-username>/Worker-safety-detection-System-v2.git
cd Worker-safety-detection-System-v2

# 2. Copy and edit environment file
cp .env.example .env
# Minimum: change SECRET_KEY

# 3. Build and start all services
docker compose up --build

# Backend API:  http://localhost:8000
# Frontend:     http://localhost:5173
# Redis:        localhost:6379
```

> **Note:** The Docker Compose file maps port `8000` for the backend container. The app internally starts on `8001` in manual mode — make sure your `.env` `ALLOWED_ORIGINS` matches whichever URL the frontend is served from.

---

### Option 2 — Manual Local Setup

**Backend**

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Copy environment file
cp .env.example .env

# Start Redis (requires Docker or a local Redis install)
docker run -d -p 6379:6379 redis:7-alpine

# Run the backend
uvicorn backend.app.main:app --host 0.0.0.0 --port 8001 --reload
```

**Frontend**

```bash
cd frontend
npm install
npm run dev
# Runs at http://localhost:5173
```

---

## Configuration

All settings are loaded from environment variables or a `.env` file at the project root. Copy `.env.example` to `.env` and set values as needed.

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | `change-me-in-production` | JWT signing key — **must change in production** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `480` | JWT lifetime (8 hours) |
| `OTP_EXPIRY_MINUTES` | `10` | OTP code validity window |
| `DB_URL` | `sqlite:///./data/safety.db` | SQLAlchemy database URL |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection string |
| `MODEL_PATH` | `yolov8n.pt` | Path to primary YOLO model |
| `SNAPSHOT_DIR` | `snapshots` | Directory for violation images |
| `CONF_THRESHOLD` | `0.4` | Minimum YOLO confidence to flag a detection |
| `ALERT_COOLDOWN_SECONDS` | `30` | Minimum gap between repeat alerts per camera |
| `ALLOWED_ORIGINS` | `http://localhost:5173,...` | CORS allowed origins (comma-separated) |
| `SMTP_HOST` | *(empty)* | SMTP server for email alerts |
| `SMTP_PORT` | `587` | SMTP port |
| `SMTP_USER` | *(empty)* | SMTP username / sender address |
| `SMTP_PASSWORD` | *(empty)* | SMTP password or app password |
| `ALERT_RECIPIENTS` | *(empty)* | Comma-separated alert email recipients |

---

## API Reference

All protected routes require `Authorization: Bearer <token>` header.

### Auth

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/auth/register` | None | Create new user (`admin` or `viewer` role) |
| `POST` | `/api/auth/login` | None | Returns JWT token |
| `POST` | `/api/auth/otp/send` | None | Generate and send OTP for email |
| `POST` | `/api/auth/otp/verify` | None | Verify OTP, returns JWT |
| `GET` | `/api/auth/me` | Required | Returns current user profile |

### Cameras

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/cameras` | Required | Add a camera by ID and source |
| `DELETE` | `/api/cameras/{id}` | Admin | Stop and remove a camera |
| `GET` | `/api/cameras` | Required | List all cameras with status |
| `GET` | `/api/cameras/{id}/stream` | Required | MJPEG live stream |
| `GET` | `/api/cameras/{id}/info` | Required | Camera runtime info (FPS, uptime, violation count) |

### Detection

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/detect` | Required | Upload a JPEG/PNG frame, returns detections + annotated image (base64) |
| `POST` | `/api/ppe` | Required | Run PPE-specific detection on an uploaded frame |

### Violations

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/api/violations` | Required | Paginated list; filter by `type`, `camera_id`, `from`, `to` |
| `GET` | `/api/violations/{id}` | Required | Single violation record |
| `DELETE` | `/api/violations/{id}` | Admin | Delete a record |

### Stats

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/api/stats` | Required | Totals, today count, active cameras, violations by type and hour |
| `GET` | `/api/stats/cameras` | Required | Per-camera violation breakdown |

### Other

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/health` | None | Health check |
| `GET` | `/api/alerts/recent` | None | Last 20 processed alerts |
| `WS` | `/ws` | None | WebSocket — receives real-time `SAFETY_ALERT` events |
| `GET` | `/snapshots/{filename}` | None | Static violation snapshot image |

Interactive docs available at `http://localhost:8001/docs` (Swagger UI).

---

## Detection Pipeline

```
Camera Source (webcam / RTSP / HTTP)
        ↓
CameraStream thread (15 FPS cap)
        ↓
SafetyDetector.process_frame()
   • YOLOv8 inference at conf ≥ 0.4
   • Person class → NO_HELMET violation (fallback when no PPE model)
   • Bounding box annotation + HUD overlay (FPS, violation count, camera ID)
   • Snapshot JPEG saved to /snapshots/
        ↓
EventPublisher (sync Redis)
   • Frame bytes → Redis key  frame_{camera_id}  (TTL: 5s)
   • Violation dict → Redis channel  violations.raw
   • Metrics (FPS, uptime) → Redis channel  stats.metrics  (every 30 frames)
        ↓
ViolationConsumer (async background task)
   • Reads violations.raw
   • Persists Violation record to SQLite
        ↓
AlertService (async background task)
   • Reads violations.raw
   • Classifies severity: HIGH (helmet) / MEDIUM (vest) / LOW (other)
   • Broadcasts SAFETY_ALERT JSON over WebSocket to all browser clients
```

---

## PPE Compliance Logic

The `PPEDetector` uses **regional spatial matching** to associate helmet and vest detections with each detected person:

- **Head region** — top 30% of each person bounding box; helmets must have their centre within this region
- **Torso region** — 30%–80% of person height; vests must centre within this band
- Helmet and vest matches require confidence ≥ 0.5

**Compliance status assigned per worker:**

| Status | Condition |
|---|---|
| `FULLY_COMPLIANT` | Helmet ✓ + Vest ✓ |
| `NO_VEST` | Helmet ✓, Vest ✗ |
| `NO_HELMET` | Helmet ✗, Vest ✓ |
| `NON_COMPLIANT` | Helmet ✗ + Vest ✗ |

Bounding box colour coding: green (compliant), yellow (partial), red (non-compliant).

If the specialised `backend/models/ppe.pt` model is absent, the system falls back to `yolov8n.pt` and flags every detected person as `NO_HELMET` — a conservative safe-fail mode.

---

## Alert System

`AlertManager` applies per `(camera_id, violation_type)` cooldown windows (default 30 seconds) to prevent the same camera from flooding the alert feed. After cooldown, it:

1. Records the alert in a 500-entry in-memory ring buffer
2. Logs a warning
3. Fires an async SMTP email to all configured recipients (non-blocking thread)

`AlertService` additionally enriches each violation with a severity label and broadcasts to all WebSocket clients:

```json
{
  "type": "SAFETY_ALERT",
  "severity": "HIGH",
  "camera_id": "webcam",
  "violation_type": "NO_HELMET",
  "timestamp": 1717000000.0,
  "confidence": 0.87,
  "snapshot_path": "snapshots/violation_webcam_1717000000_a1b2c3.jpg",
  "message": "HIGH Severity: NO_HELMET detected on webcam"
}
```

---

## Frontend Pages

| Page | Route | Description |
|---|---|---|
| Login | `/login` | JWT authentication |
| Dashboard | `/` | Live KPI cards (total violations, today count, active cameras) + recent alert feed |
| Cameras | `/cameras` | Add/remove cameras, live MJPEG stream embed, per-camera stats |
| Incidents | `/incidents` | Searchable/filterable violation log with snapshot thumbnails |
| Analytics | `/analytics` | Recharts bar charts: violations by hour (last 24h) and by type |
| Alerts | `/alerts` | Real-time incoming WebSocket alert stream |

The `WebSocketContext` maintains the WS connection globally; any tab receives live alerts immediately without polling.

---

## Default Credentials

On first startup, the system seeds a default admin account:

| Field | Value |
|---|---|
| Email | `admin@safeguard.local` |
| Password | `admin1234` |

**Change this immediately in any non-local environment.**  
The OTP debug endpoint also returns the generated OTP in the response body — remove `otp_debug` from `auth.py` before deploying to production.

---

## Known Limitations

- **Fallback violation logic** — When no specialised PPE model (`ppe.pt`) is available, every detected person is flagged as `NO_HELMET`. This is intentionally conservative but will produce false positives. Supply a proper multi-class PPE model for accurate compliance detection.
- **SQLite concurrency** — SQLite works fine for single-node deployments. Replace with PostgreSQL for multi-instance or high-throughput scenarios.
- **OTP email delivery** — OTP sending (`/api/auth/otp/send`) requires SMTP credentials; without them the OTP is returned in the response body (dev convenience only — remove before production).
- **Redis required** — The background workers depend on Redis. If Redis is unavailable at startup, alert processing and WebSocket broadcasts will be disabled; frame capture and local violation recording still function.
- **15 FPS cap** — Camera streams are capped at 15 FPS by default to manage CPU usage on YOLO inference. Adjustable via `CameraStream.fps_limit`.
