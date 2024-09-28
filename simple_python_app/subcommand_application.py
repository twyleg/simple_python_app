# Copyright (C) 2024 twyleg
import argparse
import logging
import traceback
from argparse import ArgumentParser, Namespace, _SubParsersAction
from typing import Dict, Union, Callable, List

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import NestedCompleter, WordCompleter
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.styles import Style

from simple_python_app.generic_application import GenericApplication


logm = logging.getLogger(__name__)


class Command:

    class SubcommandNotAvailableError(Exception):
        pass

    CommandDict = Dict[str, Union[None, "CommandDict"]] | None | WordCompleter
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

    def commands_to_dict(self) -> CommandDict | WordCompleter:

        def get_argument_list() -> List[str]:
            arguments: List[str] = []
            for action in self.parser._actions:
                for option_string in action.option_strings:
                    arguments.append(option_string)
            return arguments

        command_dict = {subcommand_name: subcommand.commands_to_dict() for subcommand_name, subcommand in self.subcommands.items()}
        argument_dict = {argument: None for argument in get_argument_list()}
        merged_dict = command_dict | argument_dict
        return merged_dict if len(merged_dict) else None

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
        raise Command.SubcommandNotAvailableError()

    def add_subcommand(self, command: str, help: str = "", description: str = "", handler: Handler | None = None) -> "Command":
        command_chain = command.split(" ")

        if len(command_chain) == 1:

            if self.subparser is None:
                self.subparser = self.parser.add_subparsers(required=self.handler is None, title="subcommands")

            # Handle help manually to avoid automatic exit when not desired (e.g. in shell mode)
            parser = self.subparser.add_parser(command, add_help=False, description=description, help=help)
            # fmt: off
            parser.add_argument(
                "-h",
                "--help",
                help="Show help",
                action=GenericApplication.CustomHelpAction
            )
            # fmt: on

            subcommand = Command(parser, handler)
            self.subcommands[command] = subcommand
            return subcommand

        else:
            next_command = command_chain[0]
            remaining_commands = " ".join(command_chain[1:])
            if next_command not in self.subcommands:
                self.add_subcommand(next_command)
            return self.subcommands[next_command].add_subcommand(remaining_commands, help, description, handler)


class RootCommand(Command):
    pass


class SubcommandApplication(GenericApplication):
    # fmt: off
    def __init__(self,
                 shell_enabled: bool = True,
                 **kwargs):
        # fmt: on
        super().__init__(**kwargs)
        self.shell_enabled = shell_enabled

        self.root_command = RootCommand(self._arg_parser, self._handle_root_command if self.shell_enabled else None)

    def _handle_root_command(self, args: argparse.Namespace) -> int:
        prompt_style = Style.from_dict(
            {
                # Default style.
                "": "#ff1618 bold",
                # Prompt.
                "prompt": "#1dcf84 italic",
            }
        )

        prompt_fragments = [
            ("class:prompt", f"{self.application_name} $ "),
        ]

        completer = NestedCompleter.from_nested_dict(self.root_command.commands_to_dict())  # type: ignore
        session = PromptSession(history=InMemoryHistory(), completer=completer)  # type: ignore

        while True:
            try:
                subcommand_string = session.prompt(prompt_fragments, style=prompt_style)  # type: ignore
            except (KeyboardInterrupt, EOFError):
                logm.info("Exiting...")
                return 0

            if subcommand_string:
                try:
                    logm.debug("Entered command: %s", subcommand_string)
                    self._args = self._arg_parser.parse_args(subcommand_string.split(" "))
                    self._args.handler(self._args)
                except KeyboardInterrupt as e:
                    logm.info("Command aborted...")
                except Command.SubcommandNotAvailableError as e:
                    print(f"Command unavailable: '{subcommand_string}'")
                except (GenericApplication.CustomHelpAction.HelpRequested, GenericApplication.CustomVersionAction.VersionRequested):
                    pass
                except BaseException as e:
                    logm.error("%s: %s", e.__class__.__name__, e)
                    logm.debug(traceback.format_exc())

    def add_subcommand(self, command: str, help: str, description: str, handler: Command.Handler) -> Command:
        return self.root_command.add_subcommand(command, help, description, handler)

    def run(self, args: argparse.Namespace):
        return args.handler(args)
