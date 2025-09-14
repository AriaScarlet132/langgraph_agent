"""
测试流式响应的简化版本，使用模拟工具避免数据库连接问题
"""

import json
import requests

def test_with_simple_query():
    """使用不需要数据库的简单查询测试"""
    print("=== 测试简单查询（不涉及数据库）===")
    
    payload = {
        "query": "你好，请介绍一下你自己",  # 简单查询，应该不会调用数据库工具
        "thread_id": "simple_test",
        "state": {
            "username": "TestUser"
        }
    }
    
    response = requests.post(
        "http://localhost:5000/api/chat/stream",
        json=payload,
        headers={"Content-Type": "application/json"},
        stream=True
    )
    
    print(f"状态码: {response.status_code}")
    print("流式响应:")
    print("-" * 50)
    
    try:
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                if decoded_line.startswith('data: '):
                    data = decoded_line[6:]
                    try:
                        parsed_data = json.loads(data)
                        response_type = parsed_data.get('type')
                        content = parsed_data.get('content', '')
                        
                        if response_type == 'agent_message':
                            print(content, end='', flush=True)
                        elif response_type == 'tool_call':
                            print(f"\n[调用工具] {parsed_data.get('tool_name')}")
                            print(f"参数: {parsed_data.get('arguments')}")
                        elif response_type == 'tool_message':
                            print(f"\n[工具返回] {content}")
                        elif response_type == 'message_start':
                            print(f"[开始] {parsed_data.get('thread_id')}")
                        elif response_type == 'message_end':
                            print(f"\n[结束]")
                        elif response_type == 'error':
                            print(f"\n[错误] {content}")
                    except json.JSONDecodeError as e:
                        print(f"\n[解析错误] {e}: {data}")
    except Exception as e:
        print(f"连接错误: {e}")

def test_weather_query():
    """测试天气查询工具（应该可用）"""
    print("\n=== 测试天气查询工具 ===")
    
    payload = {
        "query": "北京今天天气怎么样？",  # 应该调用天气工具
        "thread_id": "weather_test",
    }
    
    response = requests.post(
        "http://localhost:5000/api/chat/stream",
        json=payload,
        headers={"Content-Type": "application/json"},
        stream=True
    )
    
    print(f"状态码: {response.status_code}")
    print("流式响应:")
    print("-" * 50)
    
    try:
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                if decoded_line.startswith('data: '):
                    data = decoded_line[6:]
                    try:
                        parsed_data = json.loads(data)
                        response_type = parsed_data.get('type')
                        content = parsed_data.get('content', '')
                        
                        if response_type == 'agent_message':
                            print(content, end='', flush=True)
                        elif response_type == 'tool_call':
                            print(f"\n[调用工具] {parsed_data.get('tool_name')}")
                        elif response_type == 'tool_message':
                            print(f"\n[工具返回] {content[:100]}...")  # 截取前100字符
                        elif response_type == 'message_start':
                            print(f"[开始] {parsed_data.get('thread_id')}")
                        elif response_type == 'message_end':
                            print(f"\n[结束]")
                        elif response_type == 'error':
                            print(f"\n[错误] {content}")
                    except json.JSONDecodeError as e:
                        print(f"\n[解析错误] {e}")
    except Exception as e:
        print(f"连接错误: {e}")

if __name__ == "__main__":
    test_with_simple_query()
    test_weather_query()