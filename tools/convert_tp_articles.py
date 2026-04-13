#!/usr/bin/env python3
"""Convert TrainingPeaks article JSON files to Markdown with YAML frontmatter.

Reads from:  docs/research/raw/trainingpeaks/*.json
Writes to:   docs/research/trainingpeaks/*.md

Skips files that already have a corresponding .md in the output directory.
Strips HTML boilerplate (nav, breadcrumbs, related articles, trailing bios).
"""

import json
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

RAW_DIR = os.path.join(PROJECT_ROOT, "docs", "research", "raw", "trainingpeaks")
OUT_DIR = os.path.join(PROJECT_ROOT, "docs", "research", "trainingpeaks")

# ── Nav / header boilerplate ──────────────────────────────────────────────
# The TP scraper captured the full page text.  Files that went through
# content_clean already had most of this removed, but files that only have
# raw `content` still carry the site-wide navigation header.
NAV_HEADER_RE = re.compile(
    r"^Training Articles\n"
    r"Subscribe\n"
    r"Training Articles\n"
    r"/\n"
    r"Coach Blog\n"
    r"(?:.*?\n)*?"           # category links
    r"Search\n"
    r"Subscribe\n",
    re.DOTALL,
)

# Alternate shorter nav that sometimes appears
NAV_SHORT_RE = re.compile(
    r"^Training Articles\n"
    r"Subscribe\n"
    r"(?:.*?\n)*?"
    r"Subscribe\n",
    re.DOTALL,
)

# ── "BY Author" line right after title ────────────────────────────────────
BY_LINE_RE = re.compile(r"^BY\s+.+\n", re.MULTILINE)

# ── Trailing boilerplate patterns ─────────────────────────────────────────
# Related articles block (title + blurbs + Read Article lines)
RELATED_ARTICLES_RE = re.compile(
    r"\nRelated Articles\n.*",
    re.DOTALL,
)

# "About TrainingPeaks" or "About <Name>" trailing bio sections
# Use [\s\xa0] to match both regular and non-breaking spaces in names
ABOUT_SECTION_RE = re.compile(
    r"\nAbout (?:TrainingPeaks|[A-Z][a-z]+[\s\xa0]+[A-Z][a-z]+(?:[\s\xa0]+[A-Z][a-z]+)?)\n.*",
    re.DOTALL,
)

# "Visit <Name>'s Coach Profile" trailing line
COACH_PROFILE_RE = re.compile(
    r"\nVisit .+? Coach Profile\n?.*",
    re.DOTALL,
)

# Trailing hashtag categories like "#cycling", "#performance", "#Mountain Bike"
TRAILING_HASHTAGS_RE = re.compile(
    r"\n#[\w _-]+(?:\n#[\w _-]+)*\s*$",
)

# "Read The Guide" promo lines
READ_GUIDE_RE = re.compile(r"\nRead The Guide\n?")

# Trailing promo blocks — various headers lead into plan store / guide CTAs
PROMO_BLOCK_RE = re.compile(
    r"\n(?:Goals Are Best Achieved With a Plan"
    r"|Train Smarter With a Plan"
    r"|The Ultimate (?:Full-Distance )?Training Guide['\u2019]?"
    r"|Marathon: The Ultimate Training Guide['\u2019]?"
    r"|Weight Training for Triathlon: The Ultimate Guide"
    r"|Shop [\w\s-]+ Training Plans"
    r"|Top Training Plans? [Ff]or [\w\s]+"
    r"|Strength Training (?:Plans|for Triathletes)"
    r"|Training Plan Quiz"
    r"|The Ultimate (?:Home Workout|Business) Guide"
    r"|Buy a Plan[,\w\s]*)"
    r"\n.*",
    re.DOTALL,
)

# Fallback: "Training Plan Store\n..." as a standalone section near the end
PLAN_STORE_RE = re.compile(
    r"\nTraining Plan Store\n.*",
    re.DOTALL,
)


