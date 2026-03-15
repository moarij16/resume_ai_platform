"""
CLI entry point for the ATS Resume Scanner.

Mode 1: Resume vs Job Description (--resume + --jd)
Mode 2: Standalone resume quality (--resume only)
Supports batch processing with --resume-dir and --output-dir.
"""

import argparse
import sys
from pathlib import Path

# Ensure package root is on path when run as script
if __name__ == "__main__":
    _root = Path(__file__).resolve().parent.parent
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))

from ats_scanner.parsers import parse_resume
from ats_scanner.engines import score_resume_vs_jd
from ats_scanner.models import analyze_resume_quality
from ats_scanner.utils import setup_logging, format_output, get_logger

logger = get_logger(__name__)


def _load_jd(jd_arg: str) -> str:
    """Load job description from text or file path."""
    path = Path(jd_arg)
    if path.exists() and path.is_file():
        return path.read_text(encoding="utf-8", errors="replace").strip()
    return jd_arg.strip()


def run_single(
    resume_path: Path,
    jd_text: str | None,
    output_format: str,
    output_path: str | None,
) -> None:
    """Run analysis for one resume."""
    parsed = parse_resume(resume_path)
    text = parsed["text"]
    metadata = parsed["metadata"]
    if not text.strip():
        logger.error("No text extracted from resume: %s", resume_path)
        return
    if jd_text and jd_text.strip():
        result = score_resume_vs_jd(text, jd_text)
    else:
        result = analyze_resume_quality(text, metadata)
    out = format_output(result, output_format, output_path)
    if output_format == "text" and not output_path:
        print(out)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="ATS Resume Scanner — Match resume to JD or analyze resume quality.",
    )
    parser.add_argument("--resume", type=str, help="Path to resume (PDF/DOCX)")
    parser.add_argument(
        "--jd",
        type=str,
        default=None,
        help="Job description text or path to file",
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["text", "json", "html"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument("--output", type=str, default=None, help="Write output to file")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    parser.add_argument("--resume-dir", type=str, default=None, help="Batch: directory of resumes")
    parser.add_argument("--output-dir", type=str, default=None, help="Batch: directory for results")
    parser.add_argument("--rank", action="store_true", help="Batch: rank resumes by ATS score (requires --jd)")
    parser.add_argument("--top", type=int, default=None, help="Batch: output only top N ranked resumes")
    args = parser.parse_args()

    setup_logging(verbose=args.verbose)

    jd_text = _load_jd(args.jd) if args.jd else None

    if args.resume_dir:
        dir_path = Path(args.resume_dir)
        if not dir_path.is_dir():
            logger.error("Not a directory: %s", dir_path)
            sys.exit(1)
        out_dir = Path(args.output_dir) if args.output_dir else dir_path / "results"
        out_dir.mkdir(parents=True, exist_ok=True)
        files = list(dir_path.glob("*.pdf")) + list(dir_path.glob("*.docx"))
        results_with_scores: list[tuple[Path, float, dict]] = []
        for resume_path in files:
            try:
                parsed = parse_resume(resume_path)
                text = parsed["text"]
                meta = parsed["metadata"]
                if not text.strip():
                    continue
                if jd_text and jd_text.strip():
                    result = score_resume_vs_jd(text, jd_text)
                    score = result.get("ats_score", 0.0)
                else:
                    result = analyze_resume_quality(text, meta)
                    score = result.get("quality_score", 0.0)
                results_with_scores.append((resume_path, score, result))
            except Exception as e:
                logger.warning("Skip %s: %s", resume_path, e)
        if args.rank and jd_text:
            results_with_scores.sort(key=lambda x: -x[1])
        if args.top:
            results_with_scores = results_with_scores[: args.top]
        for resume_path, _score, result in results_with_scores:
            out_file = out_dir / f"result_{resume_path.stem}.{args.format if args.format != 'text' else 'txt'}"
            format_output(result, args.format, str(out_file))
        if args.rank and results_with_scores:
            rank_file = out_dir / "ranking.txt"
            with open(rank_file, "w", encoding="utf-8") as f:
                f.write("Ranking by score:\n")
                for i, (path, score, _) in enumerate(results_with_scores, 1):
                    f.write(f"  {i}. {path.name}: {score}%\n")
            logger.info("Ranking written to %s", rank_file)
        return

    if not args.resume:
        parser.error("Provide --resume PATH or --resume-dir PATH")
        return
    resume_path = Path(args.resume)
    if not resume_path.exists():
        logger.error("Resume not found: %s", resume_path)
        sys.exit(1)
    run_single(resume_path, jd_text, args.format, args.output)


if __name__ == "__main__":
    main()
