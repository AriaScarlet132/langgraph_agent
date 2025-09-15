import uuid
import json
from typing import Optional, Dict, Any, Generator, Tuple, List
from langchain_core.messages import ToolMessage, AIMessageChunk, AIMessage, HumanMessage
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
        # 注意：LangGraph/LCEL 期望的是 LangChain 的消息对象，而不是 {role, content} 字典
        # 否则下游不会把它识别为用户输入，导致“模型看不到提问”。
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
                # 用于在流式过程中暂存工具调用的参数片段
                # 结构: { index: { 'name': str|None, 'id': str|None, 'args_str': str } }
                tool_call_buffers: Dict[int, Dict[str, Any]] = {}
                # 跟踪已发出的工具调用（按 tool_call_id 关联以便结合工具返回）
                # 结构: { tool_call_id: { 'tool_name': str, 'arguments': Any } }
                pending_tool_calls: Dict[str, Dict[str, Any]] = {}

                for token, metadata in self.agent.stream(state, stream_mode="messages", config=config):
                    # 工具调用消息：不限制节点，直接转发工具执行结果
                    if isinstance(token, ToolMessage):
                        payload: Dict[str, Any] = {
                            "type": "tool_message",
                            "content": token.content,
                            "thread_id": thread_id
                        }
                        # 尝试携带 tool_call_id 和 tool_name 便于前端关联
                        tool_call_id = getattr(token, "tool_call_id", None)
                        tool_name = getattr(token, "name", None)
                        if tool_call_id:
                            payload["tool_call_id"] = tool_call_id
                        if tool_name:
                            payload["tool_name"] = tool_name
                        yield payload

                        # 如果之前记录了对应的工具调用参数，则组合一个完整的结果事件
                        if tool_call_id and tool_call_id in pending_tool_calls:
                            prev = pending_tool_calls.pop(tool_call_id)
                            yield {
                                "type": "tool_result",
                                "tool_name": tool_name or prev.get("tool_name", ""),
                                "arguments": prev.get("arguments"),
                                "result": token.content,
                                "tool_call_id": tool_call_id,
                                "thread_id": thread_id
                            }

                    # 处理 AIMessage（非分片），用于在 finish_reason=tool_calls 时输出完整工具调用
                    if isinstance(token, AIMessage) and metadata.get('langgraph_node') == 'agent':
                        # OpenAI/DeepSeek 等模型会在完成工具调用构造后给出 finish_reason=tool_calls
                        finish_reason = None
                        try:
                            finish_reason = (getattr(token, "response_metadata", None) or {}).get("finish_reason")
                        except Exception:
                            finish_reason = None

                        if finish_reason == "tool_calls":
                            # 将已累计的分片组装为完整的工具调用
                            for idx, buf in sorted(tool_call_buffers.items(), key=lambda x: x[0]):
                                name = buf.get("name")
                                args_str = buf.get("args_str", "")
                                tool_call_id = buf.get("id")

                                # 如果 name 还缺失，尝试从 token.tool_calls 补齐
                                try:
                                    if not name and getattr(token, "tool_calls", None):
                                        calls = token.tool_calls  # type: ignore
                                        if isinstance(calls, list) and idx < len(calls):
                                            name = calls[idx].get("name") or name
                                except Exception:
                                    pass

                                # 尝试解析 JSON 参数
                                parsed_args: Any = args_str
                                if isinstance(args_str, str):
                                    s = args_str.strip()
                                    if s:
                                        try:
                                            parsed_args = json.loads(s)
                                        except Exception:
                                            # 解析失败则原样返回字符串，避免丢失信息
                                            parsed_args = s

                                event: Dict[str, Any] = {
                                    "type": "tool_call",
                                    "tool_name": name or "",
                                    "arguments": parsed_args,
                                    "thread_id": thread_id
                                }
                                if tool_call_id:
                                    event["tool_call_id"] = tool_call_id
                                yield event

                                # 记录待匹配的工具调用，便于结合后续 ToolMessage 输出完整结果
                                if tool_call_id:
                                    pending_tool_calls[tool_call_id] = {
                                        "tool_name": name or "",
                                        "arguments": parsed_args,
                                    }

                            # 清空缓冲，准备下一轮
                            tool_call_buffers.clear()
                            continue

                        # 非流式（一次性提供完整 tool_calls）的兜底处理
                        if getattr(token, "tool_calls", None) and not tool_call_buffers:
                            try:
                                for call in token.tool_calls:  # type: ignore
                                    name = call.get("name", "")
                                    args_val = call.get("args")
                                    tool_call_id = call.get("id")
                                    # 如果是字符串，尽量解析 JSON
                                    if isinstance(args_val, str):
                                        try:
                                            args_val = json.loads(args_val)
                                        except Exception:
                                            pass
                                    event = {
                                        "type": "tool_call",
                                        "tool_name": name,
                                        "arguments": args_val,
                                        "thread_id": thread_id
                                    }
                                    if tool_call_id:
                                        event["tool_call_id"] = tool_call_id
                                        pending_tool_calls[tool_call_id] = {
                                            "tool_name": name,
                                            "arguments": args_val,
                                        }
                                    yield event
                            except Exception:
                                # 保底：不让异常打断主流程
                                pass

                    # 处理 AIMessageChunk（分片），累积工具调用参数与输出文本内容
                    if isinstance(token, AIMessageChunk):
                        # 文本内容分片（仅 agent 节点）
                        if metadata.get('langgraph_node') == 'agent' and token.content:
                            yield {
                                "type": "agent_message",
                                "content": token.content,
                                "thread_id": thread_id
                            }

                        # 工具调用分片（逐步拼接 JSON）
                        try:
                            tc_chunks: List[Any] = getattr(token, "tool_call_chunks", None) or []
                            for ch in tc_chunks:
                                # 兼容对象或字典两种形态
                                get = (lambda k, d=ch: getattr(d, k, None) if not isinstance(d, dict) else d.get(k))
                                idx = get("index") or 0
                                name_piece = get("name")
                                args_piece = get("args") or ""
                                id_piece = get("id")

                                buf = tool_call_buffers.setdefault(int(idx), {"name": None, "id": None, "args_str": ""})
                                if name_piece and not buf["name"]:
                                    buf["name"] = name_piece
                                if isinstance(args_piece, str):
                                    buf["args_str"] += args_piece
                                # 如果提供了 id 则记录
                                if id_piece and not buf["id"]:
                                    buf["id"] = id_piece
                        except Exception:
                            # 忽略分片解析异常，避免中断主流程
                            pass
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