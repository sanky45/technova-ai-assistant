from fastapi import (
    FastAPI,
    Depends,
    HTTPException
)

from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel, Field

from config import (
    APP_NAME,
    APP_VERSION,
    ENV
)

from utils import logger

from auth import router as auth_router

from rag import answer_question

from memory import (
    get_conversation,
    save_message,
    list_conversations,
    clear_conversation
)

from jwt_handler import get_current_user

from models import User


# ==================================================
# APPLICATION
# ==================================================

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION
)


# ==================================================
# CORS
# ==================================================
#
# Development:
#     allow_origins=["*"]
#
# Production:
#     Replace "*" with the actual frontend domain.
#
# ==================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"]
)


# ==================================================
# API ROUTES
# ==================================================

app.include_router(
    auth_router
)


# ==================================================
# STARTUP
# ==================================================

@app.on_event("startup")
def startup():

    logger.info(
        f"{APP_NAME} started | "
        f"version={APP_VERSION} | "
        f"environment={ENV}"
    )


# ==================================================
# API INFORMATION
# ==================================================

@app.get("/api")
def api_info():

    return {
        "application": APP_NAME,
        "version": APP_VERSION,
        "environment": ENV
    }


# ==================================================
# HEALTH CHECK
# ==================================================

@app.get("/health")
def health():

    return {
        "status": "Healthy",
        "application": APP_NAME,
        "version": APP_VERSION,
        "environment": ENV
    }


# ==================================================
# REQUEST MODELS
# ==================================================

class QuestionRequest(BaseModel):
    """
    Request model for the RAG endpoint.
    """

    session_id: str = Field(
        ...,
        min_length=1,
        max_length=100
    )

    question: str = Field(
        ...,
        min_length=1,
        max_length=5000
    )


# ==================================================
# SOURCE BUILDER
# ==================================================

def build_sources(
    documents
):
    """
    Convert retrieved documents into a clean
    source list for the frontend.

    Duplicate sources are removed.
    """

    sources = []

    seen_sources = set()

    for document in documents:

        metadata = document.get(
            "metadata",
            {}
        )

        file_name = metadata.get(
            "file_name"
        )

        if not file_name:
            continue

        page = metadata.get(
            "page"
        )

        slide = metadata.get(
            "slide"
        )

        source_key = (
            file_name,
            page,
            slide
        )

        if source_key in seen_sources:
            continue

        seen_sources.add(
            source_key
        )

        sources.append(
            {
                "file_name": file_name,
                "page": page,
                "slide": slide
            }
        )

    return sources


# ==================================================
# LIST USER CONVERSATIONS
# ==================================================

@app.get("/api/conversations")
def get_conversations(
    current_user: User = Depends(
        get_current_user
    )
):

    try:

        conversations = list_conversations(
            current_user.id
        )

    except Exception as error:

        logger.exception(
            f"Failed to load conversations | "
            f"user={current_user.id}"
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to load conversations."
        ) from error

    logger.info(
        f"Conversations loaded | "
        f"user={current_user.id} | "
        f"count={len(conversations)}"
    )

    return {
        "conversations": conversations
    }


# ==================================================
# GET SINGLE CONVERSATION
# ==================================================

@app.get(
    "/api/conversations/{session_id}"
)
def get_conversation_history(
    session_id: str,
    current_user: User = Depends(
        get_current_user
    )
):

    session_id = session_id.strip()

    if not session_id:

        raise HTTPException(
            status_code=400,
            detail="Session ID cannot be empty."
        )

    try:

        conversation = get_conversation(
            current_user.id,
            session_id
        )

    except Exception as error:

        logger.exception(
            f"Failed to load conversation | "
            f"user={current_user.id} | "
            f"session={session_id}"
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to load conversation."
        ) from error

    return {
        "session_id": session_id,
        "messages": conversation
    }


# ==================================================
# DELETE SINGLE CONVERSATION
# ==================================================

