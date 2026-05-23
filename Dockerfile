FROM node:20-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY . .
COPY --from=frontend /app/frontend/dist ./frontend/dist
# Bake the local cravings.db as a read-only seed of food_items + restaurants.
# The live DB lives on a volume mount at /app/cravings.db; on startup
# db.seed_sync UPSERTs content rows seed -> live without touching user data.
RUN mkdir -p /app/seed /app/images/food /app/images/cuisines \
    && if [ -f /app/cravings.db ]; then mv /app/cravings.db /app/seed/cravings.db; \
       else echo "ERROR: cravings.db missing from build context" >&2; exit 1; fi
ENV CRAVINGS_SEED_DB=/app/seed/cravings.db
ENV CRAVINGS_IMAGES_ROOT=/app/images
EXPOSE 8080
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
