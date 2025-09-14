"""
检查代理实际加载的工具
"""

try:
    from app.agents.data_agent.data_agent import agent
    
    print("=== 代理工具检查 ===")
    print(f"代理类型: {type(agent)}")
    
    # 检查代理的工具
    if hasattr(agent, 'tools'):
        print(f"工具数量: {len(agent.tools)}")
        for i, tool in enumerate(agent.tools):
            print(f"工具 {i+1}:")
            print(f"  名称: {tool.name}")
            print(f"  描述: {tool.description}")
            print(f"  参数: {tool.args}")
            print()
    else:
        print("代理没有 tools 属性")
        print("代理的属性:", dir(agent))
        
    # 尝试获取工具的其他信息
    try:
        # 对于 LangGraph 代理，可能需要不同的方式访问工具
        if hasattr(agent, 'get_graph'):
            graph = agent.get_graph()
            print(f"图结构: {graph}")
        
        # 检查状态
        if hasattr(agent, 'get_state'):
            print("代理有 get_state 方法")
    except Exception as e:
        print(f"获取图信息失败: {e}")

except ImportError as e:
    print(f"导入失败: {e}")
except Exception as e:
    print(f"其他错误: {e}")