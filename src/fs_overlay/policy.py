from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class CarrierPolicy:
    """Safety policy for carrier discovery.

    Roots are explicit. This class deliberately does not implement hidden
    machine-wide discovery or protected-path bypasses.
    """

    roots: tuple[Path, ...]
    max_overhead_ratio: float = 0.30
    min_file_size: int = 4096
    max_file_size: int = 1 << 30
    allowed_suffixes: frozenset[str] = field(
        default_factory=lambda: frozenset({".ini", ".conf", ".cfg", ".log", ".dat", ".bin", ".cache"})
    denied_names: frozenset[str] = field(
        default_factory=lambda: frozenset({".git", ".ssh", "id_rsa", "authorized_keys"})
    )

    def __post_init__(self) -> None:
        if not 0 < self.max_overhead_ratio <= 0.30:
            raise ValueError("max_overhead_ratio must be > 0 and <= 0.30")
        if self.min_file_size < 0 or self.max_file_size < self.min_file_size:
            raise ValueError("invalid file-size limits")

    def is_allowed(self, path: Path) -> bool:
        try:
            resolved = path.resolve(strict=True)
        except OSError:
            return False
        if not resolved.is_file() or resolved.name in self.denied_names:
            return False
        if resolved.suffix.lower() not in self.allowed_suffixes:
            return False
        try:
            size = resolved.stat().st_size
        except OSError:
            return False
        if not self.min_file_size <= size <= self.max_file_size:
            return False
        return any(self._under_root(resolved, root) for root in self.roots)

    @staticmethod
    def _under_root(path: Path, root: Path) -> bool:
        try:
            path.relative_to(root.resolve())
            return True
        except ValueError:
            return False

    def capacity_for(self, original_size: int) -> int:
        if original_size < self.min_file_size:
            return 0
        return min(int(original_size * self.max_overhead_ratio), self.max_file_size)
