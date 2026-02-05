# tests/test_docstrings_and_type_hints.py
"""Test that all public functions, classes, and methods have docstrings and type hints.

This test discovers all Python modules in the project (excluding the tests package) and checks that:
- The module has a non‑empty docstring.
- Every public class has a non‑empty docstring.
- Every public function (including methods) has a non‑empty docstring.
- All parameters (except ``self``/``cls``) and the return value are annotated with a type hint.
"""

import importlib
import inspect
import pathlib
from typing import get_type_hints


def iter_modules():
    """Yield the importable module name for each non‑test Python file in the repository."""
    root = pathlib.Path(__file__).parent.parent
    for py_path in root.rglob("*.py"):
        # Skip test files and the tests package itself
        if "tests" in py_path.parts:
            continue
        if py_path.name.startswith("test_"):
            continue
        # Compute the module name (dot‑separated) relative to the repo root
        rel_path = py_path.relative_to(root).with_suffix("")
        parts = list(rel_path.parts)
        # ``__init__`` modules represent the package itself
        if parts[-1] == "__init__":
            parts = parts[:-1]
        module_name = ".".join(parts)
        yield module_name


def test_docstrings_and_type_hints():
    """Verify docstrings and type hints for all public symbols in the codebase."""
    for mod_name in iter_modules():
        mod = importlib.import_module(mod_name)
        # Module docstring
        assert mod.__doc__ and mod.__doc__.strip(), (
            f"Module {mod_name} missing docstring"
        )
        for name, obj in inspect.getmembers(mod):
            # Public classes
            if inspect.isclass(obj) and not name.startswith("_"):
                assert obj.__doc__ and obj.__doc__.strip(), (
                    f"Class {mod_name}.{name} missing docstring"
                )
                # Methods of the class
                for meth_name, meth in inspect.getmembers(obj):
                    if inspect.isfunction(meth) and not meth_name.startswith("_"):
                        assert meth.__doc__ and meth.__doc__.strip(), (
                            f"Method {mod_name}.{name}.{meth_name} missing docstring"
                        )
                        hints = get_type_hints(meth)
                        # Return type must be present
                        assert "return" in hints, (
                            f"Method {mod_name}.{name}.{meth_name} missing return type hint"
                        )
                        sig = inspect.signature(meth)
                        for param_name, param in sig.parameters.items():
                            if param_name in ("self", "cls"):
                                continue
                            assert param_name in hints, (
                                f"Parameter '{param_name}' of method {mod_name}.{name}.{meth_name} missing type hint"
                            )
            # Public functions (module level)
            elif inspect.isfunction(obj) and not name.startswith("_"):
                assert obj.__doc__ and obj.__doc__.strip(), (
                    f"Function {mod_name}.{name} missing docstring"
                )
                hints = get_type_hints(obj)
                assert "return" in hints, (
                    f"Function {mod_name}.{name} missing return type hint"
                )
                sig = inspect.signature(obj)
                for param_name, param in sig.parameters.items():
                    if param_name in ("self", "cls"):
                        continue
                    assert param_name in hints, (
                        f"Parameter '{param_name}' of function {mod_name}.{name} missing type hint"
                    )
