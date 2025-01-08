# ==========================================================================
# File: plugin_manager.py
# Description: Plugin manager module for PROTEUS application.
# Date: 03/01/2023
# Version: 0.1
# Author: José María Delgado Sánchez
# ==========================================================================
# TODO: Plugins might be able to register their own resources (e.g. images
#       translations, etc.).
# TODO: Plugins might use a configuration file to define additional settings.

# --------------------------------------------------------------------------
# Standard library imports
# --------------------------------------------------------------------------

import sys
import logging
import importlib
import pkgutil
from typing import Callable, Dict, Union, List
from pathlib import Path

# --------------------------------------------------------------------------
# Third party imports
# --------------------------------------------------------------------------

# --------------------------------------------------------------------------
# Project specific imports
# --------------------------------------------------------------------------

from proteus.application.utils.abstract_meta import SingletonMeta

# logging configuration
log = logging.getLogger(__name__)


class PluginInterface:
    """
    Define the interface for modules that can be loaded as plugins.

    #TODO: Implement plugins metadata (name, version, dependencies, etc.)
    """

    @staticmethod
    def register(
        register_xslt_function: Callable[[str, Callable], None],
        register_qwebchannel_class: Callable[[str, Callable], None],
        register_proteus_component: Callable[[str, Callable, List[str]], None],
    ) -> None:
        """
        Register the plugin items in the corresponding registries.

        :param register_xslt_function: Function to register XSLT functions.
        :param register_qwebchannel_class: Function to register QWebChannel classes.
        :param register_proteus_component: Function to register ProteusComponent classes.
        """


