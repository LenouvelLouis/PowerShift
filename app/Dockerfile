FROM python:3.12-slim

WORKDIR /workspace

# System dependencies needed for PyPSA / numpy / scipy
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy only what is needed to install Python deps first (layer cache)
COPY pyproject.toml ./

# Install Python dependencies (non-editable for smaller image)
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

# Copy full source
COPY app/ ./app/

# Non-root user for security
RUN adduser --disabled-password --no-create-home --gecos "" appuser
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
