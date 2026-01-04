#!/usr/bin/env python3
"""Command-line interface for Reddit Markdown Downloader."""

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table

from .config import Settings, get_default_subreddit_mappings
from .models import PARACategory, RedditComment, RedditPost, VaultConfig
from .reddit_client import RedditClient
from .vault_manager import VaultManager

console = Console()


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="reddit-dl",
        description="Download saved Reddit articles as Markdown files for Obsidian",
    )

    parser.add_argument(
        "-v",
        "--vault",
        type=str,
        help="Path to Obsidian vault (overrides REDDIT_VAULT_PATH env var)",
    )

    parser.add_argument(
        "-n",
        "--max-items",
        type=int,
        default=None,
        help="Maximum number of items to download (default: all)",
    )

    parser.add_argument(
        "--no-comments",
        action="store_true",
        help="Skip saved comments, only download posts",
    )

    parser.add_argument(
        "--no-skip-existing",
        action="store_true",
        help="Overwrite existing files instead of skipping",
    )

    parser.add_argument(
        "--no-subreddit-folders",
        action="store_true",
        help="Don't create subfolders for each subreddit",
    )

    parser.add_argument(
        "--category",
        type=str,
        choices=["projects", "areas", "resources", "archives"],
        default="resources",
        help="Default PARA category for items (default: resources)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be downloaded without actually downloading",
    )

    parser.add_argument(
        "--list-mappings",
        action="store_true",
        help="Show default subreddit to PARA category mappings",
    )

    return parser


def show_mappings() -> None:
    """Display the default subreddit mappings."""
    mappings = get_default_subreddit_mappings()

    table = Table(title="Default Subreddit Mappings")
    table.add_column("Subreddit", style="cyan")
    table.add_column("Category", style="green")
    table.add_column("Subfolder", style="yellow")
    table.add_column("Tags", style="magenta")

    for mapping in mappings:
        table.add_row(
            f"r/{mapping.subreddit}",
            mapping.category.value,
            mapping.subfolder or "-",
            ", ".join(mapping.tags) if mapping.tags else "-",
        )

    console.print(table)


def run_download(args: argparse.Namespace) -> int:
    """Run the download process."""
    # Load settings from environment
    try:
        settings = Settings()  # type: ignore[call-arg]
    except Exception as e:
        console.print(f"[red]Error loading settings:[/red] {e}")
        console.print("\n[yellow]Required environment variables:[/yellow]")
        console.print("  REDDIT_CLIENT_ID     - Reddit API client ID")
        console.print("  REDDIT_CLIENT_SECRET - Reddit API client secret")
        console.print("  REDDIT_USERNAME      - Reddit username")
        console.print("  REDDIT_PASSWORD      - Reddit password")
        console.print("\n[yellow]Optional:[/yellow]")
        console.print("  REDDIT_VAULT_PATH    - Path to Obsidian vault")
        console.print("\nCreate a .env file or set these environment variables.")
        return 1

    # Override settings with CLI arguments
    vault_path = args.vault or settings.vault_path
    max_items = args.max_items or settings.max_items
    include_comments = not args.no_comments
    skip_existing = not args.no_skip_existing
    create_subreddit_folders = not args.no_subreddit_folders

    # Map category string to enum
    category_map = {
        "projects": PARACategory.PROJECTS,
        "areas": PARACategory.AREAS,
        "resources": PARACategory.RESOURCES,
        "archives": PARACategory.ARCHIVES,
    }
    default_category = category_map.get(args.category, PARACategory.RESOURCES)

    # Create vault config
    vault_config = VaultConfig(
        vault_path=vault_path,
        default_category=default_category,
        subreddit_mappings=get_default_subreddit_mappings(),
        create_subreddit_folders=create_subreddit_folders,
        add_frontmatter=True,
        include_comments=include_comments,
        max_items=max_items,
    )

    console.print(f"\n[bold]Reddit Markdown Downloader[/bold]")
    console.print(f"Vault: [cyan]{Path(vault_path).resolve()}[/cyan]")
    console.print(f"Default category: [green]{default_category.value}[/green]")

    if args.dry_run:
        console.print("[yellow]DRY RUN - No files will be written[/yellow]\n")

    # Initialize clients
    try:
        reddit_client = RedditClient(settings)
        console.print("[green]✓[/green] Connected to Reddit API")
    except Exception as e:
        console.print(f"[red]Error connecting to Reddit:[/red] {e}")
        return 1

    vault_manager = VaultManager(vault_config)
    console.print(f"[green]✓[/green] Vault initialized at {vault_path}\n")

    # Fetch and save items
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Downloading saved items...", total=None)

        items_processed = 0
        for item in reddit_client.get_saved_items(
            limit=max_items,
            include_comments=include_comments,
        ):
            items_processed += 1
            progress.update(task, completed=items_processed)

            # Build description
            if isinstance(item, RedditPost):
                desc = f"[cyan]Post:[/cyan] {item.title[:50]}..."
            else:
                desc = f"[magenta]Comment:[/magenta] r/{item.subreddit}"

            progress.update(task, description=desc)

            if not args.dry_run:
                try:
                    saved_path = vault_manager.save_content(item, skip_existing=skip_existing)
                    if saved_path:
                        progress.console.print(f"  [green]Saved:[/green] {saved_path.name}")
                except Exception as e:
                    vault_manager.stats.errors += 1
                    progress.console.print(f"  [red]Error:[/red] {e}")
            else:
                # Dry run - just show what would be saved
                if isinstance(item, RedditPost):
                    console.print(f"  Would save post: {item.title[:60]}")
                else:
                    console.print(f"  Would save comment from r/{item.subreddit}")

    # Print summary
    stats = vault_manager.get_stats()
    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"  Posts downloaded:    [green]{stats.posts_downloaded}[/green]")
    console.print(f"  Comments downloaded: [green]{stats.comments_downloaded}[/green]")
    console.print(f"  Skipped (existing):  [yellow]{stats.skipped}[/yellow]")
    console.print(f"  Errors:              [red]{stats.errors}[/red]")
    console.print(f"  Total processed:     {stats.total_items}")

    return 0 if stats.errors == 0 else 1


def main() -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if args.list_mappings:
        show_mappings()
        return 0

    return run_download(args)


if __name__ == "__main__":
    sys.exit(main())
