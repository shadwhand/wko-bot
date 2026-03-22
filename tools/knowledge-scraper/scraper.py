#!/usr/bin/env python3
"""Knowledge scraper — TrainingPeaks blog + Empirical Cycling podcast.

Phase 1 (this script): Crawl and save raw content.
Phase 2 (Claude Code): Triage and extract key points interactively.

Usage:
    python scraper.py blog              # Crawl TP blog, save raw articles
    python scraper.py podcast           # Download + transcribe EC podcast
    python scraper.py both              # Both
    python scraper.py blog --limit 10   # Limit to 10
    python scraper.py status            # Show what's been scraped
"""

import argparse
import json
import logging
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent
RAW_DIR = PROJECT_ROOT / "docs" / "research" / "raw"
TP_RAW = RAW_DIR / "trainingpeaks"
EC_RAW = RAW_DIR / "empirical-cycling"

# Keywords for filtering cycling-relevant content
CYCLING_KEYWORDS = [
    "cycling", "bike", "ftp", "power", "watts", "cadence", "threshold",
    "intervals", "endurance", "recovery", "training-load", "tss", "ctl",
    "pacing", "climbing", "sprinting", "time-trial", "century",
    "nutrition", "fueling", "hydration", "carb", "bonk", "calorie",
    "performance", "strength", "periodization", "base-training",
    "overtraining", "fatigue", "heart-rate", "vo2", "lactate",
    "zone", "polarized", "sweet-spot", "tempo", "critical-power",
    "durability", "stamina", "aerobic", "anaerobic", "watt",
]


# ============================================================
# TrainingPeaks Blog
# ============================================================

def get_tp_blog_urls():
    """Get cycling-relevant blog URLs from TrainingPeaks sitemaps."""
    all_urls = []
    for sitemap in [
        "https://www.trainingpeaks.com/post-sitemap.xml",
        "https://www.trainingpeaks.com/post-sitemap2.xml",
        "https://www.trainingpeaks.com/post-sitemap3.xml",
    ]:
        try:
            resp = requests.get(sitemap, timeout=30)
            if resp.status_code == 200:
                urls = re.findall(r'<loc>(.*?)</loc>', resp.text)
                all_urls.extend([u for u in urls if '/blog/' in u])
        except Exception as e:
            logger.warning(f"Sitemap fetch failed: {e}")

    relevant = [u for u in all_urls if any(kw in u.lower() for kw in CYCLING_KEYWORDS)]
    logger.info(f"Found {len(all_urls)} blog posts, {len(relevant)} cycling-relevant")
    return relevant


def scrape_tp_article(url):
    """Scrape a single TrainingPeaks article. Returns dict with metadata + content."""
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code != 200:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")

        title = ""
        title_tag = soup.find("h1")
        if title_tag:
            title = title_tag.get_text(strip=True)

        author = ""
        for sel in [
            soup.find("a", class_=re.compile("author", re.I)),
            soup.find("meta", {"name": "author"}),
            soup.find("span", class_=re.compile("author", re.I)),
        ]:
            if sel:
                author = sel.get("content", "") or sel.get_text(strip=True)
                if author:
                    break

        # TP uses utility classes — find the main content div
        # Strategy: find the div with the most text that starts with the article title
        content = ""
        best_div = None
        best_len = 0

        for div in soup.find_all("div"):
            text = div.get_text(strip=True)
            # Skip nav/header/footer divs
            cls = " ".join(div.get("class", []))
            if any(skip in cls.lower() for skip in ["nav", "header", "footer", "menu", "sidebar"]):
                continue
            # The main content div is usually 2000-15000 chars
            if 2000 < len(text) < 15000 and len(text) > best_len:
                best_div = div
                best_len = len(text)

        if best_div:
            for tag in best_div.find_all(["script", "style"]):
                tag.decompose()
            content = best_div.get_text(separator="\n", strip=True)

        # Fallback: use <main> tag
        if not content:
            main = soup.find("main")
            if main:
                for tag in main.find_all(["script", "style", "nav"]):
                    tag.decompose()
                content = main.get_text(separator="\n", strip=True)

        return {
            "url": url,
            "title": title or url.split("/blog/")[-1],
            "author": author,
            "content": content[:20000],
            "slug": url.split("/blog/")[-1].rstrip("/"),
        }
    except Exception as e:
        logger.warning(f"Scrape failed {url}: {e}")
        return None


