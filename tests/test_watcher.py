"""Tests for file watcher module."""

import pytest
import time
from pathlib import Path
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_assistant():
    return MagicMock()


@pytest.fixture
def watcher(mock_assistant, tmp_path):
    from sync.watcher import ManualWatcher

    manuals_dir = tmp_path / "manuals"
    manuals_dir.mkdir()
    return ManualWatcher(str(manuals_dir), mock_assistant)


def test_should_ignore_tmp_files(watcher):
    assert watcher._should_ignore("/path/file.tmp") is True
    assert watcher._should_ignore("/path/file.swp") is True
    assert watcher._should_ignore("/path/file~") is True


def test_should_ignore_dsfiles(watcher):
    assert watcher._should_ignore("/path/.DS_Store") is True
    assert watcher._should_ignore("/path/Thumbs.db") is True


def test_should_process_pdf_markdown(watcher, tmp_path):
    pdf_file = tmp_path / "manuals" / "test.pdf"
    pdf_file.parent.mkdir(parents=True, exist_ok=True)
    pdf_file.touch()

    md_file = tmp_path / "manuals" / "test.md"
    md_file.touch()

    assert watcher._should_process(str(pdf_file)) is True
    assert watcher._should_process(str(md_file)) is True


def test_should_not_process_other_extensions(watcher, tmp_path):
    txt_file = tmp_path / "manuals" / "test.txt"
    txt_file.touch()

    assert watcher._should_process(str(txt_file)) is False


def test_debounce_allows_after_wait(watcher, tmp_path):
    file_path = str(tmp_path / "manuals" / "test.pdf")
    tmp_path.joinpath("manuals").mkdir(parents=True, exist_ok=True)
    tmp_path.joinpath("manuals").joinpath("test.pdf").touch()

    assert watcher._debounce(file_path) is True

    watcher.last_modified[file_path] = time.time() - 3

    assert watcher._debounce(file_path) is True


def test_debounce_blocks_rapid_calls(watcher, tmp_path):
    file_path = str(tmp_path / "manuals" / "test.pdf")
    tmp_path.joinpath("manuals").mkdir(parents=True, exist_ok=True)
    tmp_path.joinpath("manuals").joinpath("test.pdf").touch()

    watcher.last_modified[file_path] = time.time()

    assert watcher._debounce(file_path) is False