def strip_boilerplate(text: str, title: str) -> str:
    """Remove navigation, related articles, trailing bios, and hashtags."""
    # 0. Normalize non-breaking spaces to regular spaces
    text = text.replace("\xa0", " ")

    # 1. Strip nav header (raw content only)
    text = NAV_HEADER_RE.sub("", text)
    text = NAV_SHORT_RE.sub("", text)

    # 2. If the text starts with the article title, remove that duplicate line
    #    (the title is already in frontmatter)
    title_norm = title.strip().replace("\xa0", " ").lower()
    lines = text.split("\n", 1)
    if lines and lines[0].strip().lower() == title_norm:
        text = lines[1] if len(lines) > 1 else ""

    # 3. Remove "BY Author" line that sometimes follows the title
    text = BY_LINE_RE.sub("", text, count=1)

    # 4. Strip trailing boilerplate (order matters: promo first, then related
    #    articles, about sections, coach profile, read guide, hashtags)
    text = PROMO_BLOCK_RE.sub("", text)
    text = PLAN_STORE_RE.sub("", text)
    text = RELATED_ARTICLES_RE.sub("", text)
    text = ABOUT_SECTION_RE.sub("", text)
    text = COACH_PROFILE_RE.sub("", text)
    text = READ_GUIDE_RE.sub("", text)
    text = TRAILING_HASHTAGS_RE.sub("", text)

    # 5. Clean up excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def escape_yaml_string(s: str) -> str:
    """Escape a string for use in YAML double-quoted scalar."""
    return s.replace("\\", "\\\\").replace('"', '\\"')


def convert_article(json_path: str, out_path: str) -> bool:
    """Convert a single JSON article to markdown. Returns True on success."""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    title = data.get("title", "").strip()
    author = data.get("real_author") or data.get("author") or ""
    author = author.strip()
    url = data.get("url", "").strip()
    slug = data.get("slug", "").strip()

    # Prefer content_clean, fall back to content
    body = data.get("content_clean") or data.get("content") or ""

    if not body.strip():
        return False

    body = strip_boilerplate(body, title)

    if not body.strip():
        return False

    # Build frontmatter
    fm_lines = [
        "---",
        f'title: "{escape_yaml_string(title)}"',
        f'author: "{escape_yaml_string(author)}"',
        f'source: "{escape_yaml_string(url)}"',
        f'slug: "{escape_yaml_string(slug)}"',
        "---",
    ]

    md = "\n".join(fm_lines) + "\n\n" + body + "\n"

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(md)

    return True


def main():
    if not os.path.isdir(RAW_DIR):
        print(f"ERROR: Raw directory not found: {RAW_DIR}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(OUT_DIR, exist_ok=True)

    json_files = sorted(
        f for f in os.listdir(RAW_DIR)
        if f.endswith(".json") and f != "_state.json"
    )

    existing_md = set(
        f for f in os.listdir(OUT_DIR)
        if f.endswith(".md")
    )

    skipped = 0
    converted = 0
    failed = 0

    for jf in json_files:
        slug = jf[:-5]  # strip .json
        md_name = slug + ".md"

        if md_name in existing_md:
            skipped += 1
            continue

        json_path = os.path.join(RAW_DIR, jf)
        out_path = os.path.join(OUT_DIR, md_name)

        ok = convert_article(json_path, out_path)
        if ok:
            converted += 1
        else:
            failed += 1
            print(f"  WARN: empty content for {jf}", file=sys.stderr)

    total_md = len([
        f for f in os.listdir(OUT_DIR)
        if f.endswith(".md")
    ])

    print(f"JSON files found:       {len(json_files)}")
    print(f"Already existed (skip): {skipped}")
    print(f"Newly converted:        {converted}")
    print(f"Failed (empty):         {failed}")
    print(f"Total .md files now:    {total_md}")


if __name__ == "__main__":
    main()
