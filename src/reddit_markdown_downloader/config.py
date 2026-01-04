"""Configuration management using pydantic-settings."""

from pathlib import Path
from typing import Optional

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from .models import PARACategory, SubredditMapping


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="REDDIT_",
        extra="ignore",
    )

    # Reddit API credentials
    client_id: str = Field(..., description="Reddit API client ID")
    client_secret: SecretStr = Field(..., description="Reddit API client secret")
    username: str = Field(..., description="Reddit username")
    password: SecretStr = Field(..., description="Reddit password")
    user_agent: str = Field(
        default="reddit-markdown-downloader:v0.1.0 (by /u/your_username)",
        description="User agent for Reddit API",
    )

    # Vault settings
    vault_path: str = Field(
        default="./obsidian-vault",
        description="Path to Obsidian vault",
    )
    default_category: PARACategory = Field(
        default=PARACategory.RESOURCES,
        description="Default PARA category for saved items",
    )

    # Download settings
    max_items: Optional[int] = Field(
        default=None,
        description="Maximum number of items to download (None for all)",
    )
    include_comments: bool = Field(
        default=True,
        description="Include saved comments",
    )
    create_subreddit_folders: bool = Field(
        default=True,
        description="Create subfolders for each subreddit",
    )
    skip_existing: bool = Field(
        default=True,
        description="Skip files that already exist",
    )

    def get_vault_path(self) -> Path:
        """Get the vault path as a Path object."""
        return Path(self.vault_path).expanduser().resolve()


def get_default_subreddit_mappings() -> list[SubredditMapping]:
    """Get default subreddit to PARA category mappings."""
    return [
        # Programming/Development -> Resources/Programming
        SubredditMapping(
            subreddit="programming",
            category=PARACategory.RESOURCES,
            subfolder="Programming",
            tags=["programming", "development"],
        ),
        SubredditMapping(
            subreddit="python",
            category=PARACategory.RESOURCES,
            subfolder="Programming/Python",
            tags=["programming", "python"],
        ),
        SubredditMapping(
            subreddit="rust",
            category=PARACategory.RESOURCES,
            subfolder="Programming/Rust",
            tags=["programming", "rust"],
        ),
        SubredditMapping(
            subreddit="golang",
            category=PARACategory.RESOURCES,
            subfolder="Programming/Go",
            tags=["programming", "go"],
        ),
        SubredditMapping(
            subreddit="javascript",
            category=PARACategory.RESOURCES,
            subfolder="Programming/JavaScript",
            tags=["programming", "javascript"],
        ),
        SubredditMapping(
            subreddit="typescript",
            category=PARACategory.RESOURCES,
            subfolder="Programming/TypeScript",
            tags=["programming", "typescript"],
        ),
        # Tech/Tools -> Resources/Technology
        SubredditMapping(
            subreddit="linux",
            category=PARACategory.RESOURCES,
            subfolder="Technology/Linux",
            tags=["technology", "linux"],
        ),
        SubredditMapping(
            subreddit="vim",
            category=PARACategory.RESOURCES,
            subfolder="Technology/Vim",
            tags=["technology", "vim", "editor"],
        ),
        SubredditMapping(
            subreddit="neovim",
            category=PARACategory.RESOURCES,
            subfolder="Technology/Neovim",
            tags=["technology", "neovim", "editor"],
        ),
        SubredditMapping(
            subreddit="emacs",
            category=PARACategory.RESOURCES,
            subfolder="Technology/Emacs",
            tags=["technology", "emacs", "editor"],
        ),
        # Learning -> Areas/Learning
        SubredditMapping(
            subreddit="learnprogramming",
            category=PARACategory.AREAS,
            subfolder="Learning/Programming",
            tags=["learning", "programming"],
        ),
        SubredditMapping(
            subreddit="learnpython",
            category=PARACategory.AREAS,
            subfolder="Learning/Python",
            tags=["learning", "python"],
        ),
        # Personal Finance -> Areas/Finance
        SubredditMapping(
            subreddit="personalfinance",
            category=PARACategory.AREAS,
            subfolder="Finance",
            tags=["finance", "personal-finance"],
        ),
        SubredditMapping(
            subreddit="financialindependence",
            category=PARACategory.AREAS,
            subfolder="Finance/FIRE",
            tags=["finance", "fire"],
        ),
        # Productivity -> Areas/Productivity
        SubredditMapping(
            subreddit="productivity",
            category=PARACategory.AREAS,
            subfolder="Productivity",
            tags=["productivity"],
        ),
        SubredditMapping(
            subreddit="ObsidianMD",
            category=PARACategory.AREAS,
            subfolder="Productivity/Obsidian",
            tags=["productivity", "obsidian", "pkm"],
        ),
    ]
