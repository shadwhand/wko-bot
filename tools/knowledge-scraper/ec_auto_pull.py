#!/usr/bin/env python3
"""Auto-pull new Empirical Cycling podcast episodes from RSS feed.

Checks RSS for new episodes, downloads MP3s, transcribes with mlx-whisper,
saves to docs/research/raw/empirical-cycling/.

Designed to run daily via cron/launchd.

Usage:
    python ec_auto_pull.py           # Check for and process new episodes
    python ec_auto_pull.py --status  # Show what's been transcribed
    python ec_auto_pull.py --all     # Process ALL episodes in the feed
"""

import argparse
import json
import logging
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("/tmp/ec_auto_pull.log"),
    ],
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent
EC_RAW = PROJECT_ROOT / "docs" / "research" / "raw" / "empirical-cycling"
RSS_URL = "http://feeds.soundcloud.com/users/soundcloud:users:609637479/sounds.rss"

# Only process episodes from this date forward
CUTOFF_DATE = datetime(2024, 10, 1)


def slugify(title):
    """Convert episode title to a filesystem-safe slug."""
    slug = title.lower().strip()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s]+', '-', slug)
    slug = re.sub(r'-+', '-', slug).strip('-')
    return slug[:80]


def parse_rss():
    """Fetch and parse the RSS feed. Returns list of episode dicts."""
    resp = requests.get(RSS_URL, timeout=30)
    resp.raise_for_status()

    root = ET.fromstring(resp.content)
    episodes = []

    for item in root.iter("item"):
        title = item.findtext("title", "").strip()
        pub_date_str = item.findtext("pubDate", "")

        # Parse date
        try:
            pub_date = datetime.strptime(pub_date_str.strip(), "%a, %d %b %Y %H:%M:%S %z")
            pub_date_naive = pub_date.replace(tzinfo=None)
        except (ValueError, AttributeError):
            pub_date_naive = None

        # Get MP3 URL from enclosure
        enclosure = item.find("enclosure")
        mp3_url = enclosure.get("url", "") if enclosure is not None else ""

        if not title or not mp3_url:
            continue

        episodes.append({
            "title": title,
            "date": pub_date_naive,
            "date_str": pub_date_naive.strftime("%Y-%m-%d") if pub_date_naive else "unknown",
            "mp3_url": mp3_url,
            "slug": slugify(title),
        })

    return episodes


def load_state():
    """Load the state file."""
    EC_RAW.mkdir(parents=True, exist_ok=True)
    state_file = EC_RAW / "_state.json"
    if state_file.exists():
        with open(state_file) as f:
            return json.load(f)
    return {}


def save_state(state):
    """Save state file atomically."""
    state_file = EC_RAW / "_state.json"
    tmp = state_file.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2)
    tmp.rename(state_file)


def download_mp3(mp3_url, slug):
    """Download MP3 file. Returns path or None."""
    audio_path = f"/tmp/ec_rss_{slug[:60]}.mp3"

    # Clean up any leftover
    if os.path.exists(audio_path):
        os.unlink(audio_path)

    try:
        subprocess.run(["curl", "-sL", "-o", audio_path, mp3_url], timeout=300)
        if os.path.exists(audio_path) and os.path.getsize(audio_path) > 100000:
            return audio_path
    except subprocess.TimeoutExpired:
        pass

    return None


def transcribe(audio_path):
    """Transcribe audio file with mlx-whisper. Returns transcript text or None."""
    try:
        import mlx_whisper
        result = mlx_whisper.transcribe(audio_path)
        transcript = result.get("text", "").strip()
        return transcript if len(transcript) > 100 else None
    except Exception as e:
        logger.warning(f"Transcription failed: {e}")
        return None


def process_new_episodes(process_all=False):
    """Check RSS for new episodes and process them."""
    logger.info("Checking RSS feed for new episodes...")
    episodes = parse_rss()
    state = load_state()

    # Build set of known slugs and titles
    known_slugs = {v.get("slug") for v in state.values() if isinstance(v, dict)}
    known_titles = {v.get("title") for v in state.values() if isinstance(v, dict)}

    # Filter to new episodes
    new_episodes = []
    for ep in episodes:
        if ep["slug"] in known_slugs or ep["title"] in known_titles:
            continue
        if not process_all and ep["date"] and ep["date"] < CUTOFF_DATE:
            continue
        new_episodes.append(ep)

    if not new_episodes:
        logger.info("No new episodes found.")
        return 0

    logger.info(f"Found {len(new_episodes)} new episodes to process")

    transcribed = 0
    for i, ep in enumerate(new_episodes):
        title = ep["title"]
        slug = ep["slug"]
        logger.info(f"[{i+1}/{len(new_episodes)}] {title} ({ep['date_str']})")

        # Download
        audio_path = download_mp3(ep["mp3_url"], slug)
        if not audio_path:
            logger.warning(f"  Download failed: {title}")
            state[ep["mp3_url"]] = {
                "status": "download_failed",
                "slug": slug,
                "title": title,
                "date": ep["date_str"],
            }
            save_state(state)
            continue

        size_mb = os.path.getsize(audio_path) / 1e6
        logger.info(f"  Downloaded: {size_mb:.0f}MB")

        # Transcribe
        logger.info(f"  Transcribing with mlx-whisper...")
        transcript = transcribe(audio_path)

        # Clean up audio
        try:
            os.unlink(audio_path)
        except OSError:
            pass

        if not transcript:
            logger.warning(f"  Transcription failed: {title}")
            state[ep["mp3_url"]] = {
                "status": "transcription_failed",
                "slug": slug,
                "title": title,
                "date": ep["date_str"],
            }
            save_state(state)
            continue

        # Save transcript
        out_path = EC_RAW / f"{slug}.txt"
        with open(out_path, "w") as f:
            f.write(f"# {title}\n\n{transcript}")

        state[ep["mp3_url"]] = {
            "status": "transcribed",
            "slug": slug,
            "title": title,
            "date": ep["date_str"],
            "length": len(transcript),
            "file": out_path.name,
        }
        transcribed += 1
        logger.info(f"  Saved: {slug}.txt ({len(transcript):,} chars)")
        save_state(state)

    total = sum(1 for v in state.values() if isinstance(v, dict) and v.get("status") == "transcribed")
    logger.info(f"Done: {transcribed} new, {total} total transcribed")
    return transcribed


def show_status():
    """Show transcription status."""
    state = load_state()
    transcribed = [v for v in state.values() if isinstance(v, dict) and v.get("status") == "transcribed"]
    failed = [v for v in state.values() if isinstance(v, dict) and "fail" in v.get("status", "")]

    print(f"Empirical Cycling Podcast Transcriptions")
    print(f"  Transcribed: {len(transcribed)}")
    print(f"  Failed: {len(failed)}")

    if transcribed:
        total_chars = sum(v.get("length", 0) for v in transcribed)
        print(f"  Total transcript size: {total_chars:,} chars ({total_chars/1e6:.1f}MB)")

    if failed:
        print(f"\n  Failed episodes:")
        for v in failed:
            print(f"    - {v.get('title', '?')} ({v.get('status', '?')})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Auto-pull Empirical Cycling podcast episodes")
    parser.add_argument("--status", action="store_true", help="Show status")
    parser.add_argument("--all", action="store_true", help="Process ALL episodes, not just recent")
    args = parser.parse_args()

    if args.status:
        show_status()
    else:
        process_new_episodes(process_all=args.all)
