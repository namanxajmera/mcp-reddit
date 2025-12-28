"""
Async Reddit Scraper - No API keys required
Based on reddit-universal-scraper by @ksanjeev284
https://github.com/ksanjeev284/reddit-universal-scraper
"""
import asyncio
import aiohttp
import aiofiles
import pandas as pd
import datetime
import time
import os
import random
from urllib.parse import urlparse
import tempfile

# Configuration
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
MIRRORS = [
    "https://old.reddit.com",
    "https://redlib.catsarch.com",
    "https://redlib.vsls.cz",
    "https://r.nf",
    "https://libreddit.northboot.xyz",
    "https://redlib.tux.pizza"
]
MAX_CONCURRENT = 10
BATCH_SIZE = 100

# Semaphore for rate limiting
semaphore = None


async def fetch_json(session, url, retries=3):
    """Fetch JSON with retry logic."""
    for attempt in range(retries):
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:
                    await asyncio.sleep(5 * (attempt + 1))
        except Exception:
            if attempt < retries - 1:
                await asyncio.sleep(2)
    return None


async def fetch_posts_page(session, base_url, target, after=None, is_user=False, batch_size=100):
    """Fetch a single page of posts."""
    if is_user:
        path = f"/user/{target}/submitted.json"
    else:
        path = f"/r/{target}/new.json"

    url = f"{base_url}{path}?limit={batch_size}&raw_json=1"
    if after:
        url += f"&after={after}"

    return await fetch_json(session, url)


async def download_media_async(session, url, save_path):
    """Download media file asynchronously."""
    global semaphore

    if os.path.exists(save_path):
        return True

    async with semaphore:
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as response:
                if response.status == 200:
                    async with aiofiles.open(save_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)
                    return True
        except Exception:
            pass
    return False


