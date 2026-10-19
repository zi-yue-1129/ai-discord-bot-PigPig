"""Tests that the story feature's Discord-facing text is translated in every locale."""

from __future__ import annotations

import ast
import asyncio
import json
import re
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple

import pytest

ROOT = Path(__file__).resolve().parents[1]
LOCALES = ("zh_TW", "zh_CN", "en_US", "ja_JP")
STORY_FILES = (
    "cogs/story_manager.py",
    "cogs/story/ui/views.py",
    "cogs/story/ui/modals.py",
    "cogs/story/ui/ui_manager.py",
)
CJK_PATTERN = re.compile(r"[　-ヿ㐀-䶿一-鿿＀-￯]")
LOG_METHODS = {"debug", "info", "warning", "error", "exception", "critical"}
TRANSLATE_NAMES = {"translate", "_t"}

# call name -> keyword arguments that end up in front of a Discord user
USER_FACING_KWARGS: Dict[str, Set[str]] = {
    "send_message": {"content"},
    "send": {"content"},
    "reply": {"content"},
    "edit_message": {"content"},
    "edit_original_response": {"content"},
    "Embed": {"title", "description"},
    "add_field": {"name", "value"},
    "set_footer": {"text"},
    "Button": {"label"},
    "button": {"label"},
    "Select": {"placeholder"},
    "select": {"placeholder"},
    "TextInput": {"label", "placeholder", "default"},
    "SelectOption": {"label", "description"},
    "__init__": {"title"},
}
# calls whose first positional argument is the visible message content
CONTENT_POSITIONAL_CALLS = {"send_message", "send", "reply", "edit_message", "edit_original_response"}


def _parse(relative_path: str) -> ast.Module:
    """Parses one of the story source files into an AST."""
    return ast.parse((ROOT / relative_path).read_text(encoding="utf-8"))


def _has_cjk(node: ast.AST) -> bool:
    """Returns True when a string constant contains CJK or full-width characters."""
    return (
        isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and CJK_PATTERN.search(node.value) is not None
    )


def _call_name(call: ast.Call) -> Optional[str]:
    """Returns the final attribute or identifier name of a call target."""
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    if isinstance(call.func, ast.Name):
        return call.func.id
    return None


def _is_log_call(call: ast.Call) -> bool:
    """Returns True for ``logger.info(...)``-style calls."""
    return isinstance(call.func, ast.Attribute) and call.func.attr in LOG_METHODS


def _docstring_nodes(tree: ast.Module) -> Set[int]:
    """Collects the ids of docstring constant nodes."""
    ids: Set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                ids.add(id(body[0].value))
    return ids


def _log_argument_nodes(tree: ast.Module) -> Set[int]:
    """Collects the ids of every node nested inside a logger call."""
    ids: Set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _is_log_call(node):
            for inner in ast.walk(node):
                ids.add(id(inner))
    return ids


def _command_registration_nodes(tree: ast.Module) -> Set[int]:
    """Collects nodes of slash-command registration (names/descriptions are global, not per guild)."""
    ids: Set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _call_name(node) in {"command", "Group"}:
            for inner in ast.walk(node):
                ids.add(id(inner))
    return ids


def _cjk_literals(tree: ast.Module, only_user_facing: bool) -> List[Tuple[int, str]]:
    """Finds CJK string literals that are not docstrings or logging arguments."""
    skipped = _docstring_nodes(tree) | _log_argument_nodes(tree) | _command_registration_nodes(tree)
    found: List[Tuple[int, str]] = []
    if only_user_facing:
        for call in (n for n in ast.walk(tree) if isinstance(n, ast.Call)):
            if _is_log_call(call):
                continue
            name = _call_name(call)
            if name in CONTENT_POSITIONAL_CALLS and call.args:
                candidates: List[ast.AST] = [call.args[0]]
            else:
                candidates = []
            for keyword in call.keywords:
                if keyword.arg in USER_FACING_KWARGS.get(name or "", set()):
                    candidates.append(keyword.value)
            if name in {"add_field"}:
                candidates.extend(call.args)
            if name == "set_footer":
                candidates.extend(call.args)
            for candidate in candidates:
                for inner in ast.walk(candidate):
                    if _has_cjk(inner) and id(inner) not in skipped:
                        found.append((inner.lineno, inner.value))
        return found
    for node in ast.walk(tree):
        if _has_cjk(node) and id(node) not in skipped:
            found.append((node.lineno, node.value))
    return found


