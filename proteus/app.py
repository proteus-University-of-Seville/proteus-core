# ==========================================================================
# File: app.py
# Description: the PROTEUS application
# Date: 09/10/2022
# Version: 0.1
# Author: Amador Durán Toro
#         José María Delgado Sánchez
# ==========================================================================

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

from pathlib import Path
import sys
import logging
import traceback
import shutil
from typing import Dict, Callable

# --------------------------------------------------------------------------
# Third party imports
# --------------------------------------------------------------------------

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus import PROTEUS_TEMP_DIR
from proteus.application.spellcheck import SpellCheckerWrapper
from proteus.application.configuration.config import Config
from proteus.application.resources.plugins import Plugins
from proteus.application.resources.translator import Translator, translate as _
from proteus.application.resources.icons import Icons
from proteus.application.state.restorer import read_state_from_file
from proteus.application.clipboard import Clipboard
from proteus.controller.command_stack import Controller
from proteus.views.components.main_window import MainWindow
from proteus.views.components.dialogs.base_dialogs import MessageBox

# Module configuration
log = logging.getLogger(__name__)  # Logger


# --------------------------------------------------------------------------
# Class: ProteusApplication
# Description: Class for the PROTEUS application
# Date: 09/10/2022
# Version: 0.1
# Author: Amador Durán Toro
#         José María Delgado Sánchez
# --------------------------------------------------------------------------


