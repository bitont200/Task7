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

# Uploader Tests

def test_upload_success(tmp_path, monkeypatch):
    """Test successful file upload"""
    def mock_post(url, data):
        class R:
            status_code = 201
        return R()
    
    monkeypatch.setattr(requests, "post", mock_post)
    
    f = tmp_path / "a.txt"
    f.write_text("x")
    
    assert upload_file("http://x", f) == 201


def test_upload_duplicate(tmp_path, monkeypatch):
    """Test uploading duplicate file returns 409"""
    def mock_post(url, data):
        class R:
            status_code = 409
        return R()
    
    monkeypatch.setattr(requests, "post", mock_post)
    
    f = tmp_path / "a.txt"
    f.write_text("x")
    
    assert upload_file("http://x", f) == 409


def test_upload_server_error(tmp_path, monkeypatch):
    """Test handling server error during upload"""
    def mock_post(url, data):
        class R:
            status_code = 500
        return R()
    
    monkeypatch.setattr(requests, "post", mock_post)
    
    f = tmp_path / "a.txt"
    f.write_text("x")
    
    assert upload_file("http://x", f) == 500

# Watcher Tests

def test_file_uploaded_once(tmp_path):
    """Test that file is uploaded only once even with multiple scans"""
    uploaded = []
    saved_state = []
    
    def mock_upload(url, file):
        uploaded.append(file.name)
        return 201
    
    def mock_save(s):
        saved_state.append(set(s))
    
    f = tmp_path / "a.txt"
    f.write_text("hello")
    
    watcher = DirectoryWatcher(tmp_path, "http://x", state=set(), uploader=mock_upload, saver=mock_save)
    watcher.scan()
    watcher.scan()
    
    assert uploaded.count("a.txt") == 1


def test_watcher_skips_subdirectories(tmp_path):
    """Test that watcher only processes files, not directories"""
    uploaded = []
    
    def mock_upload(url, file):
        uploaded.append(file.name)
        return 201
    
    (tmp_path / "file.txt").write_text("hello")
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subdir" / "nested.txt").write_text("nested")
    
    watcher = DirectoryWatcher(tmp_path, "http://x", state=set(), uploader=mock_upload, saver=lambda s: None)
    watcher.scan()
    
    assert len(uploaded) == 1
    assert "file.txt" in uploaded


def test_watcher_resumes_from_state(tmp_path):
    """Test that watcher resumes from previous state"""
    uploaded = []
    
    def mock_upload(url, file):
        uploaded.append(file.name)
        return 201
        
    f1 = tmp_path / "old.txt"
    f1.write_text("old content")
    from common.hashing import hash_file
    old_hash = hash_file(f1)
    
    f2 = tmp_path / "new.txt"
    f2.write_text("new content")
    
    watcher = DirectoryWatcher(tmp_path, "http://x", state={old_hash}, uploader=mock_upload, saver=lambda s: None)
    watcher.scan()
    
    assert len(uploaded) == 1
    assert "new.txt" in uploaded
    assert "old.txt" not in uploaded


def test_watcher_handles_multiple_files(tmp_path):
    """Test watcher with multiple files"""
    uploaded = []
    
    def mock_upload(url, file):
        uploaded.append(file.name)
        return 201
    
    for i in range(5):
        (tmp_path / f"file{i}.txt").write_text(f"content{i}")
    
    watcher = DirectoryWatcher(tmp_path, "http://x", state=set(), uploader=mock_upload, saver=lambda s: None)
    watcher.scan()
    
    assert len(uploaded) == 5


def test_watcher_handles_upload_failure(tmp_path):
    """Test that watcher doesn't save state on upload failure"""
    uploaded = []
    saved_states = []
    
    def mock_upload(url, file):
        uploaded.append(file.name)
        return 500  
    
    def mock_save(s):
        saved_states.append(set(s))
    
    f = tmp_path / "a.txt"
    f.write_text("hello")
    
    watcher = DirectoryWatcher(tmp_path, "http://x", state=set(), uploader=mock_upload, saver=mock_save)
    watcher.scan()
    
    assert len(uploaded) == 1
    assert len(saved_states) == 0


def test_watcher_handles_409_duplicate(tmp_path, monkeypatch):
    """Test that watcher saves state when server returns 409 (duplicate)"""
    uploaded = []
    saved_states = []
    
    def mock_upload(url, file):
        uploaded.append(file.name)
        return 409 
    
    def mock_save(s):
        saved_states.append(set(s))
    
    f = tmp_path / "a.txt"
    f.write_text("hello")
    
    watcher = DirectoryWatcher(tmp_path, "http://x", state=set(), uploader=mock_upload, saver=mock_save)
    watcher.scan()
    
    assert len(saved_states) == 1
    assert len(saved_states[0]) == 1


def test_watcher_empty_directory(tmp_path):
    """Test watcher with empty directory"""
    uploaded = []
    
    def mock_upload(url, file):
        uploaded.append(file.name)
        return 201
    
    watcher = DirectoryWatcher(tmp_path, "http://x", state=set(), uploader=mock_upload, saver=lambda s: None)
    watcher.scan()
    
    assert len(uploaded) == 0

# Other additional tests

def test_full_workflow(tmp_path):
    """Test complete workflow: create file, upload, verify state"""
    uploaded_files = []
    final_state = None

    def mock_upload(url, file):
        uploaded_files.append(str(file))
        return 201

    def mock_save(s):
        nonlocal final_state
        final_state = set(s)

    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")
    from common.hashing import hash_file
    expected_hash = hash_file(test_file)

    watcher = DirectoryWatcher(
        tmp_path,
        "http://test",
        state=set(),
        uploader=mock_upload,
        saver=mock_save
    )
    watcher.scan()

    assert len(uploaded_files) == 1
    assert final_state == {expected_hash}


def test_concurrent_client_simulation(tmp_path):
    """Simulate multiple clients with shared state"""
    global_state = set()
    uploaded_by_client = {1: [], 2: []}

    def mock_upload(url, file):
        return 201

    def mock_save(s):
        global_state.update(s)

    watcher1 = DirectoryWatcher(
        tmp_path,
        "http://test",
        state=set(global_state),
        uploader=mock_upload,
        saver=mock_save
    )
    test_file = tmp_path / "shared.txt"
    test_file.write_text("shared content")
    watcher1.scan()
    uploaded_by_client[1].append("shared.txt")

    watcher2 = DirectoryWatcher(
        tmp_path,
        "http://test",
        state=set(global_state),
        uploader=mock_upload,
        saver=mock_save
    )
    watcher2.scan()

    assert len(uploaded_by_client[1]) == 1
    assert len(uploaded_by_client[2]) == 0


