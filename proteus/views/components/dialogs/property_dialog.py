# ==========================================================================
# File: property_dialog.py
# Description: PyQT6 properties form component for the PROTEUS application
# Date: 26/05/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

import logging
from typing import Union, List, Dict, Any

# --------------------------------------------------------------------------
# Third-party library imports
# --------------------------------------------------------------------------

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QTabWidget,
    QFormLayout,
    QGroupBox,
    QSizePolicy,
    QSpacerItem,
)

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.model import ProteusID, PROTEUS_NAME
from proteus.model.project import Project
from proteus.model.object import Object
from proteus.model.properties import Property
from proteus.application.resources.icons import Icons, ProteusIconType
from proteus.application.resources.translator import translate as _
from proteus.views.forms.properties.property_input import PropertyInput
from proteus.views.forms.properties.property_input_factory import (
    PropertyInputFactory,
    TraceInput,
    BooleanPropertyInput,
    DatePropertyInput,
    ClassListPropertyInput,
    FilePropertyInput,
    EnumPropertyInput,
)
from proteus.views.components.dialogs.base_dialogs import ProteusDialog
from proteus.controller.commands.clone_archetype_object import CloneArchetypeObjectCommand
from proteus.controller.command_stack import Controller

# Module configuration
log = logging.getLogger(__name__)  # Logger