class ProteusApplication:
    def __init__(self, project_path: Path = None):
        """
        It initializes the PROTEUS application.
        """
        # General configuration
        self.config: Config = Config()
        self.plugin_manager: Plugins = Plugins()
        self.translator: Translator = Translator()
        self.dynamic_icons: Icons = Icons()
        self.spellchecker = SpellCheckerWrapper()

        # PyQt6 application and main window
        self.app: QApplication = None
        self.main_window: MainWindow = None

        # Optional params
        self.project_path = project_path

    def run(self) -> int:
        """
        PROTEUS application main method.
        """

        # Log initial information
        log.info(f"Current working directory: {Path.cwd()}")
        log.info(f"Home directory: {Path.home()}")
        log.info(f"{Path(__file__) = }")

        # Create the application instance and set the excepthook
        # to handle uncaught exceptions in every thread.
        sys.excepthook = self.excepthook
        self.app = QApplication(sys.argv)

        # Increase the font size of the application
        # app_font = self.app.font()
        # app_font.setPointSize(app_font.pointSize() + 2)
        # self.app.setFont(app_font)

        # Initial setup
        self.initial_setup()

        # Create the controller
        controller = Controller()

        # Clipboard initialization
        Clipboard(controller)

        # Create the main window
        self.main_window = MainWindow(parent=None, controller=controller)
        self.main_window.show()

        # Load plugin components
        self.load_plugin_components()

        # Open project on startup
        self.open_project_on_startup()

        # Execute the application
        return self.app.exec()

    # --------------------------------------------------------------------------
    # Method: initial_setup
    # Description: Initial configuration of the application.
    # Date: 12/02/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def initial_setup(self) -> None:
        """
        Initial configuration that must be done before the app start.

        It handles initialization of translator, icons, plugins,
        request interceptor and stylesheet
        """
        # App settings resources ------------------------------
        self.translator.set_language(self.config.app_settings.language)
        self.translator.set_proteus_i18n_directory(
            self.config.app_settings.i18n_directory
        )
        self.translator.load_translations(self.config.app_settings.i18n_directory)
        self.dynamic_icons.load_icons(self.config.app_settings.icons_directory)
        self.plugin_manager.load_plugins(self.config.app_settings.plugins_directory)

        # Profile resources -----------------------------------
        self.translator.load_translations(self.config.profile_settings.i18n_directory)
        self.dynamic_icons.load_icons(self.config.profile_settings.icons_directory)
        self.plugin_manager.load_plugins(self.config.profile_settings.plugins_directory)

        # SpellCheckerWrapper ----------------------
        spellchecker_language = self.config.app_settings.spellchecker_language
        if spellchecker_language is not None:
            self.spellchecker.set_language(spellchecker_language)

        # Set application style sheet -------------------------
        with open(
            self.config.app_settings.resources_directory
            / "stylesheets"
            / "proteus.qss",
            "r",
        ) as f:
            _stylesheet = f.read()
            self.app.setStyleSheet(_stylesheet)
            del _stylesheet

        # Configure QWebEngineProfile settings ----------------
        profile: QWebEngineProfile = QWebEngineProfile.defaultProfile()
        profile.settings().setAttribute(
            QWebEngineSettings.WebAttribute.JavascriptEnabled, True
        )
        profile.settings().setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True
        )
        profile.settings().setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True
        )

    # --------------------------------------------------------------------------
    # Method: load_plugin_components
    # Description: Load the ProteusComponents from the plugins.
    # Date: 09/01/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    # NOTE: This is done in app module to keep the main window clean. These are
    # components that will be not displayed but need access to the backend to
    # perform complex operations (usually XSLT related)
    def load_plugin_components(self) -> None:
        """
        Load the ProteusComponents from the plugins. It uses MainWindow instance
        as parent for the components.

        It register the functions and components methods to be used in XSLT.

        Functions are accessed from the XSLT using the name registered in the plugins.
        Methods are accessed using the component name dot method standard name (e.g. component.method).
        It is also required to include the namespace prefix. Check RenderService for more information.
        """

        xslt_methods: Dict[str, Callable] = {}

        # Components that need to be instantiated in order to not be deleted
        for (
            comp_name,
            comp_callable,
        ) in self.plugin_manager.get_proteus_components().items():
            try:
                obj = comp_callable(self.main_window)
            except Exception as e:
                log.critical(f"Error loading proteus component from plugin: {e}")

            # Check if the component has methods that has to be registered to use in XSLT
            methods_list = self.plugin_manager._proteus_components_methods.get(
                comp_name, []
            )

            # Store the callable methods references in the plugin manager
            for method_name in methods_list:
                try:
                    method = getattr(obj, method_name)
                    method_callable_str_from_xslt = f"{comp_name}.{method_name}"
                    xslt_methods[method_callable_str_from_xslt] = method
                except Exception as e:
                    log.critical(
                        f"Error loading proteus component method from plugin: {e}"
                    )

        # Add the methods to the render service namespace
        self.main_window._controller._render_service.add_functions_to_namespace(
            xslt_methods
        )

        # Add functions to the XSLT namespace
        self.main_window._controller._render_service.add_functions_to_namespace(
            self.plugin_manager.get_xslt_functions()
        )

    # --------------------------------------------------------------------------
    # Method: open_project_on_startup
    # Description: Handle startup project opening
    # Date: 13/05/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def open_project_on_startup(self) -> None:
        """
        Handle statup project opening. It will open the last project opened or
        the project passed as argument. Prioritize the project passed as argument.
        """
        project_path_to_open = ""

        if self.project_path:
            # If project path is passed as argument, set it as the project to open
            project_path_to_open = self.project_path.as_posix()
        else:
            # If no project path is passed as argument, check if the last project
            # opened is available and ask for confirmation to open it
            open_project_on_startup = self.config.app_settings.open_project_on_startup

            last_project = self.config.app_settings.get_last_project_opened()
            if last_project != "" and last_project is not None and open_project_on_startup:
                confirmation_dialog = MessageBox.question(
                    _("app.open_last_project.title"),
                    _("app.open_last_project.text"),
                    last_project,
                )

                if confirmation_dialog == QMessageBox.StandardButton.Yes:
                    project_path_to_open = last_project

        if project_path_to_open != "":
            try:
                self.main_window._controller.load_project(project_path_to_open)
                read_state_from_file(self.main_window._controller)
            except Exception as e:
                log.error(f"Error opening project on startup: {e}")

                MessageBox.critical(
                    _("main_menu.open_project.error.title"),
                    _("main_menu.open_project.error.text"),
                    e.__str__(),
                )

    # ==========================================================================
    # Exception handling
    # ==========================================================================

    # --------------------------------------------------------------------------
    # Method: excepthook
    # Description: Handle uncaught exceptions in the application.
    # Date: 01/12/2023
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    # NOTE: Exception handling for QApplication must be done overriding the
    # excepthook method. Otherwise, it will depend on the thread where the
    # exception is raised.
    # https://stackoverflow.com/questions/55819330/catching-exceptions-raised-in-qapplication
    def excepthook(self, exc_type, exc_value, exc_tb):
        tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        log.critical("Uncaught exception:\n" + tb)

        # Show the exception and its traceback in a message box
        MessageBox.critical(
            _("app.critical_error.title"), _("app.critical_error.text"), tb
        )

        # Override closeEvent in main window to avoid asking for confirmation
        # when closing the application
        self.main_window.closeEvent = lambda event: event.accept()

        self.handle_critical_error()

    # --------------------------------------------------------------------------
    # Method: handle_critical_error
    # Description: Handle a critical error in the application quitting the
    # application.
    # Date: 01/12/2023
    # Version: 0.1
    # --------------------------------------------------------------------------
    # TODO: Find a way to store application state before quitting
    # and restore it when the application is restarted.
    def handle_critical_error(self):
        """
        Handle a critical error in the application quitting the application.
        """
        # Before quitting, try to disconnect signals
        try:
            self.main_window._controller.stack.canRedoChanged.disconnect()
            self.main_window._controller.stack.canUndoChanged.disconnect()
            self.main_window._controller.stack.cleanChanged.disconnect()
            self.main_window._controller.stack.clear()
            self.main_window._controller.stack.deleteLater()
        except Exception as e:
            log.critical(f"Error clearing the undo stack: {e}")

        # Select last log file
        log_files = sorted(PROTEUS_TEMP_DIR.glob("*.log"))
        log_file = log_files[-1]

        # Build new crash report file name
        log_file_name = log_file.name
        crash_report_file_name = f"proteus_crash_report-{log_file_name}"

        # Copy log file to cwd with new name
        crash_report_file = Path.cwd() / crash_report_file_name
        shutil.copy(log_file, crash_report_file)

        # Quit the application
        self.app.quit()
