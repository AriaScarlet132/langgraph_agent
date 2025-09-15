from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from typing import Annotated
from langgraph.prebuilt import InjectedState
from langgraph.prebuilt.chat_agent_executor import AgentState

QWEN_API_KEY = "sk-8e8db79b2a674c13865028a046988791"

qwen = ChatOpenAI(
    model="qwen3-max-preview",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key=QWEN_API_KEY,
)

basic_prompt = """
you're a helpful assistant
"""

class State(AgentState):
    username: str
    city: str

def get_user_info(
    # access information that's dynamically updated inside the agent
        state: Annotated[State, InjectedState]) -> str:
    """
    Get user information.
    """
    return f"User {state['username']} is in {state['city']}."

def get_weather(
    # access information that's dynamically updated inside the agent
        state: Annotated[State, InjectedState]) -> str:
    """
    Get weather for a given city.
    """
    # 如果有全局 state，可以在这里输出
    return f"The weather in {state['city']} is sunny with a high of 25°C and a low of 15°C."

agent = create_react_agent(
    model=qwen,
    tools=[get_weather, get_user_info],
    prompt=basic_prompt,
    state_schema=State,
)

if __name__ == "__main__":
    from langchain_core.messages import HumanMessage

    response = agent.invoke(
        {
            "messages": [HumanMessage(content="我的用户名是啥？我现在在哪个城市？")],
            "username": "Aria",
            "city": "Shanghai"
        }
    )
    print("Agent Response:", response)