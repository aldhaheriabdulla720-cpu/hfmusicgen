# RunPod serverless base with CUDA 12.1 + Python 3.10
FROM runpod/serverless:py3.10-cuda12.1

# System deps (ffmpeg for mp3, libsndfile for soundfile)
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    ffmpeg libsndfile1 git build-essential cmake && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Tell pip to use CUDA 12.1 wheels for torch/torchaudio
ENV PIP_EXTRA_INDEX_URL=https://download.pytorch.org/whl/cu121

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Optional: cache dirs for HF/audiocraft
ENV HF_HOME=/root/.cache/huggingface
ENV TRANSFORMERS_CACHE=/root/.cache/huggingface/transformers
ENV AUDIOCRAFT_CACHE=/root/.cache/audiocraft

COPY handler.py .

# The runpod/serverless base automatically starts the serverless handler.
