import json
from pathlib import Path

STATE_DIR = Path.home() / ".local" / "share" / "Task7"
STATE_FILE = STATE_DIR / "state.json"

STATE_DIR.mkdir(parents=True, exist_ok=True)

def load_state():
    if not STATE_FILE.exists():
        return set()
    with open(STATE_FILE, "r") as f:
        return set(json.load(f))

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(list(state), f)
