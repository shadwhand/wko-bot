"""Local LLM pipeline — wiki-grounded Q&A via qmd + omlx server."""

import json
import logging
import os
import subprocess

import httpx

log = logging.getLogger(__name__)

OMLX_URL = os.environ.get("OMLX_URL", "http://127.0.0.1:8001")
OMLX_KEY = os.environ.get("OMLX_KEY", "9538")
WIKI_DIR = os.path.join(os.path.dirname(__file__), "..", "docs", "research", "wiki")

# Model assignments
MODEL_FAST = "Qwen3-4B-Instruct-2507-Claude-Haiku-4.5-Distill-qx86-hi-mlx"  # Fast prefetch (10.5 evid tags, 17s)
MODEL_FULL = "Qwen3.5-122B-A10B-4bit"  # Full synthesis (14.5 evid tags, 38s, MoE)
MODEL_REASONING = "Qwen3-30B-A3B-Thinking-2507-Claude-4.5-Sonnet-High-Reasoning-Distill-mxfp4-mlx"  # Deep reasoning


def _omlx_chat(messages, model=None, max_tokens=1024, temperature=0.3):
    """Send a chat completion request to the omlx server."""
    model = model or MODEL_FULL
    try:
        resp = httpx.post(
            f"{OMLX_URL}/v1/chat/completions",
            headers={"Authorization": f"Bearer {OMLX_KEY}"},
            json={
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
            timeout=120.0,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        log.error("omlx request failed: %s", e)
        return None


def _qmd_search(query, collection="wiki", limit=5):
    """Search qmd via CLI and return result text."""
    try:
        result = subprocess.run(
            ["qmd", "search", query, "-c", collection, "-n", str(limit)],
            capture_output=True, text=True, timeout=30,
        )
        return result.stdout.strip()
    except Exception as e:
        log.warning("qmd search failed: %s", e)
        return ""


def _read_wiki_index():
    """Read the wiki index for page navigation."""
    index_path = os.path.join(WIKI_DIR, "index.md")
    if os.path.exists(index_path):
        with open(index_path) as f:
            return f.read()
    return ""


def _read_wiki_page(relative_path):
    """Read a specific wiki page by relative path."""
    full_path = os.path.join(WIKI_DIR, relative_path)
    if os.path.exists(full_path):
        with open(full_path) as f:
            return f.read()
    return ""


def _select_pages(question, index_content, model=None):
    """Use fast model to select relevant wiki pages from the index."""
    model = model or MODEL_FAST
    prompt = (
        "Given this question and wiki index, return ONLY the file paths "
        "(e.g. concepts/ftp-threshold-testing.md) of the 2-3 most relevant pages. "
        "One path per line, nothing else.\n\n"
        f"Question: {question}\n\n"
        f"Index:\n{index_content}"
    )
    result = _omlx_chat(
        [{"role": "user", "content": prompt}],
        model=model,
        max_tokens=200,
        temperature=0.1,
    )
    if not result:
        return []
    paths = []
    for line in result.strip().split("\n"):
        line = line.strip().strip("-").strip("*").strip()
        if "/" in line and line.endswith(".md"):
            paths.append(line)
    return paths[:3]


def ask(question, mode="local"):
    """
    Answer a cycling training question using the wiki knowledge base.

    Modes:
        local   — omlx only (free, offline, fast)
        prefetch — omlx reads wiki, summarizes, returns compressed context
                   (for feeding to Claude as pre-digested context)
        hybrid  — omlx drafts, then could be refined by Claude (returns both)
    """
    # Step 1: Read index
    index = _read_wiki_index()
    if not index:
        return {"error": "Wiki index not found", "answer": None}

    # Step 2: Select relevant pages (fast model)
    pages = _select_pages(question, index)
    if not pages:
        # Fallback: use qmd search
        search_results = _qmd_search(question)
        return {
            "answer": None,
            "mode": mode,
            "fallback": "qmd_search",
            "search_results": search_results,
        }

    # Step 3: Read selected pages
    context_parts = []
    for path in pages:
        content = _read_wiki_page(path)
        if content:
            context_parts.append(f"--- {path} ---\n{content}")

    context = "\n\n".join(context_parts)

    # Step 4: Generate answer based on mode
    system_prompt = (
        "You are a cycling coach and sports scientist. Answer questions using ONLY "
        "the provided wiki pages as context. Cite sources using evidence tags "
        "[R] (research), [E] (experience), [O] (opinion) and episode/article IDs. "
        "Be specific with numbers. If the context doesn't cover the question, say so."
    )

    if mode == "prefetch":
        # Compress context for Claude — return summary, not full answer
        summary_prompt = (
            "Summarize the key facts from these wiki pages that are relevant to "
            f"answering this question: {question}\n\n"
            "Include specific numbers, evidence tags, and source citations. "
            "Be concise but complete — this summary will be given to another AI "
            "for final answer synthesis.\n\n"
            f"{context}"
        )
        summary = _omlx_chat(
            [{"role": "user", "content": summary_prompt}],
            model=MODEL_FAST,
            max_tokens=800,
        )
        return {
            "mode": "prefetch",
            "pages_read": pages,
            "summary": summary,
            "question": question,
        }

    # Local or hybrid — generate full answer
    answer = _omlx_chat(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ],
        model=MODEL_FULL,
        max_tokens=1024,
    )

    return {
        "mode": mode,
        "model": MODEL_FULL,
        "pages_read": pages,
        "answer": answer,
    }


def list_models():
    """List available models on the omlx server."""
    try:
        resp = httpx.get(
            f"{OMLX_URL}/v1/models",
            headers={"Authorization": f"Bearer {OMLX_KEY}"},
            timeout=5.0,
        )
        resp.raise_for_status()
        return [m["id"] for m in resp.json()["data"]]
    except Exception:
        return []
