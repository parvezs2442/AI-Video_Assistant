from dotenv import load_dotenv
load_dotenv()

from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.summarize import summarize, generate_title
from core.extractor import extract_action_items, extract_key_decisions, extract_questions
from core.rag_engine import build_rag_chain, ask_question


def run_pipeline(source: str, language: str = "english") -> dict:
    print("starting AI Video Assistant")

    # 1. Process Input (WAV chunks or direct YouTube captions)
    input_data = process_input(source)
    video_id = input_data["video_id"]
    video_title = input_data["video_title"]
    
    # 2. Get Structured Segments
    if input_data["type"] == "youtube_transcript":
        transcript_segments = input_data["data"]
    else:
        # data is a list of WAV chunks
        transcript_segments = transcribe_all(input_data["data"], language)
        
    print(f"Total transcription segments obtained: {len(transcript_segments)}")

    # Reconstruct raw full text for summary & extraction models (compatibility)
    transcript_text = " ".join([seg["text"] for seg in transcript_segments])
    
    snippet = transcript_text[:300] if len(transcript_text) > 0 else "[Empty Transcript]"
    print(f"raw transcription snippet (first 300 characters): {snippet}")

    # 3. Generate Metadata & Summaries
    title = generate_title(transcript_text) if len(transcript_text) > 0 else ""
    if not title or title.strip() == "":
        title = video_title
        
    summary = summarize(transcript_text) if len(transcript_text) > 0 else "No content to summarize."
    action_item = extract_action_items(transcript_text) if len(transcript_text) > 0 else "No action items."
    decisions = extract_key_decisions(transcript_text) if len(transcript_text) > 0 else "No key decisions."
    questions = extract_questions(transcript_text) if len(transcript_text) > 0 else "No open questions."
    
    # 4. Build RAG Chain with isolated vector index
    rag_chain = build_rag_chain(transcript_segments, video_id, title)

    return {
        "title": title,
        "transcript": transcript_text,
        "transcript_segments": transcript_segments,
        "summary": summary,
        "action_items": action_item,
        "key_decisions": decisions,
        "open_questions": questions,
        "rag_chain": rag_chain,
        "video_id": video_id
    }


if __name__ == "__main__":
    # CLI entry point
    source = input("Enter YouTube URL or local file path: ").strip()
    language = input("Language (english/hinglish): ").strip() or "english"
    result = run_pipeline(source, language)

    print("\n" + "=" * 60)
    print(f"📌 Title: {result['title']}")
    print(f"\n📋 Summary:\n{result['summary']}")
    print(f"\n✅ Action Items:\n{result['action_items']}")
    print(f"\n🔑 Key Decisions:\n{result['key_decisions']}")
    print(f"\n❓ Open Questions:\n{result['open_questions']}")
    print("=" * 60)

    # Phase 2 — Chat with your meeting via RAG
    print("\n💬 Chat with your meeting (type 'exit' to quit)\n")
    rag_chain = result["rag_chain"]
    while True:
        question = input("You: ").strip()
        if question.lower() in ["exit", "quit", "q"]:
            print("👋 Goodbye!")
            break
        if not question:
            continue
        answer = ask_question(rag_chain, question)
        print(f"\n🤖 Assistant: {answer}\n")