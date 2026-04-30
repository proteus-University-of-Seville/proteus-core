# ==========================================================================
# File: confest.py
# Description: pytest configuration for PROTEUS application tests
# Date: 01/05/2026
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

import pytest

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.tests import PROTEUS_SAMPLE_DATA_PATH
from proteus.application.configuration.config import Config


CONFIG_TEST_FILES = {
    "test_app_settings.py",
    "test_config.py",
}
TEST_CONFIG_FILE = "proteus.tests.ini"

@pytest.fixture(autouse=True)
def app_settings_test_config(monkeypatch, request):
    """
    Force normal tests to load app settings from the test configuration file.

    Config is intentionally not reset for tests already using the test config,
    because loading it again is expensive.

    Config tests files are skipped because they mock their own settings on
    demand.
    """
    is_config_test = request.node.path.name in CONFIG_TEST_FILES

    if is_config_test:
        yield
        Config._instances.pop(Config, None)
        return

    config = Config._instances.get(Config)
    if (
        config is not None
        and config.app_settings is not None
        and config.app_settings.settings_file_path.name != TEST_CONFIG_FILE
    ):
        Config._instances.pop(Config, None)

    monkeypatch.setattr(
        "proteus.application.configuration.app_settings.Path.cwd",
        lambda: PROTEUS_SAMPLE_DATA_PATH,
    )
    monkeypatch.setattr(
        "proteus.application.configuration.app_settings.CONFIG_FILE",
        TEST_CONFIG_FILE,
    )

    yield
