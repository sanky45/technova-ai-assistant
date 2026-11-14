from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    BackgroundTasks,
    UploadFile,
    File
)

from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from pathlib import Path
import hashlib
import uuid
import re

from database import SessionLocal
from models import User, Document

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
# DOCUMENT UPLOAD AND KNOWLEDGE BASE
# ==================================================

DOCUMENT_FOLDER = (
    Path(__file__).resolve().parent.parent
    / "documents"
    / "TechNova"
    / "Uploaded"
)

ALLOWED_DOCUMENT_EXTENSIONS = {
    ".pdf", ".docx", ".pptx", ".txt", ".png", ".jpg", ".jpeg"
}
MAX_UPLOAD_SIZE = 20 * 1024 * 1024  # 20 MB


def calculate_upload_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def process_uploaded_document(file_path: Path, file_hash: str):
    """Run the existing ingestion pipeline in a background task."""
    db = SessionLocal()
    try:
        from document_ingestion import get_document_record, process_document

        existing = get_document_record(db, file_path)
        process_document(db, file_path, existing, file_hash)
        logger.info("Document ingestion completed | file=%s", file_path.name)
    except Exception:
        db.rollback()
        logger.exception("Document ingestion failed | file=%s", file_path.name)
    finally:
        db.close()


@app.post("/api/documents/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Authenticated upload; indexing runs asynchronously."""
    original_name = Path(file.filename or "").name
    extension = Path(original_name).suffix.lower()

    if not original_name or extension not in ALLOWED_DOCUMENT_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Upload PDF, DOCX, PPTX, TXT, PNG or JPG."
        )

    content = await file.read(MAX_UPLOAD_SIZE + 1)
    if not content:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="Maximum upload size is 20 MB.")

    file_hash = calculate_upload_hash(content)
    db = SessionLocal()
    try:
        duplicate = (
            db.query(Document)
            .filter(Document.file_hash == file_hash)
            .first()
        )
        if duplicate and duplicate.status == "processed":
            return {
                "message": "This document is already in the knowledge base.",
                "duplicate": True,
                "document_id": duplicate.id,
                "file_name": duplicate.file_name,
                "status": duplicate.status
            }
    finally:
        db.close()

    # Isolate each upload in its own directory while preserving the original
    # basename used by the document metadata and source citations.
    safe_name = re.sub(r"[^A-Za-z0-9._ -]", "_", original_name).strip(" .")
    if not safe_name:
        safe_name = f"uploaded{extension}"
    file_path = DOCUMENT_FOLDER / uuid.uuid4().hex / safe_name
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(content)

    background_tasks.add_task(
        process_uploaded_document,
        file_path,
        file_hash
    )

    logger.info(
        "Document uploaded | user=%s | file=%s",
        current_user.id,
        safe_name
    )

    return {
        "message": "Document uploaded. Ingestion has started.",
        "duplicate": False,
        "file_name": safe_name,
        "status": "pending"
    }


@app.get("/api/documents")
def list_documents(
    current_user: User = Depends(get_current_user)
):
    """List documents and their ingestion status."""
    db = SessionLocal()
    try:
        records = (
            db.query(Document)
            .order_by(Document.created_at.desc())
            .all()
        )
        return {
            "documents": [
                {
                    "id": item.id,
                    "file_name": item.file_name,
                    "file_type": item.file_type,
                    "status": item.status,
                    "chunk_count": item.chunk_count,
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                    "updated_at": item.updated_at.isoformat() if item.updated_at else None
                }
                for item in records
            ]
        }
    finally:
        db.close()


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