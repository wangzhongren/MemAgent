# app.py - AI Agent 系统主入口

import os
import json
from agents import MainAgent, MemoryAgent, ContextAgent


class AIAgentSystem:
    def __init__(self, root_dir: str = ".", memory_file: str = "memory.json"):
        self.main_agent = MainAgent(root_dir=root_dir)
        self.memory_agent = MemoryAgent(memory_file=memory_file)
        self.context_agent = ContextAgent(self.memory_agent)
        self.conversation_history = []

    def process_user_input(self, user_input: str):
        """处理用户输入，协调三个代理工作"""
        self.conversation_history.append({"role": "user", "content": user_input})

        # 步骤1：使用上下文代理获取相关记忆
        relevant_memories = self.context_agent.find_relevant_memories(user_input)
        context_str = "\n".join([f"{k}: {v}" for k, v in relevant_memories.items()]) if relevant_memories else ""

        # 步骤2：主代理尝试响应（此处简化为判断是否含指令）
        response = None
        if "list_files" in user_input or "read_file" in user_input or "search_keyword" in user_input:
            # 模拟解析指令（实际应使用更 robust 的 parser 或 LLM）
            try:
                if "list_files" in user_input:
                    path = self._extract_path(user_input)
                    files = self.main_agent.list_files(path)
                    response = {"files": files}
                elif "read_file" in user_input:
                    file_path, start, end = self._parse_read_command(user_input)
                    content = self.main_agent.read_file_content(file_path, start, end)
                    response = {"content": content}
                elif "search_keyword" in user_input:
                    file_path, keyword = self._parse_search_command(user_input)
                    results = self.main_agent.search_keyword(file_path, keyword)
                    response = {"matches": results}
            except Exception as e:
                response = {"error": str(e)}
        else:
            # 无明确指令，交由记忆代理总结
            summary = self.memory_agent.summarize_conversation(self.conversation_history)
            if summary:
                key = f"Q: {user_input[:50]}..."
                self.memory_agent.add_memory_entry(key, summary)
            response = {"message": "已记录您的问题，暂无直接操作指令。"}

        # 记录助手回复
        self.conversation_history.append({"role": "assistant", "content": json.dumps(response, ensure_ascii=False)})
        return response

    def _extract_path(self, input_str: str) -> str:
        # 简化路径提取逻辑
        parts = input_str.split()
        return parts[1] if len(parts) > 1 else ""

    def _parse_read_command(self, input_str: str):
        # 示例格式: read_file path/to/file.txt start=100 end=300
        parts = input_str.split()
        file_path = parts[1]
        start = end = None
        for part in parts[2:]:
            if part.startswith("start="):
                start = int(part.split("=")[1])
            elif part.startswith("end="):
                end = int(part.split("=")[1])
        return file_path, start, end

    def _parse_search_command(self, input_str: str):
        # 示例格式: search_keyword path/to/file.txt keyword="error"
        parts = input_str.split()
        file_path = parts[1]
        keyword = ""
        for part in parts[2:]:
            if part.startswith('keyword='):
                keyword = part.split('=', 1)[1].strip('"')
        return file_path, keyword


if __name__ == "__main__":
    system = AIAgentSystem()
    while True:
        user_input = input("User: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        result = system.process_user_input(user_input)
        print("Assistant:", json.dumps(result, indent=2, ensure_ascii=False))