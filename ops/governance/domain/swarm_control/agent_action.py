"""Agent Action Type Alias.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Union
from .delegate import Delegate
from .finish import Finish
from .tool_call import ToolCall

AgentAction = Union[ToolCall, Delegate, Finish]
