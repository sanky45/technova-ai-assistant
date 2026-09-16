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

from pinecone_ingestion import (
    index_document
)


DOCUMENT_FOLDER = Path("../documents/TechNova/")


SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".pptx",
    ".txt",
    ".png",
    ".jpg",
    ".jpeg"
}


def calculate_file_hash(
    file_path: Path
) -> str:
    """
    Calculate SHA-256 hash for a file.
    """

    sha256 = hashlib.sha256()

    with open(
        file_path,
        "rb"
    ) as file:

        while True:

            chunk = file.read(
                1024 * 1024
            )

            if not chunk:
                break

            sha256.update(chunk)

    return sha256.hexdigest()


def get_document_record(
    db: Session,
    file_path: Path
):
    """
    Find an existing document record
    using the file name.
    """

    return (
        db.query(Document)
        .filter(
            Document.file_name == file_path.name
        )
        .first()
    )


def detect_document_status(
    existing_document,
    file_hash: str
) -> str:
    """
    Determine whether the document needs
    processing.
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
        file_path=str(file_path),
        file_hash=file_hash,
        file_type=file_path.suffix.lower(),
        status="pending",
        chunk_count=0
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return document


def update_document_status(
    db: Session,
    document: Document,
    status: str
):
    """
    Update the processing status
    of a document.
    """

    document.status = status

    db.commit()
    db.refresh(document)


def update_document_after_indexing(
    db: Session,
    document: Document,
    file_hash: str,
    chunk_count: int
):
    """
    Update the document record after
    successful Pinecone indexing.
    """

    document.file_hash = file_hash
    document.chunk_count = chunk_count
    document.status = "processed"

    db.commit()
    db.refresh(document)


def load_document(
    file_path: Path
):
    """
    Route the file to the appropriate
    document loader.
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

    if extension in {
        ".png",
        ".jpg",
        ".jpeg"
    }:
        return load_image(file_path)

    raise ValueError(
        f"Unsupported document type: "
        f"{extension}"
    )


def get_loaded_document_stats(
    documents
):
    """
    Calculate document extraction statistics.
    """

    document_count = len(documents)

    total_characters = sum(
        len(
            document.get(
                "content",
                ""
            )
        )
        for document in documents
    )

    return {
        "document_count": document_count,
        "total_characters": total_characters
    }


def get_chunk_stats(
    chunks
):
    """
    Calculate chunk statistics.
    """

    chunk_count = len(chunks)

    total_characters = sum(
        len(
            chunk.get(
                "content",
                ""
            )
        )
        for chunk in chunks
    )

    return {
        "chunk_count": chunk_count,
        "total_characters": total_characters
    }


def get_embedding_stats(
    embeddings
):
    """
    Calculate embedding statistics.
    """

    embedding_count = len(
        embeddings
    )

    embedding_dimension = 0

    if embeddings:
        embedding_dimension = len(
            embeddings[0]
        )

    return {
        "embedding_count": embedding_count,
        "embedding_dimension": embedding_dimension
    }


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
    4. Create embeddings
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

        # Preserve the previous version information
        # before updating the database record.

        previous_file_hash = (
            document.file_hash
        )

        previous_chunk_count = (
            document.chunk_count
        )

        document.file_path = str(
            file_path
        )

        document.file_type = (
            file_path.suffix.lower()
        )

        update_document_status(
            db,
            document,
            "pending"
        )

    try:

        # -----------------------------------------
        # PROCESSING STATUS
        # -----------------------------------------

        update_document_status(
            db,
            document,
            "processing"
        )

        print(
            "  → Status: processing"
        )

        # -----------------------------------------
        # DOCUMENT LOADING
        # -----------------------------------------

        print(
            "  → Loading document..."
        )

        loaded_documents = load_document(
            file_path
        )

        loaded_stats = (
            get_loaded_document_stats(
                loaded_documents
            )
        )

        print(
            "  → Document loaded successfully"
        )

        print(
            f"  → Extracted "
            f"sections/pages: "
            f"{loaded_stats['document_count']}"
        )

        print(
            f"  → Extracted "
            f"characters: "
            f"{loaded_stats['total_characters']}"
        )

        # -----------------------------------------
        # CHUNKING
        # -----------------------------------------

        print(
            "  → Creating chunks..."
        )

        chunks = chunk_documents(
            loaded_documents
        )

        chunk_stats = (
            get_chunk_stats(
                chunks
            )
        )

        print(
            "  → Chunking completed"
        )

        print(
            f"  → Chunks created: "
            f"{chunk_stats['chunk_count']}"
        )

        print(
            f"  → Chunk characters: "
            f"{chunk_stats['total_characters']}"
        )

        if not chunks:

            raise ValueError(
                "No chunks were created "
                "from the document."
            )

        # -----------------------------------------
        # EMBEDDINGS
        # -----------------------------------------

        print(
            "  → Creating embeddings..."
        )

        chunk_texts = [
            chunk["content"]
            for chunk in chunks
        ]

        embeddings = create_embeddings(
            chunk_texts
        )

        embedding_stats = (
            get_embedding_stats(
                embeddings
            )
        )

        print(
            "  → Embeddings created successfully"
        )

        print(
            f"  → Embeddings created: "
            f"{embedding_stats['embedding_count']}"
        )

        print(
            f"  → Embedding dimension: "
            f"{embedding_stats['embedding_dimension']}"
        )

        # -----------------------------------------
        # EMBEDDING VALIDATION
        # -----------------------------------------

        if (
            len(chunks)
            != len(embeddings)
        ):

            raise ValueError(
                "Chunk count does not match "
                "embedding count."
            )

        if not embeddings:

            raise ValueError(
                "No embeddings were created."
            )

        print(
            "  → Embedding validation successful"
        )

        # -----------------------------------------
        # PINECONE INDEXING
        # -----------------------------------------

        print(
            "  → Indexing vectors in Pinecone..."
        )

        pinecone_result = index_document(
            chunks=chunks,
            embeddings=embeddings,
            file_hash=file_hash,
            previous_file_hash=(
                previous_file_hash
            ),
            previous_chunk_count=(
                previous_chunk_count
            )
        )

        vector_count = (
            pinecone_result["vector_count"]
        )

        namespace = (
            pinecone_result["namespace"]
        )

        print(
            f"  → Pinecone vectors indexed: "
            f"{vector_count}"
        )

        print(
            f"  → Pinecone namespace: "
            f"{namespace}"
        )

        # -----------------------------------------
        # DATABASE UPDATE
        # -----------------------------------------

        update_document_after_indexing(
            db,
            document,
            file_hash,
            chunk_stats["chunk_count"]
        )

        print(
            "  → PostgreSQL status: processed"
        )

        print(
            "  → Document ingestion completed"
        )

        return (
            document,
            chunks,
            embeddings
        )

    except Exception:

        update_document_status(
            db,
            document,
            "failed"
        )

        raise


