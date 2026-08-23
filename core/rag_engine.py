import os
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from core.vector_store import build_vector_store, load_vector_store, get_retriever

def get_llm():
    return ChatMistralAI(
        model="mistral-small-latest",
        mistral_api_key=os.getenv("MISTRAL_API_KEY"),
        temperature=0.3,
    )

def format_time(seconds: float) -> str:
    """Format seconds into MM:SS timestamp notation."""
    if seconds is None:
        return "00:00"
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"

def format_docs(docs):
    """Format retrieved chunks into context, appending timestamp metadata."""
    formatted = []
    for doc in docs:
        start = doc.metadata.get("start_time", 0.0)
        end = doc.metadata.get("end_time", 0.0)
        time_str = f"[{format_time(start)} - {format_time(end)}]"
        formatted.append(f"{time_str} {doc.page_content}")
    return "\n\n".join(formatted)

def build_rag_chain(transcript_segments: list, video_id: str, video_title: str = ""):
    """
    Builds the RAG pipeline by indexing segments and creating a retrieval chain
    isolated strictly to the active video_id.
    """
    vector_store = build_vector_store(transcript_segments, video_id, video_title)
    retriever = get_retriever(vector_store, video_id=video_id, k=4)
    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """You are an expert meeting assistant. Answer the user's question 
based ONLY on the meeting transcript context provided below.

For your answers, always include the relevant timestamp citation in brackets, e.g., [MM:SS - MM:SS], based on the context provided.

If the answer is not found in the context, say: 
"I could not find this information in the meeting transcript."

Always be concise and precise. If quoting someone, mention it clearly. Do NOT make up or assume anything outside the context.

Context from meeting transcript:
{context}""",
        ),
        ("human", "{question}"),
    ])

    rag_chain = (
        {
            "context": retriever | RunnableLambda(format_docs),
            "question": RunnablePassthrough()
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain


def load_rag_chain(video_id: str):
    """
    Loads the RAG pipeline for an existing vector store, 
    isolating retrieval queries to the active video_id.
    """
    vector_store = load_vector_store()
    retriever = get_retriever(vector_store, video_id=video_id, k=4)
    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """You are an expert meeting assistant. Answer the user's question 
based ONLY on the meeting transcript context provided below.

For your answers, always include the relevant timestamp citation in brackets, e.g., [MM:SS - MM:SS], based on the context provided.

If the answer is not found in the context, say: 
"I could not find this information in the meeting transcript."

Always be concise and precise. If quoting someone, mention it clearly. Do NOT make up or assume anything outside the context.

Context from meeting transcript:
{context}""",
        ),
        ("human", "{question}"),
    ])

    rag_chain = (
        {
            "context": retriever | RunnableLambda(format_docs),
            "question": RunnablePassthrough(),
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain


def ask_question(rag_chain, question: str) -> str:
    print(f"Question : {question}")
    answer = rag_chain.invoke(question)
    print(f"answer :{answer}")
    return answer