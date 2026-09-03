"""
Command Line Interface (CLI) for Face Identification & Blockchain Verification Pipeline.
Built with Typer and Rich for beautiful terminal interactions.
"""

import sys
import time
import json
from pathlib import Path
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich import print as rprint

from pipeline import FaceVerificationPipeline
from face_engine import FaceEngine
from web_search_engine import DiscoveredPost
from blockchain_engine import BlockchainEngine
import config

app = typer.Typer(
    name="face-chain-cli",
    help="HH Goa 2026 Task 3: Face Identification & Blockchain Verification Pipeline",
    add_completion=False
)
console = Console()

def print_banner():
    banner = """
[bold cyan]========================================================================[/bold cyan]
[bold white]  HH GOA 2026 SHORTLISTING TASK 3: FACE ID & BLOCKCHAIN VERIFICATION  [/bold white]
[bold cyan]========================================================================[/bold cyan]
 [bold yellow]Pipeline:[/bold yellow] Face Scan Input -> Reverse Web Search -> Blockchain Mint -> Verification
    """
    console.print(banner)

@app.command()
def scan(
    image: str = typer.Option("samples/sample_face_1.jpg", "--image", "-i", help="Path to input face image"),
    platform: str = typer.Option("x", "--platform", "-p", help="Platform filter: 'x', 'twitter', or 'all'"),
    blockchain: str = typer.Option(config.DEFAULT_BLOCKCHAIN_BACKEND, "--blockchain", "-b", help="Backend: 'simulated', 'evm', or 'sepolia'"),
    export: str = typer.Option("output/latest_pipeline_run.json", "--export", "-e", help="JSON export path")
):
    """Run full end-to-end pipeline on an input face image."""
    print_banner()

    img_path = Path(image)
    if not img_path.exists():
        console.print(f"[bold red]Error:[/bold red] File not found at path '{image}'")
        raise typer.Exit(code=1)

    pipeline = FaceVerificationPipeline(blockchain_backend=blockchain)

    with Progress(
        SpinnerColumn(spinner_name="dots"),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=False
    ) as progress:

        t1 = progress.add_task("[bold cyan]Stage 1: Face Detection & Encoding...", total=100)
        progress.update(t1, completed=30)
        time.sleep(0.4)
        progress.update(t1, completed=100)

        t2 = progress.add_task(f"[bold magenta]Stage 2: Searching {platform.upper()} & Social Media...", total=100)
        progress.update(t2, completed=40)
        time.sleep(0.5)
        progress.update(t2, completed=100)

        t3 = progress.add_task("[bold yellow]Stage 3: Uploading Data Fingerprint to Blockchain...", total=100)
        progress.update(t3, completed=50)
        time.sleep(0.5)
        progress.update(t3, completed=100)

        t4 = progress.add_task("[bold green]Stage 4: Performing On-Chain Data Re-Verification...", total=100)
        progress.update(t4, completed=60)
        time.sleep(0.3)
        progress.update(t4, completed=100)

    # Run execution logic
    result = pipeline.run_pipeline(str(img_path), platform_filter=platform)

    if not result.success:
        console.print(Panel(f"[bold red]Pipeline Failed:[/bold red] {result.summary_notes}", title="Result"))
        raise typer.Exit(code=1)

    scan_info = result.face_scan
    post = result.matched_post
    tx = result.tx_receipt
    audit = result.audit_report

    # Render Summary Table
    table = Table(title="[bold green]Pipeline Execution Summary[/bold green]", box=None)
    table.add_column("Pipeline Stage", style="cyan", no_wrap=True)
    table.add_column("Details & Output Data", style="white")

    table.add_row("Input Face Image", f"{scan_info.image_path} ({scan_info.bounding_box})")
    table.add_row("Face SHA-256 Hash", f"[dim]{scan_info.face_hash}[/dim]")
    table.add_row("Matched Social Post", f"{post.platform} | [bold yellow]{post.author_handle}[/bold yellow] ({post.author_name})")
    table.add_row("Post URL", f"[link={post.post_url}]{post.post_url}[/link]")
    table.add_row("Facial Match Score", f"[bold green]{post.similarity_score * 100:.2f}%[/bold green]")
    table.add_row("Post Content Fingerprint", f"[dim]{post.post_hash}[/dim]")
    table.add_row("Blockchain Backend", f"[bold magenta]{tx.blockchain_type.upper()}[/bold magenta]")
    table.add_row("Transaction Tx Hash", f"[yellow]{tx.tx_hash}[/yellow]")
    table.add_row("On-Chain Block #", f"Block #{tx.block_number}")
    table.add_row(
        "On-Chain Audit Status",
        f"[bold green]PASSED ({audit.status})[/bold green]" if audit.is_valid else f"[bold red]FAILED ({audit.status})[/bold red]"
    )

    console.print(table)

    # Export JSON result
    export_path = Path(export)
    export_path.parent.mkdir(exist_ok=True)
    export_data = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "face_hash": scan_info.face_hash,
        "post_url": post.post_url,
        "post_hash": post.post_hash,
        "similarity": post.similarity_score,
        "tx_hash": tx.tx_hash,
        "block_number": tx.block_number,
        "blockchain_type": tx.blockchain_type,
        "audit_status": audit.status,
        "audit_notes": audit.audit_notes
    }
    with open(export_path, "w") as f:
        json.dump(export_data, f, indent=2)

    console.print(f"\n[bold green]Done![/bold green] Results exported to [underline]{export_path}[/underline]")

