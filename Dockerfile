FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for PaddleOCR, PyMuPDF, and python-magic
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    libglib2.0-0 \
    libgl1 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libfontconfig1 \
    libfreetype6 \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY main.py .

# Pre-download PaddleOCR models (caches models in the image for faster cold starts)
RUN python -c "from paddleocr import PaddleOCR; PaddleOCR(use_gpu=False, use_angle_cls=True, lang='en')"

# Environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

# Run with uvicorn
CMD uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1
