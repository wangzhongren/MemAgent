# server.py - Web API 服务，支持透明化工具调用流程

import os
import json
from flask import Flask, request, jsonify
from agents import MainAgent, MemoryAgent, ContextAgent
from agents.llm_client import LLMClient


app = Flask(__name__, static_folder='webui')
# 移除全局代理，改为会话级状态管理
session_agents = {}


def get_or_create_agents(session_id: str, work_dir: str = ".", llm_config: dict = None):
    """按会话ID管理代理实例"""
    if session_id not in session_agents:
        # 初始化 LLM 客户端
        llm_client = None
        if llm_config and llm_config.get("base_url") and llm_config.get("api_key"):
            llm_client = LLMClient(
                base_url=llm_config["base_url"],
                api_key=llm_config["api_key"],
                model_name=llm_config["model_name"]
            )
        
        main_agent = MainAgent(root_dir=work_dir, llm_client=llm_client)
        memory_agent = MemoryAgent(memory_file=os.path.join(work_dir, "memory.json"))
        context_agent = ContextAgent(memory_agent)
        
        session_agents[session_id] = {
            "main_agent": main_agent,
            "memory_agent": memory_agent,
            "context_agent": context_agent,
            "messages": []  # 存储对话历史
        }
    
    return session_agents[session_id]


@app.route('/')
def index():
    return app.send_static_file('index.html')


@app.route('/memories', methods=['GET'])
def get_memories():
    """获取所有记忆条目（使用默认会话）"""
    agents = get_or_create_agents("default")
    return jsonify(agents["memory_agent"].memories)


@app.route('/start_session', methods=['POST'])
def start_session():
    """开始新会话"""
    data = request.get_json()
    session_id = data.get("session_id", "default")
    work_dir = data.get("work_dir", ".")
    base_url = data.get("base_url", "").rstrip('/')
    api_key = data.get("api_key", "")
    model_name = data.get("model_name", "gpt-4")

    if not base_url or not api_key:
        return jsonify({"error": "缺少 base_url 或 api_key"}), 400

    llm_config = {
        "base_url": base_url,
        "api_key": api_key,
        "model_name": model_name
    }
    
    agents = get_or_create_agents(session_id, work_dir, llm_config)
    agents["messages"] = []  # 重置消息历史
    
    # 注入记忆上下文
    user_input = data.get("user_input", "")
    relevant_memories = agents["context_agent"].find_relevant_memories(user_input)
    context_str = "\n".join([f"{k}: {v}" for k, v in relevant_memories.items()]) if relevant_memories else ""
    
    if context_str:
        agents["messages"].append({
            "role": "system",
            "content": f"相关记忆:\n{context_str}"
        })
    agents["messages"].append({
        "role": "user",
        "content": user_input
    })
    
    return jsonify({
        "session_id": session_id,
        "context_used": context_str
    })


@app.route('/next_step', methods=['POST'])
def next_step():
    """执行下一步（LLM决策或工具调用）"""
    data = request.get_json()
    session_id = data.get("session_id", "default")
    
    if session_id not in session_agents:
        return jsonify({"error": "会话不存在，请先调用 /start_session"}), 400
        
    agents = session_agents[session_id]
    main_agent = agents["main_agent"]
    messages = agents["messages"]
    
    try:
        # 获取工具定义
        tools = main_agent.get_tool_definitions()
        
        # 调用大模型
        response = main_agent.llm_client.chat_completion(messages, tools=tools)
        
        # 检查是否包含工具调用
        if main_agent.llm_client.is_tool_call(response):
            tool_calls = main_agent.llm_client.extract_tool_calls(response)
            message = main_agent.llm_client.extract_content(response) or "正在执行工具调用..."
            
            # 保存模型决策消息
            model_message = {
                "role": "assistant",
                "content": message,
                "tool_calls": tool_calls
            }
            messages.append(model_message)
            
            # 返回工具调用详情（供前端显示）
            return jsonify({
                "type": "tool_call",
                "message": message,
                "tool_calls": tool_calls,
                "session_id": session_id
            })
        else:
            # 最终回复
            final_content = main_agent.llm_client.extract_content(response)
            messages.append({
                "role": "assistant",
                "content": final_content
            })
            
            # 生成记忆
            if len(messages) >= 2:
                user_msg = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
                summary = agents["memory_agent"].summarize_conversation([
                    {"role": "user", "content": user_msg},
                    {"role": "assistant", "content": final_content}
                ])
                if summary:
                    key = f"Q: {user_msg[:50]}..."
                    agents["memory_agent"].add_memory_entry(key, summary)
            
            return jsonify({
                "type": "final_response",
                "response": final_content,
                "session_id": session_id
            })
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/execute_tool', methods=['POST'])
def execute_tool():
    """执行具体工具调用"""
    data = request.get_json()
    session_id = data.get("session_id")
    tool_call = data.get("tool_call")  # 单个工具调用对象
    
    if session_id not in session_agents:
        return jsonify({"error": "会话不存在"}), 400
        
    agents = session_agents[session_id]
    main_agent = agents["main_agent"]
    messages = agents["messages"]
    
    try:
        # 执行工具
        func_name = tool_call["function"]["name"]
        args = json.loads(tool_call["function"]["arguments"])
        result = main_agent.execute_tool_call(func_name, args)
        
        # 构建工具结果消息
        tool_result_message = {
            "role": "tool",
            "tool_call_id": tool_call["id"],
            "name": func_name,
            "content": json.dumps(result, ensure_ascii=False)
        }
        messages.append(tool_result_message)
        
        return jsonify({
            "type": "tool_result",
            "result": result,
            "tool_name": func_name,
            "session_id": session_id
        })
        
    except Exception as e:
        error_result = {"error": str(e)}
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call["id"],
            "name": tool_call["function"]["name"],
            "content": json.dumps(error_result, ensure_ascii=False)
        })
        return jsonify({
            "type": "tool_result",
            "result": error_result,
            "tool_name": tool_call["function"]["name"],
            "session_id": session_id
        }), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)