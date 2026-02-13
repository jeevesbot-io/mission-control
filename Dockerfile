# Multi-stage production build: Vite frontend → FastAPI static mount
# Stage 1: Build frontend
FROM node:22-slim AS frontend-build

WORKDIR /frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ .
RUN npm run build

# Stage 2: Python runtime with built frontend
FROM python:3.13-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first for layer caching
COPY backend/pyproject.toml backend/uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy backend application code
COPY backend/ .

# Copy built frontend into static directory
COPY --from=frontend-build /frontend/dist ./static

EXPOSE 5050

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5050"]
