from http.server import HTTPServer, BaseHTTPRequestHandler
import os
import json
import hashlib

STORAGE_DIR = "server_storage"
META_FILE = "metadata.json"

os.makedirs(STORAGE_DIR, exist_ok=True)

if not os.path.exists(META_FILE):
    with open(META_FILE, "w") as f:
        json.dump({}, f)


class AssetHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        file_data = self.rfile.read(content_length)

        file_hash = hashlib.sha256(file_data).hexdigest()

        with open(META_FILE, "r") as f:
            metadata = json.load(f)

        if file_hash in metadata:
            self.send_response(409)
            self.end_headers()
            self.wfile.write(b"File already exists")
            return

        file_path = os.path.join(STORAGE_DIR, file_hash)
        with open(file_path, "wb") as f:
            f.write(file_data)

        metadata[file_hash] = {
            "size": len(file_data),
            "path": file_path
        }

        with open(META_FILE, "w") as f:
            json.dump(metadata, f, indent=2)

        self.send_response(201)
        self.end_headers()
        self.wfile.write(b"Uploaded successfully")


def run_server():
    server = HTTPServer(("0.0.0.0", 8000), AssetHandler)
    print("Server running on port 8000")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
