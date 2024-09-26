import argparse
import sys
import time
from pathlib import Path

from simple_python_app.generic_application import GenericApplication
from simple_python_app.subcommands import Command, RootCommand

FILE_DIR = Path(__name__).parent


class SimpleExampleApplication(GenericApplication):
    def __init__(self):
        super().__init__(
            application_name="simple_example_application",
            version="0.0.1",
            application_config_schema_filepath=FILE_DIR / "simple_example_application_config_schema.json",
        )

    def add_arguments(self, argparser: argparse.ArgumentParser):
        root_command = RootCommand(argparser, self. handle_root_command)
        count_up_command = root_command.add_subcommand("count up", self.handle_count_up)
        count_down_command = root_command.add_subcommand("count down", self.handle_count_down)

        for command in [count_up_command, count_down_command]:
            command.parser.add_argument('--start', type=int, default=0, help="Counter start")
            command.parser.add_argument('--end', type=int, default=None, help="Counter end (infinite by default)")
            command.parser.add_argument('--delay', type=float, default=1.0, help="Delay in seconds (float)")

    def handle_root_command(self, args: argparse.Namespace) -> int:
        self.logm.info("Root command. Nothing to do!")
        return 0

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

    def run(self, args: argparse.Namespace):
        return args.handler(args)


if __name__ == "__main__":
    simple_example_application = SimpleExampleApplication()
    simple_example_application.start()
