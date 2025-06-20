FROM python:3.11-slim

# Install system dependencies for PyAudio, PortAudio, and other common packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        portaudio19-dev \
        ffmpeg \
        git \
        curl \
        && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better Docker caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Default command
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]