from app.agents.data_agent.data_agent import agent
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, AIMessageChunk

state = {
    "messages": [HumanMessage(content="查下系统里有几个工单")],
    "username": "Admin",
    "table_description": "ServiceOrderInfoQueryDS_Datav 工单情况",
    "host": "http://lkf-datav.lbiya.cn:7080",
    "context": {}
}

import uuid

config = {"configurable": {"thread_id": f"debug_{uuid.uuid4().hex}"}}

count = 0
for token, metadata in agent.stream(state, stream_mode="messages", config=config):
    count += 1
    print(f"--- TOKEN #{count} --- type={type(token).__name__} metadata={metadata}")
    # print token attributes
    try:
        attrs = {k: getattr(token, k) for k in dir(token) if not k.startswith('_') and k.isidentifier()}
        print('attrs keys:', list(attrs.keys())[:40])
    except Exception as e:
        print('attrs read error:', e)
    # inspect common fields
    if isinstance(token, AIMessage):
        print('AIMessage.tool_calls:', getattr(token, 'tool_calls', None))
        print('AIMessage.response_metadata:', getattr(token, 'response_metadata', None))
    if isinstance(token, AIMessageChunk):
        print('AIMessageChunk.tool_call_chunks:', getattr(token, 'tool_call_chunks', None))
        print('AIMessageChunk.content:', token.content)
    if isinstance(token, ToolMessage):
        print('ToolMessage.content:', token.content)
        print('ToolMessage.tool_call_id:', getattr(token, 'tool_call_id', None))
        print('ToolMessage.name:', getattr(token, 'name', None))
    if count >= 60:
        break
print('stream finished')
