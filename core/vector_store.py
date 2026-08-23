import os
import tiktoken
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

CHROMA_DIR = "vector_db"
COLLECTION_NAME = "meeting-assistant"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": 'cpu'}
    )


def get_token_count(text: str) -> int:
    """Helper to estimate token count using tiktoken (cl100k_base)."""
    try:
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except Exception:
        # Fallback character/word token approximation
        return len(text.split()) * 4 // 3


def chunk_segments(segments: list, max_tokens: int = 180, pause_threshold: float = 2.0, overlap_size: int = 1) -> list:
    """
    Intelligently chunks speech segments based on complete sentences, 
    token limits (keeping below 256 for MiniLM), and natural pause transitions.
    """
    if not segments:
        return []
        
    chunks = []
    current_group = []
    
    i = 0
    while i < len(segments):
        seg = segments[i]
        
        # Build candidate text to estimate tokens
        candidate_text = " ".join([s["text"] for s in current_group] + [seg["text"]])
        candidate_tokens = get_token_count(candidate_text)
        
        # Check for pause thresholds indicating speaker/thought breaks
        is_pause = False
        if current_group:
            last_seg = current_group[-1]
            gap = seg["start"] - last_seg["end"]
            if gap >= pause_threshold:
                is_pause = True
                
        # Split on natural pause (silence/topic transitions)
        if len(current_group) > 0 and is_pause:
            chunk_text = " ".join([s["text"] for s in current_group])
            chunks.append({
                "text": chunk_text,
                "start": current_group[0]["start"],
                "end": current_group[-1]["end"]
            })
            current_group = [] # Fresh group, no overlap needed for natural breaks
            continue
            
        # Split on token count limit exceeded (with overlap)
        elif len(current_group) > overlap_size and candidate_tokens > max_tokens:
            chunk_text = " ".join([s["text"] for s in current_group])
            chunks.append({
                "text": chunk_text,
                "start": current_group[0]["start"],
                "end": current_group[-1]["end"]
            })
            overlap_segs = current_group[-overlap_size:]
            current_group = list(overlap_segs)
            continue
            
        else:
            current_group.append(seg)
            i += 1
            
    # Flush remaining segments
    if current_group:
        chunk_text = " ".join([s["text"] for s in current_group])
        chunks.append({
            "text": chunk_text,
            "start": current_group[0]["start"],
            "end": current_group[-1]["end"]
        })
        
    return chunks


def build_vector_store(transcript_segments: list, video_id: str, video_title: str = "") -> Chroma:
    """
    Builds Chroma vector store using timestamp-aware semantic chunking.
    Overwrites/deduplicates previous entries matching the same video_id.
    """
    print(f"building vector store for video: {video_id} ({video_title})")
    
    # 1. Generate semantic chunks
    semantic_chunks = chunk_segments(transcript_segments)
    
    # 2. Build Document list with metadata
    docs = []
    for i, chunk in enumerate(semantic_chunks):
        docs.append(Document(
            page_content=chunk["text"],
            metadata={
                "video_id": video_id,
                "video_title": video_title,
                "start_time": chunk["start"],
                "end_time": chunk["end"],
                "chunk_index": i
            }
        ))
        
    # 3. Load database collection
    embeddings = get_embeddings()
    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR
    )
    
    # 4. Deduplicate: Clean up existing entries for this video
    try:
        vector_store.delete(where={"video_id": video_id})
        print(f"Cleaned up existing database vectors for video_id: {video_id}")
    except Exception as e:
        print(f"No existing vectors cleared for this video: {e}")
        
    # 5. Add documents
    if docs:
        vector_store.add_documents(docs)
        print(f"Successfully indexed {len(docs)} chunks in Chroma DB.")
        
    return vector_store


def load_vector_store() -> Chroma:
    """Load existing Chroma vector store."""
    embeddings = get_embeddings()
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR
    )


def get_retriever(vector_store: Chroma, video_id: str = None, k: int = 4):
    """
    Create a retriever. If video_id is provided, 
    applies metadata filtering to ensure strict cross-video isolation.
    """
    search_kwargs = {"k": k}
    if video_id:
        search_kwargs["filter"] = {"video_id": video_id}
        
    return vector_store.as_retriever(
        search_type='similarity',
        search_kwargs=search_kwargs
    )