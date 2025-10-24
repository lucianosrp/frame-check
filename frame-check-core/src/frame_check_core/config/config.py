from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
import tomllib

from . import paths


@dataclass
class Config:
    nonrecursive: bool = field(default=False)
    """Default is to find files recursively."""
    _exclude: set[str] = field(
        default_factory=lambda: {paths.normalize_pattern(".venv/", True)}
    )

    @property
    def exclude(self) -> list[str]:
        """Get a list of the exclusion patterns."""
        return list(self._exclude)

    @property
    def recursive(self) -> bool:
        """Determine if directory traversal should be recursive."""
        return not self.nonrecursive

    @classmethod
    def load_from(cls, file: Path):
        """Load configuration from a TOML file."""
        config = cls()
        with open(file, "rb") as f:
            config_data = tomllib.load(f)
            if file.name == "pyproject.toml":
                config_data = config_data.get("tool", {}).get("frame-check", {})
        config.update(**config_data)

        return config

    def update_exclude(self, exclusion_patterns: Iterable[str]) -> None:
        """Processes new exclusion patterns."""
        normalized_patterns = [
            paths.normalize_pattern(pattern, self.recursive)
            for pattern in exclusion_patterns
        ]
        self._exclude.update(normalized_patterns)

    def update(
        self,
        exclude: Iterable[str] | None = None,
        nonrecursive: bool | None = None,
        **_kwargs,
    ) -> None:
        """Update configuration settings."""
        if exclude is not None:
            self.update_exclude(exclude)
        if nonrecursive is not None:
            self.nonrecursive = nonrecursive
        # Ignore unknown kwargs for forward compatibility
        # With logging, could output to debug
