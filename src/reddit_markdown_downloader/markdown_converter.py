"""Convert Reddit content to Obsidian-compatible Markdown."""

from datetime import datetime
from typing import Union

from markdownify import markdownify

from .models import ContentType, RedditComment, RedditPost, SubredditMapping


class MarkdownConverter:
    """Convert Reddit content to Markdown with Obsidian frontmatter."""

    def __init__(self, add_frontmatter: bool = True):
        """Initialize the converter."""
        self.add_frontmatter = add_frontmatter

    def convert(
        self,
        content: Union[RedditPost, RedditComment],
        mapping: SubredditMapping | None = None,
    ) -> str:
        """
        Convert Reddit content to Markdown.

        Args:
            content: The Reddit post or comment to convert
            mapping: Optional subreddit mapping for additional tags

        Returns:
            Markdown string with optional frontmatter
        """
        if content.content_type == ContentType.POST:
            return self._convert_post(content, mapping)  # type: ignore
        else:
            return self._convert_comment(content, mapping)  # type: ignore

    def _convert_post(
        self,
        post: RedditPost,
        mapping: SubredditMapping | None = None,
    ) -> str:
        """Convert a Reddit post to Markdown."""
        parts = []

        # Add frontmatter
        if self.add_frontmatter:
            parts.append(self._generate_frontmatter(post, mapping))

        # Add title as H1
        parts.append(f"# {post.title}\n")

        # Add metadata section
        parts.append(self._generate_metadata_section(post))

        # Add content
        if post.is_self and post.selftext:
            # Self post - convert HTML to markdown if available
            if post.selftext_html:
                content = self._html_to_markdown(post.selftext_html)
            else:
                content = post.selftext
            parts.append(f"\n## Content\n\n{content}\n")
        elif not post.is_self:
            # Link post
            parts.append(f"\n## Link\n\n[{post.url}]({post.url})\n")

        return "\n".join(parts)

    def _convert_comment(
        self,
        comment: RedditComment,
        mapping: SubredditMapping | None = None,
    ) -> str:
        """Convert a Reddit comment to Markdown."""
        parts = []

        # Add frontmatter
        if self.add_frontmatter:
            parts.append(self._generate_frontmatter(comment, mapping))

        # Add title (from parent post or generated)
        title = comment.link_title or f"Comment by u/{comment.author}"
        parts.append(f"# {title}\n")

        # Add metadata section
        parts.append(self._generate_metadata_section(comment))

        # Add comment content
        if comment.body_html:
            content = self._html_to_markdown(comment.body_html)
        else:
            content = comment.body

        parts.append(f"\n## Saved Comment\n\n{content}\n")

        return "\n".join(parts)

    def _generate_frontmatter(
        self,
        content: Union[RedditPost, RedditComment],
        mapping: SubredditMapping | None = None,
    ) -> str:
        """Generate YAML frontmatter for Obsidian."""
        tags = ["reddit", f"r/{content.subreddit}"]

        if mapping and mapping.tags:
            tags.extend(mapping.tags)

        if content.content_type == ContentType.COMMENT:
            tags.append("comment")
        else:
            tags.append("post")

        # Format tags for YAML
        tags_str = "\n".join(f"  - {tag}" for tag in tags)

        frontmatter = f"""---
source: reddit
subreddit: r/{content.subreddit}
author: u/{content.author}
created: {content.created_utc.strftime("%Y-%m-%d")}
saved: {datetime.now().strftime("%Y-%m-%d")}
url: {content.reddit_url}
score: {content.score}
type: {content.content_type.value}
tags:
{tags_str}
---
"""
        return frontmatter

    def _generate_metadata_section(
        self,
        content: Union[RedditPost, RedditComment],
    ) -> str:
        """Generate a metadata callout section."""
        created_date = content.created_utc.strftime("%Y-%m-%d %H:%M UTC")

        metadata = f"""> [!info] Reddit Metadata
> - **Subreddit**: [[r/{content.subreddit}]]
> - **Author**: u/{content.author}
> - **Posted**: {created_date}
> - **Score**: {content.score}
> - **Link**: [View on Reddit]({content.reddit_url})"""

        if isinstance(content, RedditPost):
            metadata += f"\n> - **Comments**: {content.num_comments}"
            if content.link_flair_text:
                metadata += f"\n> - **Flair**: {content.link_flair_text}"

        return metadata

    def _html_to_markdown(self, html: str) -> str:
        """Convert HTML to Markdown."""
        if not html:
            return ""

        # Use markdownify to convert HTML to Markdown
        markdown = markdownify(
            html,
            heading_style="ATX",
            bullets="-",
            code_language="",
            escape_asterisks=False,
            escape_underscores=False,
        )

        # Clean up excessive whitespace
        lines = markdown.split("\n")
        cleaned_lines = []
        prev_empty = False

        for line in lines:
            is_empty = not line.strip()
            if is_empty and prev_empty:
                continue
            cleaned_lines.append(line)
            prev_empty = is_empty

        return "\n".join(cleaned_lines).strip()
