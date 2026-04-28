from enum import Enum
class CatalogType(str, Enum):
    INTEREST   = "INTEREST"
    TEMPORAL   = "TEMPORAL"
    SPATIAL    = "SPATIAL"
    OBSERVABLE = "OBSERVABLE"
    REFERENCE  = "REFERENCE"

class ServiceProviderEnum(str, Enum):
    """Enum for service providers."""
    NEZ = "NEZ"
    XELHUA = "XELHUA"
    EXTERNAL = "EXTERNAL"
    OTHER = "OTHER"