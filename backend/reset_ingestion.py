from database import SessionLocal
from models import Document


def main():

    db = SessionLocal()

    try:

        documents = (
            db.query(Document)
            .all()
        )

        print(
            f"Found {len(documents)} document records."
        )

        for document in documents:

            print(
                f"Deleting: "
                f"{document.file_name}"
            )

            db.delete(document)

        db.commit()

        print(
            "\nDocument ingestion state reset successfully."
        )

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()


if __name__ == "__main__":
    main()