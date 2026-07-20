"""Persistent knowledge-ingestion command."""

from app.services.index_service import build_index


def main() -> None:
    counts = build_index()
    print(f"Indexed {counts['documents']} documents as {counts['nodes']} nodes.")


if __name__ == "__main__":
    main()
