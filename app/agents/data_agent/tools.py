from typing import Annotated
from langgraph.prebuilt import InjectedState
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from app.agents.data_agent.state import State

@tool("get_weather", parse_docstring=True)
def get_weather(city: str) -> str:
    """
    Get weather for a given city.

    Args:
        city (str): The name of the city.
    """
    return f"The weather in {city} is sunny with a high of 25°C and a low of 15°C."

@tool("query_data", parse_docstring=True)
def query_data(
        # access information that's dynamically updated inside the agent
        state: Annotated[State, InjectedState],
        # access static data that is passed at agent invocation
        config: RunnableConfig,
        sql: str, 
        table: str) -> str:
    """
    Query data from a database.

    Args:
        sql (str): The SQL query to execute.
        table (str): The name of the table to query.
    """

    from app.utils.data import get_token, query_data as query_data_func
    token = get_token(state['host'])
    data = query_data_func(state['host'], token, state['username'], sql, table)
    return str(data)