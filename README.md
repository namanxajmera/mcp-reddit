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

## Usage Modes

### Local (stdio) - Default

For local MCP clients like Claude Desktop and Claude Code:

```bash
uvx mcp-reddit
```

### Remote (HTTP/SSE)

For remote MCP clients that connect via URL:

```bash
uvx mcp-reddit --http --port 8000
```

Options:
- `--http` - Run in HTTP/SSE mode instead of stdio
- `--host` - Host to bind to (default: 0.0.0.0)
- `--port` - Port to listen on (default: 8000, or `PORT` env var)

The server exposes:
- `GET /sse` - SSE endpoint for MCP connection
- `POST /messages/` - Message endpoint
- `GET /health` - Health check

## Configuration

Add to your Claude Desktop or Claude Code settings:

### Claude Desktop (`~/Library/Application Support/Claude/claude_desktop_config.json`)

Claude Desktop doesn't inherit your shell PATH, so you need the full path to `uvx`:

```bash
# Find your uvx path
which uvx
```

Then use the full path in your config:

```json
{
  "mcpServers": {
    "reddit": {
      "command": "/Users/YOUR_USERNAME/.local/bin/uvx",
      "args": ["mcp-reddit"]
    }
  }
}
```

Replace `/Users/YOUR_USERNAME/.local/bin/uvx` with the output from `which uvx`.

### Claude Code

```bash
claude mcp add reddit -- uvx mcp-reddit
```

Or manually in `~/.claude.json`:

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

| Tool                   | Description                                            |
| ---------------------- | ------------------------------------------------------ |
| `scrape_subreddit`     | Scrape posts from a subreddit                          |
| `scrape_user`          | Scrape posts from a user's profile                     |
| `scrape_post`          | Fetch a specific post by URL (supports media download) |
| `get_posts`            | Query stored posts with filters                        |
| `get_comments`         | Query stored comments                                  |
| `search_reddit`        | Search across all scraped data                         |
| `get_top_posts`        | Get highest scoring posts                              |
| `list_scraped_sources` | List all scraped subreddits/users                      |

## Example Usage

```
"Scrape the top 50 posts from r/LocalLLaMA"

"Fetch this post and download the image: https://reddit.com/r/ClaudeAI/comments/abc123/title"

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
      "command": "/Users/YOUR_USERNAME/.local/bin/uvx",
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
