# Actionable Items, decisions, and unresolved questions extraction with token-limit protection
import os
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_text_splitters import RecursiveCharacterTextSplitter

def get_llm():
    return ChatMistralAI(
        model="mistral-small-latest",
        mistral_api_key=os.getenv("MISTRAL_API_KEY"),
        temperature=0
    )


def split_transcript(transcript: str, chunk_size: int = 8000, chunk_overlap: int = 1000) -> list:
    """Helper to split a long transcript into chunks for safe extraction."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    return splitter.split_text(transcript)


def build_chain(system_prompt: str):
    llm = get_llm()
    return (
        RunnablePassthrough() 
        | RunnableLambda(lambda x: {"text": x}) 
        | ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{text}"),
        ]) 
        | llm 
        | StrOutputParser()
    )


def extract_action_items(transcript: str) -> str:
    """Extract action items. Uses Map-Reduce if the transcript is long."""
    if len(transcript) <= 10000:
        chain = build_chain(
            "You are an expert meeting analyst. From the meeting transcript, "
            "extract all action items. For each provide:\n"
            "- Task description\n"
            "- Owner (who is responsible)\n"
            "- Deadline (if mentioned, else write 'Not specified')\n\n"
            "Format as a numbered list. If none found say 'No action items found.'"
        )
        return chain.invoke(transcript)

    # Map-Reduce for long transcripts
    llm = get_llm()
    chunks = split_transcript(transcript)

    # 1. Map Phase
    map_prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "You are an expert meeting analyst. Extract all action items from this portion of the transcript.\n"
            "Include task description, owner, and deadline (if mentioned)."
        ),
        ("human", "{text}")
    ])
    map_chain = map_prompt | llm | StrOutputParser()
    partial_actions = [map_chain.invoke({"text": chunk}) for chunk in chunks]
    combined_partial = "\n\n".join(partial_actions)

    # 2. Reduce Phase
    reduce_prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "You are an expert meeting analyst. Consolidate these partial action items "
            "into a single final numbered list. Remove duplicate items and format each item as:\n"
            "- Task description\n"
            "- Owner\n"
            "- Deadline (if mentioned, else 'Not specified')\n\n"
            "If no action items are present, write 'No action items found.'"
        ),
        ("human", "{text}")
    ])
    reduce_chain = reduce_prompt | llm | StrOutputParser()
    return reduce_chain.invoke({"text": combined_partial})


def extract_key_decisions(transcript: str) -> str:
    """Extract key decisions. Uses Map-Reduce if the transcript is long."""
    if len(transcript) <= 10000:
        chain = build_chain(
            "You are an expert meeting analyst. From the meeting transcript, "
            "extract all key decisions made. Format as a numbered list. "
            "If none found say 'No key decisions found.'"
        )
        return chain.invoke(transcript)

    # Map-Reduce for long transcripts
    llm = get_llm()
    chunks = split_transcript(transcript)

    # 1. Map Phase
    map_prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "You are an expert meeting analyst. Extract all key decisions made in this portion of the transcript."
        ),
        ("human", "{text}")
    ])
    map_chain = map_prompt | llm | StrOutputParser()
    partial_decisions = [map_chain.invoke({"text": chunk}) for chunk in chunks]
    combined_partial = "\n\n".join(partial_decisions)

    # 2. Reduce Phase
    reduce_prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "You are an expert meeting analyst. Consolidate these partial decisions "
            "into a single final numbered list. Remove duplicate items.\n"
            "If no key decisions are found, write 'No key decisions found.'"
        ),
        ("human", "{text}")
    ])
    reduce_chain = reduce_prompt | llm | StrOutputParser()
    return reduce_chain.invoke({"text": combined_partial})


def extract_questions(transcript: str) -> str:
    """Extract unresolved questions. Uses Map-Reduce if the transcript is long."""
    if len(transcript) <= 10000:
        chain = build_chain(
            "From the meeting transcript, extract all unresolved questions "
            "or topics needing follow-up. Format as a numbered list. "
            "If none found say 'No open questions found.'"
        )
        return chain.invoke(transcript)

    # Map-Reduce for long transcripts
    llm = get_llm()
    chunks = split_transcript(transcript)

    # 1. Map Phase
    map_prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "Extract all unresolved questions or follow-up items from this portion of the transcript."
        ),
        ("human", "{text}")
    ])
    map_chain = map_prompt | llm | StrOutputParser()
    partial_questions = [map_chain.invoke({"text": chunk}) for chunk in chunks]
    combined_partial = "\n\n".join(partial_questions)

    # 2. Reduce Phase
    reduce_prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "Consolidate these partial unresolved questions into a single final numbered list.\n"
            "Remove duplicates. If no open questions exist, write 'No open questions found.'"
        ),
        ("human", "{text}")
    ])
    reduce_chain = reduce_prompt | llm | StrOutputParser()
    return reduce_chain.invoke({"text": combined_partial})