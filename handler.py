import io
import base64
import runpod
import soundfile as sf
from audiocraft.models import MusicGen

# Load model at startup
model = MusicGen.get_pretrained("facebook/musicgen-small")

def handler(event):
    """
    event["input"] should contain:
    {
        "prompt": "text describing the music",
        "duration": 10   # seconds
    }
    """
    prompt = event["input"].get("prompt", "calm piano music")
    duration = int(event["input"].get("duration", 10))

    # Generate music
    model.set_generation_params(duration=duration)
    wav = model.generate([prompt])[0].cpu().numpy()

    # Save to memory as wav
    buffer = io.BytesIO()
    sf.write(buffer, wav.T, 32000, format="WAV")
    buffer.seek(0)

    # Encode to base64 for API return
    audio_b64 = base64.b64encode(buffer.read()).decode("utf-8")

    return {"audio_base64": audio_b64}

# Start RunPod serverless
runpod.serverless.start({"handler": handler})