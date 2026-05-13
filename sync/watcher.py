"""File watcher for automatic manual synchronization."""

import os
import time
import logging
from pathlib import Path
from typing import Set

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

from sync.assistant_client import AssistantClient


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


IGNORED_EXTENSIONS: Set[str] = {".tmp", ".swp", "~"}
IGNORED_PATTERNS: Set[str] = {".DS_Store", "Thumbs.db"}


class ManualWatcher(FileSystemEventHandler):
    def __init__(self, manuals_dir: str, assistant_client: AssistantClient):
        self.manuals_dir = Path(manuals_dir)
        self.assistant = assistant_client
        self.last_modified: dict = {}
        self.debounce_seconds = 2.0

    def _should_ignore(self, path: str) -> bool:
        """Check if file should be ignored."""
        file_path = Path(path)
        if file_path.name in IGNORED_PATTERNS:
            return True
        if file_path.suffix in IGNORED_EXTENSIONS:
            return True
        if file_path.name.endswith("~"):
            return True
        return False

    def _should_process(self, path: str) -> bool:
        """Check if file should be processed."""
        file_path = Path(path)
        if not file_path.is_file():
            return False
        if file_path.suffix.lower() not in {".pdf", ".md", ".markdown"}:
            return False
        try:
            file_path.relative_to(self.manuals_dir)
            return True
        except ValueError:
            return False

    def _debounce(self, path: str) -> bool:
        """Check if enough time has passed since last modification."""
        now = time.time()
        last_time = self.last_modified.get(path, 0)
        if now - last_time < self.debounce_seconds:
            return False
        self.last_modified[path] = now
        return True

    def on_modified(self, event: FileModifiedEvent):
        """Handle file modification events."""
        if event.is_directory:
            return
        if self._should_ignore(event.src_path):
            return
        if not self._should_process(event.src_path):
            return
        if not self._debounce(event.src_path):
            return

        self._reingest_file(event.src_path)

    def _reingest_file(self, file_path: str):
        """Re-ingest a modified file to Pinecone."""
        filename = Path(file_path).name
        logger.info(f"Detected change: {filename}")

        try:
            metadata = {
                "source": filename,
                "type": Path(file_path).suffix.lstrip(".")
            }
            self.assistant.upload_file(file_path, metadata=metadata)
            logger.info(f"Synced: {filename}")

            self._log_sync_event(filename)
        except Exception as e:
            logger.error(f"Failed to sync {filename}: {e}")

    def _log_sync_event(self, filename: str):
        """Log sync event to sync.log."""
        log_dir = Path("sync")
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / "sync.log"

        import datetime
        timestamp = datetime.datetime.now().isoformat()
        with open(log_file, "a") as f:
            f.write(f"{timestamp} - {filename}\n")


def start_watcher(manuals_dir: str = None, assistant_name: str = None):
    """Start the file watcher."""
    manuals_dir = manuals_dir or os.getenv("MANUALS_DIR", "manuals")
    assistant_name = assistant_name or os.getenv("PINECONE_ASSISTANT_NAME", "rag-l1-support")

    Path(manuals_dir).mkdir(exist_ok=True)

    client = AssistantClient()
    observer = Observer()
    handler = ManualWatcher(manuals_dir, client)
    observer.schedule(handler, manuals_dir, recursive=False)
    observer.start()

    logger.info(f"Watching {manuals_dir} for changes...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    start_watcher()