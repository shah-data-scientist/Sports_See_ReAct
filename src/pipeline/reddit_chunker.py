"""
FILE: reddit_chunker.py
STATUS: Active
RESPONSIBILITY: Reddit-specific chunking with ad filtering and thread preservation
LAST MAJOR UPDATE: 2026-02-10
MAINTAINER: Shahu
"""

import hashlib
import logging
import re
from typing import Any

from src.pipeline.models import ChunkData

logger = logging.getLogger(__name__)


class RedditThreadChunker:
    """
    Chunk Reddit threads preserving post + comment structure.

    Key Features:
    - Filters advertisements (Sponsoris(e), promotional URLs)
    - Preserves thread context (post + top comments together)
    - Parses nested comment structure
    - Supports NBA official content weighting
    """

    # Advertisement patterns (compiled for performance)
    AD_PATTERNS = [
        r"Sponsoris\(e\).*?(?=\n\n|\Z)",  # French "Sponsored" marker
        r"Sponsored.*?(?=\n\n|\Z)",  # English "Sponsored"
        r"xometry_europe.*?Xometry",  # Specific sponsor blocks
        r"(?:En savoir plus|Learn more)\s+pages\.[a-z]+\.[a-z]+",  # CTA + URL
        r"Rejoindre la conversation",  # Reddit UI: "Join conversation"
        r"Accéder au contenu principal",  # Reddit UI: "Access main content"
        r"Accder au contenu principal",  # OCR variant
        r"Se connecter",  # Reddit UI: "Sign in"
        r"Rechercher dans r/\w+",  # Reddit UI: "Search in r/subreddit"
        r"Trier par\s+\w+",  # Reddit UI: "Sort by"
        r"Rechercher des commentaires",  # Reddit UI: "Search comments"
        r"réponses supplémentaires",  # Reddit UI: "Additional replies"
        r"rponses supplmentaires",  # OCR variant
    ]

    # NBA official account patterns
    NBA_OFFICIAL_ACCOUNTS = [
        "NBA",
        "NBAOfficial",
        "nba",
        "Lakers",
        "Celtics",
        "Warriors",
        "Bulls",
        "Heat",
        "Knicks",
        "Nets",
        "Mavericks",
        "Rockets",
        "Suns",
        "Clippers",
        "Nuggets",
        "Bucks",
        "Sixers",
        "Raptors",
        "Pacers",
        "Cavaliers",
    ]

    # Mistral embedding max is 8192 tokens (~4 chars/token).
    # Cap at 20000 chars (~5000 tokens) for safety margin.
    DEFAULT_MAX_CHUNK_CHARS = 20000

    def __init__(self, max_comments_per_chunk: int = 5, max_chunk_chars: int | None = None):
        """
        Initialize Reddit thread chunker.

        Args:
            max_comments_per_chunk: Target comments per chunk (may be fewer if chars limit hit)
            max_chunk_chars: Maximum characters per chunk text (default 20000)
        """
        self.max_comments = max_comments_per_chunk
        self.max_chunk_chars = max_chunk_chars or self.DEFAULT_MAX_CHUNK_CHARS
        self.ad_regex = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in self.AD_PATTERNS]

    # Line-level noise patterns removed during OCR cleaning
    _OCR_NOISE_LINE_PATTERNS = [
        # Date headers repeated per PDF page (e.g., "12/06/2025 13.06")
        re.compile(r"^\d{2}/\d{2}/\d{4}\s+\d{2}[:.]\d{2}\s*$"),
        # Standalone subreddit markers ("rInba", "r/nba")
        re.compile(r"^r/?I?n?ba\s*$", re.IGNORECASE),
        # Page numbers ("1/15", "23/36")
        re.compile(r"^\d{1,3}/\d{1,3}\s*$"),
        # Reddit footer stats ("118 upvotes", "110 commentaires")
        re.compile(r"^\d[\d,.\s]*k?\s+(?:upvote|commentaire|comment)", re.IGNORECASE),
        # Sponsored/Official labels
        re.compile(r"^Sponsoris", re.IGNORECASE),
        re.compile(r"^Officiel\s*$", re.IGNORECASE),
        # Ad CTAs
        re.compile(r"^En savoir plus\s*$", re.IGNORECASE),
        re.compile(r"^S'inscrire\s*$", re.IGNORECASE),
        re.compile(r"^Wishlist\s*$", re.IGNORECASE),
        # Reddit UI navigation
        re.compile(r"^Afficher\s+plus", re.IGNORECASE),
        re.compile(r"^Voir\s+\d+", re.IGNORECASE),
        # Deleted comments (no useful content)
        re.compile(r"^\[supprim", re.IGNORECASE),
        # "N réponses supplémentaires"
        re.compile(r"^\d+\s+r[ée]ponses?\s+suppl[ée]mentaire", re.IGNORECASE),
        # URL lines (Reddit permalinks, ad URLs)
        re.compile(r"^https?://", re.IGNORECASE),
        re.compile(r"^(?:pages|ad)\.\w+\.\w+", re.IGNORECASE),
        re.compile(r"^ad\.doubleclick", re.IGNORECASE),
        # Ad brand names as standalone lines
        re.compile(r"^(?:IBM|ibm|adidas\w*|xometry\w*|enaa)\s*$", re.IGNORECASE),
        # Very short noise tokens (1-2 non-digit chars, common OCR artifacts)
        re.compile(r"^(?:YA|Ao|Ll|Vl|Am|U|C|m[.:])$"),
        # URL path fragments from Reddit links (3+ underscore-separated words)
        re.compile(r"^\w+_\w+_\w+"),
    ]

    def filter_advertisements(self, text: str) -> str:
        """
        Remove advertisements and Reddit UI noise from text.

        Args:
            text: Raw OCR text from Reddit PDF

        Returns:
            Cleaned text with ads removed
        """
        cleaned = text

        for pattern in self.ad_regex:
            cleaned = pattern.sub("", cleaned)

        # Remove excessive whitespace
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        cleaned = re.sub(r" {2,}", " ", cleaned)

        return cleaned.strip()

    def clean_ocr_noise(self, text: str) -> str:
        """Remove OCR noise, page artifacts, ads, and Reddit UI from raw text.

        This is a comprehensive line-by-line cleaning pass that runs BEFORE
        comment extraction. It removes:
        - Date headers (repeated per PDF page)
        - Standalone subreddit markers (rInba)
        - Page numbers (1/15, 23/36)
        - Ad content (Xometry, IBM, adidas blocks)
        - Reddit UI elements (Sponsorisé, Afficher, upvotes/commentaires footers)
        - URL fragments
        - Deleted comments ([supprimé])
        - Short OCR artifact tokens

        Args:
            text: Raw OCR text (after filter_advertisements)

        Returns:
            Cleaned text with noise lines removed
        """
        lines = text.split("\n")
        kept = []

        for line in lines:
            stripped = line.strip()

            # Keep blank lines (they separate content)
            if not stripped:
                kept.append(line)
                continue

            # Check against all noise patterns
            is_noise = False
            for pattern in self._OCR_NOISE_LINE_PATTERNS:
                if pattern.match(stripped):
                    is_noise = True
                    break

            if not is_noise:
                kept.append(line)

        result = "\n".join(kept)
        # Collapse excessive blank lines from removed noise
        result = re.sub(r"\n{3,}", "\n\n", result)
        return result.strip()

    # Pattern to parse French-style stat numbers ("31", "457", "1,3 k")
    _STAT_NUM_RE = re.compile(r"^[↑]?[\d][\d,.\s]*\s*[k]?\s*[↓]?$", re.IGNORECASE)

    def _parse_stat_number(self, s: str) -> int:
        """Parse a stat number like '31', '1,3 k', '457' to int."""
        s = re.sub(r"[↑↓\s]", "", s).strip()
        if "k" in s.lower():
            s = s.lower().replace("k", "").replace(",", ".").strip()
            return int(float(s) * 1000)
        return int(re.sub(r"[,.]", "", s))

    def extract_post_info(self, text: str) -> dict[str, Any]:
        """
        Extract main post information from Reddit thread.

        Handles easyOCR format (rInba + timestamp + author + title)
        and RapidOCR format (r/nba · timestamp\\nauthor\\ntitle).

        Args:
            text: Cleaned Reddit thread text

        Returns:
            Dictionary with post metadata including body text
        """
        # easyOCR produces "rInba" (slash lost), RapidOCR keeps "r/nba"
        # Match: subreddit + timestamp + author + optional badge + title
        post_match = re.search(
            r"(?:r/?I?n?ba|r/nba)\s*\n"
            r"(?:il\s*y?\s*a|ily?\s*a)\s+[^\n]+\n"
            r"([A-Za-z0-9_-]+)[^\n]*\n"
            r"(?:Comm[^\n]*\n)?"
            r"([^\n]+)",
            text,
            re.IGNORECASE,
        )

        title = "Unknown Title"
        author = "Unknown"
        title_end = 0
        if post_match:
            author = post_match.group(1)
            title = post_match.group(2).strip()
            title = " ".join(title.split())
            title_end = post_match.end()

        # Find FIRST "Partager" AFTER the title to locate stats
        upvotes = 0
        num_comments = 0
        body = ""

        partager_pos = text.find("Partager", title_end)
        if partager_pos > title_end:
            # Scan backwards from Partager for stat numbers (upvotes, comments)
            pre_partager = text[title_end:partager_pos].rstrip()
            lines = pre_partager.split("\n")

            stat_lines: list[str] = []
            for line in reversed(lines):
                line = line.strip()
                if not line:
                    continue
                if self._STAT_NUM_RE.match(line):
                    stat_lines.insert(0, line)
                    if len(stat_lines) >= 2:
                        break
                else:
                    break

            if len(stat_lines) >= 2:
                upvotes = self._parse_stat_number(stat_lines[0])
                num_comments = self._parse_stat_number(stat_lines[1])
            elif len(stat_lines) == 1:
                upvotes = self._parse_stat_number(stat_lines[0])

            # Body = text between title end and the first stat line
            body_end_pos = partager_pos
            if stat_lines:
                first_stat = stat_lines[0]
                stat_offset = pre_partager.rfind(first_stat)
                if stat_offset >= 0:
                    body_end_pos = title_end + stat_offset

            if body_end_pos > title_end:
                raw_body = text[title_end:body_end_pos].strip()
                raw_body = " ".join(raw_body.split())
                if len(raw_body) > 20:
                    body = raw_body

        return {
            "title": title,
            "author": author,
            "upvotes": upvotes,
            "num_comments": num_comments,
            "body": body,
        }

    # Noise patterns to skip when extracting comments
    _SEGMENT_NOISE = re.compile(
        r"^(?:https?://|r[ée]ponse|Afficher|Voir|\d+\s+r[ée]ponse|\[supprim)",
        re.IGNORECASE,
    )

    # Words that look like usernames but are actually UI elements/badges
    _FAKE_USERNAMES = {
        "comm", "auteur", "partager", "officiel", "top",
        "nba", "voir", "ibm", "ibx",
    }

    def extract_comments(self, text: str) -> list[dict[str, Any]]:
        """
        Extract comments from Reddit thread using Répondre markers as delimiters.

        easyOCR format per segment (between Répondre markers):
            username\\n[-timestamp]\\n[badge]\\ntext\\nupvotes

        Username detection: First line that is 3-20 alphanumeric/underscore/hyphen
        chars with no spaces (easyOCR often strips the · separator).

        Args:
            text: Cleaned Reddit thread text

        Returns:
            List of comment dictionaries sorted by upvotes (descending)
        """
        comments = []

        # Split by Répondre/Repondre/Rpondre markers
        segments = re.split(r"\s*R[éeè]?pondre\b", text, flags=re.IGNORECASE)

        for segment in segments:
            segment = segment.strip()
            if not segment or len(segment) < 20:
                continue

            # Skip noise segments (URLs, "réponses supplémentaires", etc.)
            if self._SEGMENT_NOISE.match(segment):
                continue

            lines = [l.strip() for l in segment.split("\n") if l.strip()]
            if len(lines) < 2:
                continue

            # Find username: first line that looks like a Reddit username
            # (3-20 alphanumeric/underscore/hyphen, no spaces)
            # Also accept "username · timestamp" format from RapidOCR
            username = None
            username_idx = -1
            for j, line in enumerate(lines):
                # Exact username (easyOCR format — no · separator)
                m = re.match(r"^([A-Za-z0-9_-]{3,20})$", line)
                if m:
                    candidate = m.group(1)
                    # Reject known UI/badge words
                    if candidate.lower() in self._FAKE_USERNAMES:
                        continue
                    # Reject URL fragments (3+ underscore-separated words)
                    if candidate.count("_") >= 2:
                        continue
                    username = candidate
                    username_idx = j
                    break
                # Username with · separator (RapidOCR / some easyOCR variants)
                m = re.match(r"^([A-Za-z0-9_-]{3,})\s*[·.]", line)
                if m:
                    candidate = m.group(1)
                    if candidate.lower() in self._FAKE_USERNAMES:
                        continue
                    if candidate.count("_") >= 2:
                        continue
                    username = candidate
                    username_idx = j
                    break

            if not username:
                continue

            # Find upvotes: last line that is just a number
            upvotes = 0
            upvote_idx = len(lines)  # default: end of segment
            for j in range(len(lines) - 1, username_idx, -1):
                m = re.match(r"^[↑]?(\d+)\s*[↓]?$", lines[j])
                if m:
                    upvotes = int(m.group(1))
                    upvote_idx = j
                    break

            # Comment text: between username line and upvote line
            start = username_idx + 1

            # Skip optional timestamp line (e.g. "-1 m", "~1m", "· -1 m.")
            if start < upvote_idx:
                ts_line = lines[start]
                if re.match(r"^[·~\-\s]*\d+\s*m\.?$", ts_line):
                    start += 1

            # Skip optional community badge line (e.g. "Comm. du top 1%")
            if start < upvote_idx:
                if lines[start].startswith("Comm"):
                    start += 1
                # Also skip "Auteur-rice" badge
                elif lines[start].startswith("Auteur"):
                    start += 1

            comment_lines = lines[start:upvote_idx]
            comment_text = " ".join(comment_lines)

            # Skip very short comments (likely OCR noise)
            if len(comment_text) < 10:
                continue

            comments.append({
                "author": username,
                "text": comment_text,
                "upvotes": upvotes,
                "is_nba_official": username in self.NBA_OFFICIAL_ACCOUNTS,
            })

        return comments

    def _build_post_context(self, post_info: dict[str, Any]) -> str:
        """Build compact post context block shared across all chunks.

        Args:
            post_info: Post metadata from extract_post_info()

        Returns:
            Formatted post context string
        """
        body = post_info.get("body", "")
        body_line = ""
        if body:
            if len(body) <= 300:
                body_line = f"\nPost: {body}"
            else:
                body_line = f"\nPost: {body[:250]}..."

        return (
            f"=== REDDIT POST ===\n"
            f"Title: {post_info['title']}\n"
            f"Author: u/{post_info['author']} | "
            f"Upvotes: {post_info['upvotes']} | "
            f"Comments: {post_info['num_comments']}"
            f"{body_line}"
        )

    def chunk_reddit_thread(self, text: str, source: str) -> list[ChunkData]:
        """
        Create 1-comment-per-chunk from Reddit thread for precise retrieval.

        Strategy:
        1. Filter advertisements (block-level patterns)
        2. Clean OCR noise (line-level artifacts)
        3. Extract post metadata (including body)
        4. Extract all comments
        5. Sort by upvotes descending
        6. One chunk per comment, each with post context header + body

        Args:
            text: Raw OCR text from Reddit PDF
            source: Source file path

        Returns:
            List of ChunkData objects (one per comment)
        """
        # Step 1: Filter ad blocks
        cleaned_text = self.filter_advertisements(text)

        # Step 2: Extract post info BEFORE noise cleaning (needs rInba markers)
        post_info = self.extract_post_info(cleaned_text)

        # Step 3: Clean OCR noise (line-level)
        cleaned_text = self.clean_ocr_noise(cleaned_text)

        # Step 4: Extract comments from AFTER first Partager (skip post area)
        # The zone between Partager and first Répondre contains ad noise,
        # but extract_comments is robust enough to find the first valid username.
        partager_pos = cleaned_text.find("Partager")
        if partager_pos >= 0:
            comment_text = cleaned_text[partager_pos + len("Partager"):]
        else:
            comment_text = cleaned_text
        comments = self.extract_comments(comment_text)

        if not comments:
            logger.warning(f"No comments extracted from {source}")
            # Return basic chunk with just post info
            basic_text = f"REDDIT POST: {post_info['title']}"
            chunk_id = hashlib.sha256(basic_text.encode("utf-8")).hexdigest()[:16]
            return [
                ChunkData(
                    id=chunk_id,
                    text=basic_text,
                    metadata={
                        "source": source,
                        "type": "reddit_thread",
                        "post_title": post_info["title"],
                        "post_author": post_info["author"],
                        "post_upvotes": post_info["upvotes"],
                        "num_comments": 0,
                        "chunk_index": 0,
                        "total_chunks": 1,
                        "comment_author": "",
                        "comment_upvotes": 0,
                        "is_nba_official": 0,
                    },
                )
            ]

        # Step 5: Sort ALL comments by upvotes (descending)
        sorted_comments = sorted(comments, key=lambda c: c["upvotes"], reverse=True)

        # Step 6: Compute min/max comment upvotes for relative boost (within this post)
        comment_upvotes_list = [c["upvotes"] for c in sorted_comments]
        min_comment_upvotes = min(comment_upvotes_list)
        max_comment_upvotes = max(comment_upvotes_list)

        # Step 7: Build post context block (shared across all chunks)
        post_context = self._build_post_context(post_info)

        # Step 8: One chunk per comment (precise metadata, focused retrieval)
        total_comments = len(sorted_comments)
        chunks = []

        for comment_idx, comment in enumerate(sorted_comments):
            nba_tag = " [NBA OFFICIAL]" if comment["is_nba_official"] else ""
            chunk_text = (
                f"{post_context}\n\n"
                f"=== COMMENT ({comment_idx + 1}/{total_comments}) ===\n"
                f"u/{comment['author']}{nba_tag} "
                f"({comment['upvotes']} upvotes):\n"
                f"{comment['text']}\n"
            )

            chunk_id = hashlib.sha256(chunk_text.encode("utf-8")).hexdigest()[:16]

            chunk = ChunkData(
                id=chunk_id,
                text=chunk_text,
                metadata={
                    "source": source,
                    "type": "reddit_thread",
                    "post_title": post_info["title"],
                    "post_author": post_info["author"],
                    "post_upvotes": post_info["upvotes"],
                    "num_comments": total_comments,
                    "chunk_index": comment_idx,
                    "total_chunks": total_comments,
                    "comment_author": comment["author"],
                    "comment_upvotes": comment["upvotes"],
                    "is_nba_official": int(comment["is_nba_official"]),
                    # Min/max for relative boost calculation (within-post)
                    "min_comment_upvotes_in_post": min_comment_upvotes,
                    "max_comment_upvotes_in_post": max_comment_upvotes,
                },
            )
            chunks.append(chunk)

        logger.info(
            f"Created {len(chunks)} Reddit chunks from {source}: "
            f"{post_info['title'][:50]}... "
            f"({total_comments} comments, 1 per chunk)"
        )

        return chunks

    def is_reddit_content(self, text: str) -> bool:
        """
        Detect if text is from a Reddit PDF.

        Args:
            text: OCR extracted text

        Returns:
            True if text appears to be from Reddit
        """
        reddit_indicators = [
            r"r/nba",
            r"r/\w+",
            r"Répondre",
            r"Rpondre",  # OCR variant
            r"Partager",
            r"upvotes?",
            r"commentaires?",
        ]

        # Check if at least 2 Reddit indicators are present
        matches = sum(
            1 for pattern in reddit_indicators if re.search(pattern, text, re.IGNORECASE)
        )

        return matches >= 2
