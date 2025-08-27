# Public, reproducible base with CUDA 12.1
FROM runpod/base:0.6.2-cuda12.1.0

# System deps: git (for pip+git), ffmpeg (mp3), libsndfile (for soundfile)
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    git ffmpeg libsndfile1 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Be nice to the resolver
RUN python -m pip install --upgrade --no-cache-dir pip setuptools wheel

# CUDA 12.1 wheels for torch/torchaudio
ENV PIP_EXTRA_INDEX_URL=https://download.pytorch.org/whl/cu121

# Optional caches + faster HF pulls
ENV HF_HOME=/root/.cache/huggingface
ENV TRANSFORMERS_CACHE=/root/.cache/huggingface/transformers
ENV AUDIOCRAFT_CACHE=/root/.cache/audiocraft
ENV HF_HUB_ENABLE_HF_TRANSFER=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY handler.py .

# serverless entrypoint is provided by the runpod Python lib in handler.py
