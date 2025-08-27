FROM python:3.10-slim

# System deps (include build tools for any native wheels)
RUN apt-get update && apt-get install -y             git ffmpeg libsndfile1 build-essential cmake             && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY handler.py ./

# Entrypoint for RunPod serverless
CMD ["python", "-u", "handler.py"]