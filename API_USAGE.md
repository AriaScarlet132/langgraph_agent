# LangGraph Agent REST API 使用指南

## 功能特性

✅ **已实现的需求:**
1. ✅ 接收 `query` 作为用户最新消息
2. ✅ 接收 `thread_id`，如果未传就自动生成UUID
3. ✅ 接收 `state` 字典，自动将键值对扩展到agent状态中
4. ✅ 返回流式响应作为Flask REST API端点服务

## API 端点

### 1. 健康检查
```
GET /
```

### 2. 聊天接口
```
POST /api/chat
```

**请求体示例:**
```json
{
    "query": "你能查一下系统里有几条工单吗？",
    "thread_id": "my_thread_123",  // 可选，不传会自动生成
    "stream": true,                 // 可选，默认true
    "state": {                      // 可选，会合并到agent状态中
        "username": "张三",
        "host": "http://192.168.10.21:3000",
        "table_description": "工单管理表",
        "custom_field": "自定义值"
    }
}
```

### 3. 流式聊天接口 (Server-Sent Events)
```
POST /api/chat/stream
```

**请求体格式相同，返回SSE流:**
```
data: {"type": "start", "content": "开始处理请求"}
data: {"type": "thread_id", "content": "thread_uuid123"}
data: {"type": "tool_call", "tool_name": "query_data", "arguments": {...}}
data: {"type": "ai_message", "content": "根据查询结果..."}
data: {"type": "end", "content": "处理完成"}
```

## 响应类型

- `thread_id`: 返回使用的线程ID
- `tool_call`: 工具调用信息
- `tool_message`: 工具执行结果
- `ai_message`: AI助手回复内容
- `error`: 错误信息

## 快速开始

### 1. 安装依赖
```bash
pip install -e .
# 或
uv sync
```

### 2. 启动API服务
```bash
python start_api.py
# 或
python -m app.api.main
```

### 3. 测试API
```bash
python tests/api_test.py
```

### 4. 使用curl测试
```bash
# 健康检查
curl http://localhost:5000/

# 发送聊天请求
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "你好，请介绍一下你的功能",
    "state": {
      "username": "测试用户"
    }
  }'
```

## 使用Python客户端

```python
import requests
import json

# 发送请求
response = requests.post(
    "http://localhost:5000/api/chat/stream",
    json={
        "query": "查询工单数据",
        "thread_id": "my_session",
        "state": {
            "username": "分析师",
            "table_description": "工单表"
        }
    },
    stream=True
)

# 处理流式响应
for line in response.iter_lines():
    if line and line.startswith(b'data: '):
        data = json.loads(line[6:])
        print(f"[{data['type']}] {data.get('content', '')}")
```

## 自定义状态参数

你可以通过 `state` 参数传递任何键值对，这些参数会直接合并到agent的状态中：

```json
{
    "query": "分析数据",
    "state": {
        "username": "数据分析师",
        "host": "http://custom-server:3000",
        "table_description": "自定义表描述",
        "department": "数据部门",
        "project_id": "PROJ001",
        "任意自定义字段": "任意值"
    }
}
```

## 服务器配置

默认配置:
- 主机: `0.0.0.0`
- 端口: `5000` 
- 调试模式: `True`

可在 `app/api/main.py` 中修改配置。