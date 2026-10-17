# ==========================================================================
# File: buttons.py
# Description: File containing different buttons functions for the PROTEUS
#              application
# Date: 29/05/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------


# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

from PyQt6.QtWidgets import (
    QWidget,
    QToolButton,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, QSize

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.application.resources.icons import Icons, ProteusIconType
from proteus.application.resources.themes import Themes
from proteus.model import ProteusClassTag
from proteus.model.object import Object
from proteus.application.resources.translator import translate as _


# --------------------------------------------------------------------------
# Functions
# --------------------------------------------------------------------------

# Main menu buttons
def main_menu_button(
    parent: QWidget, text: str = "", icon_key: str = "", tooltip: str = "", statustip: str = "", enabled: bool = True, shortcut: str = ""
) -> QToolButton:
    """
    Creates a create archetype button adapted to the PROTEUS application style.
    """
    # Create button with parent
    create_button = QToolButton(parent)
    create_button.setMinimumWidth(55)

    # Store the icon key as a dynamic property so components can re-apply
    # the icon when the theme changes (live theme switching).
    create_button.setProperty("icon_key", icon_key)

    # Set file icon
    button_icon = Icons().icon(ProteusIconType.MainMenu, icon_key)
    create_button.setIcon(button_icon)
    icon_size: int = Themes().metric("icon_size_button", 32)
    create_button.setIconSize(button_icon.actualSize(QSize(icon_size, icon_size)))

    # Set tooltip and status tip
    if tooltip:
        create_button.setToolTip(_(tooltip))

    if statustip:
        create_button.setStatusTip(_(statustip))

    # Set text
    if text:
        create_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        create_button.setText(_(text))
    else:
        create_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)

    # Set initial disabled value
    create_button.setEnabled(enabled)

    # Set shortcut
    if shortcut:
        create_button.setShortcut(shortcut)

    return create_button


# --------------------------------------------------------------------------
def button_group(buttons, section_name_code=None):
    # Create the main widget
    widget = QWidget()

    # Create the grid layout
    layout = QGridLayout(widget)

    # Add the buttons in the first row of the layout
    for column, button in enumerate(buttons):
        layout.addWidget(button, 0, column)

    if section_name_code is not None:
        # Add a centered label with the text "section" in the second row of the layout
        section_label = QLabel(_(section_name_code))
        section_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(section_label, 1, 0, 1, len(buttons))

    # Set layout settings
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
    layout.setSpacing(0)

    return widget


# --------------------------------------------------------------------------
def archetype_button_group(buttons) -> QWidget:
    # Create the main widget
    widget = QWidget()
    widget.setObjectName("archetype_button_group")

    # Create the grid layout
    layout = QHBoxLayout(widget)

    # Add the buttons in the first row of the layout
    for button in buttons:
        layout.addWidget(button)

    # Set layout settings
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
    layout.setSpacing(0)

    # Create a scroll area and set its widget
    scroll_area = QScrollArea()
    scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll_area.setSizePolicy(
        QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
    )
    scroll_area.setWidgetResizable(True)
    scroll_area.setWidget(widget)

    # Set up the scroll bar
    scroll_bar = scroll_area.horizontalScrollBar()
    scroll_bar.setSingleStep(20)

    return scroll_area


# --------------------------------------------------------------------------
def get_separator(vertical: bool = False) -> QFrame:
    """
    Returns a horizontal or vertical separator.

    :param vertical: If True, the separator will be vertical. If False, the
                        separator will be horizontal.
    """
    separator = QFrame()
    if vertical:
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setObjectName("v-separator")
    else:
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setObjectName("h-separator")
    separator.setFrameShadow(QFrame.Shadow.Sunken)
    return separator


# --------------------------------------------------------------------------
# Classes
# --------------------------------------------------------------------------


# NOTE: ArchetypesMenuDropdown is set as menu for each button in the
# MainMenu component when the application is initialized.
class ArchetypeMenuButton(QToolButton):
    """
    Class that creates a button for the archetype menu. The dropdown menu
    is created in the MainMenu component using the ArchetypesMenuDropdown
    class.
    """

    def __init__(self, parent: QWidget, object_class: ProteusClassTag) -> None:
        super().__init__(parent)

        # No menu variables
        self.archetype: Object = None
        self.contains_only_one_archetype: bool = False

        # Store the object class so the icon can be re-applied when the
        # theme changes (live theme switching).
        self.object_class: ProteusClassTag = object_class

        # Button settings
        self.setObjectName("archetype_menu_button")
        self.setSizePolicy(
            QSizePolicy.Policy.Minimum, QSizePolicy.Policy.MinimumExpanding
        )
        self.setMinimumWidth(90)

        # Set icon
        archetype_icon = QIcon()

        # Add icon
        archetype_icon = Icons().icon(ProteusIconType.Archetype, object_class)
        self.setIcon(archetype_icon)
        icon_size: int = Themes().metric("icon_size_button", 32)
        self.setIconSize(QSize(icon_size, icon_size))

        # Set tooltip
        translated_name = _(
            f"archetype.class.{object_class}",
            alternative_text=object_class,
            allow_new_line_characters=True,
        )
        self.setToolTip(translated_name)

        # Set text
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.setText(translated_name)

        # Set enabled initial value
        self.setEnabled(False)

    def single_archetype_mode(self, archetype: Object) -> None:
        """
        Sets the button to single archetype mode, disabling the dropdown menu.
        """
        self.contains_only_one_archetype = True
        self.archetype = archetype
