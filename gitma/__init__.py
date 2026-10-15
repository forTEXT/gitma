from importlib.metadata import PackageNotFoundError, version as _version

from .tag import Tag
from .tagset import Tagset
from .annotation import Annotation
from .project import CatmaProject
from .catma import Catma
from .property import Property
from .text import Text
from .annotation_collection import AnnotationCollection
from .selector import Selector

try:
    # The version is declared once, in pyproject.toml, and read back from the
    # installed distribution metadata.
    __version__ = _version("gitma")
except PackageNotFoundError:  # running from a source checkout without installing
    __version__ = "0.0.0.dev0"

__all__ = [
    "Annotation",
    "AnnotationCollection",
    "Catma",
    "CatmaProject",
    "Property",
    "Selector",
    "Tag",
    "Tagset",
    "Text",
    "__version__",
]
