import os
import requests
import whisper
from pydub import AudioSegment

# Sarvam sync STT API accepts audio <= 30 seconds.
SARVAM_PIECE_SECONDS = 25

# Local Whisper model configuration
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")

# Sarvam API configuration
SARVAM_STT_TRANSLATE_URL = "https://api.sarvam.ai/speech-to-text-translate"
SARVAM_MODEL = os.getenv("SARVAM_STT_MODEL", "saaras:v2.5")

# Whisper model cache
_model = None


def load_model():
    """Load Whisper model once and reuse it."""
    global _model
    if _model is None:
        print(f"Loading Whisper model: {WHISPER_MODEL} ...")
        _model = whisper.load_model(WHISPER_MODEL)
        print("Whisper model loaded.")
    return _model


def transcribe_chunk_whisper(chunk_path: str) -> list:
    """Transcribe an audio chunk using local Whisper and return segments with timestamps."""
    model = load_model()
    result = model.transcribe(chunk_path, task="transcribe")
    
    segments = []
    for seg in result.get("segments", []):
        segments.append({
            "start": round(seg["start"], 2),
            "end": round(seg["end"], 2),
            "text": seg["text"].strip()
        })
    return segments


def _send_to_sarvam(piece_path: str) -> str:
    """Send one <=25 second WAV file to Sarvam STT Translation API."""
    api_key = os.getenv("SARVAM_API_KEY")
    if not api_key:
        raise RuntimeError("SARVAM_API_KEY is not set in environment / .env")

    headers = {
        "api-subscription-key": api_key
    }

    with open(piece_path, "rb") as f:
        files = {
            "file": (os.path.basename(piece_path), f, "audio/wav")
        }
        data = {
            "model": SARVAM_MODEL,
            "with_diarization": "false"
        }
        response = requests.post(
            SARVAM_STT_TRANSLATE_URL,
            headers=headers,
            files=files,
            data=data,
            timeout=120
        )

    if not response.ok:
        print(f"\n❌ Sarvam returned {response.status_code}")
        print(f"Response body: {response.text}\n")
        response.raise_for_status()

    result = response.json()
    return result.get("transcript", "")


def transcribe_chunk_sarvam(chunk_path: str) -> list:
    """
    Split audio chunk into 25-second pieces, send to Sarvam,
    and estimate timestamps for each piece.
    """
    audio = AudioSegment.from_wav(chunk_path)
    piece_ms = SARVAM_PIECE_SECONDS * 1000
    total_pieces = (len(audio) + piece_ms - 1) // piece_ms

    segments = []

    for i, start in enumerate(range(0, len(audio), piece_ms)):
        piece = audio[start:start + piece_ms]
        piece_path = f"{chunk_path}_sv_{i}.wav"
        piece.export(piece_path, format="wav")

        piece_duration = len(piece) / 1000.0
        start_seconds = start / 1000.0
        end_seconds = start_seconds + piece_duration

        try:
            print(f"  → Sarvam piece {i + 1}/{total_pieces} ...")
            text = _send_to_sarvam(piece_path)
            if text.strip():
                segments.append({
                    "start": round(start_seconds, 2),
                    "end": round(end_seconds, 2),
                    "text": text.strip()
                })
        finally:
            if os.path.exists(piece_path):
                os.remove(piece_path)

    return segments


def transcribe_chunk(chunk_path: str, language: str = "english") -> list:
    """Select transcription engine based on language choice."""
    if language.lower() == "hinglish":
        return transcribe_chunk_sarvam(chunk_path)
    return transcribe_chunk_whisper(chunk_path)


def transcribe_all(chunks: list, language: str = "english") -> list:
    """Transcribe all audio chunks and return a list of segments with offset-corrected timestamps."""
    full_transcript_segments = []
    engine = "Sarvam AI" if language.lower() == "hinglish" else "Whisper"
    print(f"Using {engine} for transcription.")

    current_offset = 0.0

    for i, chunk in enumerate(chunks):
        print(f"Transcribing chunk {i + 1}/{len(chunks)}...")
        segments = transcribe_chunk(chunk, language=language)

        for seg in segments:
            seg["start"] = round(seg["start"] + current_offset, 2)
            seg["end"] = round(seg["end"] + current_offset, 2)
            full_transcript_segments.append(seg)

        audio = AudioSegment.from_wav(chunk)
        current_offset += len(audio) / 1000.0

    print("Transcription complete.")
    return full_transcript_segments