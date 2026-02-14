"""
FILE: compare_ocr_engines.py
STATUS: Active
RESPONSIBILITY: Compare OCR engines (EasyOCR vs PaddleOCR) on Reddit PDF samples
LAST MAJOR UPDATE: 2026-02-10
MAINTAINER: Shahu
"""

import sys
import time
import logging
import re
from pathlib import Path

import fitz  # PyMuPDF
import numpy as np
from PIL import Image

# Setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "inputs"

# Pages to test per PDF (first, middle, last-ish)
SAMPLE_PAGES = [0, 2, 5]


def render_page_to_image(pdf_path: str, page_num: int, zoom: float = 2.0) -> np.ndarray:
    """Render a PDF page to a numpy array image."""
    doc = fitz.open(pdf_path)
    if page_num >= len(doc):
        page_num = len(doc) - 1
    page = doc.load_page(page_num)
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    doc.close()
    return np.array(img)


def get_pdf_page_count(pdf_path: str) -> int:
    """Get the number of pages in a PDF."""
    doc = fitz.open(pdf_path)
    count = len(doc)
    doc.close()
    return count


def test_easyocr(images: list[tuple[str, int, np.ndarray]]) -> dict:
    """Test EasyOCR on sample images."""
    import easyocr

    logger.info("=== Initializing EasyOCR ===")
    init_start = time.time()
    reader = easyocr.Reader(["en", "fr"], gpu=False)
    init_time = time.time() - init_start
    logger.info(f"EasyOCR init: {init_time:.1f}s")

    results = {}
    total_time = 0.0

    for pdf_name, page_num, img in images:
        key = f"{pdf_name}_p{page_num}"
        logger.info(f"  EasyOCR processing {key}...")

        start = time.time()
        ocr_results = reader.readtext(img)
        elapsed = time.time() - start
        total_time += elapsed

        # Extract text and confidence
        texts = [r[1] for r in ocr_results]
        confidences = [r[2] for r in ocr_results]
        full_text = "\n".join(texts)

        results[key] = {
            "text": full_text,
            "char_count": len(full_text),
            "word_count": len(full_text.split()),
            "line_count": len(texts),
            "avg_confidence": np.mean(confidences) if confidences else 0.0,
            "min_confidence": min(confidences) if confidences else 0.0,
            "time_seconds": elapsed,
        }
        logger.info(
            f"    -> {len(full_text)} chars, {len(texts)} lines, "
            f"avg conf: {results[key]['avg_confidence']:.3f}, "
            f"time: {elapsed:.1f}s"
        )

    return {
        "engine": "EasyOCR",
        "init_time": init_time,
        "total_ocr_time": total_time,
        "pages": results,
    }


def test_surya(images: list[tuple[str, int, np.ndarray]]) -> dict:
    """Test Surya OCR on sample images."""
    from surya.detection import DetectionPredictor
    from surya.recognition import RecognitionPredictor
    from surya.foundation import FoundationPredictor
    from surya.common.surya.schema import TaskNames

    logger.info("=== Initializing Surya OCR ===")
    init_start = time.time()
    foundation_predictor = FoundationPredictor()
    det_predictor = DetectionPredictor()
    rec_predictor = RecognitionPredictor(foundation_predictor)
    init_time = time.time() - init_start
    logger.info(f"Surya OCR init: {init_time:.1f}s")

    results = {}
    total_time = 0.0

    for pdf_name, page_num, img in images:
        key = f"{pdf_name}_p{page_num}"
        logger.info(f"  Surya processing {key}...")

        # Surya v0.17 expects PIL Images
        pil_img = Image.fromarray(img)

        start = time.time()
        # Surya v0.17 API: rec_predictor(images, task_names, det_predictor)
        predictions = rec_predictor(
            [pil_img],
            task_names=[TaskNames.ocr_with_boxes],
            det_predictor=det_predictor,
        )
        elapsed = time.time() - start
        total_time += elapsed

        # predictions is list of results, one per image
        texts = []
        confidences = []
        if predictions:
            for line in predictions[0].text_lines:
                texts.append(line.text)
                confidences.append(line.confidence)

        full_text = "\n".join(texts)

        results[key] = {
            "text": full_text,
            "char_count": len(full_text),
            "word_count": len(full_text.split()),
            "line_count": len(texts),
            "avg_confidence": np.mean(confidences) if confidences else 0.0,
            "min_confidence": min(confidences) if confidences else 0.0,
            "time_seconds": elapsed,
        }
        logger.info(
            f"    -> {len(full_text)} chars, {len(texts)} lines, "
            f"avg conf: {results[key]['avg_confidence']:.3f}, "
            f"time: {elapsed:.1f}s"
        )

    return {
        "engine": "Surya OCR",
        "init_time": init_time,
        "total_ocr_time": total_time,
        "pages": results,
    }


