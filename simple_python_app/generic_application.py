# Copyright (C) 2024 twyleg
import getpass
import json
import logging
import logging.config
import argparse
import os
import platform
import sys
import jsonschema
import yaml
from collections import namedtuple
from importlib import metadata
from datetime import datetime
from pathlib import Path
from enum import Enum
from typing import Callable, Any, Dict, List, Tuple

from simple_python_app import __version__


logm = logging.getLogger(__name__)

FILE_DIR = Path(__file__).parent


class GenericApplication:
    ApplicationConfig = Dict[str, Any]

    class LoggingConfigType(Enum):
        DEFAULT = 1
        CUSTOM = 2

    class ConfigFilepathSource(Enum):
        CLI_ARG = 1
        EXPLICIT = 2
        SEARCH = 3

    class CustomHelpAction(argparse.Action):

        class HelpRequested(Exception):
            pass

        # fmt: off
        def __init__(self,
                     option_strings,
                     dest=argparse.SUPPRESS,
                     default=argparse.SUPPRESS,
                     help=None):
            super().__init__(
                option_strings=option_strings,
                dest=dest,
                default=default,
                nargs=0,
                help=help
            )
            # fmt: on

        def __call__(self, parser, namespace, values, option_string=None):
            parser.print_help()
            raise self.HelpRequested

    class CustomVersionAction(argparse.Action):

        class VersionRequested(Exception):
            pass

        # fmt: off
        def __init__(self,
                     option_strings,
                     version=None,
                     dest=argparse.SUPPRESS,
                     default=argparse.SUPPRESS,
                     help=None):
            if help is None:
                help = "show program's version number and exit"
            super().__init__(
                option_strings=option_strings,
                dest=dest,
                default=default,
                nargs=0,
                help=help
            )
            # fmt: on
            self.version = version

        def __call__(self, parser, namespace, values, option_string=None):
            version = self.version
            if version is None:
                version = parser.version
            formatter = parser._get_formatter()
            formatter.add_text(version)
            parser._print_message(formatter.format_help(), sys.stdout)
            raise self.VersionRequested

    Config = namedtuple(
        "Config",
        [
            "logging_force_log_level",
            "logging_init_custom_logging_enabled",
            "logging_init_default_logging_enabled",
            "logging_config_filepath",
            "logging_config_search_paths",
            "logging_config_search_filenames",
            "logging_default_config_filepath",
            "logging_default_format",
            "logging_default_date_format",
            "logging_logfile_output_dir",
            "logging_logfile_filename",
            "application_config_init_enabled",
            "application_config_schema_filepath",
            "application_config_filepath",
            "application_config_search_paths",
            "application_config_search_filenames",
        ],
    )

    def __init__(
        self,
        application_name: str,
        version: str,
        logging_force_log_level: None | int = None,
        logging_init_custom_logging_enabled=True,
        logging_init_default_logging_enabled=True,
        logging_config_filepath: None | Path = None,
        logging_config_search_paths: None | List[Path] = None,
        logging_config_search_filenames: None | List[str] = None,
        logging_default_config_filepath: None | Path = None,
        logging_default_format: None | str = None,
        logging_default_date_format: None | str = None,
        logging_logfile_output_dir: None | Path = None,
        logging_logfile_filename: None | str = None,
        application_config_init_enabled=True,
        application_config_schema_filepath: None | Path = None,
        application_config_filepath: Path | None = None,
        application_config_search_paths: List[Path] | None = None,
        application_config_search_filenames: List[str] | None = None,
    ):
        self.config = GenericApplication.Config(
            logging_force_log_level=logging_force_log_level,
            logging_init_custom_logging_enabled=logging_init_custom_logging_enabled,
            logging_init_default_logging_enabled=logging_init_default_logging_enabled,
            logging_config_filepath=logging_config_filepath,
            logging_config_search_paths=logging_config_search_paths,
            logging_config_search_filenames=logging_config_search_filenames,
            logging_default_config_filepath=logging_default_config_filepath,
            logging_default_format=logging_default_format,
            logging_default_date_format=logging_default_date_format,
            logging_logfile_output_dir=logging_logfile_output_dir,
            logging_logfile_filename=logging_logfile_filename,
            application_config_init_enabled=application_config_init_enabled,
            application_config_schema_filepath=application_config_schema_filepath,
            application_config_filepath=application_config_filepath,
            application_config_search_paths=application_config_search_paths,
            application_config_search_filenames=application_config_search_filenames,
        )

        self._arg_parser = argparse.ArgumentParser(prog=f"{application_name}", exit_on_error=False, add_help=False)
        self._args: None | argparse.Namespace = None
        self._subparser = None
        self._add_arguments_method_available = hasattr(self, "add_arguments") and callable(self.add_arguments)
        self._run_method_available = hasattr(self, "run") and callable(self.run)

        self._custom_init_stage_one_methods: List[Callable] = []
        self._custom_init_stage_two_methods: List[Callable] = []
        self._custom_init_stage_three_methods: List[Callable] = []

        self.application_name = application_name
        self.version = version
        self.logm = logging.getLogger(application_name)

        self.application_config_schema_filepath: None | Path = None
        self.application_config_filepath_source: None | GenericApplication.ConfigFilepathSource = None
        self.application_config_filepath: None | Path = None
        self.application_config_search_paths = (
            self.config.application_config_search_paths
            if (self.config.application_config_search_paths)
            else self.__get_application_config_default_search_paths()
        )
        self.application_config_search_filenames = (
            self.config.application_config_search_filenames
            if (self.config.application_config_search_filenames)
            else self.__get_application_config_default_search_filenames()
        )
        self.application_config: None | GenericApplication.ApplicationConfig = None

        self.logging_logfile_filepath: None | Path = None
        self.logging_config_type: None | GenericApplication.LoggingConfigType = None
        self.logging_config_filepath_source: None | GenericApplication.ConfigFilepathSource = None
        self.logging_config_filepath: None | Path = None
        self.logging_config_search_paths = (
            self.config.logging_config_search_paths if (self.config.logging_config_search_paths) else self.__get_logging_config_default_search_paths()
        )
        self.logging_config_search_filenames = (
            self.config.logging_config_search_filenames
            if (self.config.logging_config_search_filenames)
            else self.__get_logging_config_default_search_filenames()
        )

    def __get_application_config_default_search_paths(self) -> List[Path]:
        return [Path.cwd(), Path.home()]

    def __get_application_config_default_search_filenames(self) -> List[str]:
        return [
            f"{self.application_name}_config.json",
            f".{self.application_name}_config.json",
        ]

    def __get_logging_config_default_search_paths(self) -> List[Path]:
        return [Path.cwd(), Path.home()]

    def __get_logging_config_default_search_filenames(self) -> List[str]:
        return [
            "logging.yaml",
            "logging.yml",
            f"{self.application_name}_logging.yaml",
            f"{self.application_name}_logging.yml",
        ]

    def __exit(self, error=False) -> None:
        if error:
            logm.error("Exiting! (exit_code=-1)")
            sys.exit(-1)
        else:
            logm.debug("Exiting! (exit_code=0)")
            sys.exit(0)

    def __init_argparse(self, argv: List[str] | None) -> None:
        # fmt: off

        # Handle help manually to avoid automatic exit when not desired (e.g. in shell mode)
        self._arg_parser.add_argument(
            "-h",
            "--help",
            help="Show help",
            action=self.CustomHelpAction
        )

        self._arg_parser.add_argument(
            "-v",
            "--version",
            help="Show version and exit",
            action=self.CustomVersionAction,
            version=self.version,
        )

        self._arg_parser.add_argument(
            "-vv",
            "--verbose",
            help="Run with verbose logging (debug level). Incompatible with -q/--quiet!",
            action="store_true"
        )

        self._arg_parser.add_argument(
            "-q",
            "--quiet",
            help="Run quietly without unnecessary outputs. Incompatible with -v/--verbose!",
            action="store_true"
        )

        self._arg_parser.add_argument(
            "--logging-config",
            help="Logging config file to use.",
            type=str,
            default=None
        )

        self._arg_parser.add_argument(
            "--logging-dir",
            help="Application config file to use.",
            type=str,
            default=None
        )

        self._arg_parser.add_argument(
            "-c",
            "--config",
            help="Application config file to use.",
            type=str,
            default=None
        )
        # fmt: on

        try:
            if self._add_arguments_method_available:
                self.add_arguments(self._arg_parser)  # type: ignore[attr-defined]

            self._args, _ = self._arg_parser.parse_known_args(argv)

            if self._args.verbose and self._args.quiet:
                raise argparse.ArgumentError(None, "-v/--verbose and -q/--quiet are incompatible!")

        except argparse.ArgumentError as e:
            # Handle exit on error manually to avoid automatic exit in shell mode
            self.__init_default_logging()
            logm.error("Error during argument parsing:")
            logm.error(e)
            self.__exit(error=True)
        except (SystemExit, self.CustomHelpAction.HelpRequested, self.CustomVersionAction.VersionRequested):
            self.__exit(error=False)
        except BaseException as e:
            self.__init_default_logging()
            logm.error('Error during user "add_arguments()" method:', self.config.logging_config_filepath)
            logm.error(e)
            self.__exit(error=True)

    def __get_log_level(self) -> int | None:
        if self._args.verbose:  # type: ignore[union-attr]
            return logging.DEBUG
        elif self.config.logging_force_log_level:
            return self.config.logging_force_log_level
        else:
            return None

    def __get_logfile_filepath(self) -> Path:
        def get_logfile_filename() -> str:
            if self.config.logging_logfile_filename:
                return self.config.logging_logfile_filename
            else:
                return "{:%Y%m%d%H%M%S}_{}.log".format(datetime.now(), self.application_name)

        def get_logfile_output_dir() -> Path:
            if self._args.logging_dir:  # type: ignore[union-attr]
                return Path(self._args.logging_dir)  # type: ignore[union-attr]
            elif self.config.logging_logfile_output_dir:
                return self.config.logging_logfile_output_dir
            else:
                return Path.cwd()

        logfile_output_dir = get_logfile_output_dir()
        logfile_filename = get_logfile_filename()

        logfile_output_dir.mkdir(parents=True, exist_ok=True)

        return logfile_output_dir / logfile_filename

    @classmethod
    def find_file(cls, search_paths: List[Path], filenames: List[str]) -> Path | None:
        for search_path in search_paths:
            for filename in filenames:
                potential_logging_config_filepath = search_path / filename
                if potential_logging_config_filepath.exists():
                    return potential_logging_config_filepath
        return None

    @classmethod
    def __set_log_level(cls, config_dict: Dict[str, Any], log_level: int) -> None:
        level_name = logging.getLevelName(log_level)
        if "handlers" in config_dict:
            for handler in config_dict["handlers"].values():
                handler["level"] = level_name
        if "loggers" in config_dict:
            for logger in config_dict["loggers"].values():
                logger["level"] = level_name
        if "root" in config_dict:
            config_dict["root"]["level"] = level_name

    @classmethod
    def __set_file_handler_filename(cls, config_dict: Dict[str, Any], logfile_filepath: Path) -> None:
        if "handlers" in config_dict:
            for handler in config_dict["handlers"].values():
                if "class" in handler and handler["class"] == "logging.FileHandler":
                    handler["filename"] = logfile_filepath

    @classmethod
    def __init_logging(cls, config_filepath: Path, logfile_filepath: Path | None = None, force_log_level: None | int = None) -> None:
        with open(config_filepath, "r") as f:
            d = yaml.safe_load(f)

            if force_log_level:
                cls.__set_log_level(d, force_log_level)

            if logfile_filepath:
                cls.__set_file_handler_filename(d, logfile_filepath)

            logging.config.dictConfig(d)

    def __init_custom_logging(self) -> None:
        def find_logging_config_filepath() -> Tuple[Path | None, GenericApplication.ConfigFilepathSource]:
            if self._args.logging_config:  # type: ignore[union-attr]
                return self._args.logging_config, GenericApplication.ConfigFilepathSource.CLI_ARG  # type: ignore[union-attr]
            elif self.config.logging_config_filepath:
                return self.config.logging_config_filepath, GenericApplication.ConfigFilepathSource.EXPLICIT
            else:
                return (
                    self.find_file(self.logging_config_search_paths, self.logging_config_search_filenames),
                    GenericApplication.ConfigFilepathSource.SEARCH,
                )

        forced_log_level = self.__get_log_level()
        logfile_filepath = self.__get_logfile_filepath()
        logging_custom_config_filepath, logging_custom_config_filepath_source = find_logging_config_filepath()

        if logging_custom_config_filepath:
            try:
                self.__init_logging(logging_custom_config_filepath, logfile_filepath=logfile_filepath, force_log_level=forced_log_level)
                self.logging_config_type = GenericApplication.LoggingConfigType.CUSTOM
                self.logging_logfile_filepath = logfile_filepath
                self.logging_config_filepath = logging_custom_config_filepath
                self.logging_config_filepath_source = logging_custom_config_filepath_source
            except (ValueError, TypeError, AttributeError, ImportError) as e:
                self.__init_default_logging()
                logm.error("Error reading logging config (%s):", self.config.logging_config_filepath)
                logm.error(e)
                self.__exit(error=True)
        else:
            self.__init_default_logging()

    def __init_default_logging(self) -> None:
        forced_log_level = self.__get_log_level()
        logfile_filepath = self.__get_logfile_filepath()
        default_logging_config_filepath = (
            self.config.logging_default_config_filepath if self.config.logging_default_config_filepath else FILE_DIR / "resources/default_logging_config.yaml"
        )

        self.__init_logging(default_logging_config_filepath, logfile_filepath=logfile_filepath, force_log_level=forced_log_level)
        self.logging_config_type = GenericApplication.LoggingConfigType.DEFAULT
        self.logging_logfile_filepath = logfile_filepath
        self.logging_config_filepath = default_logging_config_filepath

    def __init_application_config(self) -> None:
        def find_application_config_filepath() -> Tuple[Path | None, GenericApplication.ConfigFilepathSource]:
            if self._args.config:  # type: ignore[union-attr]
                return self._args.config, GenericApplication.ConfigFilepathSource.CLI_ARG  # type: ignore[union-attr]
            elif self.config.application_config_filepath:
                return self.config.application_config_filepath, GenericApplication.ConfigFilepathSource.EXPLICIT
            else:
                return (
                    self.find_file(self.application_config_search_paths, self.application_config_search_filenames),
                    GenericApplication.ConfigFilepathSource.SEARCH,
                )

        self.application_config_filepath, self.application_config_filepath_source = find_application_config_filepath()

        if self.application_config_filepath:
            try:
                with open(self.application_config_filepath) as config_file:
                    config = json.load(config_file)

                    if self.config.application_config_schema_filepath:
                        with open(self.config.application_config_schema_filepath) as json_schema_file:
                            config_schema = json.load(json_schema_file)
                            jsonschema.validate(instance=config, schema=config_schema)

                    self.application_config = config

            except BaseException as e:
                logm.error("Error reading application config (%s):", self.application_config_filepath)
                logm.error("Application config filepath source (%s):", self.application_config_filepath_source)
                logm.error(e)
                self.__exit(error=True)
        else:
            logm.error("Unable to find application config in the following directories with the following filenames:")
            logm.error("Directories: %s", self.application_config_search_paths)
            logm.error("Filenames: %s", self.application_config_search_filenames)
            self.__exit(error=True)

    def __init_stage_one(self, argv: List[str] | None) -> None:
        """
        Init Stage One:

            First init stage doesn't depend on any user input, configs or anything else that needs be loaded
            at runtime.

            Init components:
            - argparse
        """

        self.__init_argparse(argv)

        for custom_init_stage_one_method in self._custom_init_stage_one_methods:
            custom_init_stage_one_method()

    def __init_stage_two(self) -> None:
        """
        Init Stage Two:

            Second init stage takes runtime configs etc. into account
            at runtime.

            Init components:
            - custom logging OR default logging
            - application config
        """

        if self.config.logging_init_custom_logging_enabled:
            self.__init_custom_logging()
        elif self.config.logging_init_default_logging_enabled:
            self.__init_default_logging()

        if self.config.application_config_init_enabled:
            self.__init_application_config()

        for custom_init_stage_two_method in self._custom_init_stage_two_methods:
            custom_init_stage_two_method()

    def __init_stage_three(self) -> None:
        """
        Init Stage Three:

            Third init stage prints information. From this point on, log lines are provided.
        """
        logm.debug("********************************************")
        logm.debug("simple_python_application framework started!")
        logm.debug("********************************************")

        logm.debug("system information:")
        logm.debug("- simple_python_app framework version = %s", __version__)
        logm.debug("- python version = %s", sys.version)
        logm.debug("- operating system = %s", platform.platform())
        logm.debug("- hostname = %s", platform.node())

        logm.debug("environment information:")
        logm.debug("- venv activated = %s", sys.prefix != sys.base_prefix)
        logm.debug("- prefix = %s", sys.prefix)
        logm.debug("- base prefix = %s", sys.base_prefix)
        logm.debug("- pythonpath = [")
        for path in sys.path:
            logm.debug("    %s", path)
        logm.debug("  ]")
        logm.debug("- modules = [")
        for dist in metadata.distributions():
            logm.debug("    %s==%s", dist.name, dist.version)
        logm.debug("  ]")

        logm.debug("process information:")
        logm.debug("- argv = %s", sys.argv)
        logm.debug("- pid = %d", os.getpid())
        if sys.platform != "win32":
            logm.debug("- user = %s (uid=%d,gid=%d)", getpass.getuser(), os.getuid(), os.getgid())
        else:
            logm.debug("- user = %s", os.getlogin())
        logm.debug("- cwd = %s", os.getcwd())
        logm.debug("- home dir = %s", Path.home())

        logm.debug("framework config:")
        logm.debug("- config parameter = [")
        for k, v in self.config._asdict().items():
            logm.debug("    %s = %s", k, v)
        logm.debug("  ]")
        logm.debug('- user "add_arguments()" method available = %s', self._add_arguments_method_available)

        logm.debug("logging config:")
        logm.debug("- logfile = %s", self.logging_logfile_filepath)
        logm.debug("- logging config type = %s", self.logging_config_type)
        logm.debug("- logging config filepath = %s", self.logging_config_filepath)
        logm.debug("- logging config filepath source = %s", self.logging_config_filepath_source)
        logm.debug("- logging config search paths = [")
        for logging_config_search_path in self.logging_config_search_paths:
            logm.debug("    %s", logging_config_search_path)
        logm.debug("  ]")
        logm.debug("- logging config search filenames = %s", self.logging_config_search_filenames)
        logm.debug(
            "- forced log level = %s",
            logging.getLevelName(self.config.logging_force_log_level) if self.config.logging_force_log_level else None,
        )

        logm.debug("application config:")
        logm.debug("- application config filepath = %s", self.application_config_filepath)
        logm.debug("- application config filepath source = %s", self.application_config_filepath_source)
        logm.debug("- application config search paths = [")
        for application_config_search_path in self.application_config_search_paths:
            logm.debug("    %s", application_config_search_path)
        logm.debug("  ]")
        logm.debug("- application config search filenames = %s", self.application_config_search_filenames)

        for custom_init_stage_three_method in self._custom_init_stage_three_methods:
            custom_init_stage_three_method()

    def add_custom_init_stage_one(self, custom_init_stage_method: Callable[[], None]) -> None:
        self._custom_init_stage_one_methods.append(custom_init_stage_method)

    def add_custom_init_stage_two(self, custom_init_stage_method: Callable[[], None]) -> None:
        self._custom_init_stage_two_methods.append(custom_init_stage_method)

    def add_custom_init_stage_three(self, custom_init_stage_method: Callable[[], None]) -> None:
        self._custom_init_stage_three_methods.append(custom_init_stage_method)

    def start(self, argv: List[str] | None = None) -> int:
        try:
            self.__init_stage_one(argv)
            self.__init_stage_two()
            self.__init_stage_three()

            logm.debug("********************************************")
            logm.debug("      Passing control to user code!")
            logm.debug("============================================")

            if self._run_method_available:
                if not self._args.quiet:  # type: ignore[union-attr]
                    self.logm.info("%s (version=%s) started!", self.application_name, self.version)
                ret = self.run(self._args)  # type: ignore[attr-defined]
                return ret if ret else 0
            else:
                logm.error('No "run(args)" method provided. Exiting!')
        except KeyboardInterrupt as e:
            logm.debug("Interrupted by user. Exiting...")
            return 0
        except SystemExit as e:
            ret = e.code
            if isinstance(ret, int):
                return ret
        except BaseException as e:
            logm.exception(e)
        return -1
