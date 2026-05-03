# ==========================================================================
# File: test_icons.py
# Description: pytest file for the PROTEUS icons module
# Date: 01/04/2024
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

from typing import Generator, List
from pathlib import Path

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

import pytest
from PyQt6.QtGui import QIcon

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.tests import PROTEUS_SAMPLE_ICONS_PATH
from proteus.application.resources.icons import Icons, ProteusIconType


# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------
@pytest.fixture
def icons_object() -> Generator[Icons, None, None]:
    """
    Icons is defined as a singleton, it is necessary to 'reset' the object
    before and after each test to ensure that the tests are independent when
    executed in a batch.
    """

    Icons._instances.pop(Icons, None)
    yield Icons()
    Icons._instances.pop(Icons, None)


# --------------------------------------------------------------------------
# Unit tests
# --------------------------------------------------------------------------


def test_icons_singleton(icons_object: Icons):
    """
    Test that the Icons object is a singleton.
    """

    icons_object_2 = Icons()
    assert icons_object is icons_object_2


def test_icons_load_icons_min(icons_object: Icons):
    """
    Test that the icons are loaded correctly with a minimal example directory.

    icons.xml file constains just one icon.
    """

    icons_object.load_icons(PROTEUS_SAMPLE_ICONS_PATH / "icons_valid_min")
    assert (
        len(icons_object._icons_paths) == 1
    ), "No icons types were found in the 'icons.xml' file"

    icons: List[Path] = []
    for icon_type in icons_object._icons_paths:
        icons.extend(icons_object._icons_paths[icon_type])

    assert len(icons) == 1, "No icons were found in the 'icons.xml' file"


def test_icons_load_icons_all_types(icons_object: Icons):
    """
    Test that the icons are loaded correctly with all icon types.

    icons.xml file constains just one icon.
    """

    icons_object.load_icons(PROTEUS_SAMPLE_ICONS_PATH / "icons_all_types")
    assert (
        len(icons_object._icons_paths) == 4
    ), f"Expected 4 icons types but '{len(icons_object._icons_paths)}' were found in the 'icons.xml' file"

    icons: List[Path] = []
    for icon_type in icons_object._icons_paths:
        icons.extend(icons_object._icons_paths[icon_type])

    assert (
        len(icons) == 4
    ), f"Expected 4 icons but '{len(icons)}' were found in the 'icons.xml' file"


def test_icons_load_icons_empty(icons_object: Icons):
    """
    Test that the icons are loaded correctly with a directory that does not contain any icons.

    icons.xml file just have <icons></icons> tags.
    """

    icons_object.load_icons(PROTEUS_SAMPLE_ICONS_PATH / "icons_valid_empty")
    assert (
        len(icons_object._icons_paths) == 0
    ), "Icons types were found in the 'icons.xml' file"


@pytest.mark.parametrize("sample_dir", ["icons_missing_xml_file", "nonexistingdir"])
def test_icons_load_fail(icons_object: Icons, sample_dir: str):
    """
    Test that the load method returns False when the directory is not valid (missing file, non-existing directory)
    """

    succes: bool = icons_object.load_icons(PROTEUS_SAMPLE_ICONS_PATH / sample_dir)

    assert (
        not succes
    ), f"Icons were loaded from a directory that is not supposed to be valid, directory: '{sample_dir}'"


def test_icons_load_fail_none(icons_object: Icons):
    """
    Test that the load method returns False when the directory is None.
    """

    succes: bool = icons_object.load_icons(None)

    assert (
        not succes
    ), f"Icons were loaded from a directory that is not supposed to be valid, directory: 'None'"


def test_icons_load_missing_key(icons_object: Icons):
    """
    Test that an icon is not loaded if it is missing the 'key' attribute.
    """

    icons_object.load_icons(PROTEUS_SAMPLE_ICONS_PATH / "icons_missing_key")
    assert (
        len(icons_object._icons_paths) >= 1
    ), "Expected 1 or more icons types but none were found in the 'icons.xml' file"

    icons: List[Path] = []
    for icon_type in icons_object._icons_paths:
        icons.extend(icons_object._icons_paths[icon_type])

    assert (
        len(icons) == 0
    ), f"No valid icons expected to be found in the 'icons.xml' file but '{len(icons)}' were found"


