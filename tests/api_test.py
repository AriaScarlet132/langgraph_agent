"""
Flask API 测试示例
展示如何使用 LangGraph Agent API
"""

import requests
import json
import time


# API 基础URL
BASE_URL = "http://localhost:5000"


def test_health_check():
    """测试健康检查端点"""
    print("=== 健康检查测试 ===")
    response = requests.get(f"{BASE_URL}/")
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    print()


def test_chat_non_stream():
    """测试非流式聊天API"""
    print("=== 非流式聊天测试 ===")
    
    payload = {
        "query": "你能查一下系统里有几条工单吗？",
        "stream": False,
        "state": {
            "username": "TestUser",
            "host": "http://192.168.10.21:3000",
            "table_description": "ServiceOrderInfoQueryDS_Datav 工单情况"
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/api/chat", 
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    print()


def test_chat_stream():
    """测试流式聊天API"""
    print("=== 流式聊天测试 ===")
    
    payload = {
        "query": "你好，请介绍一下你的功能",
        "thread_id": "test_thread_001",
        "state": {
            "username": "StreamTestUser"
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/api/chat/stream",
        json=payload,
        headers={"Content-Type": "application/json"},
        stream=True
    )
    
    print(f"状态码: {response.status_code}")
    print("流式响应:")
    
    for line in response.iter_lines():
        if line:
            decoded_line = line.decode('utf-8')
            if decoded_line.startswith('data: '):
                data = decoded_line[6:]  # 移除 'data: ' 前缀
                try:
                    parsed_data = json.loads(data)
                    print(f"[{parsed_data['type']}] {parsed_data.get('content', '')}")
                    
                    # 如果是工具调用，显示详细信息
                    if parsed_data['type'] == 'tool_call':
                        print(f"  工具: {parsed_data.get('tool_name')}")
                        print(f"  参数: {parsed_data.get('arguments')}")
                        
                except json.JSONDecodeError:
                    print(f"无法解析: {data}")
    print()


def test_simple_stream():
    """测试简单的流式响应"""
    print("=== 简单流式测试 ===")
    
    payload = {
        "query": "我刚刚说了什么？",
        "stream": True
    }
    
    response = requests.post(
        f"{BASE_URL}/api/chat",
        json=payload,
        headers={"Content-Type": "application/json"},
        stream=True
    )
    
    print(f"状态码: {response.status_code}")
    print("流式响应:")
    
    for line in response.iter_lines():
        if line:
            decoded_line = line.decode('utf-8')
            if decoded_line.startswith('data: '):
                data = decoded_line[6:]
                if data == '[DONE]':
                    print("[完成]")
                    break
                try:
                    parsed_data = json.loads(data)
                    print(f"[{parsed_data['type']}] {parsed_data.get('content', '')}")
                except json.JSONDecodeError:
                    print(f"无法解析: {data}")
    print()


def test_with_custom_state():
    """测试自定义状态参数"""
    print("=== 自定义状态测试 ===")
    
    payload = {
        "query": "请帮我分析数据",
        "thread_id": "custom_state_thread",
        "state": {
            "username": "DataAnalyst",
            "host": "http://custom-host:3000", 
            "table_description": "自定义数据表: 用户行为分析数据",
            "context": {
                "department": "数据分析部",
                "project": "用户画像项目"
            },
            "custom_param": "自定义参数值"
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/api/chat",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        # 获取前几个响应项来显示
        data = response.text.split('\n')[:10]
        for line in data:
            if line.strip():
                print(line)
    else:
        print(f"错误: {response.text}")
    print()


if __name__ == "__main__":
    print("LangGraph Agent API 测试")
    print("=" * 50)
    
    try:
        # 测试健康检查
        test_health_check()
        
        # 等待一秒
        time.sleep(1)
        
        # 测试非流式
        test_non_stream = input("测试非流式API？(y/n): ").lower() == 'y'
        if test_non_stream:
            test_chat_non_stream()
            time.sleep(1)
        
        # 测试流式
        test_stream = input("测试流式API？(y/n): ").lower() == 'y'
        if test_stream:
            test_chat_stream()
            time.sleep(1)
            
        # 测试简单流式
        test_simple = input("测试简单流式？(y/n): ").lower() == 'y'
        if test_simple:
            test_simple_stream()
            time.sleep(1)
            
        # 测试自定义状态
        test_custom = input("测试自定义状态？(y/n): ").lower() == 'y'
        if test_custom:
            test_with_custom_state()
            
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except requests.exceptions.ConnectionError:
        print("无法连接到API服务器，请确保服务器正在运行在 http://localhost:5000")
    except Exception as e:
        print(f"测试过程中发生错误: {e}")