async def download_reddit_video_with_audio_async(session, video_url, save_path):
    """Download Reddit video with audio (requires ffmpeg)."""
    global semaphore

    if os.path.exists(save_path):
        return True

    async with semaphore:
        try:
            base_url = video_url.rsplit('/', 1)[0]
            audio_urls = [
                f"{base_url}/DASH_audio.mp4",
                f"{base_url}/DASH_AUDIO_128.mp4",
                f"{base_url}/DASH_AUDIO_64.mp4",
                f"{base_url}/audio.mp4",
                f"{base_url}/audio"
            ]

            video_temp = tempfile.NamedTemporaryFile(suffix='_video.mp4', delete=False)
            video_temp_path = video_temp.name
            video_temp.close()

            try:
                async with session.get(video_url, timeout=aiohttp.ClientTimeout(total=60)) as response:
                    if response.status != 200:
                        return False
                    async with aiofiles.open(video_temp_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)
            except Exception:
                if os.path.exists(video_temp_path):
                    os.unlink(video_temp_path)
                return False

            audio_temp_path = None
            for audio_url in audio_urls:
                try:
                    async with session.get(audio_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                        if response.status == 200:
                            audio_temp = tempfile.NamedTemporaryFile(suffix='_audio.mp4', delete=False)
                            audio_temp_path = audio_temp.name
                            audio_temp.close()
                            async with aiofiles.open(audio_temp_path, 'wb') as f:
                                async for chunk in response.content.iter_chunked(8192):
                                    await f.write(chunk)
                            break
                except Exception:
                    continue

            if audio_temp_path:
                try:
                    cmd = [
                        'ffmpeg', '-y', '-hide_banner', '-loglevel', 'error',
                        '-i', video_temp_path,
                        '-i', audio_temp_path,
                        '-c:v', 'copy', '-c:a', 'aac',
                        '-shortest', save_path
                    ]
                    proc = await asyncio.create_subprocess_exec(
                        *cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    await asyncio.wait_for(proc.wait(), timeout=120)

                    if proc.returncode == 0:
                        os.unlink(video_temp_path)
                        os.unlink(audio_temp_path)
                        return True
                    else:
                        os.rename(video_temp_path, save_path)
                        os.unlink(audio_temp_path)
                        return True
                except FileNotFoundError:
                    os.rename(video_temp_path, save_path)
                    if audio_temp_path and os.path.exists(audio_temp_path):
                        os.unlink(audio_temp_path)
                    return True
                except Exception:
                    os.rename(video_temp_path, save_path)
                    if audio_temp_path and os.path.exists(audio_temp_path):
                        os.unlink(audio_temp_path)
                    return True
            else:
                os.rename(video_temp_path, save_path)
                return True

        except Exception:
            pass
    return False


async def fetch_comments_async(session, permalink):
    """Fetch comments asynchronously."""
    global semaphore

    async with semaphore:
        url = f"https://old.reddit.com{permalink}.json?limit=100"
        data = await fetch_json(session, url)

        if data and len(data) > 1:
            return parse_comments(data[1]['data']['children'], permalink)
    return []


def parse_comments(comment_list, post_permalink, depth=0, max_depth=3):
    """Parse comments recursively."""
    comments = []

    if depth > max_depth:
        return comments

    for item in comment_list:
        if item['kind'] != 't1':
            continue

        c = item['data']
        comments.append({
            "post_permalink": post_permalink,
            "comment_id": c.get('id'),
            "parent_id": c.get('parent_id'),
            "author": c.get('author'),
            "body": c.get('body', ''),
            "score": c.get('score', 0),
            "created_utc": datetime.datetime.fromtimestamp(c.get('created_utc', 0)).isoformat(),
            "depth": depth,
            "is_submitter": c.get('is_submitter', False),
        })

        replies = c.get('replies')
        if replies and isinstance(replies, dict):
            comments.extend(parse_comments(
                replies.get('data', {}).get('children', []),
                post_permalink, depth + 1, max_depth
            ))

    return comments


def extract_media_urls(post_data):
    """Extract all media URLs from a post."""
    media = {"images": [], "videos": [], "galleries": []}

    url = post_data.get('url', '')

    if any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
        media["images"].append(url)

    if 'i.redd.it' in url:
        media["images"].append(url)

    if post_data.get('is_video'):
        reddit_video = post_data.get('media', {})
        if reddit_video and 'reddit_video' in reddit_video:
            video_url = reddit_video['reddit_video'].get('fallback_url', '')
            if video_url:
                media["videos"].append(video_url.split('?')[0])

    preview = post_data.get('preview', {})
    if preview and 'images' in preview:
        for img in preview['images']:
            source = img.get('source', {})
            if source.get('url'):
                media["images"].append(source['url'].replace('&amp;', '&'))

    if post_data.get('is_gallery'):
        gallery_data = post_data.get('gallery_data', {})
        media_metadata = post_data.get('media_metadata', {})

        if gallery_data and media_metadata:
            for item in gallery_data.get('items', []):
                media_id = item.get('media_id')
                if media_id and media_id in media_metadata:
                    meta = media_metadata[media_id]
                    if meta.get('s', {}).get('u'):
                        media["galleries"].append(meta['s']['u'].replace('&amp;', '&'))

    return media


def extract_post_data(p):
    """Extract post data from JSON."""
    post_type = "text"
    if p.get('is_video'):
        post_type = "video"
    elif p.get('is_gallery'):
        post_type = "gallery"
    elif any(ext in p.get('url', '').lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']) or 'i.redd.it' in p.get('url', ''):
        post_type = "image"
    elif p.get('is_self'):
        post_type = "text"
    else:
        post_type = "link"

    return {
        "id": p.get('id'),
        "title": p.get('title'),
        "author": p.get('author'),
        "created_utc": datetime.datetime.fromtimestamp(p.get('created_utc', 0)).isoformat(),
        "permalink": p.get('permalink'),
        "url": p.get('url_overridden_by_dest', p.get('url')),
        "score": p.get('score', 0),
        "upvote_ratio": p.get('upvote_ratio', 0),
        "num_comments": p.get('num_comments', 0),
        "num_crossposts": p.get('num_crossposts', 0),
        "selftext": p.get('selftext', ''),
        "post_type": post_type,
        "is_nsfw": p.get('over_18', False),
        "is_spoiler": p.get('spoiler', False),
        "flair": p.get('link_flair_text', ''),
        "total_awards": p.get('total_awards_received', 0),
        "has_media": p.get('is_video', False) or p.get('is_gallery', False) or 'i.redd.it' in p.get('url', ''),
        "media_downloaded": False,
        "source": "mcp-reddit"
    }


async def scrape_async(target, limit=100, is_user=False, download_media=True, scrape_comments=True, data_dir="data"):
    """
    Main async scraping function.

    Args:
        target: Subreddit or username
        limit: Max posts to scrape
        is_user: True if scraping a user
        download_media: Download images/videos
        scrape_comments: Scrape comments
        data_dir: Directory to store data
    """
    global semaphore
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    prefix = "u" if is_user else "r"

    # Setup directories
    base_dir = f"{data_dir}/{prefix}_{target}"
    media_dir = f"{base_dir}/media"
    images_dir = f"{media_dir}/images"
    videos_dir = f"{media_dir}/videos"

    for d in [base_dir, media_dir, images_dir, videos_dir]:
        os.makedirs(d, exist_ok=True)

    start_time = time.time()
    all_posts = []
    all_comments = []
    media_tasks = []
    seen_permalinks = set()

    # Load existing data
    posts_file = f"{base_dir}/posts.csv"
    if os.path.exists(posts_file):
        try:
            df = pd.read_csv(posts_file)
            seen_permalinks = set(df['permalink'].astype(str).tolist())
        except Exception:
            pass

    async with aiohttp.ClientSession(headers={"User-Agent": USER_AGENT}) as session:
        after = None
        total_fetched = 0

        while total_fetched < limit:
            mirrors = MIRRORS.copy()
            random.shuffle(mirrors)

            data = None
            for mirror in mirrors:
                batch_size = min(100, limit - total_fetched)
                data = await fetch_posts_page(session, mirror, target, after, is_user, batch_size)
                if data:
                    break

            if not data:
                break

            children = data.get('data', {}).get('children', [])
            if not children:
                break

            batch_posts = []
            comment_tasks = []

            for child in children:
                p = child['data']
                post = extract_post_data(p)

                if post['permalink'] in seen_permalinks:
                    continue

                seen_permalinks.add(post['permalink'])
                batch_posts.append(post)

                if download_media:
                    media = extract_media_urls(p)

                    for i, img_url in enumerate(media['images'][:5]):
                        ext = os.path.splitext(urlparse(img_url).path)[1] or '.jpg'
                        save_path = f"{images_dir}/{post['id']}_{i}{ext}"
                        media_tasks.append(download_media_async(session, img_url, save_path))

                    for i, img_url in enumerate(media['galleries'][:10]):
                        save_path = f"{images_dir}/{post['id']}_gallery_{i}.jpg"
                        media_tasks.append(download_media_async(session, img_url, save_path))

                    for i, vid_url in enumerate(media['videos'][:2]):
                        if 'youtube' not in vid_url:
                            save_path = f"{videos_dir}/{post['id']}_{i}.mp4"
                            if 'v.redd.it' in vid_url or 'reddit.com' in vid_url:
                                media_tasks.append(download_reddit_video_with_audio_async(session, vid_url, save_path))
                            else:
                                media_tasks.append(download_media_async(session, vid_url, save_path))

                if scrape_comments and post['num_comments'] > 0:
                    comment_tasks.append(fetch_comments_async(session, post['permalink']))

            all_posts.extend(batch_posts)
            total_fetched += len(batch_posts)

            if comment_tasks:
                comment_results = await asyncio.gather(*comment_tasks, return_exceptions=True)
                for result in comment_results:
                    if isinstance(result, list):
                        all_comments.extend(result)

            after = data.get('data', {}).get('after')
            if not after:
                break

            await asyncio.sleep(1)

        if media_tasks:
            await asyncio.gather(*media_tasks, return_exceptions=True)

    # Save data
    if all_posts:
        df = pd.DataFrame(all_posts)
        if os.path.exists(posts_file):
            df.to_csv(posts_file, mode='a', header=False, index=False)
        else:
            df.to_csv(posts_file, index=False)

    if all_comments:
        comments_file = f"{base_dir}/comments.csv"
        df = pd.DataFrame(all_comments)
        if os.path.exists(comments_file):
            df.to_csv(comments_file, mode='a', header=False, index=False)
        else:
            df.to_csv(comments_file, index=False)

    duration = time.time() - start_time

    return {
        'posts': len(all_posts),
        'comments': len(all_comments),
        'duration': duration
    }


def run_scraper(target, limit=100, is_user=False, download_media=True, scrape_comments=True, data_dir="data"):
    """Sync wrapper to run async scraper."""
    return asyncio.run(scrape_async(target, limit, is_user, download_media, scrape_comments, data_dir))