def scan_documents():

    db = SessionLocal()

    try:

        if not DOCUMENT_FOLDER.exists():

            print(
                f"Document folder not found: "
                f"{DOCUMENT_FOLDER}"
            )

            return []

        results = []

        for file_path in DOCUMENT_FOLDER.iterdir():

            if not file_path.is_file():
                continue

            extension = file_path.suffix.lower()

            if extension not in SUPPORTED_EXTENSIONS:
                continue

            print(
                f"\nChecking: "
                f"{file_path.name}"
            )

            # -----------------------------------------
            # FILE HASH
            # -----------------------------------------

            file_hash = calculate_file_hash(
                file_path
            )

            print(
                f"  → File hash: "
                f"{file_hash}"
            )

            # -----------------------------------------
            # DATABASE LOOKUP
            # -----------------------------------------

            existing_document = (
                get_document_record(
                    db,
                    file_path
                )
            )

            # -----------------------------------------
            # STATUS DETECTION
            # -----------------------------------------

            status = detect_document_status(
                existing_document,
                file_hash
            )

            # -----------------------------------------
            # NEW DOCUMENT
            # -----------------------------------------

            if status == "new":

                print(
                    "  → New document detected"
                )

                try:

                    (
                        document,
                        chunks,
                        embeddings
                    ) = process_document(
                        db,
                        file_path,
                        None,
                        file_hash
                    )

                except Exception as error:

                    print(
                        "  → Processing failed"
                    )

                    print(
                        f"  → Error: {error}"
                    )

            # -----------------------------------------
            # PENDING DOCUMENT
            # -----------------------------------------

            elif status == "pending":

                print(
                    "  → Document is pending"
                )

                print(
                    "  → Processing document..."
                )

                try:

                    (
                        document,
                        chunks,
                        embeddings
                    ) = process_document(
                        db,
                        file_path,
                        existing_document,
                        file_hash
                    )

                except Exception as error:

                    print(
                        "  → Processing failed"
                    )

                    print(
                        f"  → Error: {error}"
                    )

            # -----------------------------------------
            # UNCHANGED DOCUMENT
            # -----------------------------------------

            elif status == "unchanged":

                print(
                    "  → No changes detected"
                )

                print(
                    "  → Skipping document"
                )

            # -----------------------------------------
            # MODIFIED DOCUMENT
            # -----------------------------------------

            elif status == "modified":

                print(
                    "  → File has been modified"
                )

                print(
                    "  → Re-processing document..."
                )

                try:

                    (
                        document,
                        chunks,
                        embeddings
                    ) = process_document(
                        db,
                        file_path,
                        existing_document,
                        file_hash
                    )

                except Exception as error:

                    print(
                        "  → Re-processing failed"
                    )

                    print(
                        f"  → Error: {error}"
                    )

            # -----------------------------------------
            # RESULT
            # -----------------------------------------

            results.append(
                {
                    "file_name":
                        file_path.name,

                    "file_path":
                        str(file_path),

                    "file_hash":
                        file_hash,

                    "file_type":
                        extension,

                    "status":
                        status
                }
            )

        return results

    finally:

        db.close()


if __name__ == "__main__":

    documents = scan_documents()

    print(
        "\nDocument Scan Result"
    )

    print(
        "===================="
    )

    if not documents:

        print(
            "No supported documents found."
        )

    for document in documents:

        print(
            f"\nFile: "
            f"{document['file_name']}"
        )

        print(
            f"Type: "
            f"{document['file_type']}"
        )

        print(
            f"Status: "
            f"{document['status']}"
        )

        print(
            f"Hash: "
            f"{document['file_hash']}"
        )