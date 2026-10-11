"""Translation helper shared by the story views and modals."""

from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from cogs.language_manager import LanguageManager


class StoryTextMixin:
    """Mixin giving a story UI component guild-aware access to translations.

    A component calls ``_init_i18n`` once, before it builds any translated
    text, and then uses ``_t`` with a literal key path.
    """

    _i18n_language_manager: "LanguageManager"
    _i18n_guild_id: Optional[int]

    def _init_i18n(self, language_manager: "LanguageManager", guild_id: Optional[int]) -> None:
        """Stores the language manager and guild used by ``_t``.

        Args:
            language_manager: The bot's LanguageManager cog.
            guild_id: Guild whose language is used for all text of this component.

        Raises:
            RuntimeError: If no language manager is available.
        """
        if language_manager is None:
            raise RuntimeError("LanguageManager cog is not loaded; cannot translate story text")
        self._i18n_language_manager = language_manager
        self._i18n_guild_id = guild_id

    def _t(self, *path: str, **kwargs: Any) -> str:
        """Translates a story UI string for this component's guild.

        Args:
            *path: Translation key path, e.g. ``"story", "views", "join_button"``.
            **kwargs: Format arguments for the translated text.

        Returns:
            The translated text.
        """
        return self._i18n_language_manager.translate(str(self._i18n_guild_id), *path, **kwargs)
