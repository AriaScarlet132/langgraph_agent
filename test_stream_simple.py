"""
简化的流式响应测试，用于验证agent_service的流式逻辑
"""

import json
from app.services.agent_service import agent_service

def test_stream_response():
    """测试agent_service的流式响应"""
    print("开始测试agent_service流式响应...")
    
    try:
        query = "你好，请介绍一下你自己"
        thread_id = "test_simple"
        
        # 使用简单的状态，不涉及数据库
        extra_state = {
            "username": "TestUser",
            "host": "http://test",
            "table_description": "测试表",
        }
        
        print(f"查询: {query}")
        print("流式响应:")
        print("-" * 50)
        
        for response in agent_service.stream_agent_response(query, thread_id, extra_state):
            print(f"响应类型: {response['type']}")
            print(f"内容: {response.get('content', '')}")
            if 'tool_name' in response:
                print(f"工具: {response['tool_name']}")
                print(f"参数: {response.get('arguments', '')}")
            print("-" * 30)
            
    except Exception as e:
        print(f"测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_stream_response()