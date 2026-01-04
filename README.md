# Reddit Markdown Downloader

Download your saved Reddit posts and comments as Markdown files, organized in a PARA-based structure for Obsidian.

## Features

- Downloads saved Reddit posts and comments
- Converts content to Obsidian-compatible Markdown with frontmatter
- Organizes files using the PARA method (Projects, Areas, Resources, Archives)
- Smart subreddit-to-category mappings
- Rich CLI with progress indicators
- Configurable via environment variables or CLI flags

## Installation

Using [uv](https://github.com/astral-sh/uv):

```bash
# Clone the repository
git clone https://github.com/yourusername/reddit-markdown-downloader.git
cd reddit-markdown-downloader

# Install with uv
uv sync

# Or install in development mode
uv pip install -e .
```

## Setup

### 1. Create a Reddit App

1. Go to [Reddit App Preferences](https://www.reddit.com/prefs/apps)
2. Click "Create App" or "Create Another App"
3. Fill in the details:
   - Name: `reddit-markdown-downloader`
   - Type: Select "script"
   - Redirect URI: `http://localhost:8080`
4. Note your `client_id` (under the app name) and `client_secret`

### 2. Configure Environment

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your Reddit credentials:

```env
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USERNAME=your_username
REDDIT_PASSWORD=your_password
REDDIT_VAULT_PATH=~/Documents/ObsidianVault
```

## Usage

### Basic Usage

```bash
# Download all saved items
uv run reddit-dl

# Download to a specific vault
uv run reddit-dl --vault ~/Documents/MyVault

# Limit number of items
uv run reddit-dl --max-items 50

# Skip comments, only download posts
uv run reddit-dl --no-comments

# Dry run (see what would be downloaded)
uv run reddit-dl --dry-run
```

### CLI Options

```
usage: reddit-dl [-h] [-v VAULT] [-n MAX_ITEMS] [--no-comments]
                 [--no-skip-existing] [--no-subreddit-folders]
                 [--category {projects,areas,resources,archives}]
                 [--dry-run] [--list-mappings]

Options:
  -v, --vault PATH          Path to Obsidian vault
  -n, --max-items N         Maximum items to download
  --no-comments             Skip saved comments
  --no-skip-existing        Overwrite existing files
  --no-subreddit-folders    Don't create subreddit subfolders
  --category CATEGORY       Default PARA category
  --dry-run                 Preview without downloading
  --list-mappings           Show subreddit mappings
```

### View Default Mappings

```bash
uv run reddit-dl --list-mappings
```

## PARA Organization

Files are organized using the PARA method:

```
ObsidianVault/
├── 1-Projects/           # Active projects
├── 2-Areas/              # Ongoing responsibilities
│   ├── Finance/
│   ├── Learning/
│   └── Productivity/
├── 3-Resources/          # Reference materials
│   ├── Programming/
│   │   ├── Python/
│   │   ├── Rust/
│   │   └── JavaScript/
│   ├── Technology/
│   └── Reddit/           # Default location
│       ├── AskReddit/
│       └── ...
└── 4-Archives/           # Inactive items
```

## Markdown Output

Each saved item creates a Markdown file with:

### Frontmatter

```yaml
---
source: reddit
subreddit: r/python
author: u/username
created: 2024-01-15
saved: 2024-01-20
url: https://reddit.com/r/python/...
score: 42
type: post
tags:
  - reddit
  - r/python
  - programming
  - python
---
```

### Content

```markdown
# Post Title

> [!info] Reddit Metadata
> - **Subreddit**: [[r/python]]
> - **Author**: u/username
> - **Posted**: 2024-01-15 14:30 UTC
> - **Score**: 42
> - **Link**: [View on Reddit](https://reddit.com/...)

## Content

The actual post content converted to Markdown...
```

## Customizing Subreddit Mappings

Edit `src/reddit_markdown_downloader/config.py` to customize which subreddits map to which PARA categories:

```python
SubredditMapping(
    subreddit="your_subreddit",
    category=PARACategory.AREAS,
    subfolder="Custom/Path",
    tags=["custom", "tags"],
),
```

## Development

```bash
# Install dev dependencies
uv sync

# Run tests
uv run pytest

# Format code
uv run ruff format .

# Lint
uv run ruff check .
```

## License

MIT License
