from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import List, Optional

from src.parsing import LexerError, ParserError, ValidationError, parse_program
from src.utils.program_logging import log_program, Colors
from src.exec import solve
from src.exec.exec_context import ExecContext
from src.exec.status import Status


class _ColorFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": Colors.BLUE,
        "INFO": Colors.GREEN,
        "WARNING": Colors.YELLOW,
        "ERROR": Colors.RED,
        "CRITICAL": Colors.MAGENTA,
    }
    RESET = Colors.RESET

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
    parser.add_argument("--interactive", "-i", action="store_true", help="Enable interactive fact modification mode")
    parser.add_argument("--reasoning", "-r", action="store_true", help="Enable natural language reasoning explanations")
    args = parser.parse_args(argv)

    config_path = Path(args.config)
    if not config_path.is_file():
        logging.error("File '%s' does not exist.", config_path)
        return 1

    logging.info("Using configuration file: %s", config_path)

    config_data = config_path.read_text(encoding="utf-8")
    try:
        program = parse_program(config_data)
    except (LexerError, ParserError, ValidationError) as error:
        logging.error("Failed to parse '%s': %s", config_path, error)
        return 1

    log_program(program)

    # Interactive mode loop
    if args.interactive:
        from src.bonus.interactive import run_interactive_mode
        return run_interactive_mode(program, config_data)

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

    _display_results(ctx, results, program, config_data, args.reasoning)
    return 0


def _display_results(ctx: ExecContext, results, program, config_data: str, reasoning: bool = False) -> int:
    """Display reasoning, contradictions, and results."""
    # Display contradictions if any were detected
    if hasattr(ctx, 'contradictions') and ctx.contradictions:
        print("")
        error_color = Colors.RED
        warning_color = Colors.YELLOW
        reset = Colors.RESET
        print(f"{error_color}{'=' * 60}{reset}")
        print(f"{error_color}CONTRADICTIONS DETECTED{reset}")
        print(f"{error_color}{'=' * 60}{reset}")
        for contradiction in ctx.contradictions:
            print(f"{warning_color}{contradiction}{reset}")
        print(f"{error_color}{'=' * 60}{reset}")
        print("")
        logging.error("Cannot provide reliable results due to contradictions in the rule base.")
        return 1

    # Display natural language reasoning if enabled
    if reasoning:
        from src.bonus.reasoning_visualization import visualize_reasoning
        visualize_reasoning(ctx, program, results)
        return 0

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

    _log_evaluation_results(program, config_data)


def _log_evaluation_results(program, config_data: str = "") -> None:
    """Display which operators are used in the rule file."""
    import src.exec as exec_module

    logging.info("")
    header_color = Colors.MAGENTA
    label_color = Colors.CYAN
    true_color = Colors.GREEN
    false_color = Colors.RED
    reset = Colors.RESET

    logging.info("%sOperators used in rules%s", header_color, reset)

    def _colorize(value: bool) -> str:
        return f"{true_color}{value}{reset}" if value else f"{false_color}{value}{reset}"

    def _log(label: str, value: bool) -> None:
        logging.info("%s%s%s: %s", label_color, label, reset, _colorize(value))

    # Check if operators are actually used in the rules
    def has_operator_in_condition(cond, operator_type) -> bool:
        """Recursively check if a condition contains a specific operator."""
        if isinstance(cond, operator_type):
            return True
        if isinstance(cond, (exec_module.AndCondition, exec_module.OrCondition, exec_module.XorCondition)):
            return has_operator_in_condition(cond.left, operator_type) or has_operator_in_condition(cond.right, operator_type)
        if isinstance(cond, exec_module.NotCondition):
            return has_operator_in_condition(cond.condition, operator_type)
        return False

    has_and = False
    has_or = False
    has_xor = False
    has_not = False

    for rule in program.rules:
        # Check condition
        if has_operator_in_condition(rule.condition, exec_module.AndCondition):
            has_and = True
        if has_operator_in_condition(rule.condition, exec_module.OrCondition):
            has_or = True
        if has_operator_in_condition(rule.condition, exec_module.XorCondition):
            has_xor = True
        if has_operator_in_condition(rule.condition, exec_module.NotCondition):
            has_not = True

        # Check conclusion
        if has_operator_in_condition(rule.conclusion, exec_module.AndCondition):
            has_and = True
        if has_operator_in_condition(rule.conclusion, exec_module.OrCondition):
            has_or = True
        if has_operator_in_condition(rule.conclusion, exec_module.XorCondition):
            has_xor = True
        if has_operator_in_condition(rule.conclusion, exec_module.NotCondition):
            has_not = True

    _log("AND", has_and)
    _log("OR", has_or)
    _log("XOR", has_xor)
    _log("NOT", has_not)

    # Check for IIF operator in source (it's expanded to two rules during parsing)
    has_iif = "<=>" in config_data if config_data else False
    _log("IIF", has_iif)


def run_cli(argv: Optional[List[str]] = None) -> int:
    """Entry point used by main.py and tests."""
    exit_code = _run(argv)
    if argv is None:
        raise SystemExit(exit_code)
    return exit_code


__all__ = ["run_cli", "_display_results"]
