# llm_client.py - 大模型客户端，支持 OpenAI 兼容 API

import os
import requests
from typing import List, Dict, Optional


class LLMClient:
    def __init__(self, base_url: str, api_key: str, model_name: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.model_name = model_name
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def chat_completion(self, messages: List[Dict[str, str]], tools: Optional[List] = None) -> Dict:
        """
        调用大模型聊天接口，支持工具调用
        """
        payload = {
            "model": self.model_name,
            "messages": messages
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=self.headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return response.json()

    def is_tool_call(self, response_data: Dict) -> bool:
        """
        判断响应是否包含工具调用
        """
        choices = response_data.get("choices", [])
        if not choices:
            return False
        message = choices[0].get("message", {})
        return "tool_calls" in message and len(message["tool_calls"]) > 0

    def extract_tool_calls(self, response_data: Dict) -> List[Dict]:
        """
        提取工具调用信息
        """
        choices = response_data.get("choices", [])
        if not choices:
            return []
        message = choices[0].get("message", {})
        return message.get("tool_calls", [])

    def extract_content(self, response_data: Dict) -> str:
        """
        提取模型回复内容
        """
        choices = response_data.get("choices", [])
        if not choices:
            return ""
        message = choices[0].get("message", {})
        return message.get("content", "")