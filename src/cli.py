from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import List, Optional

from version import __version__

from src.parsing import LexerError, ParserError, ValidationError, parse_program
from src.utils.conditions import Conditions
from src.utils.program_logging import log_program
from src.exec import solve
from src.exec.exec_context import ExecContext
from src.exec.status import Status


class _ColorFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\033[94m",  # Blue
        "INFO": "\033[92m",  # Green
        "WARNING": "\033[93m",  # Yellow
        "ERROR": "\033[91m",  # Red
        "CRITICAL": "\033[95m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        if not record.getMessage():
            return ""
        color = self.COLORS.get(record.levelname, self.RESET)
        base = super().format(record)
        return f"{color}{base}{self.RESET}"


_handler = logging.StreamHandler()
_handler.setFormatter(_ColorFormatter("[%(levelname)s] %(message)s"))
logging.basicConfig(level=logging.INFO, handlers=[_handler])


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
    try:
        program = parse_program(config_data)
    except (LexerError, ParserError, ValidationError) as error:
        logging.error("Failed to parse '%s': %s", config_path, error)
        return 1

    log_program(program)

    # Build execution context and run the program
    try:
        ctx = ExecContext.from_program(program)
    except Exception as error:
        logging.error("Failed to build execution context: %s", error)
        return 1

    try:
        results = solve.run_queries(ctx)
    except Exception as error:
        logging.error("Execution error: %s", error)
        return 1

    # Log actual evaluation results from exec
    logging.info("")
    header_color = "\033[95m"
    reset = "\033[0m"
    logging.info("%sExecution results%s", header_color, reset)

    true_color = "\033[92m"
    false_color = "\033[91m"
    undetermined_color = "\033[93m"  # Yellow for undetermined

    def _colorize(status: Status) -> str:
        if status is Status.TRUE:
            return f"{true_color}TRUE{reset}"
        elif status is Status.FALSE:
            return f"{false_color}FALSE{reset}"
        elif status is Status.UNDETERMINED:
            return f"{undetermined_color}UNDETERMINED{reset}"
        else:
            return f"{status.name}"

    for label, status in results.items():
        logging.info("%s: %s", label, _colorize(status))

    _log_evaluation_results()
    return 0


def _log_evaluation_results() -> None:
    logging.info("")
    header_color = "\033[95m"
    label_color = "\033[96m"
    true_color = "\033[92m"
    false_color = "\033[91m"
    reset = "\033[0m"

    logging.info("%sEvaluation summary%s", header_color, reset)

    def _colorize(value: bool) -> str:
        return f"{true_color}{value}{reset}" if value else f"{false_color}{value}{reset}"

    def _log(label: str, value: bool) -> None:
        logging.info("%s%s%s: %s", label_color, label, reset, _colorize(value))

    # Demonstrate logical operations for logging purposes, not actual program evaluation
    and_condition = Conditions.and_operation(True, False)
    _log("AND result", and_condition)

    or_condition = Conditions.or_operation(True, False)
    _log("OR result", or_condition)

    xor_condition = Conditions.xor_operation(True, False)
    _log("XOR result", xor_condition)

    not_condition = Conditions.not_operation(True)
    _log("NOT result", not_condition)

    logging.info("")
    logging.info("Program ready for evaluation.")


def run_cli(argv: Optional[List[str]] = None) -> int:
    """Entry point used by main.py and tests."""
    exit_code = _run(argv)
    if argv is None:
        raise SystemExit(exit_code)
    return exit_code


__all__ = ["run_cli"]
