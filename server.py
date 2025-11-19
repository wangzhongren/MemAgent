# server.py - Web API 服务，集成大模型调用

import os
import json
from flask import Flask, request, jsonify
from agents import MainAgent, MemoryAgent, ContextAgent
from agents.llm_client import LLMClient


app = Flask(__name__, static_folder='webui')
main_agent = None
memory_agent = None
context_agent = None


def initialize_agents(work_dir: str = ".", llm_config: dict = None):
    global main_agent, memory_agent, context_agent
    
    # 初始化 LLM 客户端（如果提供了配置）
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


@app.route('/')
def index():
    return app.send_static_file('index.html')


@app.route('/memories', methods=['GET'])
def get_memories():
    """获取所有记忆条目"""
    if memory_agent is None:
        initialize_agents()
    return jsonify(memory_agent.memories)


@app.route('/process', methods=['POST'])
def process_input():
    """处理用户输入，通过大模型驱动主代理"""
    data = request.get_json()
    user_input = data.get("user_input", "")
    work_dir = data.get("work_dir", ".")
    base_url = data.get("base_url", "").rstrip('/')
    api_key = data.get("api_key", "")
    model_name = data.get("model_name", "gpt-4")

    # 验证必要参数
    if not base_url or not api_key:
        return jsonify({"error": "缺少 base_url 或 api_key"}), 400

    # 初始化带 LLM 的代理
    llm_config = {
        "base_url": base_url,
        "api_key": api_key,
        "model_name": model_name
    }
    initialize_agents(work_dir, llm_config)

    # 获取相关记忆作为上下文
    relevant_memories = context_agent.find_relevant_memories(user_input)
    context_str = "\n".join([f"{k}: {v}" for k, v in relevant_memories.items()]) if relevant_memories else ""

    # 构建消息历史
    messages = []
    if context_str:
        messages.append({
            "role": "system",
            "content": f"相关记忆:\n{context_str}"
        })
    messages.append({
        "role": "user",
        "content": user_input
    })

    try:
        # 通过主代理与大模型交互（自动处理工具调用循环）
        final_response = main_agent.chat_with_tools(messages)
        
        # 尝试生成记忆（基于最终问答）
        summary = memory_agent.summarize_conversation([
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": final_response}
        ])
        if summary:
            key = f"Q: {user_input[:50]}..."
            memory_agent.add_memory_entry(key, summary)

        return jsonify({
            "response": final_response,
            "context_used": context_str
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    # 默认初始化（无 LLM）
    initialize_agents()
    app.run(host='0.0.0.0', port=8000, debug=True)