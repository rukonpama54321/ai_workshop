# Single-image build: compiles the React frontend and serves it from FastAPI.
# Used for the Render deploy so the whole app lives on one onrender.com URL
# (no separate frontend host, no CORS, no API proxy).

# Stage 1 — build the React app
FROM node:20-slim AS frontend
WORKDIR /fe
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2 — Python backend that also serves the built frontend
FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
COPY backend/tests ./tests
COPY --from=frontend /fe/dist ./static

ENV PYTHONPATH=/app
EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