def quality_analysis(text: str) -> dict:
    """Analyze OCR text quality for Reddit-specific patterns."""
    metrics = {}

    # 1. URL integrity: count broken vs valid URLs
    valid_urls = len(re.findall(r"https?://[^\s]+", text))
    broken_urls = len(re.findall(r"https?:/[^/]", text))
    metrics["valid_urls"] = valid_urls
    metrics["broken_urls"] = broken_urls

    # 2. Reddit-specific markers detected
    reddit_markers = {
        "subreddit": len(re.findall(r"r/\w+", text)),
        "username": len(re.findall(r"u/\w+", text)),
        "upvotes": len(re.findall(r"\d+\s*upvotes?", text, re.IGNORECASE)),
        "repondre": len(re.findall(r"R[ée]pondre", text, re.IGNORECASE)),
        "partager": len(re.findall(r"Partager", text, re.IGNORECASE)),
    }
    metrics["reddit_markers"] = reddit_markers
    metrics["total_reddit_markers"] = sum(reddit_markers.values())

    # 3. French accented characters preserved
    accented = len(re.findall(r"[éèêëàâäùûüôîïç]", text, re.IGNORECASE))
    metrics["accented_chars"] = accented

    # 4. Gibberish detection (sequences of consonants > 5)
    gibberish = len(re.findall(r"[bcdfghjklmnpqrstvwxyz]{6,}", text, re.IGNORECASE))
    metrics["gibberish_sequences"] = gibberish

    # 5. Number integrity (detect isolated single digits that might be noise)
    isolated_numbers = len(re.findall(r"(?<!\w)\d(?!\w)", text))
    metrics["isolated_single_digits"] = isolated_numbers

    # 6. Sentence-like structures (capitalized word followed by text ending in punctuation)
    sentences = len(re.findall(r"[A-Z][a-z]+.*?[.!?]", text))
    metrics["sentence_structures"] = sentences

    return metrics


