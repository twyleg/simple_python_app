# Copyright (C) 2024 twyleg
# fmt: off
import argparse
import importlib
import logging
import re
from typing import List
from logging import ERROR, WARNING, INFO, DEBUG

from pathlib import Path

from simple_python_app.generic_application import GenericApplication

from fixtures import valid_custom_logging_config, project_dir, print_tmp_path, valid_custom_logging_config_with_alternative_name_in_alternative_directory


#
# General naming convention for unit tests:
#               test_INITIALSTATE_ACTION_EXPECTATION
#


FILE_DIR = Path(__file__).parent


def log_file_exists(log_file_filepath: Path) -> bool:
    return log_file_filepath.is_file()


def log_file_filename_format_is_correct(log_file_filepath: Path) -> bool:
    p = re.compile(r"^\d{14}_\S+?\.log$")
    return p.match(log_file_filepath.name) is not None


def log_file_contains_string(filepath: Path, string: str) -> bool:
    with open(filepath, 'r') as f:
        p = re.compile(string)
        file_content = f.read()
        res = re.findall(p, file_content)
        return len(res) != 0


def log_file_contains_test_log_line_on_levels(log_file_filepath: Path, levels: List[int]) -> bool:
    for level in levels:
        if not log_file_contains_string(log_file_filepath, f"\\[{logging.getLevelName(level)}\\]\\[test_application\\]: test log line"):
            return False
    return True


def log_file_not_containing_log_lines_on_levels(log_file_filepath: Path, levels: List[int]) -> bool:
    for level in levels:
        if log_file_contains_string(log_file_filepath, logging.getLevelName(level)):
            return False
    return True


class BaseTestApplication(GenericApplication):
    def __init__(self, **kwargs):
        super().__init__(
            application_name="test_application",
            version="0.0.1",
            application_config_init_enabled=False,
            **kwargs
        )

    def run(self, argparser: argparse.ArgumentParser):
        self.logm.error("test log line")
        self.logm.warning("test log line")
        self.logm.info("test log line")
        self.logm.debug("test log line")


class DefaultLoggingApplication(BaseTestApplication):
    def __init__(self):
        super().__init__(
            logging_init_custom_logging_enabled=False
        )


class DefaultVerboseLoggingApplication(BaseTestApplication):
    def __init__(self):
        super().__init__(
            logging_init_custom_logging_enabled=False,
            logging_force_log_level=logging.DEBUG
        )


class CustomLoggingWithExplicitConfigApplication(BaseTestApplication):
    def __init__(self):
        super().__init__(
            logging_config_filepath=Path.cwd() / "logging.yaml"
        )


class CustomLoggingWithoutExplicitConfigApplication(BaseTestApplication):
    def __init__(self):
        super().__init__()


class CustomLoggingWithExplicitConfigSearchDirectoriesAndFilenamesApplication(BaseTestApplication):
    def __init__(self):
        super().__init__(
            logging_config_search_paths=[Path.cwd(), Path.cwd() / "subdir"],
            logging_config_search_filenames=["foo.log", "alternative_logging_config.yaml"]
        )


class TestDefaultLogging:

    def test_DefaultLoggingApplication_StartApplication_DefaultLoggingConfigLoaded(
            self,
            caplog,
            project_dir,
            valid_custom_logging_config
    ):
        test_app = DefaultLoggingApplication()
        test_app.start([])

        assert test_app.logging_config_type == GenericApplication.LoggingConfigType.DEFAULT
        assert test_app.logging_config_filepath != valid_custom_logging_config
        assert log_file_exists(test_app.logging_logfile_filepath)
        assert log_file_filename_format_is_correct(test_app.logging_logfile_filepath)
        assert log_file_contains_test_log_line_on_levels(test_app.logging_logfile_filepath, [ERROR, WARNING, INFO])
        assert log_file_not_containing_log_lines_on_levels(test_app.logging_logfile_filepath, [DEBUG])

    def test_DefaultLoggingApplication_StartApplicationWithVerboseFlag_DefaultLoggingConfigLoaded(
            self,
            caplog,
            project_dir,
            valid_custom_logging_config
    ):
        test_app = DefaultLoggingApplication()
        test_app.start(["-vv"])

        assert test_app.logging_config_type == GenericApplication.LoggingConfigType.DEFAULT
        assert test_app.logging_config_filepath != valid_custom_logging_config
        assert log_file_exists(test_app.logging_logfile_filepath)
        assert log_file_filename_format_is_correct(test_app.logging_logfile_filepath)
        assert log_file_contains_test_log_line_on_levels(test_app.logging_logfile_filepath, [ERROR, WARNING, INFO, DEBUG])

    def test_DefaultVerboseLoggingApplication_StartApplication_DefaultLoggingConfigWithDebugLogLevelLoaded(
            self,
            caplog,
            project_dir,
            valid_custom_logging_config
    ):
        test_app = DefaultVerboseLoggingApplication()
        test_app.start([])

        assert test_app.logging_config_type == GenericApplication.LoggingConfigType.DEFAULT
        assert test_app.logging_config_filepath != valid_custom_logging_config
        assert log_file_exists(test_app.logging_logfile_filepath)
        assert log_file_filename_format_is_correct(test_app.logging_logfile_filepath)
        assert log_file_contains_test_log_line_on_levels(test_app.logging_logfile_filepath, [ERROR, WARNING, INFO, DEBUG])