@app.delete(
    "/api/conversations/{session_id}"
)
def delete_conversation(
    session_id: str,
    current_user: User = Depends(
        get_current_user
    )
):

    session_id = session_id.strip()

    if not session_id:

        raise HTTPException(
            status_code=400,
            detail="Session ID cannot be empty."
        )

    try:

        clear_conversation(
            current_user.id,
            session_id
        )

    except Exception as error:

        logger.exception(
            f"Failed to delete conversation | "
            f"user={current_user.id} | "
            f"session={session_id}"
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to delete conversation."
        ) from error

    logger.info(
        f"Conversation deleted | "
        f"user={current_user.id} | "
        f"session={session_id}"
    )

    return {
        "message": "Conversation deleted successfully",
        "session_id": session_id
    }


# ==================================================
# RAG ENDPOINT
# ==================================================

@app.post("/api/ask")
def ask_question(
    request: QuestionRequest,
    current_user: User = Depends(
        get_current_user
    )
):

    # --------------------------------------------------
    # STEP 1 — Clean request values
    # --------------------------------------------------

    session_id = request.session_id.strip()

    question = request.question.strip()

    # --------------------------------------------------
    # STEP 2 — Validate request
    # --------------------------------------------------

    if not session_id:

        raise HTTPException(
            status_code=400,
            detail="Session ID cannot be empty."
        )

    if not question:

        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )

    logger.info(
        f"RAG question received | "
        f"user={current_user.id} | "
        f"session={session_id}"
    )

    # --------------------------------------------------
    # STEP 3 — Load conversation history
    # --------------------------------------------------

    try:

        conversation_history = get_conversation(
            current_user.id,
            session_id
        )

    except Exception as error:

        logger.exception(
            f"Failed to load conversation history | "
            f"user={current_user.id} | "
            f"session={session_id}"
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to load conversation history."
        ) from error

    logger.info(
        f"Conversation history loaded | "
        f"user={current_user.id} | "
        f"session={session_id} | "
        f"messages={len(conversation_history)}"
    )

    # --------------------------------------------------
    # STEP 4 — Execute RAG pipeline
    # --------------------------------------------------

    try:

        result = answer_question(
            question=question,
            conversation_history=conversation_history
        )

    except ValueError as error:

        logger.warning(
            f"RAG validation error | "
            f"user={current_user.id} | "
            f"session={session_id} | "
            f"error={error}"
        )

        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error

    except Exception as error:

        logger.exception(
            f"RAG pipeline failed | "
            f"user={current_user.id} | "
            f"session={session_id}"
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to generate an answer."
        ) from error

    # --------------------------------------------------
    # STEP 5 — Save user message
    # --------------------------------------------------

    try:

        save_message(
            current_user.id,
            session_id,
            "user",
            question
        )

    except Exception as error:

        logger.exception(
            f"Failed to save user message | "
            f"user={current_user.id} | "
            f"session={session_id}"
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to save conversation."
        ) from error

    # --------------------------------------------------
    # STEP 6 — Save assistant response
    # --------------------------------------------------

    try:

        save_message(
            current_user.id,
            session_id,
            "assistant",
            result["answer"]
        )

    except Exception as error:

        logger.exception(
            f"Failed to save assistant message | "
            f"user={current_user.id} | "
            f"session={session_id}"
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to save conversation."
        ) from error

    # --------------------------------------------------
    # STEP 7 — Build sources
    # --------------------------------------------------

    sources = build_sources(
        result.get(
            "documents",
            []
        )
    )

    # --------------------------------------------------
    # STEP 8 — Log successful request
    # --------------------------------------------------

    logger.info(
        f"RAG question completed | "
        f"user={current_user.id} | "
        f"session={session_id} | "
        f"sources={len(sources)}"
    )

    # --------------------------------------------------
    # STEP 9 — Return response
    # --------------------------------------------------

    return {
        "session_id": session_id,

        "question": question,

        "answer": result["answer"],

        "sources": sources
    }


# ==================================================
# FRONTEND
# ==================================================
#
# IMPORTANT:
# Keep this LAST.
#
# FastAPI must register API routes before the
# catch-all frontend route.
#
# ==================================================

app.mount(
    "/",
    StaticFiles(
        directory="../frontend",
        html=True
    ),
    name="frontend"
)