def print_comparison(easyocr_results: dict, surya_results: dict):
    """Print side-by-side comparison of OCR results."""
    alt_name = surya_results["engine"]

    print("\n" + "=" * 80)
    print("OCR ENGINE COMPARISON RESULTS")
    print("=" * 80)

    # Init times
    print(f"\n{'Metric':<35} {'EasyOCR':>20} {alt_name:>20}")
    print("-" * 75)
    print(f"{'Initialization time (s)':<35} {easyocr_results['init_time']:>20.1f} {surya_results['init_time']:>20.1f}")
    print(f"{'Total OCR time (s)':<35} {easyocr_results['total_ocr_time']:>20.1f} {surya_results['total_ocr_time']:>20.1f}")

    # Per-page comparison
    print("\n\nPER-PAGE COMPARISON:")
    print("-" * 75)

    all_easy_quality = []
    all_alt_quality = []

    for key in easyocr_results["pages"]:
        easy = easyocr_results["pages"][key]
        alt = surya_results["pages"].get(key, {})

        if not alt:
            continue

        print(f"\n  [{key}]")
        print(f"  {'Metric':<30} {'EasyOCR':>20} {alt_name:>20}")
        print(f"  {'-' * 70}")
        print(f"  {'Characters':<30} {easy['char_count']:>20} {alt['char_count']:>20}")
        print(f"  {'Words':<30} {easy['word_count']:>20} {alt['word_count']:>20}")
        print(f"  {'Lines detected':<30} {easy['line_count']:>20} {alt['line_count']:>20}")
        print(f"  {'Avg confidence':<30} {easy['avg_confidence']:>20.3f} {alt['avg_confidence']:>20.3f}")
        print(f"  {'Min confidence':<30} {easy['min_confidence']:>20.3f} {alt['min_confidence']:>20.3f}")
        print(f"  {'Time (s)':<30} {easy['time_seconds']:>20.1f} {alt['time_seconds']:>20.1f}")

        # Quality analysis
        easy_qual = quality_analysis(easy["text"])
        alt_qual = quality_analysis(alt["text"])
        all_easy_quality.append(easy_qual)
        all_alt_quality.append(alt_qual)

        print(f"\n  Quality Metrics:")
        print(f"  {'Reddit markers found':<30} {easy_qual['total_reddit_markers']:>20} {alt_qual['total_reddit_markers']:>20}")
        print(f"  {'Accented chars':<30} {easy_qual['accented_chars']:>20} {alt_qual['accented_chars']:>20}")
        print(f"  {'Gibberish sequences':<30} {easy_qual['gibberish_sequences']:>20} {alt_qual['gibberish_sequences']:>20}")
        print(f"  {'Sentence structures':<30} {easy_qual['sentence_structures']:>20} {alt_qual['sentence_structures']:>20}")
        print(f"  {'Broken URLs':<30} {easy_qual['broken_urls']:>20} {alt_qual['broken_urls']:>20}")

    # Aggregate summary
    print("\n\n" + "=" * 80)
    print("AGGREGATE SUMMARY")
    print("=" * 80)

    total_easy_chars = sum(p["char_count"] for p in easyocr_results["pages"].values())
    total_alt_chars = sum(p["char_count"] for p in surya_results["pages"].values())
    total_easy_words = sum(p["word_count"] for p in easyocr_results["pages"].values())
    total_alt_words = sum(p["word_count"] for p in surya_results["pages"].values())

    avg_easy_conf = np.mean([p["avg_confidence"] for p in easyocr_results["pages"].values()])
    avg_alt_conf = np.mean([p["avg_confidence"] for p in surya_results["pages"].values()])

    total_easy_reddit = sum(q["total_reddit_markers"] for q in all_easy_quality)
    total_alt_reddit = sum(q["total_reddit_markers"] for q in all_alt_quality)
    total_easy_gibberish = sum(q["gibberish_sequences"] for q in all_easy_quality)
    total_alt_gibberish = sum(q["gibberish_sequences"] for q in all_alt_quality)
    total_easy_accented = sum(q["accented_chars"] for q in all_easy_quality)
    total_alt_accented = sum(q["accented_chars"] for q in all_alt_quality)
    total_easy_sentences = sum(q["sentence_structures"] for q in all_easy_quality)
    total_alt_sentences = sum(q["sentence_structures"] for q in all_alt_quality)

    print(f"\n{'Metric':<35} {'EasyOCR':>20} {alt_name:>20} {'Winner':>12}")
    print("-" * 87)
    winner = alt_name if total_alt_chars > total_easy_chars else "EasyOCR"
    print(f"{'Total characters':<35} {total_easy_chars:>20} {total_alt_chars:>20} {winner:>12}")
    winner = alt_name if total_alt_words > total_easy_words else "EasyOCR"
    print(f"{'Total words':<35} {total_easy_words:>20} {total_alt_words:>20} {winner:>12}")
    winner = alt_name if avg_alt_conf > avg_easy_conf else "EasyOCR"
    print(f"{'Avg confidence':<35} {avg_easy_conf:>20.3f} {avg_alt_conf:>20.3f} {winner:>12}")
    winner = alt_name if surya_results['total_ocr_time'] < easyocr_results['total_ocr_time'] else "EasyOCR"
    print(f"{'Total OCR time (s)':<35} {easyocr_results['total_ocr_time']:>20.1f} {surya_results['total_ocr_time']:>20.1f} {winner:>12}")
    winner = alt_name if total_alt_reddit > total_easy_reddit else "EasyOCR"
    print(f"{'Reddit markers detected':<35} {total_easy_reddit:>20} {total_alt_reddit:>20} {winner:>12}")
    winner = alt_name if total_alt_accented > total_easy_accented else "EasyOCR"
    print(f"{'Accented chars preserved':<35} {total_easy_accented:>20} {total_alt_accented:>20} {winner:>12}")
    winner = "EasyOCR" if total_easy_gibberish < total_alt_gibberish else alt_name
    print(f"{'Gibberish sequences (lower=better)':<35} {total_easy_gibberish:>20} {total_alt_gibberish:>20} {winner:>12}")
    winner = alt_name if total_alt_sentences > total_easy_sentences else "EasyOCR"
    print(f"{'Sentence structures detected':<35} {total_easy_sentences:>20} {total_alt_sentences:>20} {winner:>12}")

    # Print text samples for visual comparison
    print("\n\n" + "=" * 80)
    print("TEXT SAMPLE COMPARISON (First 500 chars from first page)")
    print("=" * 80)

    first_key = list(easyocr_results["pages"].keys())[0]
    print(f"\n--- EasyOCR ({first_key}) ---")
    print(easyocr_results["pages"][first_key]["text"][:500])
    print(f"\n--- {alt_name} ({first_key}) ---")
    print(surya_results["pages"][first_key]["text"][:500])

    # Also show a content-rich page
    print("\n\n" + "=" * 80)
    print("TEXT SAMPLE COMPARISON (First 500 chars from Reddit 2 page 2)")
    print("=" * 80)
    sample_key = "Reddit 2.pdf_p2"
    if sample_key in easyocr_results["pages"] and sample_key in surya_results["pages"]:
        print(f"\n--- EasyOCR ({sample_key}) ---")
        print(easyocr_results["pages"][sample_key]["text"][:500])
        print(f"\n--- {alt_name} ({sample_key}) ---")
        print(surya_results["pages"][sample_key]["text"][:500])


