# ==========================================================================
# File: __init__.py
# Description: PROTEUS 'properties' package initializer
# Date: 27/08/2022
# Version: 0.1
# Author: José María Delgado Sánchez
#         Amador Durán Toro
# ==========================================================================
# Update: 30/08/2022 (Amador)
# Description:
# - Added support for property categories.
# - Added PropertyFactory class to avoid Property class definition to be
#   splitted into two parts.
# ==========================================================================
# Update: 17/09/2022 (Amador)
# Description:
# - Added default category value in constructors.
# ==========================================================================
# Update: 29/09/2022 (Amador)
# Description:
# - Code review.
# - Argument "value" is always a string in __init()__, its conversion to
#   the right type is checked in each subclass.
# ==========================================================================
# Update: 15/10/2022 (Amador)
# Description:
# - Use of dataclass and __post_init()__.
# - ValueError exception handling in type conversions.
# - RealProperty -> FloatProperty.
# - Added FileProperty.
# - MarkdownProperty is now a subclass of StringProperty.
# - lxml is not very MyPy-friendly. Installed lxlm-stub in venv.
# - Added pytest parametrized tests in proteus/tests/test_properties.py.
# - Use dataclasses.replace(obj,value=new_value) to clone a property with a
#   new value. The new_value must be in string format, as in the constructor.
# ==========================================================================
# Update: 17/10/2022 (Amador)
# Description:
# - clone(new_value=None) added.
# ==========================================================================
# Update: 22/10/2022 (Amador)
# Description:
# - UrlProperty::is_valid computed property added.
# - URLs without protocol (i.e. https://) are not valid.
# - FileProperty::is_file computed property added.
# - EnumProperty: split() without arguments uses space and returns an
#   empty list if the splitted string is empty. split(' ') returns [''],
#   which is not an empty list.
# - EnumProperty assings first choice instead of random choice if value is
#   not specified.
# - EnumProperty replaces spaces by underscores in values.
# - PropertyFactory: fixed error in reduce expression for ClasslistProperty.
# ==========================================================================
# Update: 06/04/2023 (José María)
# Description:
# - Refactor module 'property' into package 'properties'.
# ==========================================================================

from proteus.model import PROTEUS_DEPENDENCY

# Constants
BOOLEAN_PROPERTY_TAG    = str('booleanProperty')
STRING_PROPERTY_TAG     = str('stringProperty')
DATE_PROPERTY_TAG       = str('dateProperty')
TIME_PROPERTY_TAG       = str('timeProperty')
MARKDOWN_PROPERTY_TAG   = str('markdownProperty')
INTEGER_PROPERTY_TAG    = str('integerProperty')
FLOAT_PROPERTY_TAG      = str('floatProperty')
ENUM_PROPERTY_TAG       = str('enumProperty')
URL_PROPERTY_TAG        = str('urlProperty')
FILE_PROPERTY_TAG       = str('fileProperty')
CLASSLIST_PROPERTY_TAG  = str('classListProperty')
CODE_PROPERTY_TAG       = str('codeProperty')
TRACE_PROPERTY_TAG      = str('traceProperty')
TRACE_TYPE_LIST_PROPERTY_TAG = str('traceTypeListProperty')
UNIT_PROPERTY_TAG       = str('unitProperty')

CLASS_TAG               = str('class')
TYPE_TAG                = str('type')
PREFIX_TAG              = str('prefix')
NUMBER_TAG              = str('number')
SUFFIX_TAG              = str('suffix')
TRACE_TAG               = str('trace')
UNIT_TAG                = str('unit')
VALUE_TAG               = str('value')

DEFAULT_NAME            = str('unnamed')
DEFAULT_CATEGORY        = str('general')
DEFAULT_TRACE_TYPE      = PROTEUS_DEPENDENCY

DATE_FORMAT             = str('%Y-%m-%d')
TIME_FORMAT             = str('%H:%M:%S')

NO_TARGETS_LIMIT = -1


# Making classes available at the package level
# NOTE: This must be below the constants definition
#       to avoid circular imports

from proteus.model.properties.property import Property
from proteus.model.properties.property_factory import PropertyFactory

from proteus.model.properties.boolean_property import BooleanProperty
from proteus.model.properties.string_property import StringProperty
from proteus.model.properties.date_property import DateProperty
from proteus.model.properties.time_property import TimeProperty
from proteus.model.properties.markdown_property import MarkdownProperty
from proteus.model.properties.integer_property import IntegerProperty
from proteus.model.properties.float_property import FloatProperty
from proteus.model.properties.enum_property import EnumProperty
from proteus.model.properties.url_property import UrlProperty
from proteus.model.properties.file_property import FileProperty
from proteus.model.properties.classlist_property import ClassListProperty
from proteus.model.properties.code_property import CodeProperty
from proteus.model.properties.trace_property import TraceProperty
from proteus.model.properties.tracetypelist_property import TraceTypeListProperty
from proteus.model.properties.unit_property import UnitProperty