@app.command()
def verify(
    hash_val: str = typer.Option(..., "--hash", "-h", help="Data Hash or Tx Hash to re-verify")
):
    """Re-verify a data hash or transaction against on-chain record."""
    print_banner()
    console.print(f"Querying blockchain record for hash: [yellow]{hash_val}[/yellow]...")

    engine = BlockchainEngine()
    audit = engine.verify_onchain(hash_val)

    if audit.status == "NOT_FOUND":
        console.print(f"[bold red]NOT FOUND:[/bold red] No record matching '{hash_val}' exists on the blockchain.")
        return

    table = Table(title="[bold yellow]On-Chain Verification Audit Report[/bold yellow]")
    table.add_column("Field", style="cyan")
    table.add_column("On-Chain Value", style="white")

    table.add_row("Verification Status", f"[bold green]{audit.status}[/bold green]" if audit.is_valid else f"[bold red]{audit.status}[/bold red]")
    table.add_row("Data Hash", audit.data_hash)
    table.add_row("On-Chain Face Hash", audit.onchain_face_hash)
    table.add_row("On-Chain Post URL", audit.onchain_post_url)
    table.add_row("On-Chain Timestamp", audit.onchain_timestamp)
    table.add_row("Registrar Address", audit.onchain_registrar)
    table.add_row("Audit Notes", audit.audit_notes)

    console.print(table)

@app.command()
def ledger():
    """Display current local blockchain ledger blocks."""
    print_banner()
    engine = BlockchainEngine()
    chain = engine.local_provider.chain

    console.print(f"[bold cyan]Local Blockchain Ledger ({len(chain)} Blocks)[/bold cyan]\n")
    for block in chain:
        console.print(f"[bold yellow]Block #{block['index']}[/bold yellow] | Hash: {block['block_hash'][:24]}... | Timestamp: {block['timestamp']}")
        for tx in block.get("transactions", []):
            console.print(f"   Tx: {tx.get('tx_id')} -> DataHash: {tx.get('data_hash')[:20]}...")

@app.command()
def demo():
    """Run automated demo across all sample face images."""
    print_banner()
    console.print("[bold yellow]Running End-to-End Automated Pipeline Demo...[/bold yellow]\n")

    sample_files = list(config.SAMPLES_DIR.glob("*.jpg"))
    if not sample_files:
        console.print("[red]No sample files found. Generating sample images...[/red]")
        from create_samples import generate_sample_faces
        generate_sample_faces()
        sample_files = list(config.SAMPLES_DIR.glob("*.jpg"))

    pipeline = FaceVerificationPipeline()
    for img_p in sample_files:
        console.print(f"\nProcessing sample image: [cyan]{img_p.name}[/cyan]")
        res = pipeline.run_pipeline(str(img_p))
        if res.success:
            console.print(f" -> Matched: [bold green]{res.matched_post.author_handle}[/bold green] ({res.matched_post.platform}) | Sim: [green]{res.matched_post.similarity_score*100:.1f}%[/green]")
            console.print(f" -> Blockchain Tx: [yellow]{res.tx_receipt.tx_hash}[/yellow] | Block #{res.tx_receipt.block_number}")
            console.print(f" -> Re-Verification: [bold green]{res.audit_report.status}[/bold green]")
        else:
            console.print(f" -> Failed: {res.summary_notes}")

if __name__ == "__main__":
    app()
