"""Manage the Obsidian vault with PARA organization."""

import re
from pathlib import Path
from typing import Union

from .markdown_converter import MarkdownConverter
from .models import (
    DownloadStats,
    PARACategory,
    RedditComment,
    RedditPost,
    SubredditMapping,
    VaultConfig,
)


class VaultManager:
    """Manage saving Reddit content to an Obsidian vault using PARA organization."""

    def __init__(self, config: VaultConfig):
        """Initialize the vault manager."""
        self.config = config
        self.vault_path = Path(config.vault_path).expanduser().resolve()
        self.converter = MarkdownConverter(add_frontmatter=config.add_frontmatter)
        self.stats = DownloadStats()

        # Ensure vault directory exists
        self._ensure_vault_structure()

    def _ensure_vault_structure(self) -> None:
        """Create the PARA folder structure if it doesn't exist."""
        for category in PARACategory:
            category_path = self.vault_path / category.value
            category_path.mkdir(parents=True, exist_ok=True)

        # Create a Reddit subfolder in Resources by default
        reddit_path = self.vault_path / PARACategory.RESOURCES.value / "Reddit"
        reddit_path.mkdir(parents=True, exist_ok=True)

    def save_content(
        self,
        content: Union[RedditPost, RedditComment],
        skip_existing: bool = True,
    ) -> Path | None:
        """
        Save Reddit content to the vault.

        Args:
            content: The Reddit post or comment to save
            skip_existing: Skip if file already exists

        Returns:
            Path to the saved file, or None if skipped
        """
        self.stats.total_items += 1

        # Determine the target path
        target_path = self._get_target_path(content)

        # Check if file exists
        if skip_existing and target_path.exists():
            self.stats.skipped += 1
            return None

        # Get mapping for additional tags
        mapping = self._get_mapping_for_subreddit(content.subreddit)

        # Convert to markdown
        markdown_content = self.converter.convert(content, mapping)

        # Ensure parent directory exists
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Write the file
        target_path.write_text(markdown_content, encoding="utf-8")

        # Update stats
        if isinstance(content, RedditPost):
            self.stats.posts_downloaded += 1
        else:
            self.stats.comments_downloaded += 1

        return target_path

    def _get_target_path(self, content: Union[RedditPost, RedditComment]) -> Path:
        """Determine the target file path for content."""
        # Get PARA category and subfolder for subreddit
        category, subfolder = self.config.get_category_for_subreddit(content.subreddit)

        # Build the path
        path = self.vault_path / category.value

        if subfolder:
            path = path / subfolder
        elif self.config.create_subreddit_folders:
            # Use subreddit name as subfolder under Reddit
            path = path / "Reddit" / content.filename_safe_subreddit

        # Generate filename
        filename = self._generate_filename(content)
        return path / filename

    def _generate_filename(self, content: Union[RedditPost, RedditComment]) -> str:
        """Generate a safe filename for the content."""
        # Get base title
        title = content.filename_safe_title

        # Add date prefix for sorting
        date_prefix = content.created_utc.strftime("%Y-%m-%d")

        # Sanitize and create filename
        # Remove any remaining problematic characters
        safe_title = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "-", title)
        safe_title = re.sub(r"-+", "-", safe_title)  # Collapse multiple dashes
        safe_title = safe_title.strip("- ")

        # Limit length (account for date prefix and extension)
        max_title_len = 150
        if len(safe_title) > max_title_len:
            safe_title = safe_title[:max_title_len].rsplit(" ", 1)[0]

        return f"{date_prefix} - {safe_title}.md"

    def _get_mapping_for_subreddit(self, subreddit: str) -> SubredditMapping | None:
        """Get the SubredditMapping for a subreddit if one exists."""
        subreddit_lower = subreddit.lower()
        for mapping in self.config.subreddit_mappings:
            if mapping.subreddit.lower() == subreddit_lower:
                return mapping
        return None

    def get_stats(self) -> DownloadStats:
        """Get download statistics."""
        return self.stats

    def reset_stats(self) -> None:
        """Reset download statistics."""
        self.stats = DownloadStats()
