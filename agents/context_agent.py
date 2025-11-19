# context_agent.py - 上下文代理：筛选相关记忆作为主代理参考

import json
from typing import Dict, List, Optional
from agents.memory_agent import MemoryAgent


class ContextAgent:
    def __init__(self, memory_agent: MemoryAgent):
        self.memory_agent = memory_agent

    def find_relevant_memories(self, query: str, top_k: int = 3) -> Dict[str, str]:
        """
        根据查询关键词筛选最相关的记忆条目（简化版：关键词包含匹配）
        实际项目中可替换为向量相似度搜索
        """
        relevant = {}
        query_lower = query.lower()
        for key, value in self.memory_agent.memories.items():
            if query_lower in key.lower() or query_lower in value.lower():
                relevant[key] = value
                if len(relevant) >= top_k:
                    break
        return relevant