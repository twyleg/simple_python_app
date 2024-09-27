# Copyright (C) 2024 twyleg
import argparse
import time
from pathlib import Path

from simple_python_app.subcommand_application import SubcommandApplication


FILE_DIR = Path(__file__).parent


class SubcommandApplicationCounterExample(SubcommandApplication):
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
        count_up_command = self.add_subcommand("count up", self.handle_count_up)
        count_down_command = self.add_subcommand("count down", self.handle_count_down)

        for command in [count_up_command, count_down_command]:
            command.parser.add_argument("--start", type=int, default=0, help="Counter start")
            command.parser.add_argument("--end", type=int, default=None, help="Counter end (infinite by default)")
            command.parser.add_argument("--delay", type=float, default=1.0, help="Delay in seconds (float)")

    def handle_count_up(self, args: argparse.Namespace) -> int:
        i = args.start
        while True:
            self.logm.info("%d", i)
            i += 1
            if args.end and i > args.end:
                break
            time.sleep(args.delay)
        return 0

    def handle_count_down(self, args: argparse.Namespace) -> int:
        i = args.start
        while True:
            self.logm.info("%d", i)
            i -= 1
            if args.end and i < args.end:
                break
            time.sleep(args.delay)
        return 0


if __name__ == "__main__":
    subcommand_application_counter_example = SubcommandApplicationCounterExample()
    subcommand_application_counter_example.start()
