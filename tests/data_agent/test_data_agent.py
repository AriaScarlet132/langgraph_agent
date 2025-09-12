from app.agents.data_agent.data_agent import agent
from langchain_core.messages import ToolMessage, AIMessageChunk, AIMessage, HumanMessage

def stream_agent_response(query, config=None):
	# 假设 agent.invoke 支持 stream=True 参数并返回可迭代对象
	for token, metadata in agent.stream(query, stream_mode="messages", config=config):
		if metadata['langgraph_node'] == 'agent':
			if isinstance(token, ToolMessage):
				print(f"[工具消息] {token.content}\n", flush=True)
			if isinstance(token, AIMessage):
				if token.tool_calls:
					for call in token.tool_calls:
						print(f"[调用工具] {call['name']}，参数: {call['args']}\n", flush=True)
			if isinstance(token, AIMessageChunk) and token.content and token.content != '':
				print(token.content, end='', flush=True)
				
		# elif metadata['langgraph_node'] == 'pre_model_hook':
		# 	print("[摘要节点输出]", token, flush=True)
		# 	print("\n", flush=True)
		# 	print(metadata, flush=True)
		# 	print("\n", flush=True)

if __name__ == "__main__":
	config = {
		"configurable": {
			"thread_id": "test_thread_11",
		}
	}

	# 构造 state - 使用正确的消息格式
	state = {
		"messages": [HumanMessage(content="我刚刚说了什么？")],
		"username": "Admin",
		"table_description": "ServiceOrderInfoQueryDS_Datav 工单情况",
		"host": "http://192.168.10.21:3000",
		"context": {}
	}

	stream_agent_response(state, config=config)
