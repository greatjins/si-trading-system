# Multi-stage build for production
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# package.json 복사 및 의존성 설치
COPY frontend/package*.json ./
RUN npm install

# 소스 복사
COPY frontend/ ./

# PATH에 node_modules/.bin 추가하여 tsc, vite 실행 가능하게
ENV PATH="/app/frontend/node_modules/.bin:$PATH"

# 빌드 실행
RUN npm run build

# Python backend
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Python requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy built frontend
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]