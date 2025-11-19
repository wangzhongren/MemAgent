# memory_agent.py - 记忆代理：会话总结与记忆条目生成

import json
from typing import Dict, List, Optional


class MemoryAgent:
    def __init__(self, memory_file: str = "memory.json"):
        self.memory_file = memory_file
        self.memories: Dict[str, str] = self._load_memories()

    def _load_memories(self) -> Dict[str, str]:
        """从文件加载现有记忆"""
        try:
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_memories(self):
        """保存记忆到文件"""
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(self.memories, f, ensure_ascii=False, indent=2)

    def summarize_conversation(self, conversation_history: List[Dict]) -> Optional[str]:
        """
        对会话进行总结（此处为简化逻辑，实际可接入LLM）
        返回总结文本，若无可总结内容则返回 None
        """
        # 示例逻辑：若用户提出具体问题且有解答，则生成记忆
        if len(conversation_history) < 2:
            return None
        user_msg = None
        assistant_reply = None
        for msg in reversed(conversation_history):
            if msg["role"] == "user" and user_msg is None:
                user_msg = msg["content"]
            elif msg["role"] == "assistant" and assistant_reply is None:
                assistant_reply = msg["content"]
            if user_msg and assistant_reply:
                break
        if user_msg and assistant_reply and not assistant_reply.startswith("<"):
            # 假设非指令回复为有效解答
            return f"问题：{user_msg.strip()}；解答：{assistant_reply.strip()}"
        return None

    def add_memory_entry(self, key: str, value: str):
        """添加记忆条目（key-value）"""
        self.memories[key] = value
        self.save_memories()