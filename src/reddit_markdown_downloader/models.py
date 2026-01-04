"""Pydantic models for Reddit content."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, computed_field


class PARACategory(str, Enum):
    """PARA organization categories."""

    PROJECTS = "1-Projects"
    AREAS = "2-Areas"
    RESOURCES = "3-Resources"
    ARCHIVES = "4-Archives"


class ContentType(str, Enum):
    """Type of Reddit content."""

    POST = "post"
    COMMENT = "comment"


class RedditContent(BaseModel):
    """Base model for Reddit content."""

    id: str
    author: str
    subreddit: str
    created_utc: datetime
    permalink: str
    score: int
    url: str
    content_type: ContentType

    @computed_field
    @property
    def reddit_url(self) -> str:
        """Full Reddit URL."""
        return f"https://reddit.com{self.permalink}"

    @computed_field
    @property
    def filename_safe_subreddit(self) -> str:
        """Subreddit name safe for filenames."""
        return self.subreddit.replace("/", "_").replace("\\", "_")


class RedditPost(RedditContent):
    """Model for a Reddit post/submission."""

    title: str
    selftext: str = ""
    selftext_html: Optional[str] = None
    is_self: bool = True
    link_flair_text: Optional[str] = None
    num_comments: int = 0
    upvote_ratio: float = 0.0
    content_type: ContentType = ContentType.POST

    @computed_field
    @property
    def filename_safe_title(self) -> str:
        """Title safe for use as filename."""
        # Remove/replace characters not allowed in filenames
        unsafe_chars = '<>:"/\\|?*'
        safe_title = self.title
        for char in unsafe_chars:
            safe_title = safe_title.replace(char, "-")
        # Limit length and strip whitespace
        return safe_title[:100].strip()


class RedditComment(RedditContent):
    """Model for a Reddit comment."""

    body: str
    body_html: Optional[str] = None
    link_title: str = ""
    link_id: str = ""
    parent_id: str = ""
    is_submitter: bool = False
    content_type: ContentType = ContentType.COMMENT

    @computed_field
    @property
    def filename_safe_title(self) -> str:
        """Generate a filename from comment context."""
        # Use first 50 chars of body or link title
        title = self.link_title or self.body[:50]
        unsafe_chars = '<>:"/\\|?*\n\r'
        safe_title = title
        for char in unsafe_chars:
            safe_title = safe_title.replace(char, "-")
        return f"comment-{safe_title[:80].strip()}"


class SubredditMapping(BaseModel):
    """Mapping of subreddit to PARA category and optional subfolder."""

    subreddit: str
    category: PARACategory = PARACategory.RESOURCES
    subfolder: Optional[str] = None
    tags: list[str] = Field(default_factory=list)


class VaultConfig(BaseModel):
    """Configuration for the Obsidian vault."""

    vault_path: str
    para_categories: dict[str, PARACategory] = Field(default_factory=dict)
    default_category: PARACategory = PARACategory.RESOURCES
    subreddit_mappings: list[SubredditMapping] = Field(default_factory=list)
    create_subreddit_folders: bool = True
    add_frontmatter: bool = True
    include_comments: bool = False
    max_items: Optional[int] = None

    def get_category_for_subreddit(self, subreddit: str) -> tuple[PARACategory, Optional[str]]:
        """Get the PARA category and subfolder for a subreddit."""
        subreddit_lower = subreddit.lower()

        # Check explicit mappings first
        for mapping in self.subreddit_mappings:
            if mapping.subreddit.lower() == subreddit_lower:
                return mapping.category, mapping.subfolder

        # Check category patterns
        if subreddit_lower in self.para_categories:
            return self.para_categories[subreddit_lower], None

        return self.default_category, None


class DownloadStats(BaseModel):
    """Statistics for a download session."""

    total_items: int = 0
    posts_downloaded: int = 0
    comments_downloaded: int = 0
    errors: int = 0
    skipped: int = 0

    def summary(self) -> str:
        """Return a summary of the download session."""
        return (
            f"Downloaded: {self.posts_downloaded} posts, {self.comments_downloaded} comments | "
            f"Skipped: {self.skipped} | Errors: {self.errors} | Total: {self.total_items}"
        )