class Plugins(metaclass=SingletonMeta):
    """
    Manage PROTEUS plugins. A plugin is a module that can be loaded at runtime
    and register XSLT functions/methods and QWebChannel classes for use in the templates.
    ProteusComponents can also be registered with no specific use case if needed
    to access controller functionality.
    """

    # --------------------------------------------------------------------------
    # Method: __init__
    # Description: Constructor for Plugins class.
    # Date: 03/01/2023
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def __init__(self):
        """
        It initializes the Plugins class.
        """
        # --------------------------------
        # Initialize the plugin registries
        # --------------------------------
        # Plugins (k: module name, v: module)
        self._plugins: Dict[str, PluginInterface] = {}

        # Functions registered in the XSLT engine namespace (k: function name, v: function)
        self._xslt_functions: Dict[str, Callable] = {}

        # QWebChannel classes registered in QWebEngineView (k: class name, v: class)
        self._qwebchannel_classes: Dict[str, Callable] = {}

        # ProteusComponent classes initialized in the application (k: class name, v: class)
        self._proteus_components: Dict[str, Callable] = {}

        # ProteusComponent methods that will be registered in the XSLT engine (k: class name, v: methods)
        self._proteus_components_methods: Dict[str, List[str]] = {}

    # --------------------------------------------------------------------------
    # Method: _import_plugin
    # Description: Import a module given a module name.
    # Date: 03/01/2023
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def _import_plugin(self, module_name: str) -> Union[PluginInterface, None]:
        """
        Import a plugin given a module name. If the module is not found, it
        returns None.

        :param module_name: Name of the plugin to import.
        """
        log.info(f"Importing plugin '{module_name}'")
        try:
            return importlib.import_module(module_name)
        except ModuleNotFoundError as e:
            log.warning(f"Module '{module_name}' not found: {e}")
            return None

    # --------------------------------------------------------------------------
    # Method: load_plugins
    # Description: Load the plugins from a plugins directory.
    # Date: 03/01/2023
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def load_plugins(self, plugins_directory: Path) -> None:
        """
        Load the plugins from a plugins directory. Iterate over the modules
        in the plugins directory and try to import them. If the module is
        successfully imported, it will call the register function of the module
        to register the XSLT functions and QWebChannel classes.

        :param plugins_directory: Path to the plugins directory.
        """
        if plugins_directory is None:
            log.warning("Plugins directory is None")
            return
        
        log.info(
            f"Loading PROTEUS plugins from plugins directory '{plugins_directory.as_posix()}'"
        )

        # Import the package
        if not plugins_directory.exists():
            log.error(
                f"Plugins directory '{plugins_directory.as_posix()}' does not exist"
            )
            return

        # Include in sys.path the plugins directory
        # NOTE: This is neccessary in order to import modules outside in directories outside
        # the root package and use application modules in those plugins.
        sys.path.append(plugins_directory.as_posix())

        # Get the plugin modules from the directory
        plugins_modules = [
            module_name
            for _, module_name, _ in pkgutil.iter_modules(
                [plugins_directory.as_posix()]
            )
        ]
        if plugins_modules is None:
            log.error(
                f"No modules found in plugins directory '{plugins_directory.as_posix()}'"
            )
            return
        else:
            log.info(f"Plugins found in plugins package: {plugins_modules}")

        # Iterate over the modules in the plugins directory
        for module_name in plugins_modules:
            # Import the module
            module = self._import_plugin(module_name)

            if module is None:
                continue

            try:
                # Register the plugin items
                module.register(
                    self.register_xslt_function,
                    self.register_qwebchannel_class,
                    self.register_proteus_component,
                )

                # Save the plugin
                self._plugins[module_name] = module
            except AttributeError:
                log.warning(f"Module {module_name} does not have a register function")
                continue
            except Exception as e:
                log.error(f"Error registering module {module_name}: {e}")
                continue

    # --------------------------------------------------------------------------
    # Method: get_xslt_functions
    # Description: Get the XSLT functions registered in the plugin manager.
    # Date: 03/01/2023
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def get_xslt_functions(self) -> Dict[str, Callable]:
        """
        Get the XSLT functions registered in the plugin manager.
        """
        return self._xslt_functions

    # --------------------------------------------------------------------------
    # Method: get_qwebchannel_classes
    # Description: Get the QWebChannel classes registered in the plugin manager.
    # Date: 03/01/2023
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def get_qwebchannel_classes(self) -> Dict[str, Callable]:
        """
        Get the QWebChannel classes registered in the plugin manager.
        """
        return self._qwebchannel_classes

    # --------------------------------------------------------------------------
    # Method: get_proteus_components
    # Description: Get the ProteusComponent classes registered in the plugin manager.
    # Date: 09/01/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def get_proteus_components(self) -> Dict[str, Callable]:
        """
        Get the ProteusComponent classes registered in the plugin manager.
        """
        return self._proteus_components

    # --------------------------------------------------------------------------
    # Method: get_plugins
    # Description: Get the plugins loaded in the plugin manager.
    # Date: 03/01/2023
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def get_plugins(self) -> List[str]:
        """
        Get the plugins loaded in the plugin manager.
        """
        return list(self._plugins.keys())

    # ==========================================================================
    # Register methods (used by plugins)
    # ==========================================================================

    # --------------------------------------------------------------------------
    # Method: register_xslt_function
    # Description: Register an XSLT function in the plugin manager.
    # Date: 03/01/2023
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def register_xslt_function(self, name: str, function: Callable) -> None:
        """
        Register an XSLT function in the plugin manager. If there is already a
        function registered with the same name, it will be ignored.

        It validates if the function is callable.

        :param name: Name of the XSLT function.
        :param function: Function to register.
        """
        # Validate the function
        if not callable(function):
            log.error(f"XSLT function '{name}' is not callable, ignoring it")
            return

        # Register the function
        if name in self._xslt_functions:
            log.error(f"XSLT function '{name}' already registered, ignoring it")
            return

        log.info(f"Registering XSLT function '{name}'")
        self._xslt_functions[name] = function

    # --------------------------------------------------------------------------
    # Method: register_qwebchannel_class
    # Description: Register a QWebChannel class in the plugin manager.
    # Date: 03/01/2023
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def register_qwebchannel_class(self, name: str, class_: Callable) -> None:
        """
        Register a QWebChannel class in the plugin manager. If there is already a
        class registered with the same name, it will be ignored.

        It validates if the class is callable.

        :param name: Name of the QWebChannel class.
        :param class_: Class to register.
        """
        # Validate the class
        if not callable(class_):
            log.error(f"QWebChannel class '{name}' is not callable, ignoring it")
            return

        # Register the class
        if name in self._qwebchannel_classes:
            log.error(f"QWebChannel class '{name}' already registered, ignoring it")
            return

        log.info(f"Registering QWebChannel class '{name}'")
        self._qwebchannel_classes[name] = class_

    # --------------------------------------------------------------------------
    # Method: register_proteus_component
    # Description: Register a ProteusComponent class in the plugin manager.
    # Date: 09/01/2024
    # Version: 0.1
    # Author: José María Delgado Sánchez
    # --------------------------------------------------------------------------
    def register_proteus_component(
        self, name: str, class_: Callable, methods: List[str] = []
    ) -> None:
        """
        Register a ProteusComponent class in the plugin manager. If there is already a
        class registered with the same name, it will be ignored. Object methods can also
        be registered in order to be used in the XSLT engine.

        It validates if the class is callable.

        :param name: Name of the ProteusComponent class.
        :param class_: Class to register.
        :param methods: List of methods to register from the given class.
        """
        # Validate the class
        if not callable(class_):
            log.error(f"ProteusComponent class '{name}' is not callable, ignoring it")
            return

        # Register the class
        if name in self._proteus_components:
            log.error(
                f"ProteusComponent class '{name}' already registered, ignoring it"
            )
            return

        log.info(f"Registering ProteusComponent class '{name}'")
        self._proteus_components[name] = class_

        # If methods are provided, register them
        if methods:

            valid_methods: List[str] = []

            # Check every method is in the class
            for method in methods:
                if not hasattr(class_, method):
                    log.error(
                        f"Method '{method}' not found in class '{class_.__name__}'"
                    )
                    continue
                valid_methods.append(method)
                log.info(
                    f"Registering method '{method}' from class '{class_.__name__}'"
                )

            # Extend the list of methods to be instantiated for the class
            if self._proteus_components_methods.get(name):
                self._proteus_components_methods[name].extend(valid_methods)
            else:
                self._proteus_components_methods[name] = valid_methods