# --------------------------------------------------------------------------
# Class: PropertyDialog
# Description: Class for the PROTEUS application properties form component.
# Date: 27/05/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# --------------------------------------------------------------------------
class PropertyDialog(ProteusDialog):
    """
    Class for the PROTEUS application properties form component. It is used
    to display the properties of an element in a form. Properties are grouped
    by categories in tabs. Each property is displayed in a widget that is
    created using the PropertyInputFactory class.
    """

    # ----------------------------------------------------------------------
    # Method     : __init__
    # Description: Class constructor, invoke the parents class constructors
    #              and create the component.
    # Date       : 27/05/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def __init__(
        self, element_id=None, delete_object_on_cancel: bool = False, *args, **kwargs
    ) -> None:
        """
        Class constructor, invoke the parents class constructors and create
        the component.

        Store the element id, reference to the element whose properties will
        be displayed, and the PropertyInput widgets in a dictionary.

        :param element_id: The id of the element to edit.
        :param delete_object_on_cancel: Boolean to delete the object on cancel.
        """
        super(PropertyDialog, self).__init__(*args, **kwargs)

        # Set the element id, reference to the element whose properties
        # will be displayed
        self.element_id: ProteusID = element_id
        self.delete_object_on_cancel: bool = delete_object_on_cancel
        self.project_dialog: bool = False

        # Create a dictionary to hold the input widgets for each property
        # NOTE: This is used to get the input values when the form is
        #       accepted
        self.input_widgets: Dict[str, PropertyInput] = {}

        # Store the category tabs that has been opened so the focus is set just once
        self.opened_tabs: List[int] = []

        # Create the component
        self.create_component()

    # ----------------------------------------------------------------------
    # Method     : create_component
    # Description: Create the component.
    # Date       : 27/05/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def create_component(self) -> None:
        """
        Create the dialog component. This method is called from the constructor.

        It creates a vertical layout where a tab widget is added. Each tab contains
        a form layout with the PropertyInput widgets for each category (properties).

        Store the input widgets in a dictionary to get the values when the form
        is accepted.

        Creation is dynamic, depending on the properties of the element.
        """

        # Retrieve properties and traces --------------------------------

        self.object: Union[Project, Object] = self._controller.get_element(
            self.element_id
        )

        # Get the object's properties dictionary
        properties_dict: Dict[str, Property] = self.object.properties.copy()

        main_obj_class: str
        icon_type: ProteusIconType
        try:
            # Get the main object class to set the icon
            main_obj_class = self.object.classes[-1]
            icon_type = ProteusIconType.Archetype

        # Project will raise an AttributeError
        except AttributeError:
            log.debug("Project properties form.")

            main_obj_class = "proteus_icon"
            icon_type = ProteusIconType.App

        # Dialog settings (icon is set later) ---------------------------
        self.sizeHint = lambda: QSize(500, 300)

        window_name: str = self.object.get_property(PROTEUS_NAME).value
        self.setWindowTitle(window_name)

        dialog_icon: QIcon = Icons().icon(icon_type, main_obj_class)
        self.setWindowIcon(dialog_icon)

        # Properties and traces layout ----------------------------------

        # Create a dictionary to hold category widgets
        category_widgets: Dict[str, QWidget] = self.create_category_widgets(
            properties_dict
        )

        # Iterate over the properties and create widgets for each category
        prop: Property = None
        for prop in properties_dict.values():

            # Get the category widget
            category_widget: QWidget = category_widgets[prop.category]

            # Add a row to the category widget with the property input widget and label
            self.add_row_to_category_widget(category_widget, prop)

        # Insert a QSpacerItem to the end of the each category layout
        # NOTE: This is a workaround to add an stretch to a QFormLayout
        # Inspired by: https://stackoverflow.com/a/13847010
        for category_widget in category_widgets.values():
            category_layout: QFormLayout = category_widget.layout()
            category_layout.addItem(
                QSpacerItem(
                    0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum
                )
            )

        # Tabs layout ---------------------------------------------------

        # Create the form vertical layout and the tab widget
        # to organize the properties by category
        tabbed_layout: QVBoxLayout = QVBoxLayout()
        tab_widget: QTabWidget = QTabWidget(self)

        # Get selected category to preselect the tab (only for objects)
        try:
            selected_category: str = self.object.selectedCategory
        except AttributeError:
            selected_category = ""

        # Add the category widgets as tabs in the tab widget
        for category, category_widget in category_widgets.items():
            translated_category: str = _(
                f"archetype.prop_category.{category}",
                alternative_text=category,
            )
            tab_widget.addTab(category_widget, translated_category)

            if category == selected_category:
                tab_widget.setCurrentWidget(category_widget)

        # Connect the tab changed signal to the change_focus_on_tab_changed method
        tab_widget.currentChanged.connect(self.change_focus_on_tab_changed)
        tab_widget.currentChanged.emit(tab_widget.currentIndex())

        # Add the tab widget to the main form layout
        tabbed_layout.addWidget(tab_widget)

        self.accept_button.clicked.connect(self.save_button_clicked)

        self.set_content_layout(tabbed_layout)

    # ======================================================================
    # Helper private methods
    # ======================================================================

    def create_category_widgets(
        self, properties_dict: Dict[str, Property]
    ) -> Dict[str, QWidget]:
        """
        Create the category widgets tabs for the properties and traces available
        categories.
        """
        # Create a dictionary to hold category widgets
        category_widgets: Dict[str, QWidget] = {}

        # Iterate over the properties and create widgets for each category
        prop: Property = None
        for prop in properties_dict.values():

            # Create a QWidget for the category if it doesn't exist
            if prop.category not in category_widgets:
                category_widget: QWidget = QWidget()
                category_layout: QFormLayout = QFormLayout(category_widget)
                category_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
                category_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
                category_widgets[prop.category] = category_widget

        return category_widgets

    def add_row_to_category_widget(
        self, category_widget: QWidget, prop: Property
    ) -> None:
        """
        Add a row to the category widget with the property input widget and label.
        """
        # Create the property input widget and label
        input_field_widget: PropertyInput = PropertyInputFactory.create(
            prop, element_id=self.element_id, controller=self._controller
        )
        input_label: QLabel = PropertyInputFactory.generate_label(prop)

        # Get the category layout
        category_layout: QFormLayout = category_widget.layout()

        # Some properties are displayed in a group box
        if input_field_widget.wrap_in_group_box:
            group_box: QGroupBox = QGroupBox()
            group_box.setTitle(input_label.text())
            group_box_layout: QVBoxLayout = QVBoxLayout()
            group_box_layout.addWidget(input_field_widget)
            group_box_layout.setContentsMargins(0, 0, 0, 0)
            group_box.setLayout(group_box_layout)

            category_layout.addRow(group_box)
        else:
            # Add the input field widget and label to the category layout
            category_layout.addRow(input_label, input_field_widget)

        # Add the input field widget to the input widgets dictionary
        # NOTE: This is used to retrieve the values of the widgets that changed
        self.input_widgets[prop.name] = input_field_widget

    # ======================================================================
    # Dialog slots methods (connected to the component signals)
    # ======================================================================

    # ----------------------------------------------------------------------
    # Method     : save_button_clicked
    # Description: Manage the save button clicked event. It gets the values
    #              of the input widgets and updates the properties of the
    #              element.
    # Date       : 27/05/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def save_button_clicked(self):
        """
        Manage the save button clicked event. It gets the values of the
        input widgets and updates the propertie and traces of the element.

        This method compares the values of the input widgets with the
        original properties and traces of the element. If there are changes,
        just the properties and traces that changed are updated.

        Form errors are checked before updating the properties. All errors
        are displayed in each input widget. If there are errors, the
        properties update method is not called

        Controller update_properties method is called. Both properties and
        traces are passed in the same list, they can be processed separately
        later.
        """
        # Empty dictionary to hold the properties to update
        update_list: List[Property] = []

        # Get the original object properties (and merge with traces if needed)
        properties_dict: Dict[str, Property] = self.object.properties.copy()

        # Boolean property to check if there are errors
        form_has_errors: bool = False

        # Iterate over the input widgets and update the properties dictionary
        for prop_name in properties_dict.keys():
            # Get the property input value
            input_widget: PropertyInput = self.input_widgets[prop_name]

            # Check if the widget has errors and update the form errors flag
            widget_has_errors: bool = input_widget.has_errors()
            form_has_errors = form_has_errors or widget_has_errors

            # If the widget has errors or previous errors exist, continue
            if widget_has_errors or form_has_errors:
                continue

            # Get the value of the property (or trace property)
            new_prop_value: Any = input_widget.get_value()

            # Get the original property and its value
            original_prop: Property = properties_dict[prop_name]
            original_prop_value: Any = original_prop.value

            # If the values are different, clone the original property with the new value
            if new_prop_value != original_prop_value:
                cloned_property: Property = original_prop.clone(new_prop_value)
                update_list.append(cloned_property)

        # If there are errors, do not update the properties
        if form_has_errors:
            return

        # Update the properties of the element if there are changes
        if len(update_list) > 0:
            self._controller.update_properties(
                self.element_id, new_properties=update_list
            )

        # Close the form window
        self.close()
        self.deleteLater()

    # ----------------------------------------------------------------------
    # Method     : reject_button_clicked
    # Description: Manage the cancel button clicked event. It closes the
    #              form window without saving any changes.
    # Date       : 27/05/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    def reject_button_clicked(self):
        """
        Manage the cancel button clicked event. It closes the form window
        without saving any changes.
        """

        # NOTE: This is a workaround for https://github.com/Josdelsan/Proteus/issues/47
        # When delete_object_on_cancel is True, the last command is supposed to be a
        # clone object archetype command, so we undo it to delete the object
        if self.delete_object_on_cancel:
            log.debug("Deleting cloned object on properties dialog cancel.")
            current_index = self._controller.stack.count()

            if current_index == 0:
                log.error("No commands found in stack. Object archetype clone command not found.")
                super().reject_button_clicked()

            current_command = self._controller.stack.command(current_index-1)

            if not isinstance(current_command, CloneArchetypeObjectCommand):
                log.error("Last command is not a clone object archetype command.")
                super().reject_button_clicked()

            self._controller.undo()

        super().reject_button_clicked()

    # ---------------------------------------------------------------------
    # Method     : change_focus_on_tab_changed
    # Description: Set the keyboard focus to the first input widget of the
    #              selected tab if no other widget has the focus.
    # Date       : 24/10/2024
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ---------------------------------------------------------------------
    def change_focus_on_tab_changed(self, index: int) -> None:
        """
        Set the keyboard focus to the first input widget of the selected tab
        if no other widget has the focus.

        :param index: The index of the selected tab.
        """
        # Get the selected tab widget
        tab_widget: QTabWidget = self.sender()
        selected_widget: QWidget = tab_widget.widget(index)

        if selected_widget is None:
            log.error("Selected widget is None in PropertyDialog")
            return

        inputs: List[PropertyInput] = selected_widget.findChildren(PropertyInput)

        # Check if the tab has been opened before to avoid setting the focus multiple
        # times, this avoids overwriting the focus set by the user
        if index in self.opened_tabs:
            return
        else:
            self.opened_tabs.append(index)

        # Set the keyboard focus to the first input widget of the selected tab
        for input_widget in inputs:
            if input_widget.property.inmutable or isinstance(
                input_widget,
                (
                    TraceInput,
                    BooleanPropertyInput,
                    DatePropertyInput,
                    ClassListPropertyInput,
                    FilePropertyInput,
                    EnumPropertyInput,
                ),
            ):
                continue
            input_widget.setKeyboardFocus()
            break

    # ======================================================================
    # Dialog static methods (create and show the form window)
    # ======================================================================

    # ----------------------------------------------------------------------
    # Method     : create_dialog (static)
    # Description: Handle the creation and display of the form window.
    # Date       : 05/06/2023
    # Version    : 0.1
    # Author     : José María Delgado Sánchez
    # ----------------------------------------------------------------------
    @staticmethod
    def create_dialog(
        controller: Controller,
        element_id: ProteusID,
        delete_object_on_cancel: bool = False,
    ) -> "PropertyDialog":
        """
        Handle the creation and display of the form window.

        :param controller: A Controller instance.
        :param element_id: The id of the element to edit.
        :param delete_object_on_cancel: (Use only after archetype object clone) Boolean to delete the object on cancel.
        """
        dialog = PropertyDialog(
            element_id=element_id,
            delete_object_on_cancel=delete_object_on_cancel,
            controller=controller,
        )
        dialog.exec()
        return dialog
