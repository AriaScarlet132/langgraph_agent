#!/usr/bin/env python3
"""
LangGraph Agent API 启动脚本
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.api.main import app

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 启动 LangGraph Agent API 服务")
    print("=" * 50)
    print("API 端点:")
    print("  健康检查: GET  /")
    print("  聊天接口: POST /api/chat")
    print("  流式聊天: POST /api/chat/stream")
    print("=" * 50)
    print("服务器将在 http://0.0.0.0:5000 启动")
    print("按 Ctrl+C 停止服务")
    print("=" * 50)
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except Exception as e:
        print(f"❌ 启动服务时发生错误: {e}")