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
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose reasoning output")
    parser.add_argument("--interactive", "-i", action="store_true", help="Enable interactive fact modification mode")
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

    # Interactive mode loop
    if args.interactive:
        return _run_interactive_mode(program, args.verbose, config_data)

    # Build execution context and run the program
    try:
        ctx = ExecContext.from_program(program, verbose=args.verbose)
    except Exception as error:
        logging.error("Failed to build execution context: %s", error)
        return 1

    try:
        results = solve.run_queries(ctx)
    except Exception as error:
        logging.error("Execution error: %s", error)
        return 1

    _display_results(ctx, results, program, config_data, args.verbose)
    return 0


def _display_results(ctx: ExecContext, results, program, config_data: str, verbose: bool) -> int:
    """Display reasoning, contradictions, and results."""
    # Log verbose reasoning if enabled
    if verbose and hasattr(ctx, 'reasoning_log') and ctx.reasoning_log:
        print("")
        header_color = "\033[95m"
        reset = "\033[0m"
        print(f"{header_color}Reasoning Process{reset}")
        for line in ctx.reasoning_log:
            print(line)

    # Display contradictions if any were detected
    if hasattr(ctx, 'contradictions') and ctx.contradictions:
        print("")
        error_color = "\033[91m"
        warning_color = "\033[93m"
        reset = "\033[0m"
        print(f"{error_color}{'=' * 60}{reset}")
        print(f"{error_color}CONTRADICTIONS DETECTED{reset}")
        print(f"{error_color}{'=' * 60}{reset}")
        for contradiction in ctx.contradictions:
            print(f"{warning_color}{contradiction}{reset}")
        print(f"{error_color}{'=' * 60}{reset}")
        print("")
        logging.error("Cannot provide reliable results due to contradictions in the rule base.")
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

    _log_evaluation_results(program, config_data)


def _run_interactive_mode(program, verbose: bool, config_data: str) -> int:
    """Run the expert system in interactive mode, allowing fact modification."""
    from copy import deepcopy

    cyan = "\033[96m"
    green = "\033[92m"
    yellow = "\033[93m"
    red = "\033[91m"
    blue = "\033[94m"
    magenta = "\033[95m"
    reset = "\033[0m"
    bold = "\033[1m"

    # Store original facts
    original_facts = deepcopy(program.facts)
    current_facts = deepcopy(program.facts)

    print(f"\n{magenta}{'=' * 60}{reset}")
    print(f"{magenta}{bold}INTERACTIVE FACT VALIDATION MODE{reset}")
    print(f"{magenta}{'=' * 60}{reset}")
    print(f"{cyan}Commands:{reset}")
    print(f"  {green}set <symbol> <true|false>{reset} - Set a fact value")
    print(f"  {green}unset <symbol>{reset}            - Remove a fact")
    print(f"  {green}list{reset}                      - Show current facts")
    print(f"  {green}reset{reset}                     - Reset to original facts")
    print(f"  {green}run{reset}                       - Execute queries with current facts")
    print(f"  {green}help{reset}                      - Show this help")
    print(f"  {green}quit{reset} or {green}exit{reset}              - Exit interactive mode")
    print(f"{magenta}{'=' * 60}{reset}\n")

    while True:
        try:
            user_input = input(f"{blue}expert-system>{reset} ").strip()

            if not user_input:
                continue

            parts = user_input.split()
            command = parts[0].lower()

            if command in ["quit", "exit", "q"]:
                print(f"{yellow}Exiting interactive mode.{reset}")
                return 0

            elif command == "help":
                print(f"\n{cyan}Available commands:{reset}")
                print(f"  {green}set <symbol> <true|false>{reset} - Set a fact value")
                print(f"  {green}unset <symbol>{reset}           - Remove a fact")
                print(f"  {green}list{reset}                     - Show current facts")
                print(f"  {green}reset{reset}                    - Reset to original facts")
                print(f"  {green}run{reset}                      - Execute queries with current facts")
                print(f"  {green}help{reset}                     - Show this help")
                print(f"  {green}quit{reset} or {green}exit{reset}            - Exit interactive mode\n")

            elif command == "list":
                if current_facts:
                    print(f"\n{cyan}Current facts:{reset}")
                    for symbol, value in sorted(current_facts.items()):
                        color = green if value else red
                        print(f"  {symbol}: {color}{value}{reset}")
                else:
                    print(f"{yellow}No facts defined.{reset}")
                print()

            elif command == "reset":
                current_facts = deepcopy(original_facts)
                print(f"{green}Facts reset to original values.{reset}\n")

            elif command == "set":
                if len(parts) != 3:
                    print(f"{red}Usage: set <symbol> <true|false>{reset}\n")
                    continue

                symbol = parts[1].upper()
                value_str = parts[2].lower()

                if value_str not in ["true", "false"]:
                    print(f"{red}Value must be 'true' or 'false'{reset}\n")
                    continue

                if not symbol.isalpha() or len(symbol) != 1:
                    print(f"{red}Symbol must be a single uppercase letter{reset}\n")
                    continue

                current_facts[symbol] = value_str == "true"
                color = green if current_facts[symbol] else red
                print(f"{green}Set {symbol} = {color}{current_facts[symbol]}{reset}\n")

            elif command == "unset":
                if len(parts) != 2:
                    print(f"{red}Usage: unset <symbol>{reset}\n")
                    continue

                symbol = parts[1].upper()
                if symbol in current_facts:
                    del current_facts[symbol]
                    print(f"{green}Removed fact {symbol}{reset}\n")
                else:
                    print(f"{yellow}Fact {symbol} not found{reset}\n")

            elif command == "run":
                # Create a modified program with current facts
                modified_program = deepcopy(program)
                modified_program.facts = current_facts

                print(f"\n{magenta}Running queries with current facts...{reset}\n")

                try:
                    ctx = ExecContext.from_program(modified_program, verbose=verbose)
                    results = solve.run_queries(ctx)
                    _display_results(ctx, results, modified_program, config_data, verbose)
                except Exception as error:
                    print(f"{red}Execution error: {error}{reset}\n")

            else:
                print(f"{red}Unknown command: {command}{reset}")
                print(f"{cyan}Type 'help' for available commands{reset}\n")

        except KeyboardInterrupt:
            print(f"\n{yellow}Use 'quit' or 'exit' to leave interactive mode{reset}\n")
        except EOFError:
            print(f"\n{yellow}Exiting interactive mode.{reset}")
            return 0


def _log_evaluation_results(program, config_data: str = "") -> None:
    """Display which operators are used in the rule file."""
    import src.exec as exec_module

    logging.info("")
    header_color = "\033[95m"
    label_color = "\033[96m"
    true_color = "\033[92m"
    false_color = "\033[91m"
    reset = "\033[0m"

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


__all__ = ["run_cli"]
