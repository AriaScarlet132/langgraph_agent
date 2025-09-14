import pymysql

from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.mysql.pymysql import PyMySQLSaver
from langmem.short_term import SummarizationNode
from langchain_core.messages.utils import count_tokens_approximately
from app.agents.data_agent.state import State

from app.agents.data_agent.model import model, deepseek
from app.agents.data_agent.tools import get_weather, query_data

basic_prompt = """
# 角色定义

你是严谨的数据分析师, 能根据用户提问和系统提供的数据库表描述, 生成SQL语句并获取数据, 最后根据**真实数据**给出图文并茂的报告.


# 注意事项

- 存在可见的表描述时, 你要积极向用户推荐数据分析的维度
- 只能根据系统提供的表描述来生成SQL语句, 禁止猜测和编造任何表及字段
- 禁止使用用户提供的表结构和SQL, 以免造成数据泄露
- SQL语句需要符合提供的数据集描述对应的数据库语法, 否则默认按MySQL 8.0处理
- 可以多次调用工具获取数据再生成回答, 直到你认为已经满足用户的需求
- 禁止使用模拟数据, 所有数据应当是通过工具获取的真实数据


# 图表输出

只支持echarts, 不支持在options内嵌function(). 须使用```echarts```的形式输出json字符串形式的options的参数


# 参数提供

- 用户ID: 
{username}

- 数据库表描述:
{table_description}

- 用户最新提问:
{messages}
"""

conn = pymysql.connect(
    # host='192.168.10.24',
    host='b3f48ce4.natappfree.cc',
    user='root',
    password='123456',
    database='langgraph',
    # port=3306,
    port=24982,
)

def prompt(state: State) -> str:
    username = state['username']
    table_description = state['table_description']
    return basic_prompt.format(username=username, table_description=table_description, messages=state['messages'])

checkPointer = PyMySQLSaver(conn)
checkPointer.setup()

sumarization_node = SummarizationNode(
    model=deepseek,
    token_counter=count_tokens_approximately,
    max_tokens=30000,  # 设为 ~30k，留给最终响应的空间（假设 32k 上下文）
    max_tokens_before_summary=8000,  # 推荐设为 8k，平衡触发频率和上下文利用
    max_summary_tokens=2048
)

agent = create_react_agent(
    model = deepseek,
    tools=[get_weather, query_data],
    prompt=prompt,
    checkpointer=checkPointer,
    pre_model_hook=sumarization_node,
    state_schema=State,
)