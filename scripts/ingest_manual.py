#!/usr/bin/env python3
"""CLI script to ingest manuals into Pinecone Assistant."""

import argparse
import sys
from pathlib import Path

from sync.assistant_client import AssistantClient


def ingest_manual(file_path: str, metadata: dict = None):
    """Ingest a manual file to Pinecone Assistant."""
    path = Path(file_path)

    if not path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    if path.suffix.lower() not in {".pdf", ".md", ".markdown"}:
        print(f"Error: Unsupported file type: {path.suffix}")
        print("Supported: .pdf, .md, .markdown")
        sys.exit(1)

    client = AssistantClient()

    metadata = metadata or {}
    metadata["source"] = path.name
    metadata["type"] = path.suffix.lstrip(".")

    print(f"Ingesting {path.name}...")
    result = client.upload_file(str(path.absolute()), metadata=metadata)

    print(f"Success: {path.name} uploaded")
    print(f"File ID: {result.get('id', 'N/A')}")

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Ingest technical manuals into Pinecone Assistant"
    )
    parser.add_argument(
        "--file",
        required=True,
        help="Path to the manual file (PDF or Markdown)"
    )
    parser.add_argument(
        "--category",
        help="Category metadata for the manual"
    )
    parser.add_argument(
        "--department",
        help="Department metadata for the manual"
    )

    args = parser.parse_args()

    metadata = {}
    if args.category:
        metadata["category"] = args.category
    if args.department:
        metadata["department"] = args.department

    ingest_manual(args.file, metadata if metadata else None)


if __name__ == "__main__":
    main()