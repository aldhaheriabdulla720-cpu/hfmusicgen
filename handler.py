import os, io, uuid, base64, subprocess, tempfile
from typing import Dict, Any

import torch
import soundfile as sf
import runpod
from audiocraft.models import MusicGen

MODEL_NAME     = os.getenv("MODEL_NAME", "facebook/musicgen-small")
MAX_DURATION   = int(os.getenv("MAX_DURATION", "30"))
DEFAULT_PROMPT = "lofi chill beat, warm keys, mellow, relaxing"

device = "cuda" if torch.cuda.is_available() else "cpu"
if device == "cuda":
    try:
        torch.set_float32_matmul_precision("medium")
    except Exception:
        pass

_model = None
SAMPLE_RATE = 32000  # will be updated after first load

def _ensure_model():
    global _model, SAMPLE_RATE
    if _model is None:
        m = MusicGen.get_pretrained(MODEL_NAME, device=device)
        if device == "cuda":
            try:
                m = m.to(torch.float16)
            except Exception:
                pass
        m.eval()
        _model = m
        SAMPLE_RATE = int(getattr(_model, "sample_rate", 32000))

def _to_mp3(wav_bytes: bytes, sr: int) -> bytes:
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False, dir="/tmp") as in_f:
        in_path = in_f.name
        in_f.write(wav_bytes)
    out_path = os.path.join("/tmp", f"{uuid.uuid4().hex}.mp3")
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", in_path, "-vn", "-ar", str(sr), "-b:a", "192k", out_path],
            check=True
        )
        with open(out_path, "rb") as f:
            return f.read()
    finally:
        for p in (in_path, out_path):
            try:
                if os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass

def handler(event: Dict[str, Any]) -> Dict[str, Any]:
    inp = (event or {}).get("input", {}) or {}

    # Instant readiness check path (no model load)
    if inp.get("healthcheck") or inp.get("warmup"):
        return {"ok": True, "ready": True, "device": device, "model": MODEL_NAME}

    prompt   = str(inp.get("prompt", DEFAULT_PROMPT))[:500]
    duration = int(inp.get("duration", 10))
    seed     = int(inp.get("seed", 42))
    fmt      = str(inp.get("format", "mp3")).lower()

    if duration < 1: duration = 1
    if duration > MAX_DURATION: duration = MAX_DURATION
    if fmt not in ("wav", "mp3"): fmt = "mp3"

    try:
        torch.manual_seed(seed)
        if device == "cuda":
            torch.cuda.manual_seed_all(seed)
    except Exception:
        pass

    try:
        _ensure_model()
        _model.set_generation_params(duration=duration)
        with torch.inference_mode():
            wav = _model.generate([prompt], progress=False)[0].cpu().numpy()
    except Exception as e:
        return {"error": f"generation_failed: {e.__class__.__name__}: {e}", "model": MODEL_NAME, "prompt": prompt, "duration": duration, "format": fmt}

    try:
        buf = io.BytesIO()
        sf.write(buf, wav.T, SAMPLE_RATE, format="WAV")
        wav_bytes = buf.getvalue()
    except Exception as e:
        return {"error": f"wav_encode_failed: {e}"}

    if fmt == "wav":
        audio_bytes, mime = wav_bytes, "audio/wav"
    else:
        try:
            audio_bytes = _to_mp3(wav_bytes, SAMPLE_RATE)
            mime = "audio/mpeg"
        except Exception:
            audio_bytes, mime = wav_bytes, "audio/wav"

    return {
        "model": MODEL_NAME,
        "prompt": prompt,
        "duration": duration,
        "format": fmt,
        "sample_rate": SAMPLE_RATE,
        "content_type": mime,
        "audio_base64": base64.b64encode(audio_bytes).decode("utf-8"),
    }

runpod.serverless.start({"handler": handler})
