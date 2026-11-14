from pathlib import Path
import hashlib

from sqlalchemy.orm import Session

from database import SessionLocal
from models import Document

from document_loader import (
    load_txt,
    load_pdf,
    load_docx,
    load_pptx,
    load_image
)

from chunking import chunk_documents
from embeddings import create_embeddings

from pinecone_ingestion import index_document


# ==================================================
# DOCUMENT CONFIGURATION
# ==================================================

# Project structure:
#
# KStore-AI-v2/
# ├── backend/
# │   └── document_ingestion.py
# └── documents/
#     └── TechNova/
#
DOCUMENT_FOLDER = (
    Path(__file__).resolve().parent.parent
    / "documents"
    / "TechNova"
)


SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".pptx",
    ".txt",
    ".png",
    ".jpg",
    ".jpeg"
}


# ==================================================
# FILE HASH
# ==================================================

def calculate_file_hash(file_path: Path) -> str:
    """
    Calculate SHA-256 hash for a file.
    """

    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:

        while True:

            chunk = file.read(1024 * 1024)

            if not chunk:
                break

            sha256.update(chunk)

    return sha256.hexdigest()


# ==================================================
# DATABASE DOCUMENT LOOKUP
# ==================================================

def get_document_record(
    db: Session,
    file_path: Path
):
    """
    Find an existing document using its
    absolute file path.

    This prevents filename collisions when
    different folders contain files with
    the same name.
    """

    return (
        db.query(Document)
        .filter(
            Document.file_path == str(file_path.resolve())
        )
        .first()
    )


# ==================================================
# DOCUMENT STATUS DETECTION
# ==================================================

def detect_document_status(
    existing_document,
    file_hash: str
) -> str:
    """
    Determine whether the document needs processing.
    """

    if existing_document is None:
        return "new"

    if (
        existing_document.file_hash == file_hash
        and existing_document.status == "processed"
    ):
        return "unchanged"

    if existing_document.file_hash != file_hash:
        return "modified"

    return "pending"


# ==================================================
# REGISTER DOCUMENT
# ==================================================

