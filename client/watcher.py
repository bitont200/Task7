import time
from pathlib import Path
from common.hashing import hash_file
from client.state import load_state, save_state
from client.uploader import upload_file
from rich.console import Console
from datetime import datetime

console = Console()

class DirectoryWatcher:

    def __init__(self, directory, server_url, state=None, uploader=None, saver=None, verbose=False):
        self.directory = Path(directory)
        self.server_url = server_url
        self.state = state if state is not None else load_state()
        self.upload_file = uploader if uploader is not None else upload_file
        self.save_state_func = saver if saver is not None else save_state
        self.verbose = verbose
        self.stats = {
            'uploaded': 0,
            'skipped': 0,
            'failed': 0,
            'duplicates': 0
        }

    def log(self, message, style=""):
        """Log message if verbose mode is enabled"""
        if self.verbose:
            timestamp = datetime.now().strftime("%H:%M:%S")
            console.print(f"[dim]{timestamp}[/dim] {message}", style=style)

    def scan(self):
        files = [f for f in self.directory.iterdir() if f.is_file()]
        
        if self.verbose:
            self.log(f"Scanning directory: {len(files)} file(s) found", "cyan")
        
        for file in files:
            try:
                file_hash = hash_file(file)

                if file_hash in self.state:
                    self.stats['skipped'] += 1
                    self.log(f"Skipped: {file.name} (already uploaded)", "dim")
                    continue

                self.log(f"Uploading: {file.name}...", "yellow")
                status = self.upload_file(self.server_url, file)

                if status == 201:
                    self.state.add(file_hash)
                    self.save_state_func(self.state)
                    self.stats['uploaded'] += 1
                    self.log(f"Uploaded: {file.name}", "green")
                elif status == 409:
                    self.state.add(file_hash)
                    self.save_state_func(self.state)
                    self.stats['duplicates'] += 1
                    self.log(f"Duplicate: {file.name} (already on server)", "blue")
                else:
                    self.stats['failed'] += 1
                    self.log(f"Failed: {file.name} (status {status})", "red")
                    
            except Exception as e:
                self.stats['failed'] += 1
                self.log(f"Error processing {file.name}: {e}", "red")

    def print_stats(self):
        """Print statistics summary"""
        console.print("\n[bold]Session Statistics:[/bold]")
        console.print(f"  Uploaded: {self.stats['uploaded']}")
        console.print(f"  Duplicates: {self.stats['duplicates']}")
        console.print(f"  Skipped: {self.stats['skipped']}")
        console.print(f"  Failed: {self.stats['failed']}")

    def run(self, interval=5):
        try:
            while True:
                self.scan()
                if self.verbose:
                    self.log(f"Sleeping for {interval}s...\n", "dim")
                time.sleep(interval)
        except KeyboardInterrupt:
            if self.verbose:
                self.print_stats()
            raise