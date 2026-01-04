"""Reddit API client using PRAW."""

from collections.abc import Iterator
from datetime import datetime, timezone
from typing import Union

import praw
from praw.models import Comment, Submission

from .config import Settings
from .models import ContentType, RedditComment, RedditPost


class RedditClient:
    """Client for interacting with the Reddit API."""

    def __init__(self, settings: Settings):
        """Initialize the Reddit client with settings."""
        self.settings = settings
        self.reddit = praw.Reddit(
            client_id=settings.client_id,
            client_secret=settings.client_secret.get_secret_value(),
            username=settings.username,
            password=settings.password.get_secret_value(),
            user_agent=settings.user_agent,
        )

    def get_saved_items(
        self,
        limit: int | None = None,
        include_comments: bool = True,
    ) -> Iterator[Union[RedditPost, RedditComment]]:
        """
        Fetch saved items from the authenticated user's account.

        Args:
            limit: Maximum number of items to fetch (None for all)
            include_comments: Whether to include saved comments

        Yields:
            RedditPost or RedditComment objects
        """
        user = self.reddit.user.me()
        if user is None:
            raise RuntimeError("Failed to authenticate with Reddit")

        saved_items = user.saved(limit=limit)

        for item in saved_items:
            if isinstance(item, Submission):
                yield self._submission_to_post(item)
            elif isinstance(item, Comment) and include_comments:
                yield self._comment_to_model(item)

    def _submission_to_post(self, submission: Submission) -> RedditPost:
        """Convert a PRAW Submission to a RedditPost model."""
        return RedditPost(
            id=submission.id,
            author=str(submission.author) if submission.author else "[deleted]",
            subreddit=str(submission.subreddit),
            created_utc=datetime.fromtimestamp(submission.created_utc, tz=timezone.utc),
            permalink=submission.permalink,
            score=submission.score,
            url=submission.url,
            title=submission.title,
            selftext=submission.selftext or "",
            selftext_html=submission.selftext_html,
            is_self=submission.is_self,
            link_flair_text=submission.link_flair_text,
            num_comments=submission.num_comments,
            upvote_ratio=submission.upvote_ratio,
            content_type=ContentType.POST,
        )

    def _comment_to_model(self, comment: Comment) -> RedditComment:
        """Convert a PRAW Comment to a RedditComment model."""
        # Get the parent submission's title
        link_title = ""
        try:
            link_title = comment.link_title
        except AttributeError:
            pass

        return RedditComment(
            id=comment.id,
            author=str(comment.author) if comment.author else "[deleted]",
            subreddit=str(comment.subreddit),
            created_utc=datetime.fromtimestamp(comment.created_utc, tz=timezone.utc),
            permalink=comment.permalink,
            score=comment.score,
            url=f"https://reddit.com{comment.permalink}",
            body=comment.body or "",
            body_html=comment.body_html,
            link_title=link_title,
            link_id=comment.link_id,
            parent_id=comment.parent_id,
            is_submitter=comment.is_submitter,
            content_type=ContentType.COMMENT,
        )

    def unsave_item(self, item_id: str) -> None:
        """Remove an item from saved list after successful download."""
        # This could be used to unsave items after downloading
        # Implementation depends on whether user wants this feature
        pass
