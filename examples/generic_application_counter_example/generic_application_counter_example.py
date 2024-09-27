# Copyright (C) 2024 twyleg
import argparse
import time
from pathlib import Path

from simple_python_app.generic_application import GenericApplication


FILE_DIR = Path(__file__).parent


class GenericApplicationCounterExample(GenericApplication):
    def __init__(self):
        super().__init__(
            application_name="simple_counter_app_example",
            version="0.0.1",
            application_config_schema_filepath=FILE_DIR / "resources/config/simple_counter_app_config_schema.json",
            application_config_filepath=FILE_DIR / "resources/config/simple_counter_app_config.json",
            logging_config_filepath=FILE_DIR / "resources/config/logging.yaml",
            logging_logfile_output_dir=FILE_DIR / "logs/",
        )

    def add_arguments(self, argparser: argparse.ArgumentParser):
        argparser.add_argument("--start", type=int, default=0, help="Counter start")
        argparser.add_argument("--end", type=int, default=None, help="Counter end (infinite by default)")
        argparser.add_argument("--delay", type=float, default=1.0, help="Delay in seconds (float)")

    def run(self, args: argparse.Namespace):
        i = args.start
        while True:
            self.logm.info("%d", i)
            i += 1
            if args.end and i > args.end:
                break
            time.sleep(args.delay)
        return 0


if __name__ == "__main__":
    generic_application_counter_example = GenericApplicationCounterExample()
    generic_application_counter_example.start()
