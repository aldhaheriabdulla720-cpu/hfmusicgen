FROM runpod/base:0.6.2-cuda12.1.0

# System deps
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    git ffmpeg libsndfile1 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Env
ENV PIP_NO_CACHE_DIR=1
ENV PIP_EXTRA_INDEX_URL=https://download.pytorch.org/whl/cu121
ENV HF_HOME=/root/.cache/huggingface
ENV TRANSFORMERS_CACHE=/root/.cache/huggingface/transformers
ENV AUDIOCRAFT_CACHE=/root/.cache/audiocraft
ENV HF_HUB_ENABLE_HF_TRANSFER=1
ENV TOKENIZERS_PARALLELISM=false
ENV PYTHONUNBUFFERED=1

# Tooling
RUN python3 -m pip install --upgrade pip setuptools wheel

# ✅ Pin NumPy BEFORE everything else (prevents the runtime crash)
RUN python3 -m pip install "numpy==1.25.2"

# Python deps
COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# App
COPY handler.py .

# Start serverless worker
CMD ["python3", "-u", "handler.py"]
