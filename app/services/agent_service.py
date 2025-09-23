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
            
        Returns:
            generator: yields response event dictionaries
        """
        generator_closing = False
        current_message_id: Optional[str] = None
        try:
            state, config = self.prepare_state(query, thread_id, extra_state)

            # 返回开始/结束标记（开始）
            thread_id = config["configurable"]["thread_id"]
            # 发送一条空的 message_start，用于客户端标记对话开始
            # 为本次回复生成一个共享的 message_id，所有片段和工具事件将使用同一个 id
            current_message_id = str(uuid.uuid4())
            yield {
                "type": "message_start",
                "content": "",
                "thread_id": thread_id,
                "message_id": current_message_id
            }

            # 流式处理代理响应 - 完全按照test_data_agent.py的逻辑
            tool_call_buffers: Dict[int, Dict[str, Any]] = {}
            pending_tool_calls: Dict[str, Dict[str, Any]] = {}

            stream_iter = self.agent.stream(state, stream_mode="messages", config=config)
            try:
                for token, metadata in stream_iter:
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
                        payload["message_id"] = current_message_id or str(uuid.uuid4())
                        # 如果没有 current_message_id（极端情况），回退为新的 uuid
                        if not current_message_id:
                            current_message_id = payload["message_id"]
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
                                "thread_id": thread_id,
                                "message_id": prev.get("message_id") or current_message_id or str(uuid.uuid4())
                            }

                    # 处理 AIMessage（非分片），用于在 finish_reason=tool_calls 时输出完整工具调用
                    if isinstance(token, AIMessage) and metadata.get('langgraph_node') == 'agent':
                        finish_reason = None
                        try:
                            finish_reason = (getattr(token, "response_metadata", None) or {}).get("finish_reason")
                        except Exception:
                            finish_reason = None

                        if finish_reason == "tool_calls":
                            for idx, buf in sorted(tool_call_buffers.items(), key=lambda x: x[0]):
                                name = buf.get("name")
                                args_str = buf.get("args_str", "")
                                tool_call_id = buf.get("id")

                                try:
                                    if not name and getattr(token, "tool_calls", None):
                                        calls = token.tool_calls  # type: ignore
                                        if isinstance(calls, list) and idx < len(calls):
                                            name = calls[idx].get("name") or name
                                except Exception:
                                    pass

                                parsed_args: Any = args_str
                                if isinstance(args_str, str):
                                    s = args_str.strip()
                                    if s:
                                        try:
                                            parsed_args = json.loads(s)
                                        except Exception:
                                            parsed_args = s

                                event: Dict[str, Any] = {
                                    "type": "tool_call",
                                    "tool_name": name or "",
                                    "arguments": parsed_args,
                                    "thread_id": thread_id
                                }
                                if tool_call_id:
                                    event["tool_call_id"] = tool_call_id
                                event["message_id"] = current_message_id or str(uuid.uuid4())
                                if not current_message_id:
                                    current_message_id = event["message_id"]
                                yield event

                                if tool_call_id:
                                    pending_tool_calls[tool_call_id] = {
                                        "tool_name": name or "",
                                        "arguments": parsed_args,
                                    }

                            tool_call_buffers.clear()
                            continue

                        if getattr(token, "tool_calls", None) and not tool_call_buffers:
                            try:
                                for call in token.tool_calls:  # type: ignore
                                    name = call.get("name", "")
                                    args_val = call.get("args")
                                    tool_call_id = call.get("id")
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
                                    event["message_id"] = current_message_id or str(uuid.uuid4())
                                    if not current_message_id:
                                        current_message_id = event["message_id"]
                                    # yield event # 此为预置节点 也就是大模型开始调用工具但是未拼装好参数时的消息
                            except Exception:
                                pass

                    # 处理 AIMessageChunk（分片），累积工具调用参数与输出文本内容
                    if isinstance(token, AIMessageChunk):
                        # 文本内容分片（仅 agent 节点）
                        if metadata.get('langgraph_node') == 'agent' and getattr(token, 'content', None):
                            yield {
                                "type": "agent_message",
                                "content": token.content,
                                "thread_id": thread_id,
                                "message_id": current_message_id or str(uuid.uuid4())
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
                                if id_piece and not buf["id"]:
                                    buf["id"] = id_piece
                                # 将本次片段所属的 message_id 也记录到缓冲，便于后续组合
                                if current_message_id:
                                    buf.setdefault("message_id", current_message_id)
                        except Exception:
                            pass
            except GeneratorExit:
                # 标记为正在关闭，避免在外层 finally 中再 yield
                generator_closing = True
                try:
                    if hasattr(stream_iter, 'close'):
                        stream_iter.close()
                except Exception:
                    pass
                # 返回以正常结束生成器（不要重新抛出 GeneratorExit）
                return
            except Exception as stream_error:
                yield {
                    "type": "error",
                    "content": f"流式处理中断: {str(stream_error)}",
                    "thread_id": thread_id,
                    "message_id": current_message_id or str(uuid.uuid4())
                }
            finally:
                try:
                    if hasattr(stream_iter, 'close'):
                        stream_iter.close()
                except Exception:
                    pass

        except GeneratorExit:
            # 外部关闭生成器（例如客户端断开），优雅结束
            generator_closing = True
            return
        except Exception as e:
            yield {
                "type": "error",
                "content": f"处理请求时发生错误: {str(e)}",
                "thread_id": thread_id if 'thread_id' in locals() else None,
                "message_id": current_message_id or str(uuid.uuid4())
            }
        finally:
            # 流处理完成，发送一条空的 message_end，用于客户端标记对话结束
            try:
                # 只有在生成器没有被外部关闭的情况下发送结束事件
                if not generator_closing:
                    yield {
                        "type": "message_end",
                        "content": "",
                        "thread_id": thread_id,
                        "message_id": current_message_id or str(uuid.uuid4())
                    }
            except Exception:
                # 在极端错误情况下，忽略结束消息发送错误
                pass


# 全局服务实例
agent_service = AgentService()