def main():
    sys.stdout.reconfigure(encoding="utf-8")

    # Find Reddit PDFs
    pdf_files = sorted(DATA_DIR.glob("Reddit*.pdf"))
    if not pdf_files:
        logger.error(f"No Reddit PDFs found in {DATA_DIR}")
        return

    print(f"Found {len(pdf_files)} Reddit PDFs:")
    for pdf in pdf_files:
        pages = get_pdf_page_count(str(pdf))
        print(f"  {pdf.name}: {pdf.stat().st_size / 1024 / 1024:.1f} MB, {pages} pages")

    # Render sample pages
    print(f"\nRendering {len(SAMPLE_PAGES)} sample pages per PDF at 2x resolution...")
    images = []
    for pdf in pdf_files:
        page_count = get_pdf_page_count(str(pdf))
        for page_num in SAMPLE_PAGES:
            actual_page = min(page_num, page_count - 1)
            logger.info(f"Rendering {pdf.name} page {actual_page}...")
            img = render_page_to_image(str(pdf), actual_page)
            images.append((pdf.name, actual_page, img))

    print(f"Rendered {len(images)} images total\n")

    # Test EasyOCR
    easyocr_results = test_easyocr(images)

    # Test Surya OCR
    surya_results = test_surya(images)

    # Print comparison
    print_comparison(easyocr_results, surya_results)


if __name__ == "__main__":
    main()
