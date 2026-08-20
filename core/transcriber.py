import os
import requests
import whisper

from pydub import AudioSegment


# ============================================================
# CONFIGURATION
# ============================================================

# Sarvam sync STT API accepts audio <= 30 seconds.
# We use 25 seconds to keep a safety margin.
SARVAM_PIECE_SECONDS = 25

# Local Whisper model
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")

# Sarvam API configuration
SARVAM_STT_TRANSLATE_URL = "https://api.sarvam.ai/speech-to-text-translate"

SARVAM_MODEL = os.getenv(
    "SARVAM_STT_MODEL",
    "saaras:v2.5"
)

# Whisper model cache
_model = None


# ============================================================
# WHISPER
# ============================================================

def load_model():
    """
    Load Whisper model only once and reuse it.
    """

    global _model

    if _model is None:
        print(f"Loading Whisper model: {WHISPER_MODEL} ...")

        _model = whisper.load_model(WHISPER_MODEL)

        print("Whisper model loaded.")

    return _model


def transcribe_chunk_whisper(chunk_path: str) -> str:
    """
    Transcribe an audio chunk using local Whisper.
    """

    model = load_model()

    result = model.transcribe(
        chunk_path,
        task="transcribe"
    )

    return result["text"]


# ============================================================
# SARVAM
# ============================================================

def _send_to_sarvam(piece_path: str) -> str:
    """
    Send one <=25 second WAV file to Sarvam
    and return the transcript.
    """

    # IMPORTANT:
    # Read API key here instead of at module level.
    # This ensures .env has already been loaded.
    api_key = os.getenv("SARVAM_API_KEY")

    if not api_key:
        raise RuntimeError(
            "SARVAM_API_KEY is not set in environment / .env"
        )

    headers = {
        "api-subscription-key": api_key
    }

    with open(piece_path, "rb") as f:

        files = {
            "file": (
                os.path.basename(piece_path),
                f,
                "audio/wav"
            )
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

    # Handle API errors
    if not response.ok:

        print(
            f"\n❌ Sarvam returned "
            f"{response.status_code}"
        )

        print(
            f"Response body: "
            f"{response.text}\n"
        )

        response.raise_for_status()

    result = response.json()

    return result.get("transcript", "")


# ============================================================
# SARVAM CHUNK TRANSCRIPTION
# ============================================================

def transcribe_chunk_sarvam(chunk_path: str) -> str:
    """
    Sarvam sync API accepts <=30 seconds of audio.

    We split every audio chunk into 25-second pieces,
    send each piece to Sarvam,
    then combine all transcripts.
    """

    # Get API key at runtime
    api_key = os.getenv("SARVAM_API_KEY")

    if not api_key:
        raise RuntimeError(
            "SARVAM_API_KEY is not set in environment / .env"
        )

    # Load WAV file
    audio = AudioSegment.from_wav(chunk_path)

    # Convert seconds to milliseconds
    piece_ms = SARVAM_PIECE_SECONDS * 1000

    # Calculate number of pieces
    total_pieces = (
        len(audio) + piece_ms - 1
    ) // piece_ms

    full_text = ""

    # Process every piece
    for i, start in enumerate(
        range(0, len(audio), piece_ms)
    ):

        # Extract 25-second piece
        piece = audio[
            start:start + piece_ms
        ]

        # Temporary file
        piece_path = (
            f"{chunk_path}_sv_{i}.wav"
        )

        # Export as WAV
        piece.export(
            piece_path,
            format="wav"
        )

        try:

            print(
                f"  → Sarvam piece "
                f"{i + 1}/{total_pieces} ..."
            )

            # Send to Sarvam
            text = _send_to_sarvam(
                piece_path
            )

            # Append transcript
            if text:
                full_text += text + " "

        finally:

            # Delete temporary piece
            if os.path.exists(piece_path):
                os.remove(piece_path)

    return full_text.strip()


# ============================================================
# TRANSCRIPTION ROUTER
# ============================================================

def transcribe_chunk(
    chunk_path: str,
    language: str = "english"
) -> str:
    """
    Select transcription engine based on language.

    english  -> Local Whisper
    hinglish -> Sarvam AI
    """

    if language.lower() == "hinglish":

        return transcribe_chunk_sarvam(
            chunk_path
        )

    return transcribe_chunk_whisper(
        chunk_path
    )


# ============================================================
# TRANSCRIBE ALL CHUNKS
# ============================================================

def transcribe_all(
    chunks: list,
    language: str = "english"
) -> str:
    """
    Transcribe all audio chunks and combine
    them into one complete transcript.
    """

    full_transcript = ""

    # Display selected engine
    engine = (
        "Sarvam AI"
        if language.lower() == "hinglish"
        else "Whisper"
    )

    print(
        f"Using {engine} for transcription."
    )

    # Process every chunk
    for i, chunk in enumerate(chunks):

        print(
            f"Transcribing chunk "
            f"{i + 1}/{len(chunks)}..."
        )

        text = transcribe_chunk(
            chunk,
            language=language
        )

        if text:
            full_transcript += text + " "

    print(
        "Transcription complete."
    )

    return full_transcript.strip()