import os
import io
import base64
import uuid
import subprocess
from typing import Dict, Any

import runpod
import torch
import soundfile as sf
from audiocraft.models import MusicGen

# --- Model load at cold start ---
MODEL_NAME = os.getenv("MODEL_NAME", "facebook/musicgen-small")
device = "cuda" if torch.cuda.is_available() else "cpu"

model = MusicGen.get_pretrained(MODEL_NAME, device=device)
# default generation params (override per request)
model.set_generation_params(duration=10)

def _to_mp3(wav_bytes: bytes) -> bytes:
    """Convert WAV bytes -> MP3 bytes using ffmpeg."""
    in_path = f"/tmp/{uuid.uuid4().hex}.wav"
    out_path = f"/tmp/{uuid.uuid4().hex}.mp3"
    with open(in_path, "wb") as f:
        f.write(wav_bytes)
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", in_path, "-vn", "-ar", "32000", "-b:a", "192k", out_path
    ]
    subprocess.run(cmd, check=True)
    with open(out_path, "rb") as f:
        return f.read()

def handler(event: Dict[str, Any]) -> Dict[str, Any]:
    inp = (event or {}).get("input", {}) if isinstance(event, dict) else {}
    prompt = inp.get("prompt", "lofi chill beat, warm keys, mellow, relaxing")
    duration = int(inp.get("duration", 10))
    seed = int(inp.get("seed", 42))
    fmt = str(inp.get("format", "mp3")).lower()  # "mp3" or "wav"

    torch.manual_seed(seed)
    model.set_generation_params(duration=duration)
    wav = model.generate([prompt], progress=False)[0].cpu().numpy()
    sr = 32000

    # Write WAV to memory
    wav_buf = io.BytesIO()
    sf.write(wav_buf, wav.T, sr, format="WAV")
    wav_bytes = wav_buf.getvalue()

    if fmt == "wav":
        audio_bytes = wav_bytes
        mime = "audio/wav"
    else:
        audio_bytes = _to_mp3(wav_bytes)
        mime = "audio/mpeg"

    b64 = base64.b64encode(audio_bytes).decode("utf-8")
    return {
        "model": MODEL_NAME,
        "prompt": prompt,
        "duration": duration,
        "format": fmt,
        "sample_rate": sr,
        "audio_base64": b64,
        "content_type": mime,
    }

runpod.serverless.start({"handler": handler})
