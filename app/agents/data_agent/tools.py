from typing import Annotated
from langgraph.prebuilt import InjectedState
from langchain_core.runnables import RunnableConfig
from app.agents.data_agent.state import State

def get_weather(city: str) -> str:
    """
    Get weather for a given city.

    Args:
        city (str): The name of the city.
    """
    return f"The weather in {city} is sunny with a high of 25°C and a low of 15°C."

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

    from app.utils.data import get_token, query_data
    token = get_token(state['host'])
    data = query_data(state['host'], token, state['username'], sql, table)
    return str(data)