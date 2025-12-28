"""
Reddit MCP Server - Scrape Reddit without API keys
Based on reddit-universal-scraper by @ksanjeev284
https://github.com/ksanjeev284/reddit-universal-scraper
"""
import asyncio
import json
import os
from pathlib import Path
from typing import Any
from datetime import datetime

import pandas as pd
from mcp.server import Server
from mcp.types import Tool, TextContent, ToolAnnotations

from .scraper import run_scraper

# Data directory - defaults to ~/.mcp-reddit/data
DATA_DIR = os.environ.get("MCP_REDDIT_DATA_DIR", os.path.expanduser("~/.mcp-reddit/data"))

# Initialize MCP server
app = Server("mcp-reddit")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available Reddit scraping tools."""
    return [
        Tool(
            name="scrape_subreddit",
            description="Scrape posts from a subreddit. Returns post data including titles, authors, scores, comments, and media URLs.",
            inputSchema={
                "type": "object",
                "properties": {
                    "subreddit": {
                        "type": "string",
                        "description": "Name of the subreddit to scrape (without r/)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of posts to scrape (default: 100)",
                        "default": 100
                    },
                    "download_media": {
                        "type": "boolean",
                        "description": "Whether to download images and videos (default: false)",
                        "default": False
                    },
                    "scrape_comments": {
                        "type": "boolean",
                        "description": "Whether to scrape comments (default: true)",
                        "default": True
                    }
                },
                "required": ["subreddit"]
            },
            annotations=ToolAnnotations(
                title="Scrape Subreddit",
                readOnlyHint=False,
                destructiveHint=False,
            )
        ),
        Tool(
            name="scrape_user",
            description="Scrape posts from a Reddit user's profile. Returns their post history with metadata.",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "Reddit username to scrape (without u/)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of posts to scrape (default: 50)",
                        "default": 50
                    },
                    "download_media": {
                        "type": "boolean",
                        "description": "Whether to download images and videos (default: false)",
                        "default": False
                    },
                    "scrape_comments": {
                        "type": "boolean",
                        "description": "Whether to scrape comments (default: false)",
                        "default": False
                    }
                },
                "required": ["username"]
            },
            annotations=ToolAnnotations(
                title="Scrape User",
                readOnlyHint=False,
                destructiveHint=False,
            )
        ),
        Tool(
            name="get_posts",
            description="Retrieve scraped posts from local database with optional filters. Use this to access previously scraped data.",
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "Subreddit or username to get posts from"
                    },
                    "is_user": {
                        "type": "boolean",
                        "description": "Whether target is a username (default: false)",
                        "default": False
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of posts to return (default: 50)",
                        "default": 50
                    },
                    "min_score": {
                        "type": "integer",
                        "description": "Minimum post score/upvotes filter",
                        "default": 0
                    },
                    "post_type": {
                        "type": "string",
                        "description": "Filter by post type: text, image, video, gallery, link",
                        "enum": ["text", "image", "video", "gallery", "link"]
                    },
                    "search_query": {
                        "type": "string",
                        "description": "Search for posts containing this text in title or body"
                    }
                },
                "required": ["target"]
            },
            annotations=ToolAnnotations(
                title="Get Posts",
                readOnlyHint=True,
                destructiveHint=False,
            )
        ),
        Tool(
            name="get_comments",
            description="Retrieve comments from scraped posts. Returns comment threads with scores and metadata.",
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "Subreddit or username to get comments from"
                    },
                    "is_user": {
                        "type": "boolean",
                        "description": "Whether target is a username (default: false)",
                        "default": False
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of comments to return (default: 100)",
                        "default": 100
                    },
                    "min_score": {
                        "type": "integer",
                        "description": "Minimum comment score filter",
                        "default": 0
                    },
                    "search_query": {
                        "type": "string",
                        "description": "Search for comments containing this text"
                    }
                },
                "required": ["target"]
            },
            annotations=ToolAnnotations(
                title="Get Comments",
                readOnlyHint=True,
                destructiveHint=False,
            )
        ),
        Tool(
            name="search_reddit",
            description="Search across all scraped Reddit data for posts or comments matching a query. Useful for finding specific topics or trends.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query to find in posts and comments"
                    },
                    "search_in": {
                        "type": "string",
                        "description": "What to search: posts, comments, or both (default: both)",
                        "enum": ["posts", "comments", "both"],
                        "default": "both"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 50)",
                        "default": 50
                    }
                },
                "required": ["query"]
            },
            annotations=ToolAnnotations(
                title="Search Reddit",
                readOnlyHint=True,
                destructiveHint=False,
            )
        ),
        Tool(
            name="get_top_posts",
            description="Get top posts by score from a scraped subreddit or user. Great for finding popular content.",
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "Subreddit or username"
                    },
                    "is_user": {
                        "type": "boolean",
                        "description": "Whether target is a username (default: false)",
                        "default": False
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of top posts to return (default: 25)",
                        "default": 25
                    }
                },
                "required": ["target"]
            },
            annotations=ToolAnnotations(
                title="Get Top Posts",
                readOnlyHint=True,
                destructiveHint=False,
            )
        ),
        Tool(
            name="list_scraped_sources",
            description="List all subreddits and users that have been scraped. Shows available data sources.",
            inputSchema={
                "type": "object",
                "properties": {}
            },
            annotations=ToolAnnotations(
                title="List Scraped Sources",
                readOnlyHint=True,
                destructiveHint=False,
            )
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool execution."""
    try:
        if name == "scrape_subreddit":
            result = await scrape_subreddit(
                arguments["subreddit"],
                arguments.get("limit", 100),
                arguments.get("download_media", False),
                arguments.get("scrape_comments", True)
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "scrape_user":
            result = await scrape_user(
                arguments["username"],
                arguments.get("limit", 50),
                arguments.get("download_media", False),
                arguments.get("scrape_comments", False)
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_posts":
            result = await get_posts(
                arguments["target"],
                arguments.get("is_user", False),
                arguments.get("limit", 50),
                arguments.get("min_score", 0),
                arguments.get("post_type"),
                arguments.get("search_query")
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_comments":
            result = await get_comments(
                arguments["target"],
                arguments.get("is_user", False),
                arguments.get("limit", 100),
                arguments.get("min_score", 0),
                arguments.get("search_query")
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "search_reddit":
            result = await search_reddit(
                arguments["query"],
                arguments.get("search_in", "both"),
                arguments.get("limit", 50)
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_top_posts":
            result = await get_top_posts(
                arguments["target"],
                arguments.get("is_user", False),
                arguments.get("limit", 25)
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "list_scraped_sources":
            result = await list_scraped_sources()
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


# Tool implementation functions

async def scrape_subreddit(subreddit: str, limit: int, download_media: bool, scrape_comments: bool) -> dict:
    """Scrape a subreddit."""
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            run_scraper,
            subreddit,
            limit,
            False,  # is_user
            download_media,
            scrape_comments,
            DATA_DIR
        )

        prefix = "r"
        base_dir = f"{DATA_DIR}/{prefix}_{subreddit}"
        posts_file = f"{base_dir}/posts.csv"

        if os.path.exists(posts_file):
            df = pd.read_csv(posts_file)
            recent_posts = df.tail(min(limit, len(df))).to_dict('records')

            return {
                "success": True,
                "subreddit": subreddit,
                "posts_scraped": result.get('posts', 0),
                "comments_scraped": result.get('comments', 0),
                "duration_seconds": result.get('duration', 0),
                "recent_posts": recent_posts[:10],
                "total_posts_in_db": len(df),
                "data_location": base_dir
            }

        return {
            "success": True,
            "message": "Scrape completed but no data file found",
            "result": result
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def scrape_user(username: str, limit: int, download_media: bool, scrape_comments: bool) -> dict:
    """Scrape a user's posts."""
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            run_scraper,
            username,
            limit,
            True,  # is_user
            download_media,
            scrape_comments,
            DATA_DIR
        )

        prefix = "u"
        base_dir = f"{DATA_DIR}/{prefix}_{username}"
        posts_file = f"{base_dir}/posts.csv"

        if os.path.exists(posts_file):
            df = pd.read_csv(posts_file)
            recent_posts = df.tail(min(limit, len(df))).to_dict('records')

            return {
                "success": True,
                "username": username,
                "posts_scraped": result.get('posts', 0),
                "comments_scraped": result.get('comments', 0),
                "duration_seconds": result.get('duration', 0),
                "recent_posts": recent_posts[:10],
                "total_posts_in_db": len(df),
                "data_location": base_dir
            }

        return {
            "success": True,
            "message": "Scrape completed but no data file found",
            "result": result
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def get_posts(target: str, is_user: bool, limit: int, min_score: int, post_type: str | None, search_query: str | None) -> dict:
    """Get posts from local database."""
    try:
        prefix = "u" if is_user else "r"
        posts_file = f"{DATA_DIR}/{prefix}_{target}/posts.csv"

        if not os.path.exists(posts_file):
            return {
                "success": False,
                "error": f"No data found for {prefix}/{target}. Run scrape_subreddit or scrape_user first."
            }

        df = pd.read_csv(posts_file)

        if min_score > 0:
            df = df[df['score'] >= min_score]

        if post_type:
            df = df[df['post_type'] == post_type]

        if search_query:
            mask = df['title'].str.contains(search_query, case=False, na=False) | \
                   df['selftext'].fillna('').str.contains(search_query, case=False, na=False)
            df = df[mask]

        results = df.head(limit).to_dict('records')

        return {
            "success": True,
            "target": f"{prefix}/{target}",
            "total_matching": len(df),
            "returned": len(results),
            "posts": results
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def get_comments(target: str, is_user: bool, limit: int, min_score: int, search_query: str | None) -> dict:
    """Get comments from local database."""
    try:
        prefix = "u" if is_user else "r"
        comments_file = f"{DATA_DIR}/{prefix}_{target}/comments.csv"

        if not os.path.exists(comments_file):
            return {
                "success": False,
                "error": f"No comments found for {prefix}/{target}. Make sure scrape_comments was enabled."
            }

        df = pd.read_csv(comments_file)

        if min_score > 0:
            df = df[df['score'] >= min_score]

        if search_query:
            df = df[df['body'].str.contains(search_query, case=False, na=False)]

        results = df.head(limit).to_dict('records')

        return {
            "success": True,
            "target": f"{prefix}/{target}",
            "total_matching": len(df),
            "returned": len(results),
            "comments": results
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def search_reddit(query: str, search_in: str, limit: int) -> dict:
    """Search across all scraped data."""
    try:
        results: dict[str, list[Any]] = {"posts": [], "comments": []}
        data_dir = Path(DATA_DIR)

        if not data_dir.exists():
            return {
                "success": False,
                "error": "No scraped data found. Run scrape_subreddit or scrape_user first."
            }

        if search_in in ["posts", "both"]:
            for posts_file in data_dir.glob("*/posts.csv"):
                try:
                    df = pd.read_csv(posts_file)
                    mask = df['title'].str.contains(query, case=False, na=False) | \
                           df['selftext'].fillna('').str.contains(query, case=False, na=False)
                    matches = df[mask].to_dict('records')

                    source = posts_file.parent.name
                    for match in matches:
                        match['source'] = source
                        results['posts'].append(match)
                except Exception:
                    continue

        if search_in in ["comments", "both"]:
            for comments_file in data_dir.glob("*/comments.csv"):
                try:
                    df = pd.read_csv(comments_file)
                    mask = df['body'].str.contains(query, case=False, na=False)
                    matches = df[mask].to_dict('records')

                    source = comments_file.parent.name
                    for match in matches:
                        match['source'] = source
                        results['comments'].append(match)
                except Exception:
                    continue

        if results['posts']:
            results['posts'] = sorted(results['posts'], key=lambda x: x.get('score', 0), reverse=True)[:limit]
        if results['comments']:
            results['comments'] = sorted(results['comments'], key=lambda x: x.get('score', 0), reverse=True)[:limit]

        return {
            "success": True,
            "query": query,
            "posts_found": len(results['posts']),
            "comments_found": len(results['comments']),
            "results": results
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def get_top_posts(target: str, is_user: bool, limit: int) -> dict:
    """Get top posts by score."""
    try:
        prefix = "u" if is_user else "r"
        posts_file = f"{DATA_DIR}/{prefix}_{target}/posts.csv"

        if not os.path.exists(posts_file):
            return {
                "success": False,
                "error": f"No data found for {prefix}/{target}"
            }

        df = pd.read_csv(posts_file)
        df = df.sort_values('score', ascending=False)
        results = df.head(limit).to_dict('records')

        return {
            "success": True,
            "target": f"{prefix}/{target}",
            "posts": results
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def list_scraped_sources() -> dict:
    """List all scraped sources."""
    try:
        data_dir = Path(DATA_DIR)

        if not data_dir.exists():
            return {
                "success": True,
                "subreddits": [],
                "users": [],
                "message": "No data scraped yet"
            }

        subreddits = []
        users = []

        for dir in data_dir.iterdir():
            if dir.is_dir() and dir.name.startswith("r_"):
                name = dir.name[2:]
                posts_file = dir / "posts.csv"
                if posts_file.exists():
                    df = pd.read_csv(posts_file)
                    subreddits.append({
                        "name": name,
                        "posts": len(df),
                        "last_updated": datetime.fromtimestamp(posts_file.stat().st_mtime).isoformat()
                    })

            elif dir.is_dir() and dir.name.startswith("u_"):
                name = dir.name[2:]
                posts_file = dir / "posts.csv"
                if posts_file.exists():
                    df = pd.read_csv(posts_file)
                    users.append({
                        "name": name,
                        "posts": len(df),
                        "last_updated": datetime.fromtimestamp(posts_file.stat().st_mtime).isoformat()
                    })

        return {
            "success": True,
            "subreddits": subreddits,
            "users": users,
            "total_sources": len(subreddits) + len(users)
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def run_server():
    """Run the MCP server."""
    import mcp.server.stdio
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


def main():
    """Entry point."""
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
