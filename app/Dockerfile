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

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
