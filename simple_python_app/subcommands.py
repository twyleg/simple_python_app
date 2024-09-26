# Copyright (C) 2024 twyleg
import logging
from argparse import ArgumentParser, Namespace, _SubParsersAction
from typing import Dict, Union, Callable


logm = logging.getLogger(__name__)


class SubcommandNotAvailableError(Exception):
    pass


class Command:

    CommandDict = Dict[str, Union[None, "CommandDict"]] | None
    Handler = Callable[[Namespace], int]

    def __init__(self, parser: ArgumentParser, handler: Handler | None = None):
        self.parser = parser
        self.subparser: _SubParsersAction | None = None
        self.subcommands: Dict[str, Command] = {}
        self.handler = handler
        if handler:
            self.parser.set_defaults(handler=handler)
        else:
            self.parser.set_defaults(handler=self.default_handler)

    def default_handler(self, args: Namespace) -> None:
        logm.error("Function not yet implemented!")

    def commands_to_dict(self) -> CommandDict:
        if len(self.subcommands):
            return {subcommand_name: subcommand.commands_to_dict() for subcommand_name, subcommand in self.subcommands.items()}
        else:
            return None

    def find_subcommand(self, command: str) -> "Command":
        command_chain = command.split(" ")

        if len(command_chain) == 1:
            if command in self.subcommands:
                return self.subcommands[command]
        else:
            next_command = command_chain[0]
            remaining_commands = " ".join(command_chain[1:])
            if next_command in self.subcommands:
                return self.subcommands[next_command].find_subcommand(remaining_commands)
        raise SubcommandNotAvailableError()

    def add_subcommand(self, command: str, handler: Handler | None = None) -> "Command":
        command_chain = command.split(" ")

        if len(command_chain) == 1:

            if self.subparser is None:
                self.subparser = self.parser.add_subparsers(required=self.handler is None, title="subcommands")

            parser = self.subparser.add_parser(command)
            subcommand = Command(parser, handler)
            self.subcommands[command] = subcommand
            return subcommand

        else:
            next_command = command_chain[0]
            remaining_commands = " ".join(command_chain[1:])
            if next_command not in self.subcommands:
                self.add_subcommand(next_command)
            return self.subcommands[next_command].add_subcommand(remaining_commands, handler)


class RootCommand(Command):
    pass


# class RootCommand(Command):
#     def __init__(self):
#         super().__init__(argparse.ArgumentParser(usage="classroom_utils"))
#
#     def handle(self, args: argparse.Namespace):
#         pass
#
#     def parse(self, args=None) -> argparse.Namespace:
#         if args is None:
#             args = sys.argv[1:]
#         return self.parser.parse_args(args)
