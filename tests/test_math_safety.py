"""Safety tests for MathCalculatorCog: sandbox-escape strings and DoS-style expressions.

The DoS cases are rejected before evaluation. If that guard regresses, the offending
expression would block the interpreter, so the guard strings are asserted on directly.
"""
import asyncio
import importlib
from typing import Optional

import pytest


class _StubBot:
    """Bot with no cogs registered, so the calculator returns plain English errors."""

    def get_cog(self, name: str) -> None:
        """Return no cog for any name."""
        return None


@pytest.fixture(scope="module")
def cog():
    """Build the calculator cog against a stub bot."""
    math_module = importlib.import_module("cogs.math")
    return math_module.MathCalculatorCog(bot=_StubBot())


def _calculate(cog, expression: str, guild_id: Optional[str] = "0") -> str:
    """Run calculate_math to completion for a single expression."""
    return asyncio.run(cog.calculate_math(expression, guild_id=guild_id))


@pytest.mark.parametrize(
    "expression",
    [
        "__import__('os').system('id')",
        "(lambda: 1)()",
        "getattr(1, '__class__')",
    ],
)
def test_sandbox_escape_expressions_are_not_evaluated(cog, expression: str) -> None:
    """Sandbox-escape strings must yield an error, never a computed result."""
    assert "Result" not in _calculate(cog, expression)


@pytest.mark.parametrize("expression", ["9**9**9", "2**99999999", "2**(99999)"])
def test_stacked_or_oversized_exponents_are_rejected(cog, expression: str) -> None:
    """Stacked powers and exponents of five or more digits are refused before evaluation."""
    assert "exponentiations are not allowed" in _calculate(cog, expression)


@pytest.mark.parametrize(
    "expression",
    ["factorial(99999999)", "factorial(1000*1000*1000)", "factorial(factorial(9))", "gamma(123456)"],
)
def test_combinatorial_functions_reject_large_or_computed_arguments(cog, expression: str) -> None:
    """factorial/gamma only accept a bare literal of at most five digits."""
    assert "small literal argument" in _calculate(cog, expression)


@pytest.mark.parametrize(
    ("expression", "expected"),
    [("2+3*4", "= 14"), ("2**10", "= 1024"), ("factorial(10)+gamma(5)", "= 3628824")],
)
def test_legitimate_expressions_still_evaluate(cog, expression: str, expected: str) -> None:
    """The safety guards must not reject ordinary calculations."""
    assert expected in _calculate(cog, expression)
