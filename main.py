import logging
import argparse
import os

from conditions.and_condition import AndCondition
# from conditions.or_condition import OrCondition
# from conditions.xor_condition import XorCondition
# from conditions.not_condition import NotCondition
from logging import StreamHandler
from handle_logging import ColoredFormatter

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

    and_condition = AndCondition(*config_lines)
    result = and_condition.evaluate()

    logging.info(f"AND condition evaluation result: {result}")