@pytest.mark.parametrize("relative_path", STORY_FILES)
def test_no_cjk_in_user_facing_calls(relative_path: str) -> None:
    """User-facing call arguments (including f-strings) must not hard-code CJK text."""
    offenders = _cjk_literals(_parse(relative_path), only_user_facing=True)
    assert not offenders, f"{relative_path} hard-codes user-facing text: {offenders[:5]}"


@pytest.mark.parametrize("relative_path", STORY_FILES)
def test_no_cjk_string_literals_outside_logs_and_docstrings(relative_path: str) -> None:
    """Strings assigned to variables and sent later must not hide CJK text either."""
    offenders = _cjk_literals(_parse(relative_path), only_user_facing=False)
    assert not offenders, f"{relative_path} contains CJK literals: {offenders[:5]}"


# ------------------------------------------------------------ translation files


def _story_translation_files(locale: str) -> List[Path]:
    """Lists every story-related translation file of one locale."""
    base = ROOT / "translations" / locale
    files = sorted((base / "story").glob("*.json"))
    files.append(base / "commands" / "story.json")
    return files


def _flatten(data: Any, prefix: Tuple[str, ...] = ()) -> Iterator[Tuple[str, ...]]:
    """Yields every leaf key path of a nested dictionary."""
    if isinstance(data, dict):
        for key, value in data.items():
            yield from _flatten(value, prefix + (key,))
    else:
        yield prefix


def _placeholders(text: str) -> Set[str]:
    """Extracts ``{name}`` format placeholders from a translated string."""
    return set(re.findall(r"\{(\w+)\}", text))


def _resolve(locale: str, path: Tuple[str, ...]) -> Optional[Any]:
    """Resolves a translate() path against the JSON files of one locale."""
    for split in range(len(path) - 1, 0, -1):
        candidate = ROOT / "translations" / locale / Path(*path[:split]).with_suffix(".json")
        if candidate.is_file():
            node: Any = json.loads(candidate.read_text(encoding="utf-8"))
            for key in path[split:]:
                if not isinstance(node, dict) or key not in node:
                    return None
                node = node[key]
            return node
    return None


def test_story_translation_files_exist_in_every_locale() -> None:
    """Each locale ships the same set of story translation files."""
    names = {
        locale: sorted(p.relative_to(ROOT / "translations" / locale).as_posix() for p in _story_translation_files(locale))
        for locale in LOCALES
    }
    for locale in LOCALES:
        assert names[locale] == names["zh_TW"], f"{locale} story files differ from zh_TW"
        for path in _story_translation_files(locale):
            assert path.is_file(), f"missing {path}"


def test_story_translation_key_sets_identical_across_locales() -> None:
    """Every story translation file has exactly the same keys in all locales."""
    for relative in (p.relative_to(ROOT / "translations" / "zh_TW") for p in _story_translation_files("zh_TW")):
        key_sets = {
            locale: set(_flatten(json.loads((ROOT / "translations" / locale / relative).read_text(encoding="utf-8"))))
            for locale in LOCALES
        }
        for locale in LOCALES:
            assert key_sets[locale] == key_sets["zh_TW"], (
                f"{relative} keys differ in {locale}: "
                f"missing={sorted(key_sets['zh_TW'] - key_sets[locale])} "
                f"extra={sorted(key_sets[locale] - key_sets['zh_TW'])}"
            )


def test_story_translation_placeholders_match_across_locales() -> None:
    """Format placeholders must be the same in every locale of a key."""
    for relative in (p.relative_to(ROOT / "translations" / "zh_TW") for p in _story_translation_files("zh_TW")):
        loaded = {
            locale: json.loads((ROOT / "translations" / locale / relative).read_text(encoding="utf-8"))
            for locale in LOCALES
        }
        for key_path in _flatten(loaded["zh_TW"]):
            expected = None
            for locale in LOCALES:
                node: Any = loaded[locale]
                for key in key_path:
                    node = node[key]
                assert isinstance(node, str) and node.strip(), f"{relative}:{key_path} empty in {locale}"
                if expected is None:
                    expected = _placeholders(node)
                assert _placeholders(node) == expected, f"{relative}:{key_path} placeholders differ in {locale}"


