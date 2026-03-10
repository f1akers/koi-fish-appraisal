FROM python:3.11-slim

# Install system dependencies for OpenCV
RUN apt-get update && \
    apt-get install -y --no-install-recommends libgl1 libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy ML models
COPY models/ ./models/

# Copy application code and supporting data
COPY app/ ./app/
COPY images/ ./images/

# Production defaults
ENV DEBUG=False \
    MODEL_PATH=./models \
    IMAGES_PATH=./images \
    ALLOWED_ORIGINS="*" \
    PORT=8000

CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT
