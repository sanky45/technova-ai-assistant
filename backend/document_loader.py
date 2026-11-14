from pathlib import Path
from io import BytesIO
from zipfile import ZipFile

from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
)

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from PIL import Image, UnidentifiedImageError
from pypdf import PdfReader

from ocr import perform_ocr


# Resolve the document folder relative to this file.
# Expected structure:
# backend/
#   document_loader.py
#   documents/
#     TechNova/
#       PDF_Policies_and_Manuals/
#       DOCX_Operational_Standards/
#       PPTX_Company_and_Technology/
DOCUMENT_FOLDER = (
    Path(__file__).resolve().parent
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
    ".jpeg",
}


def _base_metadata(file_path: Path) -> dict:
    """Build consistent source metadata for a loaded file."""
    return {
        "file_name": file_path.name,
        "file_type": file_path.suffix.lower(),
        "source": str(file_path.resolve()),
    }


def _ocr_image_bytes(image_data: bytes) -> str:
    """Run OCR against image bytes and return extracted text."""
    with Image.open(BytesIO(image_data)) as image:
        return perform_ocr(image) or ""


def load_txt(file_path: Path) -> list:
    """Load a UTF-8 text file."""
    loader = TextLoader(str(file_path), encoding="utf-8")
    documents = loader.load()

    if not documents:
        return []

    content = documents[0].page_content.strip()
    if not content:
        return []

    return [
        {
            "content": content,
            "metadata": _base_metadata(file_path),
        }
    ]


def load_pdf(file_path: Path) -> list:
    """Extract native PDF text and OCR images embedded on each page."""
    loader = PyPDFLoader(str(file_path))
    documents = loader.load()
    reader = PdfReader(str(file_path))

    pdf_documents = []

    for page_number, document in enumerate(documents, start=1):
        text_parts = []
        native_text = (document.page_content or "").strip()
        if native_text:
            text_parts.append(native_text)

        pdf_page = reader.pages[page_number - 1]

        try:
            for embedded_image in pdf_page.images:
                try:
                    image_text = _ocr_image_bytes(embedded_image.data).strip()
                    if image_text:
                        text_parts.append(image_text)
                except Exception as error:
                    print(
                        f"OCR failed for image on page {page_number} "
                        f"of {file_path.name}: {error}"
                    )
        except Exception as error:
            print(
                f"Unable to inspect embedded images on page {page_number} "
                f"of {file_path.name}: {error}"
            )

        page_content = "\n\n".join(text_parts).strip()
        if not page_content:
            continue

        metadata = _base_metadata(file_path)
        metadata["page"] = page_number

        pdf_documents.append(
            {
                "content": page_content,
                "metadata": metadata,
            }
        )

    return pdf_documents


def load_docx(file_path: Path) -> list:
    """Extract DOCX text and OCR images stored in the DOCX package."""
    loader = Docx2txtLoader(str(file_path))
    documents = loader.load()

    content_parts = []
    if documents and documents[0].page_content:
        native_text = documents[0].page_content.strip()
        if native_text:
            content_parts.append(native_text)

    # DOCX files are ZIP containers; embedded images are under word/media/.
    with ZipFile(file_path, "r") as zip_file:
        image_files = [
            name
            for name in zip_file.namelist()
            if name.startswith("word/media/") and not name.endswith("/")
        ]

        for image_file in image_files:
            try:
                image_text = _ocr_image_bytes(zip_file.read(image_file)).strip()
                if image_text:
                    content_parts.append(image_text)
            except (UnidentifiedImageError, OSError, Exception) as error:
                print(
                    f"OCR failed for embedded image {image_file} "
                    f"in {file_path.name}: {error}"
                )

    content = "\n\n".join(content_parts).strip()
    if not content:
        return []

    return [
        {
            "content": content,
            "metadata": _base_metadata(file_path),
        }
    ]


def _extract_shape_text_and_images(shape, slide_content: list, slide_number: int, file_path: Path):
    """Extract text and OCR images from a PowerPoint shape, including groups."""
    if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
        for child_shape in shape.shapes:
            _extract_shape_text_and_images(
                child_shape, slide_content, slide_number, file_path
            )
        return

    if getattr(shape, "has_text_frame", False):
        text = (shape.text or "").strip()
        if text:
            slide_content.append(text)

    if getattr(shape, "has_table", False):
        for row in shape.table.rows:
            cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if cells:
                slide_content.append(" | ".join(cells))

    if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
        try:
            image_text = _ocr_image_bytes(shape.image.blob).strip()
            if image_text:
                slide_content.append(image_text)
        except Exception as error:
            print(
                f"OCR failed for image on slide {slide_number} "
                f"of {file_path.name}: {error}"
            )


def load_pptx(file_path: Path) -> list:
    """Extract text, tables and OCR-readable images from each slide."""
    presentation = Presentation(str(file_path))
    ppt_documents = []

    for slide_number, slide in enumerate(presentation.slides, start=1):
        slide_content = []

        for shape in slide.shapes:
            _extract_shape_text_and_images(
                shape, slide_content, slide_number, file_path
            )

        content = "\n\n".join(slide_content).strip()
        if not content:
            continue

        metadata = _base_metadata(file_path)
        metadata["slide"] = slide_number

        ppt_documents.append(
            {
                "content": content,
                "metadata": metadata,
            }
        )

    return ppt_documents


def load_image(file_path: Path) -> list:
    """Extract text from a standalone image using OCR."""
    try:
        with Image.open(file_path) as image:
            text = (perform_ocr(image) or "").strip()
    except Exception as error:
        raise ValueError(
            f"Unable to open or OCR image {file_path.name}: {error}"
        ) from error

    if not text:
        return []

    return [
        {
            "content": text,
            "metadata": _base_metadata(file_path),
        }
    ]


def load_document(file_path: Path) -> list:
    """Load one supported document using the matching loader."""
    file_path = Path(file_path)
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

    raise ValueError(f"Unsupported document type: {extension}")


def load_documents() -> list:
    """Recursively load every supported file under the TechNova folder."""
    if not DOCUMENT_FOLDER.exists():
        raise FileNotFoundError(
            f"Document folder not found: {DOCUMENT_FOLDER}"
        )

    all_documents = []

    for file_path in sorted(DOCUMENT_FOLDER.rglob("*")):
        if not file_path.is_file():
            continue

        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        try:
            loaded = load_document(file_path)
            all_documents.extend(loaded)
            print(
                f"Loaded {file_path.name}: "
                f"{len(loaded)} page/slide/document section(s)"
            )
        except Exception as error:
            # Continue scanning other files, but make the failure visible.
            print(f"Failed to load {file_path.name}: {error}")

    return all_documents
