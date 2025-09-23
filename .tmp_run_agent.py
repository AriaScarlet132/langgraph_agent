from app.agents.data_agent.data_agent import agent
from langchain_core.messages import HumanMessage

state = {
    "messages": [HumanMessage(content="查下系统里有几个工单")],
    "username": "Admin",
    "table_description": "ServiceOrderInfoQueryDS_Datav",
    "host": "http://lkf-datav.lbiya.cn:7080",
    "context": {}
}

config = {"configurable": {"thread_id": "debug_thread"}}

print('Running agent.run...')
try:
    out = agent.run(state, config=config)
    print('Agent run output:')
    print(out)
except Exception as e:
    print('Agent run error:')
    import traceback
    traceback.print_exc()