def scrape_tp_blog(limit=None):
    """Crawl TrainingPeaks blog and save raw articles."""
    TP_RAW.mkdir(parents=True, exist_ok=True)
    state_file = TP_RAW / "_state.json"

    state = {}
    if state_file.exists():
        with open(state_file) as f:
            state = json.load(f)

    urls = get_tp_blog_urls()
    unprocessed = [u for u in urls if u not in state]
    logger.info(f"{len(unprocessed)} new articles to scrape")

    if limit:
        unprocessed = unprocessed[:limit]

    scraped = 0
    for i, url in enumerate(unprocessed):
        slug = url.split("/blog/")[-1].rstrip("/")[:60]
        logger.info(f"[{i+1}/{len(unprocessed)}] {slug}")

        article = scrape_tp_article(url)
        if not article or len(article["content"]) < 200:
            state[url] = {"status": "empty", "title": slug}
            continue

        # Save raw article
        filepath = TP_RAW / f"{article['slug'][:60]}.json"
        with open(filepath, "w") as f:
            json.dump(article, f, indent=2)

        state[url] = {
            "status": "scraped",
            "title": article["title"],
            "author": article["author"],
            "length": len(article["content"]),
            "file": str(filepath.name),
        }
        scraped += 1

        if (i + 1) % 25 == 0:
            with open(state_file, "w") as f:
                json.dump(state, f, indent=2)
            logger.info(f"  Checkpoint: {scraped} scraped")

        time.sleep(0.5)  # be polite

    with open(state_file, "w") as f:
        json.dump(state, f, indent=2)

    logger.info(f"Done: {scraped} articles scraped")


# ============================================================
# Empirical Cycling Podcast
# ============================================================

EC_SOUNDCLOUD = "https://soundcloud.com/empiricalcyclingpodcast"


def _slugify(title):
    """Convert episode title to a filesystem-safe slug."""
    slug = title.lower().strip()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s]+', '-', slug)
    slug = re.sub(r'-+', '-', slug).strip('-')
    return slug[:80]


def get_ec_episodes(limit=None):
    """Get episode URLs + titles from Soundcloud profile via yt-dlp.

    Returns list of dicts: [{url, title, slug}, ...] in reverse chronological order.
    """
    try:
        cmd = [
            "yt-dlp", "--flat-playlist", "--no-warnings",
            "--print", "%(url)s\t%(title)s",
            EC_SOUNDCLOUD,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            logger.warning(f"yt-dlp playlist fetch failed: {result.stderr[:200]}")
            return []

        episodes = []
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split("\t", 1)
            if len(parts) != 2:
                continue
            url, title = parts
            episodes.append({
                "url": url.strip(),
                "title": title.strip(),
                "slug": _slugify(title),
            })

        if limit:
            episodes = episodes[:limit]

        logger.info(f"Found {len(episodes)} podcast episodes from Soundcloud")
        return episodes
    except subprocess.TimeoutExpired:
        logger.warning("yt-dlp playlist fetch timed out")
        return []
    except Exception as e:
        logger.warning(f"Failed to get EC episodes: {e}")
        return []


def _download_episode(url, slug):
    """Download audio from Soundcloud URL. Returns path to audio file or None."""
    import glob
    audio_path = f"/tmp/ec_{slug}"

    # Clean up any leftover files from previous attempts
    for old in glob.glob(f"/tmp/ec_{slug}.*"):
        try:
            os.unlink(old)
        except OSError:
            pass

    try:
        result = subprocess.run(
            ["yt-dlp", "--extract-audio", "--no-warnings",
             "--output", audio_path + ".%(ext)s", url],
            capture_output=True, text=True, timeout=300,
        )
    except subprocess.TimeoutExpired:
        return None

    files = glob.glob(f"/tmp/ec_{slug}.*")
    audio_files = [f for f in files if not f.endswith(('.part', '.ytdl'))]
    if not audio_files:
        return None

    return audio_files[0]


def _transcribe_episode(audio_file):
    """Transcribe audio file with Whisper. Returns transcript text or None."""
    whisper_out = "/tmp/whisper_ec"
    os.makedirs(whisper_out, exist_ok=True)

    # CPU-only: MPS has torch.AcceleratorError bugs with Whisper beam search
    # base model on CPU runs ~5x real-time (~14min for 1hr episode)
    try:
        logger.info(f"  Transcribing with Whisper (cpu, base model)...")
        result = subprocess.run(
            ["whisper", audio_file, "--model", "base", "--device", "cpu",
             "--output_format", "txt", "--output_dir", whisper_out, "--language", "en"],
            capture_output=True, text=True, timeout=3600,
        )
        if result.returncode != 0:
            logger.warning(f"  Whisper failed (rc={result.returncode}): {result.stderr[:200]}")
            return None
    except subprocess.TimeoutExpired:
        logger.warning(f"  Whisper timed out after 3600s")
        return None

    basename = Path(audio_file).stem
    txt_path = Path(whisper_out) / f"{basename}.txt"
    if not txt_path.exists():
        return None

    transcript = txt_path.read_text().strip()
    txt_path.unlink(missing_ok=True)
    return transcript if len(transcript) > 100 else None


def scrape_ec_podcast(limit=None):
    """Download and transcribe Empirical Cycling podcast episodes.

    Uses yt-dlp to enumerate episodes directly from the Soundcloud profile.
    Episodes are processed in reverse chronological order (newest first).
    """
    EC_RAW.mkdir(parents=True, exist_ok=True)
    state_file = EC_RAW / "_state.json"

    state = {}
    if state_file.exists():
        with open(state_file) as f:
            state = json.load(f)

    episodes = get_ec_episodes(limit=limit)

    # Filter to unprocessed (check both URL and slug to avoid re-processing)
    processed_slugs = {v.get("slug") for v in state.values() if isinstance(v, dict)}
    unprocessed = [
        e for e in episodes
        if e["url"] not in state and e["slug"] not in processed_slugs
    ]
    logger.info(f"{len(unprocessed)} new episodes to process")

    transcribed = 0
    failed = 0

    for i, ep in enumerate(unprocessed):
        url = ep["url"]
        slug = ep["slug"]
        title = ep["title"]
        logger.info(f"[{i+1}/{len(unprocessed)}] {title}")

        # Download
        audio_file = _download_episode(url, slug)
        if not audio_file:
            state[url] = {"status": "download_failed", "slug": slug, "title": title}
            failed += 1
            logger.warning(f"  Download failed: {title}")
            _save_state(state_file, state)
            continue

        size_mb = os.path.getsize(audio_file) / 1e6
        logger.info(f"  Downloaded: {os.path.basename(audio_file)} ({size_mb:.0f}MB)")

        # Transcribe
        transcript = _transcribe_episode(audio_file)

        # Clean up audio file
        try:
            os.unlink(audio_file)
        except OSError:
            pass

        if not transcript:
            state[url] = {"status": "transcription_failed", "slug": slug, "title": title}
            failed += 1
            logger.warning(f"  Transcription failed: {title}")
            _save_state(state_file, state)
            continue

        # Save transcript with title as header
        out_path = EC_RAW / f"{slug}.txt"
        with open(out_path, "w") as f:
            f.write(f"# {title}\n\n{transcript}")

        state[url] = {
            "status": "transcribed",
            "slug": slug,
            "title": title,
            "length": len(transcript),
            "file": str(out_path.name),
        }
        transcribed += 1

        logger.info(f"  Saved: {slug}.txt ({len(transcript):,} chars)")
        _save_state(state_file, state)

    _save_state(state_file, state)
    total_transcribed = sum(1 for v in state.values() if isinstance(v, dict) and v.get("status") == "transcribed")
    logger.info(f"Done: {transcribed} new transcriptions ({total_transcribed} total), {failed} failed")


def _save_state(state_file, state):
    """Save state file atomically."""
    tmp = state_file.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2)
    tmp.rename(state_file)