class TestCustomLogging:

    def test_CustomLoggingWithExplicitConfigFileApplication_StartApplication_CustomLoggingConfigLoaded(
            self,
            caplog,
            project_dir,
            valid_custom_logging_config
    ):
        test_app = CustomLoggingWithExplicitConfigApplication()
        test_app.start([])

        assert test_app.logging_config_type == GenericApplication.LoggingConfigType.CUSTOM
        assert test_app.logging_config_filepath == valid_custom_logging_config
        assert log_file_exists(test_app.logging_logfile_filepath)
        assert log_file_filename_format_is_correct(test_app.logging_logfile_filepath)
        assert log_file_contains_test_log_line_on_levels(test_app.logging_logfile_filepath, [ERROR, WARNING, INFO])
        assert log_file_not_containing_log_lines_on_levels(test_app.logging_logfile_filepath, [DEBUG])

    def test_CustomLoggingWithExplicitConfigFileApplication_StartApplicationWithVerboseFlag_CustomLoggingConfigLoaded(
            self,
            caplog,
            project_dir,
            valid_custom_logging_config
    ):
        test_app = CustomLoggingWithExplicitConfigApplication()
        test_app.start(["-vv"])

        assert test_app.logging_config_type == GenericApplication.LoggingConfigType.CUSTOM
        assert test_app.logging_config_filepath == valid_custom_logging_config
        assert log_file_exists(test_app.logging_logfile_filepath)
        assert log_file_filename_format_is_correct(test_app.logging_logfile_filepath)
        assert log_file_contains_test_log_line_on_levels(test_app.logging_logfile_filepath, [ERROR, WARNING, INFO, DEBUG])

    def test_CustomLoggingWithoutExplicitConfigFileApplication_StartApplication_CustomLoggingConfigFoundAndLoaded(
            self,
            caplog,
            project_dir,
            valid_custom_logging_config
    ):
        test_app = CustomLoggingWithExplicitConfigApplication()
        test_app.start([])

        assert test_app.logging_config_type == GenericApplication.LoggingConfigType.CUSTOM
        assert test_app.logging_config_filepath == valid_custom_logging_config
        assert log_file_exists(test_app.logging_logfile_filepath)
        assert log_file_filename_format_is_correct(test_app.logging_logfile_filepath)
        assert log_file_contains_test_log_line_on_levels(test_app.logging_logfile_filepath, [ERROR, WARNING, INFO])
        assert log_file_not_containing_log_lines_on_levels(test_app.logging_logfile_filepath, [DEBUG])

    def test_CustomLoggingWithExplicitConfigSearchDirectoriesAndFilenames_StartApplication_CustomLoggingConfigFoundAndLoaded(
            self,
            caplog,
            project_dir,
            valid_custom_logging_config,
            valid_custom_logging_config_with_alternative_name_in_alternative_directory
    ):
        test_app = CustomLoggingWithExplicitConfigSearchDirectoriesAndFilenamesApplication()
        test_app.start([])

        assert test_app.logging_config_type == GenericApplication.LoggingConfigType.CUSTOM
        assert test_app.logging_config_filepath == valid_custom_logging_config_with_alternative_name_in_alternative_directory
        assert log_file_exists(test_app.logging_logfile_filepath)
        assert log_file_filename_format_is_correct(test_app.logging_logfile_filepath)
        assert log_file_contains_test_log_line_on_levels(test_app.logging_logfile_filepath, [ERROR, WARNING, INFO])
        assert log_file_not_containing_log_lines_on_levels(test_app.logging_logfile_filepath, [DEBUG])


class TestVerboseSystemInformationLogging:

    def test_DefaultVeroseLoggingApplication_StartApplication_VerboseSystemInformationLogged(
            self,
            caplog,
            project_dir,
            valid_custom_logging_config
    ):
        test_app = DefaultVerboseLoggingApplication()
        test_app.start([])

        assert log_file_contains_string(test_app.logging_logfile_filepath,
                                        r"\[DEBUG\]\[simple_python_app.generic_application\]: - simple_python_app framework version = ")
        assert log_file_contains_string(test_app.logging_logfile_filepath,
                                        r"\[DEBUG\]\[simple_python_app.generic_application\]: - python version = ")
        assert log_file_contains_string(test_app.logging_logfile_filepath,
                                        r"\[DEBUG\]\[simple_python_app.generic_application\]: - pid = ")