def _literal_translate_paths(relative_path: str) -> List[Tuple[int, Tuple[str, ...]]]:
    """Collects the literal key paths passed to translate()/_t() in one file."""
    paths: List[Tuple[int, Tuple[str, ...]]] = []
    for call in (n for n in ast.walk(_parse(relative_path)) if isinstance(n, ast.Call)):
        name = _call_name(call)
        if name not in TRANSLATE_NAMES or any(isinstance(arg, ast.Starred) for arg in call.args):
            continue  # the _t() wrapper definitions forward *path and are not call sites
        first_is_literal_key = isinstance(call.args[0], ast.Constant) if call.args else False
        # translate() always takes the guild id first; _t() takes it only when the class has no fixed guild.
        skip_first = name == "translate" or not first_is_literal_key
        args = call.args[1:] if skip_first else call.args
        literal: List[str] = []
        for arg in args:
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                literal.append(arg.value)
            else:
                break
        paths.append((call.lineno, tuple(literal)))
    return paths


@pytest.mark.parametrize("relative_path", STORY_FILES)
def test_translate_paths_resolve_in_all_locales(relative_path: str) -> None:
    """Every literal translate() path resolves to a string in all four locales."""
    paths = _literal_translate_paths(relative_path)
    for line, path in paths:
        assert len(path) >= 3, f"{relative_path}:{line} has an incomplete translate path {path}"
        for locale in LOCALES:
            assert isinstance(_resolve(locale, path), str), f"{relative_path}:{line} {path} missing in {locale}"


def test_story_files_actually_use_translate() -> None:
    """The converted files must route their text through the translation layer."""
    for relative_path in STORY_FILES:
        assert _literal_translate_paths(relative_path), f"{relative_path} never calls translate()"


# ------------------------------------------------------------ runtime behaviour


class _FakeLanguageManager:
    """Returns the dotted key path so tests can see which key was requested."""

    def translate(self, guild_id: str, *path: str, **kwargs: Any) -> str:
        """Mimics LanguageManager.translate with a recognisable output."""
        suffix = f"|{sorted(kwargs.items())}" if kwargs else ""
        return f"<{guild_id}:{'.'.join(path)}{suffix}>"


def _fake_manager() -> SimpleNamespace:
    """Builds the minimal StoryManager stand-in the UI classes need."""
    return SimpleNamespace(
        language_manager=_FakeLanguageManager(),
        character_db=SimpleNamespace(),
        _get_db=lambda guild_id: SimpleNamespace(),
        interventions={},
        bot=SimpleNamespace(),
    )


def test_modals_use_translated_titles_and_labels() -> None:
    """Modal titles and text inputs come from the language manager, per guild."""
    from cogs.story.ui import modals

    async def build() -> List[Any]:
        manager = _fake_manager()
        return [
            modals.WorldCreateModal(manager, 42),
            modals.CharacterCreateModal(manager, 42),
            modals.StoryStartModal(manager, manager.bot, 42, 7, "world"),
            modals.InterventionModal(manager, 42),
        ]

    for modal in asyncio.run(build()):
        assert modal.title.startswith("<42:story.modals."), modal.title
        for child in modal.children:
            assert child.label and child.label.startswith("<42:story.modals."), child.label
            if child.placeholder:
                assert child.placeholder.startswith("<42:story.modals."), child.placeholder


def test_modal_inputs_are_not_shared_between_guilds() -> None:
    """Two modals for different guilds must not overwrite each other's labels."""
    from cogs.story.ui import modals

    async def build() -> Tuple[Any, Any]:
        manager = _fake_manager()
        return modals.WorldCreateModal(manager, 1), modals.WorldCreateModal(manager, 2)

    first, second = asyncio.run(build())
    assert first.world_name.label.startswith("<1:")
    assert second.world_name.label.startswith("<2:")


def test_active_story_view_buttons_are_translated() -> None:
    """The active-story control panel labels its buttons through translate()."""
    from cogs.story.ui import views

    async def build() -> Any:
        instance = SimpleNamespace(
            guild_id=9, channel_id=3, is_active=True, narration_enabled=True, active_character_ids=[]
        )
        return views.ActiveStoryView(manager=_fake_manager(), story_instance=instance)

    view = asyncio.run(build())
    labels = [child.label for child in view.children]
    assert len(labels) == 4
    assert all(label.startswith("<9:story.views.") for label in labels), labels


def test_initial_story_view_is_translated() -> None:
    """The pre-story menu labels its select and buttons through translate()."""
    from cogs.story.ui import views

    async def build() -> Any:
        return views.InitialStoryView(manager=_fake_manager(), channel_id=3, guild_id=9, ui_manager=SimpleNamespace())

    view = asyncio.run(build())
    for child in view.children:
        text = child.placeholder if hasattr(child, "placeholder") else child.label
        assert text.startswith("<9:story.views."), text
