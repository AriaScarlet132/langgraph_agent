"""
调试流式响应的详细脚本
"""

import json
import requests

def debug_stream_response():
    """详细调试流式响应"""
    print("=== 调试流式响应 ===")
    
    payload = {
        "query": "查一下ServiceOrderInfoQueryDS_Datav这个表有几条记录",
        "thread_id": "debug_thread",
        "state": {
            "username": "DebugUser"
        }
    }
    
    response = requests.post(
        "http://localhost:5000/api/chat/stream",
        json=payload,
        headers={"Content-Type": "application/json"},
        stream=True
    )
    
    print(f"状态码: {response.status_code}")
    print("原始响应流:")
    print("-" * 80)
    
    line_count = 0
    for line in response.iter_lines():
        if line:
            line_count += 1
            decoded_line = line.decode('utf-8')
            print(f"第{line_count}行: {decoded_line}")
            
            if decoded_line.startswith('data: '):
                data = decoded_line[6:]  # 移除 'data: ' 前缀
                print(f"  -> 数据部分: {data}")
                try:
                    parsed_data = json.loads(data)
                    print(f"  -> 解析结果: {parsed_data}")
                    print(f"  -> 类型: {parsed_data.get('type')}")
                    print(f"  -> 内容: {parsed_data.get('content', 'N/A')}")
                    if 'tool_name' in parsed_data:
                        print(f"  -> 工具: {parsed_data.get('tool_name')}")
                        print(f"  -> 参数: {parsed_data.get('arguments')}")
                except json.JSONDecodeError as e:
                    print(f"  -> JSON解析错误: {e}")
            print("-" * 40)
    
    print(f"总共收到 {line_count} 行响应")

if __name__ == "__main__":
    debug_stream_response()