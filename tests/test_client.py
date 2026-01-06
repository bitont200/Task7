import pytest
import requests
from pathlib import Path
from client.watcher import DirectoryWatcher
from client.uploader import upload_file
from client.state import load_state, save_state
from common.hashing import hash_file

# Hash Tests

def test_hash_file_empty_file(tmp_path):
    """Test hashing an empty file"""
    empty_file = tmp_path / "empty.txt"
    empty_file.write_bytes(b"")
    
    file_hash = hash_file(empty_file)
    
    expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    assert file_hash == expected


def test_hash_file_binary_content(tmp_path):
    """Test hashing binary content"""
    binary_file = tmp_path / "binary.bin"
    binary_file.write_bytes(bytes(range(256)))
    
    file_hash = hash_file(binary_file)
    
    assert file_hash is not None
    assert len(file_hash) == 64


def test_hash_file_large_file(tmp_path):
    """Test hashing a large file"""
    large_file = tmp_path / "large.bin"
    large_file.write_bytes(b"A" * 10000)
    
    file_hash = hash_file(large_file)
    
    assert file_hash is not None
    assert len(file_hash) == 64


def test_same_file_same_hash(tmp_path):
    """Test that same file produces same hash"""
    f = tmp_path / "a.txt"
    f.write_text("hello")
    assert hash_file(f) == hash_file(f)


def test_different_content_different_hash(tmp_path):
    """Test that different content produces different hashes"""
    f1 = tmp_path / "a.txt"
    f2 = tmp_path / "b.txt"
    f1.write_text("hello")
    f2.write_text("world")
    assert hash_file(f1) != hash_file(f2)


def test_hash_file_unicode_content(tmp_path):
    """Test hashing file with unicode content"""
    unicode_file = tmp_path / "unicode.txt"
    unicode_file.write_text("שלום עולם", encoding="utf-8")
    
    file_hash = hash_file(unicode_file)
    
    assert file_hash is not None
    assert len(file_hash) == 64


def test_hash_file_identical_content_different_names(tmp_path):
    """Test that files with same content but different names have same hash"""
    f1 = tmp_path / "file1.txt"
    f2 = tmp_path / "file2.txt"
    content = "identical content"
    
    f1.write_text(content)
    f2.write_text(content)
    
    assert hash_file(f1) == hash_file(f2)

# State Management Tests

def test_save_and_load_state(tmp_path, monkeypatch):
    """Test saving and loading state"""
    monkeypatch.setattr("client.state.STATE_FILE", tmp_path / "state.json")
    
    state = {"abc", "def"}
    save_state(state)
    loaded = load_state()
    
    assert state == loaded


def test_load_state_nonexistent_file(tmp_path, monkeypatch):
    """Test loading state when file doesn't exist"""
    monkeypatch.setattr("client.state.STATE_FILE", tmp_path / "nonexistent.json")
    
    loaded = load_state()
    
    assert loaded == set()


def test_save_state_creates_directory(tmp_path, monkeypatch):
    """Test that save_state creates directory if needed"""
    state_file = tmp_path / "new_dir" / "state.json"
    monkeypatch.setattr("client.state.STATE_DIR", tmp_path / "new_dir")
    monkeypatch.setattr("client.state.STATE_FILE", state_file)
    
    (tmp_path / "new_dir").mkdir(parents=True, exist_ok=True)
    
    state = {"test"}
    save_state(state)
    
    assert state_file.exists()


def test_state_persists_empty_set(tmp_path, monkeypatch):
    """Test that empty state can be saved and loaded"""
    monkeypatch.setattr("client.state.STATE_FILE", tmp_path / "state.json")
    
    state = set()
    save_state(state)
    loaded = load_state()
    
    assert loaded == set()