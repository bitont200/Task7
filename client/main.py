import typer
from pathlib import Path
from typing import Optional
from client.watcher import DirectoryWatcher
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
import sys

app = typer.Typer(help="Asset Catalog Client - Watch and upload files to server")
console = Console()

@app.command()
def watch(
    directory: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        help="Directory to watch for file changes"
    ),
    server_url: str = typer.Option(
        "http://localhost:8000",
        "--server",
        "-s",
        help="Server URL to upload files to"
    ),
    interval: int = typer.Option(
        5,
        "--interval",
        "-i",
        min=1,
        help="Scan interval in seconds"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output"
    )
):

    try:
        console.print(f"[bold green]Starting Asset Catalog Client[/bold green]")
        console.print(f"[cyan]Watching:[/cyan] {directory.absolute()}")
        console.print(f"[cyan]Server:[/cyan] {server_url}")
        console.print(f"[cyan]Scan interval:[/cyan] {interval}s")
        console.print("[yellow]Press Ctrl+C to stop[/yellow]\n")
        
        watcher = DirectoryWatcher(directory, server_url, verbose=verbose)
        watcher.run(interval=interval)
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down gracefully...[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)

@app.command()
def status(
    directory: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=False,
        dir_okay=True,
        help="Directory to check status for"
    )
):
    
    from client.state import load_state
    from common.hashing import hash_file
    
    state = load_state()
    console.print(f"[bold]Status for:[/bold] {directory.absolute()}\n")
    console.print(f"[cyan]Total files uploaded:[/cyan] {len(state)}")
    
    files = [f for f in directory.iterdir() if f.is_file()]
    uploaded_count = 0
    pending_count = 0
    
    console.print(f"\n[bold]Current files in directory:[/bold]")
    for file in files:
        file_hash = hash_file(file)
        if file_hash in state:
            console.print(f"[green]{file.name}[/green] (uploaded)")
            uploaded_count += 1
        else:
            console.print(f"[yellow]{file.name}[/yellow] (pending)")
            pending_count += 1
    
    console.print(f"\n[cyan]Summary:[/cyan]")
    console.print(f"  Uploaded: {uploaded_count}")
    console.print(f"  Pending: {pending_count}")

@app.command()
def reset():
    
    from client.state import STATE_FILE, save_state
    
    confirm = typer.confirm("Are you sure you want to reset the state? This will cause all files to be uploaded again.")
    
    if confirm:
        save_state(set())
        console.print("[green]State reset successfully![/green]")
    else:
        console.print("[yellow]Reset cancelled.[/yellow]")

if __name__ == "__main__":
    app()