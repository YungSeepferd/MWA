from typing import List, Literal, Type

from .base import BaseProvider
from .immoscout import ImmoScoutProvider
from .wg_gesucht import WGGesuchtProvider

# Registry mapping provider identifiers to their concrete classes
PROVIDER_REGISTRY: dict[str, Type[BaseProvider]] = {
    "immoscout": ImmoScoutProvider,
    "wg_gesucht": WGGesuchtProvider,
}


def build_providers(names: List[Literal["immoscout", "wg_gesucht"]], config=None) -> List[BaseProvider]:
    """
    Instantiate provider classes based on the ordered list from configuration.
    Raises ValueError if an unknown provider name is supplied.
    
    Args:
        names: List of provider names to instantiate
        config: Optional Settings instance to pass to providers
        
    Returns:
        List of provider instances
    """
    instances: List[BaseProvider] = []
    for name in names:
        provider_cls = PROVIDER_REGISTRY.get(name)
        if provider_cls is None:
            raise ValueError(f"Unknown provider '{name}'. Available: {list(PROVIDER_REGISTRY)}")
        
        # Initialize with config if supported
        try:
            instance = provider_cls(config=config) if config else provider_cls()
        except TypeError:
            # Fallback for providers that don't accept config parameter
            instance = provider_cls()
        
        instances.append(instance)
    return instances