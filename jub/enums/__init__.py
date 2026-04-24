from enum import Enum
class CatalogType(str, Enum):
    INTEREST   = "INTEREST"
    TEMPORAL   = "TEMPORAL"
    SPATIAL    = "SPATIAL"
    OBSERVABLE = "OBSERVABLE"
    REFERENCE  = "REFERENCE"