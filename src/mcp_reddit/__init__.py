"""
MCP Reddit - Scrape Reddit without API keys
Based on reddit-universal-scraper by @ksanjeev284
https://github.com/ksanjeev284/reddit-universal-scraper
"""
from .server import main
from .scraper import run_scraper, scrape_async

__version__ = "0.1.0"
__all__ = ["main", "run_scraper", "scrape_async"]
