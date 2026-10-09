"""Command Line Interface (CLI) for KDMC MyNet HTTP Report Automation.

Provides commands for single-date proof of concept testing, batch report generation,
and date iteration previewing.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional, Sequence

from app.auth import SessionExpiredError, SessionManager
from app.batch_runner import BatchRunner
from app.client import KDMCClient
from app.config import AppConfig, load_config
from app.date_engine import HTTPDateEngine, parse_date_string
from app.logging_config import setup_logging
from app.pdf_export import (
    get_target_file_path,
    render_html_to_pdf,
    save_debug_html,
)
from app.report_parser import ReportParser

logger = logging.getLogger("flash_automator.cli")


def cmd_test_date(args: argparse.Namespace, config: AppConfig) -> int:
    """Execute Phase 3: Single-date proof of concept."""
    logger.info(f"--- Running Single-Date Proof of Concept for {args.date} ---")

    # Validate date format
    try:
        parsed_date = parse_date_string(args.date)
        date_str = parsed_date.strftime("%d/%m/%Y")
    except ValueError as e:
        logger.error(f"Invalid date argument: {e}")
        return 1

    # Override config options from CLI flags if given
    if args.output_dir:
        config.output_dir = Path(args.output_dir)
    if args.save_html:
        config.save_html = True
    if args.overwrite:
        config.overwrite = True

    session_mgr = SessionManager(
        session_cookie=config.session_cookie,
        csrf_token=config.csrf_token,
    )

    if not session_mgr.has_session_cookie:
        logger.warning(
            "No session cookie (JSESSIONID) configured in environment or .env. "
            "Municipal portal requests may fail or redirect to Login.html. "
            "Set KDMC_SESSION_COOKIE in .env to use an authorized session."
        )

    client = KDMCClient(config=config, session_manager=session_mgr)

    # 1. Acquire / verify CSRF token
    if not session_mgr.csrf_token:
        logger.info("Attempting to acquire CSRF token from portal...")
        client.refresh_csrf_token()

    # 2. Check target output path and duplicate protection
    target_path, already_exists = get_target_file_path(
        output_dir=config.output_dir,
        date_input=parsed_date,
        overwrite=config.overwrite,
    )
    if already_exists and not config.overwrite:
        logger.warning(
            f"File already exists: {target_path}. "
            "Use --overwrite to re-download and replace."
        )
        return 0

    # 3. Submit request
    try:
        logger.info(f"Submitting verified report POST request for date {date_str}...")
        resp = client.fetch_report(date_str)
    except SessionExpiredError as e:
        logger.error(f"Session Authentication Failed: {e}")
        return 2
    except Exception as e:
        logger.error(f"HTTP Request Failed: {e}")
        return 1

    logger.info(f"HTTP Status: {resp.status_code} ({len(resp.content)} bytes received)")

    # 4. Save debug HTML if enabled
    if config.save_html:
        saved_debug = save_debug_html(resp.text, config.debug_dir, date_str)
        logger.info(f"Saved raw response HTML to: {saved_debug}")

    # 5. Validate response structure
    val_res = ReportParser.validate_response(resp.text)
    if not val_res.is_valid:
        logger.error(f"Response Validation Failed: {val_res.error_message}")
        return 1

    if val_res.is_empty:
        logger.info(
            f"Result: Date {date_str} returned no bank statement records "
            f"({val_res.error_message})"
        )
        return 0

    logger.info(
        f"Validation Passed! Found valid report table titled '{val_res.title}' "
        f"with {val_res.record_count} account balance rows."
    )

    # 6. Extract clean HTML and generate PDF
    try:
        clean_html = ReportParser.extract_clean_printable_html(resp.text)
        pdf_path = render_html_to_pdf(clean_html, target_path)
        logger.info(f"Successfully generated PDF report: {pdf_path}")
        logger.info(f"Size: {pdf_path.stat().st_size:,} bytes | Destination: {pdf_path.resolve()}")
    except Exception as e:
        logger.error(f"PDF Export Failed: {e}")
        return 1

    logger.info("--- Single-date test completed successfully ---")
    return 0


def cmd_batch(args: argparse.Namespace, config: AppConfig) -> int:
    """Execute Phase 6: Sequential Batch Runner."""
    logger.info(f"--- Running Batch Statement Automation from {args.start} to {args.end} ---")

    # Override config options
    if args.output_dir:
        config.output_dir = Path(args.output_dir)
    if args.delay is not None:
        config.request_delay = float(args.delay)
    if args.save_html:
        config.save_html = True
    if args.overwrite:
        config.overwrite = True

    # Parse exclusions
    excluded_dates = []
    if args.exclude_dates:
        excluded_dates = [d.strip() for d in args.exclude_dates.split(",") if d.strip()]

    excluded_weekdays = set()
    if args.skip_sundays:
        excluded_weekdays.add(6)
    if args.skip_saturdays:
        excluded_weekdays.add(5)

    try:
        date_engine = HTTPDateEngine(
            start_date=args.start,
            end_date=args.end,
            weekdays_only=args.weekdays_only,
            exclude_weekdays=sorted(list(excluded_weekdays)) if excluded_weekdays else None,
            exclude_dates=excluded_dates if excluded_dates else None,
        )
    except ValueError as e:
        logger.error(f"Invalid date range or parameters: {e}")
        return 1

    session_mgr = SessionManager(
        session_cookie=config.session_cookie,
        csrf_token=config.csrf_token,
    )
    client = KDMCClient(config=config, session_manager=session_mgr)

    runner = BatchRunner(
        client=client,
        config=config,
        date_engine=date_engine,
        resume=not args.no_resume,
    )

    results = runner.run()

    successes = sum(1 for r in results if r.status == "SUCCESS")
    skipped = sum(1 for r in results if r.status == "SKIPPED")
    no_records = sum(1 for r in results if r.status == "NO_RECORDS")
    errors = sum(1 for r in results if r.status == "ERROR")
    cancelled = sum(1 for r in results if r.status == "CANCELLED")

    logger.info("--- Batch Execution Summary ---")
    logger.info(f"Total Evaluated: {len(results)}")
    logger.info(f"Successful:      {successes}")
    logger.info(f"Skipped/Resumed: {skipped}")
    logger.info(f"No Records:      {no_records}")
    logger.info(f"Errors:          {errors}")
    if cancelled:
        logger.info(f"Cancelled:       {cancelled}")

    return 0 if errors == 0 else 1


def cmd_generate_dates(args: argparse.Namespace) -> int:
    """Preview evaluated date schedule."""
    excluded_dates = []
    if args.exclude_dates:
        excluded_dates = [d.strip() for d in args.exclude_dates.split(",") if d.strip()]

    excluded_weekdays = set()
    if args.skip_sundays:
        excluded_weekdays.add(6)
    if args.skip_saturdays:
        excluded_weekdays.add(5)

    try:
        date_engine = HTTPDateEngine(
            start_date=args.start,
            end_date=args.end,
            weekdays_only=args.weekdays_only,
            exclude_weekdays=sorted(list(excluded_weekdays)) if excluded_weekdays else None,
            exclude_dates=excluded_dates if excluded_dates else None,
        )
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    all_items = date_engine.get_all_items()
    included_count = sum(1 for item in all_items if item.is_included)
    skipped_count = len(all_items) - included_count

    print(f"Date Iteration Preview ({args.start} to {args.end}):")
    print(f"{'#':<4} {'Date':<12} {'Day':<11} {'Status':<10} {'Reason'}")
    print("-" * 65)

    for i, item in enumerate(all_items, 1):
        status = "INCLUDED" if item.is_included else "SKIPPED"
        reason = item.skip_reason or ""
        print(f"{i:<4} {item.date_str:<12} {item.weekday_name:<11} {status:<10} {reason}")

    print("-" * 65)
    print(f"Total: {len(all_items)} | Included: {included_count} | Skipped: {skipped_count}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build command line argument parser."""
    parser = argparse.ArgumentParser(
        prog="flash-automator",
        description="Flash Automator: KDMC MyNet Bank Account Statement HTTP Automation",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable debug-level logging",
    )
    parser.add_argument(
        "--env-file",
        type=str,
        default=None,
        help="Path to custom .env configuration file",
    )

    subparsers = parser.add_subparsers(dest="subcommand", help="Available subcommands")

    # Subcommand: test-date
    p_test = subparsers.add_parser("test-date", help="Execute single-date proof of concept")
    p_test.add_argument(
        "--date",
        type=str,
        required=True,
        help="Date to generate statement for (e.g. 10/10/2026)",
    )
    p_test.add_argument(
        "--save-html",
        action="store_true",
        help="Save raw response HTML to debug directory",
    )
    p_test.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory to save generated PDF (default: ./output)",
    )
    p_test.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing output PDF if present",
    )

    # Subcommand: batch
    p_batch = subparsers.add_parser("batch", help="Execute sequential batch report generation")
    p_batch.add_argument(
        "--start",
        type=str,
        required=True,
        help="Start date in DD/MM/YYYY format (e.g. 01/10/2026)",
    )
    p_batch.add_argument(
        "--end",
        type=str,
        required=True,
        help="End date in DD/MM/YYYY format (e.g. 31/10/2026)",
    )
    p_batch.add_argument(
        "--weekdays-only",
        action="store_true",
        help="Skip Saturdays and Sundays",
    )
    p_batch.add_argument(
        "--skip-sundays",
        action="store_true",
        help="Skip Sundays",
    )
    p_batch.add_argument(
        "--skip-saturdays",
        action="store_true",
        help="Skip Saturdays",
    )
    p_batch.add_argument(
        "--exclude-dates",
        type=str,
        default=None,
        help="Comma-separated dates to exclude (e.g. 15/10/2026,24/10/2026)",
    )
    p_batch.add_argument(
        "--delay",
        type=float,
        default=None,
        help="Polite pause delay between requests in seconds (default: 1.5)",
    )
    p_batch.add_argument(
        "--no-resume",
        action="store_true",
        help="Do not skip dates that already have valid PDFs",
    )
    p_batch.add_argument(
        "--save-html",
        action="store_true",
        help="Save raw HTML response files into debug folder",
    )
    p_batch.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory to save generated PDFs",
    )
    p_batch.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing output files",
    )

    # Subcommand: generate-dates
    p_gen = subparsers.add_parser("generate-dates", help="Preview date schedule without HTTP calls")
    p_gen.add_argument(
        "--start",
        type=str,
        required=True,
        help="Start date (DD/MM/YYYY)",
    )
    p_gen.add_argument(
        "--end",
        type=str,
        required=True,
        help="End date (DD/MM/YYYY)",
    )
    p_gen.add_argument(
        "--weekdays-only",
        action="store_true",
        help="Skip Saturdays and Sundays",
    )
    p_gen.add_argument(
        "--skip-sundays",
        action="store_true",
        help="Skip Sundays",
    )
    p_gen.add_argument(
        "--skip-saturdays",
        action="store_true",
        help="Skip Saturdays",
    )
    p_gen.add_argument(
        "--exclude-dates",
        type=str,
        default=None,
        help="Comma-separated dates to exclude",
    )

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Main CLI entrypoint."""
    parser = build_parser()
    args = parser.parse_args(argv)

    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(level=log_level)

    if not args.subcommand:
        parser.print_help()
        return 0

    if args.subcommand == "generate-dates":
        return cmd_generate_dates(args)

    config = load_config(args.env_file)

    if args.subcommand == "test-date":
        return cmd_test_date(args, config)
    elif args.subcommand == "batch":
        return cmd_batch(args, config)

    return 0


if __name__ == "__main__":
    sys.exit(main())
