import asyncio
from functools import lru_cache

import clickhouse_connect
from agno.agent import Agent
from agno.models.openai.like import OpenAILike
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from mistralai import Mistral
from pydantic import BaseModel

from settings.main_settings import settings


# ---------------------------------------------------------------------------
# FastAPI
# ---------------------------------------------------------------------------

app = FastAPI(
    title="AI Retail Analytics Backend",
    description=(
        "AI-powered backend for querying retail warehouse data "
        "through natural-language and voice interfaces."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Fine for development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# API models
# ---------------------------------------------------------------------------

class TextQueryRequest(BaseModel):
    question: str


class TextQueryResponse(BaseModel):
    question: str
    answer: str


class VoiceQueryResponse(BaseModel):
    transcription: str
    answer: str


# ---------------------------------------------------------------------------
# ClickHouse
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_clickhouse_client():
    """Create and reuse a ClickHouse client."""

    return clickhouse_connect.get_client(
        host=settings.D_HOST,
        port=settings.D_PORT,
        username=settings.D_USER,
        password=settings.D_PASSWORD,
    )


@lru_cache(maxsize=1)
def get_clickhouse_schema() -> str:
    """Retrieve and cache the current ClickHouse schema."""

    client = get_clickhouse_client()

    result = client.query(
        """
        SELECT
            table,
            name,
            type
        FROM system.columns
        WHERE database = currentDatabase()
        ORDER BY table, position
        """
    )

    schema = {}

    for table, column, column_type in result.result_rows:
        schema.setdefault(table, []).append(
            f"{column} ({column_type})"
        )

    return "\n\n".join(
        f"Table: {table}\n"
        + "\n".join(f"- {column}" for column in columns)
        for table, columns in schema.items()
    )


def validate_read_only_query(sql: str) -> str:
    """
    Prevent the LLM from executing write/destructive database operations.

    The agent should only be able to analyze data.
    """

    query = sql.strip().rstrip(";")

    if not query:
        raise ValueError("SQL query cannot be empty.")

    first_word = query.split(maxsplit=1)[0].upper()

    if first_word not in {"SELECT", "WITH"}:
        raise ValueError("Only read-only SELECT queries are allowed.")

    forbidden_operations = (
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "ALTER",
        "TRUNCATE",
        "CREATE",
        "RENAME",
    )

    query_upper = query.upper()

    if any(
        operation in query_upper
        for operation in forbidden_operations
    ):
        raise ValueError("Write operations are not allowed.")

    return query


def run_clickhouse_query(sql: str) -> list[dict]:
    """Execute a read-only SQL query against ClickHouse."""

    sql = validate_read_only_query(sql)

    client = get_clickhouse_client()
    result = client.query(sql)

    return [
        dict(zip(result.column_names, row))
        for row in result.result_rows
    ]


# ---------------------------------------------------------------------------
# LLM agent
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_agent() -> Agent:
    """Create the retail analytics agent only once."""

    schema = get_clickhouse_schema()

    model = OpenAILike(
        id="openai/gpt-oss-120b",
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
    )

    return Agent(
        model=model,
        tools=[run_clickhouse_query],
        instructions=[
            "You are a retail analytics assistant.",
            "Answer questions using the ClickHouse warehouse.",
            "Convert user questions into valid ClickHouse SQL.",
            "Use only tables and columns that exist in the schema.",
            "Use the run_clickhouse_query tool to execute SQL.",
            "Generate read-only SELECT queries only.",
            "Never invent database results.",
            "If the schema cannot answer the question, say so clearly.",
            f"Database schema:\n{schema}",
        ],
    )


async def process_query(question: str) -> str:
    """Process a natural-language question through the LLM agent."""

    question = question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty.",
        )

    try:
        agent = get_agent()
        response = await agent.arun(question)

        if not response.content:
            raise RuntimeError("Agent returned an empty response.")

        return str(response.content)

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Unable to process the analytics query.",
        ) from exc


# ---------------------------------------------------------------------------
# Voice transcription
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_mistral_client() -> Mistral:
    """Create and reuse the Mistral client."""

    return Mistral(
        api_key=settings.MISTRAL_API_KEY,
    )


async def transcribe_audio(file: UploadFile) -> str:
    """Transcribe an uploaded audio query using Mistral Voxtral."""

    audio_bytes = await file.read()

    if not audio_bytes:
        raise HTTPException(
            status_code=400,
            detail="Uploaded audio file is empty.",
        )

    client = get_mistral_client()

    try:
        # The Mistral SDK call is synchronous, so move it to a worker
        # thread instead of blocking FastAPI's event loop.
        transcription = await asyncio.to_thread(
            client.audio.transcriptions.complete,
            model="voxtral-mini-latest",
            file={
                "content": audio_bytes,
                "file_name": file.filename or "audio",
            },
        )

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Unable to transcribe audio.",
        ) from exc

    if not transcription.text:
        raise HTTPException(
            status_code=502,
            detail="Transcription returned an empty result.",
        )

    return transcription.text.strip()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
async def root():
    return {
        "message": "AI Retail Analytics Backend is running",
        "docs": "/docs",
    }


@app.post(
    "/text-query",
    response_model=TextQueryResponse,
)
async def text_query(
    request: TextQueryRequest,
):
    answer = await process_query(request.question)

    return TextQueryResponse(
        question=request.question,
        answer=answer,
    )


@app.post(
    "/voice-query",
    response_model=VoiceQueryResponse,
)
async def voice_query(
    file: UploadFile = File(...),
):
    transcription = await transcribe_audio(file)
    answer = await process_query(transcription)

    return VoiceQueryResponse(
        transcription=transcription,
        answer=answer,
    )
# To run the server:
# uvicorn main:app --reload
