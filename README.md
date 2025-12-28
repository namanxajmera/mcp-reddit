# mcp-reddit

MCP server for scraping Reddit - **no API keys required**.

Scrapes posts, comments, and media from subreddits and user profiles using old.reddit.com and Libreddit mirrors.

## Features

- **No API keys** - Scrapes directly, no Reddit API credentials needed
- **Media downloads** - Images, videos with audio (requires ffmpeg)
- **Local persistence** - Query scraped data offline
- **Rich filtering** - By post type, score, keywords
- **Comments included** - Full thread scraping

## Installation

```bash
pip install mcp-reddit
```

Or with uvx:

```bash
uvx mcp-reddit
```

## Configuration

Add to your Claude Desktop or Claude Code settings:

### Claude Desktop (`~/Library/Application Support/Claude/claude_desktop_config.json`)

```json
{
  "mcpServers": {
    "reddit": {
      "command": "uvx",
      "args": ["mcp-reddit"]
    }
  }
}
```

### Claude Code (`~/.claude/settings.json`)

```json
{
  "mcpServers": {
    "reddit": {
      "command": "uvx",
      "args": ["mcp-reddit"]
    }
  }
}
```

## Available Tools

| Tool                   | Description                        |
| ---------------------- | ---------------------------------- |
| `scrape_subreddit`     | Scrape posts from a subreddit      |
| `scrape_user`          | Scrape posts from a user's profile |
| `get_posts`            | Query stored posts with filters    |
| `get_comments`         | Query stored comments              |
| `search_reddit`        | Search across all scraped data     |
| `get_top_posts`        | Get highest scoring posts          |
| `list_scraped_sources` | List all scraped subreddits/users  |

## Example Usage

```
"Scrape the top 50 posts from r/LocalLLaMA"

"Search my scraped data for posts about 'fine-tuning'"

"Get the top 10 posts from r/ClaudeAI by score"
```

## Data Storage

Data is stored in `~/.mcp-reddit/data/` by default.

Set `MCP_REDDIT_DATA_DIR` environment variable to customize:

```json
{
  "mcpServers": {
    "reddit": {
      "command": "uvx",
      "args": ["mcp-reddit"],
      "env": {
        "MCP_REDDIT_DATA_DIR": "/path/to/your/data"
      }
    }
  }
}
```

## Optional: Video with Audio

To download Reddit videos with audio, install ffmpeg:

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg

# Windows
choco install ffmpeg
```

## Credits

Built on top of [reddit-universal-scraper](https://github.com/ksanjeev284/reddit-universal-scraper)
by [@ksanjeev284](https://github.com/ksanjeev284) - a full-featured Reddit scraper with
analytics dashboard, REST API, and plugin system.

## License

MIT