def register_new_document(
    db: Session,
    file_path: Path,
    file_hash: str
):
    """
    Register a new document in PostgreSQL.
    """

    document = Document(
        file_name=file_path.name,
        file_path=str(file_path.resolve()),
        file_hash=file_hash,
        file_type=file_path.suffix.lower(),
        status="pending",
        chunk_count=0
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return document


# ==================================================
# UPDATE DOCUMENT STATUS
# ==================================================

def update_document_status(
    db: Session,
    document: Document,
    status: str
):
    """
    Update document processing status.
    """

    document.status = status

    db.commit()
    db.refresh(document)


# ==================================================
# UPDATE DOCUMENT AFTER INDEXING
# ==================================================

def update_document_after_indexing(
    db: Session,
    document: Document,
    file_hash: str,
    chunk_count: int
):
    """
    Update document record after successful
    Pinecone indexing.
    """

    document.file_hash = file_hash
    document.chunk_count = chunk_count
    document.status = "processed"

    db.commit()
    db.refresh(document)


# ==================================================
# DOCUMENT LOADER ROUTER
# ==================================================

def load_document(file_path: Path):
    """
    Route the file to the appropriate loader.
    """

    extension = file_path.suffix.lower()

    if extension == ".pdf":
        return load_pdf(file_path)

    if extension == ".docx":
        return load_docx(file_path)

    if extension == ".pptx":
        return load_pptx(file_path)

    if extension == ".txt":
        return load_txt(file_path)

    if extension in {".png", ".jpg", ".jpeg"}:
        return load_image(file_path)

    raise ValueError(
        f"Unsupported document type: {extension}"
    )


# ==================================================
# DOCUMENT STATISTICS
# ==================================================

def get_loaded_document_stats(documents):
    """
    Calculate document extraction statistics.
    """

    document_count = len(documents)

    total_characters = sum(
        len(document.get("content", ""))
        for document in documents
    )

    return {
        "document_count": document_count,
        "total_characters": total_characters
    }


def get_chunk_stats(chunks):
    """
    Calculate chunk statistics.
    """

    chunk_count = len(chunks)

    total_characters = sum(
        len(chunk.get("content", ""))
        for chunk in chunks
    )

    return {
        "chunk_count": chunk_count,
        "total_characters": total_characters
    }


def get_embedding_stats(embeddings):
    """
    Calculate embedding statistics.
    """

    embedding_count = len(embeddings)

    embedding_dimension = 0

    if embeddings:
        embedding_dimension = len(embeddings[0])

    return {
        "embedding_count": embedding_count,
        "embedding_dimension": embedding_dimension
    }


# ==================================================
# PROCESS DOCUMENT
# ==================================================

def process_document(
    db: Session,
    file_path: Path,
    existing_document,
    file_hash: str
):
    """
    Complete document processing pipeline.

    Steps:
    1. Load document
    2. Extract text / OCR
    3. Create chunks
    4. Generate OpenRouter embeddings
    5. Index vectors in Pinecone
    6. Update PostgreSQL status
    """

    previous_file_hash = None
    previous_chunk_count = 0

    if existing_document is None:

        document = register_new_document(
            db,
            file_path,
            file_hash
        )

    else:

        document = existing_document

        previous_file_hash = document.file_hash
        previous_chunk_count = document.chunk_count

        document.file_path = str(file_path.resolve())
        document.file_name = file_path.name
        document.file_type = file_path.suffix.lower()

        update_document_status(
            db,
            document,
            "pending"
        )

    try:

        # ------------------------------------------
        # PROCESSING STATUS
        # ------------------------------------------

        update_document_status(
            db,
            document,
            "processing"
        )

        print("  -> Status: processing")

        # ------------------------------------------
        # DOCUMENT LOADING
        # ------------------------------------------

        print("  -> Loading document...")

        loaded_documents = load_document(file_path)

        loaded_stats = get_loaded_document_stats(
            loaded_documents
        )

        print("  -> Document loaded successfully")

        print(
            f"  -> Extracted sections/pages: "
            f"{loaded_stats['document_count']}"
        )

        print(
            f"  -> Extracted characters: "
            f"{loaded_stats['total_characters']}"
        )

        # ------------------------------------------
        # CHUNKING
        # ------------------------------------------

        print("  -> Creating chunks...")

        chunks = chunk_documents(loaded_documents)

        chunk_stats = get_chunk_stats(chunks)

        print("  -> Chunking completed")

        print(
            f"  -> Chunks created: "
            f"{chunk_stats['chunk_count']}"
        )

        print(
            f"  -> Chunk characters: "
            f"{chunk_stats['total_characters']}"
        )

        if not chunks:
            raise ValueError(
                "No chunks were created from the document."
            )

        # ------------------------------------------
        # EMBEDDINGS
        # ------------------------------------------

        print("  -> Creating OpenRouter embeddings...")

        chunk_texts = [
            chunk["content"]
            for chunk in chunks
        ]

        embeddings = create_embeddings(chunk_texts)

        embedding_stats = get_embedding_stats(embeddings)

        print("  -> Embeddings created successfully")

        print(
            f"  -> Embeddings created: "
            f"{embedding_stats['embedding_count']}"
        )

        print(
            f"  -> Embedding dimension: "
            f"{embedding_stats['embedding_dimension']}"
        )

        # ------------------------------------------
        # EMBEDDING VALIDATION
        # ------------------------------------------

        if len(chunks) != len(embeddings):
            raise ValueError(
                "Chunk count does not match embedding count."
            )

        if not embeddings:
            raise ValueError(
                "No embeddings were created."
            )

        print("  -> Embedding validation successful")

        # ------------------------------------------
        # PINECONE INDEXING
        # ------------------------------------------

        print("  -> Indexing vectors in Pinecone...")

        pinecone_result = index_document(
            chunks=chunks,
            embeddings=embeddings,
            file_hash=file_hash,
            previous_file_hash=previous_file_hash,
            previous_chunk_count=previous_chunk_count
        )

        vector_count = pinecone_result["vector_count"]
        namespace = pinecone_result["namespace"]

        print(
            f"  -> Pinecone vectors indexed: {vector_count}"
        )

        print(
            f"  -> Pinecone namespace: {namespace}"
        )

        # ------------------------------------------
        # DATABASE UPDATE
        # ------------------------------------------

        update_document_after_indexing(
            db,
            document,
            file_hash,
            chunk_stats["chunk_count"]
        )

        print("  -> PostgreSQL status: processed")
        print("  -> Document ingestion completed")

        return document, chunks, embeddings

    except Exception:

        db.rollback()

        update_document_status(
            db,
            document,
            "failed"
        )

        raise


# ==================================================
# SCAN DOCUMENTS
# ==================================================

def scan_documents():
    """
    Recursively scan the TechNova folder
    and process all supported documents.
    """

    db = SessionLocal()

    try:

        if not DOCUMENT_FOLDER.exists():

            print(
                f"Document folder not found: "
                f"{DOCUMENT_FOLDER}"
            )

            return []

        print("\nStarting TechNova document ingestion")
        print("=" * 60)

        print(f"Document folder: {DOCUMENT_FOLDER}")

        results = []

        # Recursively scan all subfolders
        for file_path in DOCUMENT_FOLDER.rglob("*"):

            if not file_path.is_file():
                continue

            extension = file_path.suffix.lower()

            if extension not in SUPPORTED_EXTENSIONS:
                continue

            print(f"\nChecking: {file_path.relative_to(DOCUMENT_FOLDER)}")

            # --------------------------------------
            # FILE HASH
            # --------------------------------------

            file_hash = calculate_file_hash(file_path)

            print(f"  -> File hash: {file_hash}")

            # --------------------------------------
            # DATABASE LOOKUP
            # --------------------------------------

            existing_document = get_document_record(
                db,
                file_path
            )

            # --------------------------------------
            # STATUS DETECTION
            # --------------------------------------

            status = detect_document_status(
                existing_document,
                file_hash
            )

            print(f"  -> Detected status: {status}")

            # --------------------------------------
            # NEW DOCUMENT
            # --------------------------------------

            if status == "new":

                print("  -> New document detected")

                try:

                    document, chunks, embeddings = process_document(
                        db,
                        file_path,
                        None,
                        file_hash
                    )

                    results.append({
                        "file_name": file_path.name,
                        "file_path": str(file_path.resolve()),
                        "status": "processed",
                        "chunk_count": len(chunks)
                    })

                except Exception as error:

                    print("  -> Processing failed")
                    print(f"  -> Error: {error}")

                    results.append({
                        "file_name": file_path.name,
                        "file_path": str(file_path.resolve()),
                        "status": "failed",
                        "error": str(error)
                    })

            # --------------------------------------
            # PENDING DOCUMENT
            # --------------------------------------

            elif status == "pending":

                print("  -> Processing pending document")

                try:

                    document, chunks, embeddings = process_document(
                        db,
                        file_path,
                        existing_document,
                        file_hash
                    )

                    results.append({
                        "file_name": file_path.name,
                        "file_path": str(file_path.resolve()),
                        "status": "processed",
                        "chunk_count": len(chunks)
                    })

                except Exception as error:

                    print("  -> Processing failed")
                    print(f"  -> Error: {error}")

                    results.append({
                        "file_name": file_path.name,
                        "file_path": str(file_path.resolve()),
                        "status": "failed",
                        "error": str(error)
                    })

            # --------------------------------------
            # UNCHANGED DOCUMENT
            # --------------------------------------

            elif status == "unchanged":

                print("  -> No changes detected")
                print("  -> Skipping document")

                results.append({
                    "file_name": file_path.name,
                    "file_path": str(file_path.resolve()),
                    "status": "unchanged"
                })

            # --------------------------------------
            # MODIFIED DOCUMENT
            # --------------------------------------

            elif status == "modified":

                print("  -> File has been modified")
                print("  -> Re-processing document")

                try:

                    document, chunks, embeddings = process_document(
                        db,
                        file_path,
                        existing_document,
                        file_hash
                    )

                    results.append({
                        "file_name": file_path.name,
                        "file_path": str(file_path.resolve()),
                        "status": "processed",
                        "chunk_count": len(chunks)
                    })

                except Exception as error:

                    print("  -> Re-processing failed")
                    print(f"  -> Error: {error}")

                    results.append({
                        "file_name": file_path.name,
                        "file_path": str(file_path.resolve()),
                        "status": "failed",
                        "error": str(error)
                    })

        return results

    finally:

        db.close()


# ==================================================
# MAIN EXECUTION
# ==================================================

if __name__ == "__main__":

    documents = scan_documents()

    print("\nDocument Ingestion Summary")
    print("=" * 60)

    if not documents:
        print("No supported documents found.")

    successful = 0
    failed = 0
    unchanged = 0

    for document in documents:

        status = document["status"]

        if status == "processed":
            successful += 1

        elif status == "failed":
            failed += 1

        elif status == "unchanged":
            unchanged += 1

        print(f"\nFile: {document['file_name']}")
        print(f"Status: {status}")

        if "chunk_count" in document:
            print(f"Chunks: {document['chunk_count']}")

        if "error" in document:
            print(f"Error: {document['error']}")

    print("\nFinal Summary")
    print("-" * 40)
    print(f"Processed: {successful}")
    print(f"Failed: {failed}")
    print(f"Unchanged: {unchanged}")
    print(f"Total scanned: {len(documents)}")