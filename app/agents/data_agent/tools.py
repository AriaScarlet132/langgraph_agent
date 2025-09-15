from typing import Annotated
from langgraph.prebuilt import InjectedState
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from app.agents.data_agent.state import State
import logging

@tool
def get_weather(city: str) -> str:
    """
    Get weather for a given city.

    Args:
        city (str): The name of the city.
    """
    print(f"[get_weather] Called with city: {city}")
    # 如果有全局 state，可以在这里输出
    return f"The weather in {city} is sunny with a high of 25°C and a low of 15°C."

@tool
def query_data(
        # access information that's dynamically updated inside the agent
        state: Annotated[State, InjectedState],
        sql: str,
        table: str) -> str:
    """
    Query data from a database.

    Args:
        sql (str): The SQL query to execute.
        table (str): The name of the table to query.
    """


    print(f"[query_data] Called with sql: {sql}, table: {table}")
    print(f"[query_data] State: {state}")

    from app.utils.data import get_token, query_data as query_data_func
    # token = get_token(state['host'])
    # data = query_data_func(state['host'], token, state['username'], sql, table)
    return "12334"