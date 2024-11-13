# Copyright (C) 2024 twyleg
# fmt: off
import argparse
from pathlib import Path

from simple_python_app.generic_application import GenericApplication

from fixtures import print_tmp_path, valid_custom_logging_config, project_dir

#
# General naming convention for unit tests:
#               test_INITIALSTATE_ACTION_EXPECTATION
#


FILE_DIR = Path(__file__).parent


class BaseTestApplication(GenericApplication):
    def __init__(self, **kwargs):
        super().__init__(
            application_name="test_application",
            version="0.0.1",
            logging_init_default_logging_enabled=False,  # Caution: This is necessary because otherwise log init will
            logging_init_custom_logging_enabled=False,   # remove pytest handler and caplog won't work.
            application_config_init_enabled=False,
            **kwargs
        )

    def run(self, argparser: argparse.ArgumentParser) -> None:
        pass


class TestCli:
    def test_NoArgument_Started_SuccessfullReturnCode(self, caplog, project_dir):
        test_app = BaseTestApplication()
        assert test_app.start([]) == 0

    def test_PrintVersion_Started_VersionPrintedSuccessfullReturnCode(self, caplog, project_dir):
        test_app = BaseTestApplication()
        assert test_app.start(["--version"]) == 0
