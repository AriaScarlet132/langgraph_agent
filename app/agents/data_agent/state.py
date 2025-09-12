
from typing import Any
from langgraph.prebuilt.chat_agent_executor import AgentState

class State(AgentState):
    username: str
    table_description: str
    host: str
    context: dict[str, Any]
