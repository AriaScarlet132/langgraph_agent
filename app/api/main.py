from flask import Flask, request, Response, jsonify
import json
from typing import Optional, Dict, Any
from app.api.agent_service import agent_service


app = Flask(__name__)


@app.route('/')
def hello():
    """健康检查端点"""
    return jsonify({
        "status": "ok",
        "message": "LangGraph Agent API is running"
    })


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    聊天API端点，支持流式响应
    
    请求体:
    {
        "query": "用户查询内容",
        "thread_id": "可选的线程ID", 
        "state": {
            "username": "可选的用户名",
            "host": "可选的主机地址",
            "table_description": "可选的表描述",
            "其他状态参数": "值"
        }
    }
    """
    try:
        # 解析请求数据
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求体不能为空"}), 400
        
        query = data.get('query')
        if not query:
            return jsonify({"error": "query 参数是必需的"}), 400
        
        thread_id = data.get('thread_id')
        extra_state = data.get('state', {})
        
        # 检查是否请求流式响应
        stream = data.get('stream', True)
        
        if stream:
            # 返回流式响应
            def generate():
                for response in agent_service.stream_agent_response(query, thread_id, extra_state):
                    yield f"data: {json.dumps(response, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
            
            return Response(
                generate(),
                mimetype='text/plain',
                headers={
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'X-Accel-Buffering': 'no'
                }
            )
        else:
            # 返回完整响应
            responses = []
            for response in agent_service.stream_agent_response(query, thread_id, extra_state):
                responses.append(response)
            
            return jsonify({
                "success": True,
                "responses": responses
            })
            
    except Exception as e:
        return jsonify({"error": f"处理请求时发生错误: {str(e)}"}), 500


@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    """
    专用的流式聊天端点 (Server-Sent Events)
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求体不能为空"}), 400
        
        query = data.get('query')
        if not query:
            return jsonify({"error": "query 参数是必需的"}), 400
        
        thread_id = data.get('thread_id')
        extra_state = data.get('state', {})
        
        def generate():
            yield "data: " + json.dumps({"type": "start", "content": "开始处理请求"}, ensure_ascii=False) + "\n\n"
            
            for response in agent_service.stream_agent_response(query, thread_id, extra_state):
                yield f"data: {json.dumps(response, ensure_ascii=False)}\n\n"
            
            yield "data: " + json.dumps({"type": "end", "content": "处理完成"}, ensure_ascii=False) + "\n\n"
        
        return Response(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'X-Accel-Buffering': 'no'
            }
        )
        
    except Exception as e:
        return jsonify({"error": f"处理请求时发生错误: {str(e)}"}), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "端点不存在"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "服务器内部错误"}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
