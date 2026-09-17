"""Guarantee that every shipped module parses and imports.

A module that cannot be parsed or imported is a broken shipped surface even when
no other module in the repository references it: it is still packaged into the
sdist/wheel, and ``import fs_overlay.<module>`` fails for any consumer. This
gate exists because a syntactically invalid ``fs_overlay.policy`` shipped while
the ordinary test matrix stayed green.
"""
from __future__ import annotations

import ast
import importlib
import pkgutil
from pathlib import Path

import pytest

import fs_overlay

_MODULE_NAMES = sorted(f"fs_overlay.{module.name}" for module in pkgutil.iter_modules(fs_overlay.__path__))
_PACKAGE_DIR = Path(fs_overlay.__path__[0])


def _module_path(module_name: str) -> Path:
    return _PACKAGE_DIR / f"{module_name.split('.', 1)[1]}.py"


def test_package_exposes_expected_modules() -> None:
    assert _MODULE_NAMES, "package discovery returned no modules"
    assert "fs_overlay.policy" in _MODULE_NAMES
    assert "fs_overlay.cli" in _MODULE_NAMES


@pytest.mark.parametrize("module_name", _MODULE_NAMES)
def test_module_source_parses(module_name: str) -> None:
    source_path = _module_path(module_name)
    assert source_path.is_file(), f"missing source for {module_name}"
    ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))


@pytest.mark.parametrize("module_name", _MODULE_NAMES)
def test_module_is_importable(module_name: str) -> None:
    importlib.import_module(module_name)
