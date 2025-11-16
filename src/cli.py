from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import List, Optional

from version import __version__

from src.parsing import build_conditions, build_context, parse_config_sections
from src.utils import handle_logging  # noqa: F401 - configure logging on import
from src.utils.conditions import Conditions


def _run(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run the expert system.")
    parser.add_argument("config", type=str, help="Path to the configuration file")
    args = parser.parse_args(argv)

    config_path = Path(args.config)
    if not config_path.is_file():
        logging.error("File '%s' does not exist.", config_path)
        return 1

    logging.info("Expert System %s", __version__)
    logging.info("Using configuration file: %s", config_path)

    config_data = config_path.read_text(encoding="utf-8")
    sections = parse_config_sections(config_data)
    print(f'Sections: {sections}')
    context = build_context(sections["facts"])
    logging.debug("Initial context: %s", context)

    conditions = build_conditions(sections)
    if not conditions:
        logging.warning("No conditions found to evaluate.")
        return 0

    and_condition = Conditions.and_operation(True, False)
    logging.info("AND condition evaluation result: %s", and_condition)

    or_condition = Conditions.or_operation(True, False)
    logging.info("OR condition evaluation result: %s", or_condition)

    xor_condition = Conditions.xor_operation(True, False)
    logging.info("XOR condition evaluation result: %s", xor_condition)

    not_condition = Conditions.not_operation(True)
    logging.info("NOT condition evaluation result: %s", not_condition)

    logging.info("Processed %d condition(s).", len(conditions))
    return 0


def run_cli(argv: Optional[List[str]] = None) -> int:
    """Entry point used by main.py and tests."""
    exit_code = _run(argv)
    if argv is None:
        raise SystemExit(exit_code)
    return exit_code


__all__ = ["run_cli"]
