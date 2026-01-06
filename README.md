# Task 7: Asset Catalog

A distributed asset catalog system for uploading and storing files from multiple remote clients to a centralized server.

## 📁 Project Structure

```
Task7/
├── client/
│   ├── __init__.py
│   ├── main.py          # CLI entry point (Typer)
│   ├── watcher.py       # Directory watcher with scanning logic
│   ├── uploader.py      # HTTP upload functionality
│   └── state.py         # State persistence management
├── server/
│   ├── __init__.py
│   └── server.py        # HTTP server implementation
├── common/
│   ├── __init__.py
│   └── hashing.py       # SHA-256 file hashing utility
├── tests/
│   ├── __init__.py
│   └── test_client.py   # Comprehensive test suite 
├── requirements.txt      # Python dependencies
├── README.md            # This file
└── .gitignore          
```

## 🎯 Features

### Client
- 📁 **Directory Watching** - Monitors directories for file changes
- 🔒 **Deduplication** - SHA-256 hash-based duplicate detection
- 💾 **State Persistence** - Recovers from previous sessions
- 🔄 **Multi-Client Support** - Multiple clients can run concurrently
- 🎨 **Rich CLI** - Beautiful terminal interface with Typer
- 📊 **Status Tracking** - View upload status of files

## 📋 Requirements

- Python 3.8+
- See `requirements.txt` for dependencies

## 🚀 Installation

```bash
cd Task7
pip install -r requirements.txt
```

## 💻 Usage

### Start the Server

```bash
python -m server.server
```

Server will start on `http://localhost:8000`

### Start the Client

```bash
python -m client.main watch /path/to/directory
```

## 🧪 Testing

```bash
python -m pytest
```