def test_icons_load_missing_file_path(icons_object: Icons):
    """
    Test that an icon is not loaded if it is missing the 'file'(path) attribute.
    """

    icons_object.load_icons(PROTEUS_SAMPLE_ICONS_PATH / "icons_missing_file_path")
    assert (
        len(icons_object._icons_paths) >= 1
    ), "Expected 1 or more icons types but none were found in the 'icons.xml' file"

    icons: List[Path] = []
    for icon_type in icons_object._icons_paths:
        icons.extend(icons_object._icons_paths[icon_type])

    assert (
        len(icons) == 0
    ), f"No valid icons expected to be found in the 'icons.xml' file but '{len(icons)}' were found"


def test_icons_load_non_existing_file_path(icons_object: Icons):
    """
    Test that an icon is not loaded if the file path does not exist.
    """

    icons_object.load_icons(PROTEUS_SAMPLE_ICONS_PATH / "icons_non_existing_file_path")
    assert (
        len(icons_object._icons_paths) >= 1
    ), "Expected 1 or more icons types but none were found in the 'icons.xml' file"

    icons: List[Path] = []
    for icon_type in icons_object._icons_paths:
        icons.extend(icons_object._icons_paths[icon_type])

    assert (
        len(icons) == 0
    ), f"No valid icons expected to be found in the 'icons.xml' file but '{len(icons)}' were found"


def test_icon_path(icons_object: Icons):
    """
    Test that the icon path is returned correctly.
    """

    icons_object.load_icons(PROTEUS_SAMPLE_ICONS_PATH / "icons_sample")
    icon_path = icons_object.icon_path(ProteusIconType.App, "dummy")

    assert icon_path is not None, "Icon path is None"
    assert icon_path.exists(), "Icon path does not exist"
    assert icon_path.is_file(), "Icon path is not a file"
    assert icon_path.name == "dummy.jpg", "Icon path is not the expected file"


def test_icon_path_not_found_key_return_default(icons_object: Icons):
    """
    Test that the icon path is returned correctly when the key is not found.
    """

    icons_object.load_icons(PROTEUS_SAMPLE_ICONS_PATH / "icons_sample")
    icon_path = icons_object.icon_path(ProteusIconType.App, "non_existing_key")

    assert icon_path is not None, "Icon path is None"
    assert icon_path.exists(), "Icon path does not exist"
    assert icon_path.is_file(), "Icon path is not a file"
    assert icon_path.name == "default.jpg", "Icon path is not the expected file"


def test_icon_path_not_found_key_and_not_default(icons_object: Icons):
    """
    Test that the icon path is returned correctly when the key is not found and there is no default icon.
    """

    icons_object.load_icons(PROTEUS_SAMPLE_ICONS_PATH / "icons_all_types")
    icon_path = icons_object.icon_path(ProteusIconType.App, "non_existing_key")

    assert icon_path is None, "Icon path is not None"


def test_icon_path_incorrect_type(icons_object: Icons):
    """
    Test that the icon path is returned correctly when the icon type is incorrect.
    """

    icons_object.load_icons(PROTEUS_SAMPLE_ICONS_PATH / "icons_sample")
    icon_path = icons_object.icon_path("no-type")

    assert icon_path is None, "Icon path is not None"


# It is not possible to instantiate a QIcon from these sample icons files. Forcing QIcon() to be returned.
def test_icon_without_memo(mocker, icons_object: Icons):
    """
    Test that the QIcon is returned correctly the first time it is requested.
    """
    icons_object.load_icons(PROTEUS_SAMPLE_ICONS_PATH / "icons_sample")

    mocker.patch.object(icons_object, "icon_path", return_value=None)

    icon = icons_object.icon(ProteusIconType.App, "dummy")

    assert icon is not None, "Icon is None"
    assert isinstance(icon, QIcon), "Icon is not a QIcon object"
    icons_object.icon_path.assert_called_once_with(ProteusIconType.App, "dummy")

def test_icon_with_memo(mocker, icons_object: Icons):
    """
    Test that the QIcon is returned correctly the first time it is requested.
    """
    icons_object.load_icons(PROTEUS_SAMPLE_ICONS_PATH / "icons_sample")
    mocker.patch.object(icons_object, "icon_path", return_value=None)

    icons_object.icon(ProteusIconType.App, "dummy")
    icon = icons_object.icon(ProteusIconType.App, "dummy")

    assert icon is not None, "Icon is None"
    assert isinstance(icon, QIcon), "Icon is not a QIcon object"
    icons_object.icon_path.assert_called_once_with(ProteusIconType.App, "dummy")

