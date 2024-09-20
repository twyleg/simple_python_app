# Copyright (C) 2024 twyleg
import argparse
import time
from pathlib import Path

from simple_python_app.generic_application import GenericApplication


FILE_DIR = Path(__name__).parent


class SimpleExampleApplication(GenericApplication):
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
        argparser.add_argument("--delay", type=int, default=1000, help="Delay (millis) for counter")

    def run(self, args: argparse.Namespace):
        self.logm.info("Starting counter:")

        i = 0
        while True:
            self.logm.info("%d", i)
            i += 1
            time.sleep(args.delay / 1000.0)


if __name__ == "__main__":
    simple_example_application = SimpleExampleApplication()
    simple_example_application.start()
