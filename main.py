import logging
import argparse
import os

from utils.conditions import Conditions
from utils.handle_logging import ColoredFormatter
from logging import StreamHandler

logging.root.handlers.clear()
handler = StreamHandler()
handler.setFormatter(ColoredFormatter())
logging.root.addHandler(handler)
logging.root.setLevel(logging.DEBUG)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the expert system.")
    parser.add_argument("config", type=str, help="Path to the configuration file")
    args = parser.parse_args()

    if not os.path.isfile(args.config):
        logging.error(f"File '{args.config}' does not exist.")
        exit(1)

    logging.info(f"Using configuration file: {args.config}")

    with open(args.config, "r") as file:
        config_data = file.read()

    config_lines = [
        line.strip()
        for line in config_data.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

    and_condition = Conditions.and_operation(True, False)
    logging.info(f"AND condition evaluation result: {and_condition}")

    or_condition = Conditions.or_operation(True, False)
    logging.info(f"OR condition evaluation result: {or_condition}")

    xor_condition = Conditions.xor_operation(True, False)
    logging.info(f"XOR condition evaluation result: {xor_condition}")

    not_condition = Conditions.not_operation(True)
    logging.info(f"NOT condition evaluation result: {not_condition}")
