FROM runpod/base:0.6.2-cuda12.1.0

# System dependencies
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    git ffmpeg libsndfile1 python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Environment variables
ENV PIP_NO_CACHE_DIR=1
ENV PIP_EXTRA_INDEX_URL=https://download.pytorch.org/whl/cu121
ENV HF_HOME=/root/.cache/huggingface
ENV TRANSFORMERS_CACHE=/root/.cache/huggingface/transformers
ENV AUDIOCRAFT_CACHE=/root/.cache/audiocraft
ENV HF_HUB_ENABLE_HF_TRANSFER=1
ENV TOKENIZERS_PARALLELISM=false
ENV PYTHONUNBUFFERED=1

# Upgrade pip + setuptools + wheel
RUN python3 -m pip install --upgrade "pip<24.1" setuptools wheel

# Copy requirements first (for caching)
COPY requirements.txt .

# 🔹 Pin numpy BEFORE installing the rest so it doesn’t pull v2.x
RUN python3 -m pip install "numpy==1.26.4" \
 && python3 -m pip install -r requirements.txt

# Copy app code
COPY handler.py .

CMD ["python3", "-u", "handler.py"]
