"""ModelManager: Loads config/llm.yaml and returns ModelFallbackMiddleware or priority lists based on agent_type."""
from __future__ import annotations

import asyncio
from typing import List, Tuple, Any
from addons.logging import get_logger

logger = get_logger(server_id="Bot", source="llm.model_manager")

from langchain.agents.middleware import ModelFallbackMiddleware

from addons import settings
from function import func
from llm.utils.model_init import create_model_instance


class ModelManager:
    """Manages LLM model priority by loading configuration and creating ModelFallbackMiddleware."""

    def __init__(self) -> None:
        self._load_config()

    def _load_config(self) -> None:
        try:
            # 從 addons.settings 的 llm_config 取得 model_priorities
            self.priorities = settings.llm_config.model_priorities or {}
        except Exception as e:
            try:
                asyncio.create_task(func.report_error(e, "llm/model_manager.py/_load_config"))
            except Exception:
                logger.error(f"llm/model_manager.py: failed to load llm_config: {e}")
            self.priorities = {}

    def _resolve_priority_list(self, agent_type: str) -> List[str]:
        """將設定檔中指定的 agent_type 轉成 provider:model 字串清單，順序保留"""
        try:
            if not self.priorities:
                return []
            # 支援 dict 或 list 結構
            entries = self.priorities.get(agent_type) if isinstance(self.priorities, dict) else None
            if entries is None and isinstance(self.priorities, list):
                # 如果 model_priorities 是 list，嘗試搜尋 list 中的 dict 項
                for item in self.priorities:
                    if isinstance(item, dict) and agent_type in item:
                        entries = item[agent_type]
                        break
            if entries is None:
                return []
            result: List[str] = []
            # entries 預期為 list of dicts: [{google: [..]}, {ollama: [..]}, ...]
            for provider_entry in entries:
                if isinstance(provider_entry, dict):
                    for provider, models in provider_entry.items():
                        if models is None:
                            continue
                        for model in models:
                            result.append(f"{provider}:{model}")
            return result
        except Exception as e:
            try:
                asyncio.create_task(func.report_error(e, "llm/model_manager.py/_resolve_priority_list"))
            except Exception:
                logger.error(f"llm/model_manager.py/_resolve_priority_list error: {e}")
            return []

    def get_model_priority_list(self, agent_type: str) -> List[str]:
        """Returns the full list of models for a given agent_type.

        This method is useful for streaming fallback scenarios where
        ModelFallbackMiddleware doesn't work (streaming mode).

        Args:
            agent_type: The agent type to get models for (e.g., 'info_model').

        Returns:
            List of model strings in priority order (e.g., ['google_genai:gemini-2.5-flash', 'ollama:gpt-oss:20b']).

        Raises:
            ValueError: If no model priorities are configured for the agent_type.
        """
        priorities = self._resolve_priority_list(agent_type)
        if not priorities:
            err = ValueError(f"No model priorities configured for agent_type '{agent_type}'")
            try:
                asyncio.create_task(func.report_error(err, "llm/model_manager.py/get_model_priority_list"))
            except Exception:
                logger.error("Failed to schedule func.report_error for missing model priorities")
            raise err
        return priorities

    def get_model(
        self, agent_type: str, *, guild_id: str = "0",
    ) -> Tuple[str, ModelFallbackMiddleware]:
        """Return the primary identifier and instrumented fallback middleware.

        Args:
            agent_type: Configured model priority category.
            guild_id: Guild context for fallback models, or ``0`` when absent.

        Returns:
            The primary identifier and middleware using recorded model instances.

        Raises:
            ValueError: No priorities are configured for the category.
        """
        # 先解析 priorities 並記錄，便於後續排查
        priorities = self._resolve_priority_list(agent_type)

        if not priorities:
            err = ValueError(f"No model priorities configured for agent_type '{agent_type}'")
            try:
                # 非同步上報錯誤，不要阻塞呼叫流程
                asyncio.create_task(func.report_error(err, "llm/model_manager.py/get_model"))
            except Exception:
                logger.error("Failed to schedule func.report_error for missing model priorities")
            # 明確丟出例外，讓呼叫端能夠判斷並處理
            raise err

        try:
            primary = priorities[0]
            fallback_models = [
                create_model_instance(model_name, guild_id=guild_id)
                for model_name in priorities[1:]
            ]
            fallback_mw = ModelFallbackMiddleware(*fallback_models)
            return primary, fallback_mw
        except Exception as e:
            try:
                asyncio.create_task(func.report_error(e, "llm/model_manager.py/get_model"))
            except Exception:
                logger.error("Failed to schedule func.report_error for ModelFallbackMiddleware error")
            # 保留原始例外以便上層取得詳細錯誤資訊
            raise


__all__ = ["ModelManager"]