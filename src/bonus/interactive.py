"""Interactive fact validation mode for the expert system.

This module provides an interactive REPL interface that allows users to:
- Modify facts without editing source files
- Test different scenarios interactively
- Clarify undetermined facts from OR/XOR conclusions
- Explore "what-if" situations
"""

from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.parsing.parser import Program

from src.utils.program_logging import Colors


def run_interactive_mode(program: "Program", config_data: str) -> int:
    """
    Run the expert system in interactive mode, allowing fact modification.

    Args:
        program: The parsed program with rules, facts, and queries
        config_data: Original source code (for operator detection)

    Returns:
        Exit code (0 for success)
    """
    from src.exec.exec_context import ExecContext
    from src.exec import solve

    cyan = Colors.CYAN
    green = Colors.GREEN
    yellow = Colors.YELLOW
    red = Colors.RED
    blue = Colors.BLUE
    magenta = Colors.MAGENTA
    reset = Colors.RESET
    bold = Colors.BOLD

    # Store original facts
    original_facts = deepcopy(program.facts)
    current_facts = deepcopy(program.facts)

    _print_welcome_message(cyan, green, magenta, reset, bold)

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
                _print_help(cyan, green, reset)

            elif command == "list":
                _list_facts(current_facts, cyan, green, red, yellow, reset)

            elif command == "reset":
                current_facts = deepcopy(original_facts)
                print(f"{green}Facts reset to original values.{reset}\n")

            elif command == "set":
                _handle_set_command(parts, current_facts, green, red, reset)

            elif command == "unset":
                _handle_unset_command(parts, current_facts, green, red, yellow, reset)

            elif command == "run":
                _handle_run_command(
                    program, current_facts, config_data,
                    magenta, red, reset
                )

            else:
                print(f"{red}Unknown command: {command}{reset}")
                print(f"{cyan}Type 'help' for available commands{reset}\n")

        except KeyboardInterrupt:
            print(f"\n{yellow}Use 'quit' or 'exit' to leave interactive mode{reset}\n")
        except EOFError:
            print(f"\n{yellow}Exiting interactive mode.{reset}")
            return 0


def _print_welcome_message(cyan: str, green: str, magenta: str, reset: str, bold: str) -> None:
    """Print the welcome message for interactive mode."""
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


def _print_help(cyan: str, green: str, reset: str) -> None:
    """Print the help message."""
    print(f"\n{cyan}Available commands:{reset}")
    print(f"  {green}set <symbol> <true|false>{reset} - Set a fact value")
    print(f"  {green}unset <symbol>{reset}           - Remove a fact")
    print(f"  {green}list{reset}                     - Show current facts")
    print(f"  {green}reset{reset}                    - Reset to original facts")
    print(f"  {green}run{reset}                      - Execute queries with current facts")
    print(f"  {green}help{reset}                     - Show this help")
    print(f"  {green}quit{reset} or {green}exit{reset}            - Exit interactive mode\n")


def _list_facts(current_facts: dict, cyan: str, green: str, red: str, yellow: str, reset: str) -> None:
    """List all current facts."""
    if current_facts:
        print(f"\n{cyan}Current facts:{reset}")
        for symbol, value in sorted(current_facts.items()):
            color = green if value else red
            print(f"  {symbol}: {color}{value}{reset}")
    else:
        print(f"{yellow}No facts defined.{reset}")
    print()


def _handle_set_command(parts: list, current_facts: dict, green: str, red: str, reset: str) -> None:
    """Handle the 'set' command to modify a fact."""
    if len(parts) != 3:
        print(f"{red}Usage: set <symbol> <true|false>{reset}\n")
        return

    symbol = parts[1].upper()
    value_str = parts[2].lower()

    if value_str not in ["true", "false"]:
        print(f"{red}Value must be 'true' or 'false'{reset}\n")
        return

    if not symbol.isalpha() or len(symbol) != 1:
        print(f"{red}Symbol must be a single uppercase letter{reset}\n")
        return

    current_facts[symbol] = value_str == "true"
    color = green if current_facts[symbol] else red
    print(f"{green}Set {symbol} = {color}{current_facts[symbol]}{reset}\n")


def _handle_unset_command(parts: list, current_facts: dict, green: str, red: str, yellow: str, reset: str) -> None:
    """Handle the 'unset' command to remove a fact."""
    if len(parts) != 2:
        print(f"{red}Usage: unset <symbol>{reset}\n")
        return

    symbol = parts[1].upper()
    if symbol in current_facts:
        del current_facts[symbol]
        print(f"{green}Removed fact {symbol}{reset}\n")
    else:
        print(f"{yellow}Fact {symbol} not found{reset}\n")


def _handle_run_command(
    program: "Program",
    current_facts: dict,
    config_data: str,
    magenta: str,
    red: str,
    reset: str
) -> None:
    """Handle the 'run' command to execute queries with current facts."""
    from src.exec.exec_context import ExecContext
    from src.exec import solve
    from src.cli import _display_results

    # Create a modified program with current facts
    modified_program = deepcopy(program)
    modified_program.facts = current_facts

    print(f"\n{magenta}Running queries with current facts...{reset}\n")

    try:
        ctx = ExecContext.from_program(modified_program)
        results = solve.run_queries(ctx)
        _display_results(ctx, results, modified_program, config_data, reasoning=False)
    except Exception as error:
        print(f"{red}Execution error: {error}{reset}\n")


__all__ = ["run_interactive_mode"]
