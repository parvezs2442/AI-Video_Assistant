# import whisper 
# import os 


# WHISPER_MODEL = os.getenv("WHISPER_MODEL","tiny")

# _model = None
# def load_model():
#     global _model
#     if _model is None:
#         print(f"loading model ...")
#         _model = whisper.load_model(WHISPER_MODEL) 
#         print("Whisper model loaded successfully")

#     return _model

# def transcribe_chunk(chunk_path: str, translate: bool = False) -> str:

#     model = load_model()
#     task ="translate" if translate else "transcribe"
#     result = model.transcribe(chunk_path, task = task)
#     return result['text']

# def transcribe_all(chunks: list, translate: bool = False) -> str:
#     full_transcript = ""

#     for i, chunk in enumerate(chunks):
#         print(f"Transcribing chunkn {i+1}")
#         text = transcribe_chunk(chunk, translate=translate) 
#         full_transcript += text + " "

#     print("Transcription completed")
#     return full_transcript








import whisper
import os

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "tiny")

_model = None
def load_model():
    global _model

    if _model is None:
        print(f"Loading Whisper model: {WHISPER_MODEL}...", flush=True)
        _model = whisper.load_model(WHISPER_MODEL)
        print("Whisper model loaded successfully", flush=True)
    return _model


def transcribe_chunk(chunk_path: str, translate: bool = False) -> str:
    model = load_model()
    task = "translate" if translate else "transcribe"
    print(f"Starting transcription: {os.path.basename(chunk_path)}", flush=True)
    print(f"Task: {task}", flush=True)
    result = model.transcribe(
        chunk_path,
        task=task,
        fp16=False,
        verbose=True
    )
    text = result["text"].strip()
    print("Chunk transcription completed", flush=True)
    return text

def transcribe_all(chunks: list, translate: bool = False) -> str:
    full_transcript = ""
    total_chunks = len(chunks)
    print(f"\nStarting transcription of {total_chunks} chunks...\n", flush=True)
    for i, chunk in enumerate(chunks):
        print(
            f"\n{'=' * 50}\n"
            f"Transcribing chunk {i + 1}/{total_chunks}\n"
            f"File: {chunk}\n"
            f"{'=' * 50}",
            flush=True
        )
        text = transcribe_chunk(
            chunk,
            translate=translate
        )
        full_transcript += text + " "
        print(
            f"Chunk {i + 1}/{total_chunks} completed.",
            flush=True
        )
    print("\n" + "=" * 50, flush=True)
    print("TRANSCRIPTION COMPLETED", flush=True)
    print("=" * 50, flush=True)

    return full_transcript.strip()