"""Audio input: anything soundfile can decode (wav, flac, ogg, mp3) -> 16 kHz mono float32 WAV. Video or exotic
containers go through ffmpeg if it is on PATH (optional dependency, never required for audio files)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import numpy as np

ORNEKLEME = 16000
GIZLI = getattr(subprocess, "CREATE_NO_WINDOW", 0)  # Windows: no console window for the child


def yukle(kaynak: Path) -> np.ndarray:
    import soundfile

    try:
        veri, hiz = soundfile.read(str(kaynak), dtype="float32", always_2d=True)
    except Exception as hata:  # soundfile cannot open it: try ffmpeg (video containers, exotic codecs)
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise RuntimeError(f"ses çözülemedi ({hata}); video/karma dosya için ffmpeg gerekir (PATH'te yok)") from hata
        cmd = [ffmpeg, "-nostdin", "-loglevel", "error", "-i", str(kaynak), "-f", "f32le", "-ac", "1", "-ar", str(ORNEKLEME), "-"]
        ham = subprocess.run(cmd, capture_output=True, check=True, creationflags=GIZLI).stdout
        return np.frombuffer(ham, dtype=np.float32).copy()
    mono = veri.mean(axis=1) if veri.shape[1] > 1 else veri[:, 0]
    if hiz != ORNEKLEME:
        import soxr

        mono = soxr.resample(mono, hiz, ORNEKLEME, quality="HQ").astype(np.float32)
    return np.ascontiguousarray(mono, dtype=np.float32)


def wav_yaz(hedef: Path, ses: np.ndarray) -> float:
    """Writes 16 kHz mono PCM16 WAV atomically (tmp + replace); returns duration in seconds."""
    import soundfile

    hedef.parent.mkdir(parents=True, exist_ok=True)
    gecici = hedef.with_name(hedef.name + ".part")
    soundfile.write(str(gecici), ses, ORNEKLEME, subtype="PCM_16", format="WAV")  # .part uzantısı biçimi vermez
    gecici.replace(hedef)
    return len(ses) / ORNEKLEME
