"""
Generator protocol for all Tarim-Shaiel HTML generators.

Provides a common interface so utilities/build.py can discover and
invoke any generator without knowing its implementation details.
"""
from typing import Protocol, Sequence


class Generator(Protocol):
    """Minimal interface that all generator wrapper classes must satisfy."""

    name: str         # CLI registry key, e.g. "campaign-frame"
    description: str  # One-line human description for build.py list output

    def run(self, argv: Sequence[str] | None = None) -> int:
        """Invoke the generator.

        argv: CLI arguments (without the script name). If None, reads
              from sys.argv as normal (standalone-script behaviour).
        Returns: exit code — 0 for success, non-zero for failure.
        """
        ...
