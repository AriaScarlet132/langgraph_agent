import uuid
from typing import Optional, Dict, Any, Generator, Tuple
from langchain_core.messages import HumanMessage, ToolMessage, AIMessageChunk, AIMessage
from app.agents.data_agent.data_agent import agent


class AgentService:
    """LangGraph 代理服务，提供流式响应功能"""
    
    def __init__(self):
        self.agent = agent
    
    def generate_thread_id(self) -> str:
        """生成唯一的线程ID"""
        return f"thread_{uuid.uuid4().hex[:12]}"
    
    def prepare_state(self, 
                     query: str, 
                     thread_id: Optional[str] = None,
                     extra_state: Optional[Dict[str, Any]] = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        准备代理状态和配置
        
        Args:
            query: 用户查询消息
            thread_id: 线程ID，如果为None则自动生成
            extra_state: 额外的状态参数，会合并到state中
            
        Returns:
            tuple: (state, config)
        """
        if thread_id is None:
            thread_id = self.generate_thread_id()
        
        # 基础状态
        base_state = {
            "messages": [HumanMessage(content=query)],
            "username": "Admin",
            "table_description": "", 
            "host": "http://192.168.10.21:3000",
            "context": {}
        }
        
        # 合并额外状态
        if extra_state:
            base_state.update(extra_state)
        
        config = {
            "configurable": {
                "thread_id": thread_id,
            }
        }
        
        return base_state, config
    
    def stream_agent_response(self, 
                            query: str, 
                            thread_id: Optional[str] = None,
                            extra_state: Optional[Dict[str, Any]] = None) -> Generator[Dict[str, Any], None, None]:
        """
        生成代理的流式响应
        
        Args:
            query: 用户查询消息
            thread_id: 线程ID，如果为None则自动生成
            extra_state: 额外的状态参数
            
        Yields:
            dict: 包含响应类型和内容的字典
        """
        try:
            state, config = self.prepare_state(query, thread_id, extra_state)
            
            # 返回开始/结束标记（开始）
            thread_id = config["configurable"]["thread_id"]
            # 发送一条空的 message_start，用于客户端标记对话开始
            yield {
                "type": "message_start",
                "content": "",
                "thread_id": thread_id
            }
            
            # 流式处理代理响应 - 完全按照test_data_agent.py的逻辑
            try:
                for token, metadata in self.agent.stream(state, stream_mode="messages", config=config):
                    if metadata['langgraph_node'] == 'agent':
                        print(f"[AgentService] Agent token: \n{token}, \nmetadata: \n{metadata}")
                        # 工具调用消息
                        if isinstance(token, ToolMessage):
                            yield {
                                "type": "tool_message",
                                "content": token.content,
                                "thread_id": thread_id
                            }
                        
                        # AI消息（只处理工具调用，不处理内容）
                        if isinstance(token, AIMessage):
                            if token.tool_calls:
                                for call in token.tool_calls:
                                    yield {
                                        "type": "tool_call",
                                        "tool_name": call['name'],
                                        "arguments": call['args'],
                                        "thread_id": thread_id
                                    }
                        
                        # AI消息流式内容块（这是实际的响应内容）
                        if isinstance(token, AIMessageChunk) and token.content and token.content != '':
                            yield {
                                "type": "agent_message",
                                "content": token.content,
                                "thread_id": thread_id
                            }
            except Exception as stream_error:
                yield {
                    "type": "error", 
                    "content": f"流式处理中断: {str(stream_error)}",
                    "thread_id": thread_id
                }
                        
        except Exception as e:
            yield {
                "type": "error",
                "content": f"处理请求时发生错误: {str(e)}",
                "thread_id": thread_id if 'thread_id' in locals() else None
            }
        finally:
            # 流处理完成，发送一条空的 message_end，用于客户端标记对话结束
            try:
                yield {
                    "type": "message_end",
                    "content": "",
                    "thread_id": thread_id
                }
            except Exception:
                # 在极端错误情况下，忽略结束消息发送错误
                pass


# 全局服务实例
agent_service = AgentService()