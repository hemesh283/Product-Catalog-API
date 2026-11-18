# syntax=docker/dockerfile:1

# ---------- base: Python + production dependencies ----------
FROM python:3.14-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /code

COPY requirements.txt .
RUN pip install -r requirements.txt


# ---------- test: dev dependencies + tests, runs pytest ----------
FROM base AS test

COPY requirements-dev.txt .
RUN pip install -r requirements-dev.txt

COPY pytest.ini .
COPY app/ app/
COPY tests/ tests/

CMD ["pytest", "-v"]


# ---------- runtime: the image you ship ----------
FROM base AS runtime

RUN useradd --create-home --uid 10001 appuser

COPY app/ app/

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]