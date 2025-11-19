import importlib.metadata
from typing import Dict, List, Type
from .base import Provider, Listing


class ProviderRegistry:
    """
    Registry for scraper providers discovered via entry-points.
    Singleton pattern – instantiated once at import time.
    """

    _instance: "ProviderRegistry | None" = None

    def __new__(cls) -> "ProviderRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._providers: Dict[str, Type[Provider]] = {}
            cls._instance._load_providers()
        return cls._instance

    def _load_providers(self) -> None:
        """
        Discover providers registered under the 'mwa_core.providers' entry-point group.
        """
        eps = importlib.metadata.entry_points()
        group = "mwa_core.providers"
        # Use select() for forward compatibility
        for ep in eps.select(group=group):
                try:
                    provider_cls = ep.load()
                    self._providers[ep.name] = provider_cls
                except Exception as exc:
                    # Log and skip broken providers
                    print(f"Failed to load provider {ep.name}: {exc}")

    def get(self, name: str) -> Type[Provider] | None:
        """
        Retrieve a provider class by name.
        """
        return self._providers.get(name)

    def list(self) -> List[str]:
        """
        Return list of registered provider names.
        """
        return list(self._providers.keys())

    def instantiate(self, name: str, *args, **kwargs) -> Provider | None:
        """
        Instantiate a provider by name.
        """
        cls = self.get(name)
        if cls is None:
            return None
        return cls(*args, **kwargs)