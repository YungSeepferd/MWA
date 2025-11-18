from typing import List, Literal, Type

from .base import BaseProvider
from .immoscout import ImmoScoutProvider
from .wg_gesucht import WGGesuchtProvider

# Registry mapping provider identifiers to their concrete classes
PROVIDER_REGISTRY: dict[str, Type[BaseProvider]] = {
    "immoscout": ImmoScoutProvider,
    "wg_gesucht": WGGesuchtProvider,
}


def build_providers(names: List[Literal["immoscout", "wg_gesucht"]]) -> List[BaseProvider]:
    """
    Instantiate provider classes based on the ordered list from configuration.
    Raises ValueError if an unknown provider name is supplied.
    """
    instances: List[BaseProvider] = []
    for name in names:
        provider_cls = PROVIDER_REGISTRY.get(name)
        if provider_cls is None:
            raise ValueError(f"Unknown provider '{name}'. Available: {list(PROVIDER_REGISTRY)}")
        instances.append(provider_cls())
    return instances