# ============================================================
# Status
# ============================================================

def show_status():
    """Show what's been scraped."""
    print("=" * 60)
    print("Knowledge Scraper Status")
    print("=" * 60)

    # TP Blog
    tp_state = TP_RAW / "_state.json"
    if tp_state.exists():
        with open(tp_state) as f:
            state = json.load(f)
        scraped = sum(1 for v in state.values() if isinstance(v, dict) and v.get("status") == "scraped")
        empty = sum(1 for v in state.values() if isinstance(v, dict) and v.get("status") == "empty")
        print(f"\nTrainingPeaks Blog:")
        print(f"  Scraped: {scraped}")
        print(f"  Empty/failed: {empty}")
        print(f"  Raw files: {len(list(TP_RAW.glob('*.json'))) - 1}")  # minus state file
    else:
        print(f"\nTrainingPeaks Blog: not started")

    # EC Podcast
    ec_state = EC_RAW / "_state.json"
    if ec_state.exists():
        with open(ec_state) as f:
            state = json.load(f)
        transcribed = sum(1 for v in state.values() if isinstance(v, dict) and v.get("status") == "transcribed")
        failed = sum(1 for v in state.values() if isinstance(v, dict) and v.get("status") in ("download_failed", "transcription_failed", "download_timeout", "transcription_timeout"))
        print(f"\nEmpirical Cycling Podcast:")
        print(f"  Transcribed: {transcribed}")
        print(f"  Failed: {failed}")
        print(f"  Transcript files: {len(list(EC_RAW.glob('*.txt')))}")
    else:
        print(f"\nEmpirical Cycling Podcast: not started")

    # Curated knowledge cards
    tp_curated = PROJECT_ROOT / "docs" / "research" / "trainingpeaks"
    ec_curated = PROJECT_ROOT / "docs" / "research" / "empirical-cycling"
    tp_cards = len(list(tp_curated.glob("*.md"))) if tp_curated.exists() else 0
    ec_cards = len(list(ec_curated.glob("*.md"))) if ec_curated.exists() else 0
    print(f"\nCurated Knowledge Cards:")
    print(f"  TrainingPeaks: {tp_cards}")
    print(f"  Empirical Cycling: {ec_cards}")


# ============================================================
# Main
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Knowledge scraper for cycling training content")
    parser.add_argument("source", choices=["blog", "podcast", "both", "status"],
                       help="What to scrape, or 'status' to show progress")
    parser.add_argument("--limit", type=int, help="Limit number of items")
    args = parser.parse_args()

    if args.source == "status":
        show_status()
        return

    if args.source in ("blog", "both"):
        scrape_tp_blog(limit=args.limit)

    if args.source in ("podcast", "both"):
        scrape_ec_podcast(limit=args.limit)


if __name__ == "__main__":
    main()
