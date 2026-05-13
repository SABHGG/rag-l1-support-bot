"""Pinecone Assistant client wrapper."""

import os
from typing import Optional

from pinecone import Pinecone


class AssistantClient:
    def __init__(self, api_key: Optional[str] = None, assistant_name: Optional[str] = None):
        self.api_key = api_key or os.getenv("PINECONE_API_KEY")
        self.assistant_name = assistant_name or os.getenv("PINECONE_ASSISTANT_NAME")

        if not self.api_key:
            raise ValueError("PINECONE_API_KEY is required")
        if not self.assistant_name:
            raise ValueError("PINECONE_ASSISTANT_NAME is required")

        self.pc = Pinecone(api_key=self.api_key)

    def upload_file(self, file_path: str, metadata: Optional[dict] = None) -> dict:
        return self.pc.assistants.upload_file(
            assistant_name=self.assistant_name,
            file_path=file_path,
            metadata=metadata or {},
        )

    def chat(self, message: str, model: str = "gpt-4o") -> dict:
        return self.pc.assistants.chat(
            assistant_name=self.assistant_name,
            messages=[{"role": "user", "content": message}],
            model=model
        )

    def chat_stream(self, message: str, model: str = "gpt-4o"):
        return self.pc.assistants.chat(
            assistant_name=self.assistant_name,
            messages=[{"role": "user", "content": message}],
            model=model,
            stream=True
        )