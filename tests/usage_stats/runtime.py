"""Load real test frameworks without disturbing legacy global dependency stubs."""
from __future__ import annotations

import sys

_FRAMEWORK_PREFIXES = ("discord", "langchain", "langchain_core", "langgraph")
_original_modules = {
    name: module for name, module in sys.modules.copy().items()
    if name.split(".")[0] in _FRAMEWORK_PREFIXES
}
for _name in _original_modules:
    del sys.modules[_name]

try:
    import discord
    from discord.ext import commands
    from langchain.agents import create_agent
    from langchain_core.callbacks import (
        AsyncCallbackHandler, CallbackManager, CallbackManagerForLLMRun,
    )
    from langchain_core.language_models import BaseChatModel
    from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage, HumanMessage
    from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult

    FRAMEWORK_MODULES = {
        name: module for name, module in sys.modules.copy().items()
        if name.split(".")[0] in _FRAMEWORK_PREFIXES
    }
finally:
    for _name in tuple(sys.modules):
        if _name.split(".")[0] in _FRAMEWORK_PREFIXES:
            del sys.modules[_name]
    sys.modules.update(_original_modules)
