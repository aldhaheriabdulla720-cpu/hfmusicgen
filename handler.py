import os, io, uuid, base64, subprocess
from typing import Dict, Any
import runpod, torch, soundfile as sf
from audiocraft.models import MusicGen

MODEL_NAME = os.getenv("MODEL_NAME", "facebook/musicgen-small")
MAX_DURATION = int(os.getenv("MAX_DURATION", "30"))  # hard safety cap

device = "cuda" if torch.cuda.is_available() else "cpu"

# Load once (cold start)
model = MusicGen.get_pretrained(MODEL_NAME, device=device)
# Use model's declared sample rate when available (MusicGen uses 32k)
SAMPLE_RATE = int(getattr(model, "sample_rate", 32000))

def _to_mp3(wav_bytes: bytes, sr: int) -> bytes:
    in_p  = f"/tmp/{uuid.uuid4().hex}.wav"
    out_p = f"/tmp/{uuid.uuid4().hex}.mp3"
    with open(in_p, "wb") as f:
        f.write(wav_bytes)
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
             "-i", in_p, "-vn", "-ar", str(sr), "-b:a", "192k", out_p],
            check=True
        )
        with open(out_p, "rb") as f:
            return f.read()
    finally:
        # Best-effort cleanup
        try: os.remove(in_p)
        except: pass
        try: os.remove(out_p)
        except: pass

def handler(event: Dict[str, Any]) -> Dict[str, Any]:
    inp = (event or {}).get("input", {})

    prompt   = str(inp.get("prompt", "lofi chill beat, warm keys, mellow, relaxing"))
    duration = int(inp.get("duration", 10))
    seed     = int(inp.get("seed", 42))
    fmt      = str(inp.get("format", "mp3")).lower()

    # Basic input validation
    if duration < 1: duration = 1
    if duration > MAX_DURATION: duration = MAX_DURATION
    if fmt not in ("wav", "mp3"): fmt = "mp3"

    # Reproducibility
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    # Per-request params
    model.set_generation_params(duration=duration)

    with torch.inference_mode():
        wav = model.generate([prompt], progress=False)[0].cpu().numpy()

    # Write WAV to memory (sf expects (T, C))
    buf = io.BytesIO()
    sf.write(buf, wav.T, SAMPLE_RATE, format="WAV")
    wav_bytes = buf.getvalue()

    if fmt == "wav":
        audio_bytes, mime = wav_bytes, "audio/wav"
    else:
        audio_bytes, mime = _to_mp3(wav_bytes, SAMPLE_RATE), "audio/mpeg"

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
