# Stage 1: Build Vue SPA
FROM node:20-alpine AS frontend-build

RUN npm install -g pnpm

WORKDIR /app/frontend

COPY frontend/pnpm-lock.yaml frontend/package.json frontend/.npmrc ./
RUN pnpm install --frozen-lockfile

COPY frontend/ ./
RUN pnpm build
# Output: /app/backend/static_build/spa (per vite.config.ts outDir)

# Stage 2: Django runtime
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Install Python dependencies via uv (frozen = respektuje uv.lock)
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev

COPY backend ./backend

# Copy Vue build output from frontend stage
COPY --from=frontend-build /app/backend/static_build ./backend/static_build

WORKDIR /app/backend

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate && python manage.py collectstatic --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:8000"]
