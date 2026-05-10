"""
Generator protocol and factory for all Tarim-Shaiel HTML generators.

Provides a common interface so utilities/build.py can discover and
invoke any generator without knowing its implementation details.

Usage
-----
At the bottom of each generator module::

    from shared.base_generator import make_generator
    generator = make_generator("my-generator", "One-line description", main)

That replaces the repetitive _Generator boilerplate class entirely.
"""
import sys
from typing import Callable, Optional, Protocol, Sequence


class Generator(Protocol):
    """Minimal interface that all generator wrapper classes must satisfy."""

    name: str         # CLI registry key, e.g. "campaign-frame"
    description: str  # One-line human description for build.py list output

    def run(self, argv: Optional[Sequence[str]] = None) -> int:
        """Invoke the generator.

        argv: CLI arguments (without the script name). If None, reads
              from sys.argv as normal (standalone-script behaviour).
        Returns: exit code — 0 for success, non-zero for failure.
        """
        ...


class _FactoryGenerator:
    """Generator wrapper produced by make_generator().

    Injects *argv* into sys.argv for the duration of the call, then
    restores it — the correct approach for generators whose main()
    reads from sys.argv directly.
    """

    def __init__(self, name: str, description: str, main_fn: Callable) -> None:
        self.name = name
        self.description = description
        self._main_fn = main_fn

    def run(self, argv: Optional[Sequence[str]] = None) -> int:
        saved = sys.argv[1:]
        if argv is not None:
            sys.argv[1:] = list(argv)
        try:
            result = self._main_fn()
            return result if isinstance(result, int) else 0
        except SystemExit as e:
            return int(e.code) if isinstance(e.code, int) else 0
        finally:
            sys.argv[1:] = saved


def make_generator(name: str, description: str, main_fn: Callable) -> _FactoryGenerator:
    """Create a Generator-protocol-compliant object wrapping a *main_fn*.

    Args:
        name:        Registry key used by build.py (e.g. ``"campaign-frame"``).
        description: One-line human description shown by ``build.py list``.
        main_fn:     The module-level ``main()`` function to wrap.

    Returns:
        A :class:`_FactoryGenerator` instance satisfying the
        :class:`Generator` protocol.
    """
    return _FactoryGenerator(name, description, main_fn)
