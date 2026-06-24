FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# system packages if needed
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# install uv
RUN pip install --no-cache-dir uv

# copy dependency files first for layer caching
COPY pyproject.toml uv.lock ./

# install dependencies from pyproject + uv.lock
RUN uv sync --frozen --no-dev

# copy backend code
COPY . .

# App Service injects PORT; default to 8000 locally
CMD ["sh", "-c", ". .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]