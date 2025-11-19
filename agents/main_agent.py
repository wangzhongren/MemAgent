# main_agent.py - 主代理：负责与客户对话及文件操作（集成大模型）

import os
import json
from typing import List, Dict, Optional, Tuple
from agents.llm_client import LLMClient


class MainAgent:
    def __init__(self, root_dir: str = ".", llm_client: Optional[LLMClient] = None):
        self.root_dir = os.path.abspath(root_dir)
        self.llm_client = llm_client

    def list_files(self, sub_path: str = "") -> List[str]:
        """列出指定子目录下的所有文件（非递归）"""
        target_dir = os.path.join(self.root_dir, sub_path)
        if not os.path.exists(target_dir):
            raise FileNotFoundError(f"Directory not found: {target_dir}")
        return [f for f in os.listdir(target_dir) if os.path.isfile(os.path.join(target_dir, f))]

    def read_file_content(self, file_path: str, start: Optional[int] = None, end: Optional[int] = None) -> str:
        """读取文件内容，可指定起止位置"""
        full_path = os.path.join(self.root_dir, file_path)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {full_path}")
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        if start is not None or end is not None:
            start = start if start is not None else 0
            end = end if end is not None else len(content)
            return content[start:end]
        return content

    def search_keyword(self, file_path: str, keyword: str) -> List[Dict]:
        """在文件中搜索关键词，返回每个匹配位置前后200字符的上下文"""
        content = self.read_file_content(file_path)
        results = []
        start = 0
        while True:
            pos = content.find(keyword, start)
            if pos == -1:
                break
            before = max(0, pos - 200)
            after = min(len(content), pos + len(keyword) + 200)
            results.append({
                "position": pos,
                "context_before": content[before:pos],
                "matched": content[pos:pos + len(keyword)],
                "context_after": content[pos + len(keyword):after]
            })
            start = pos + 1
        return results

    def get_tool_definitions(self) -> List[Dict]:
        """返回可用工具的 OpenAI 格式定义"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "list_files",
                    "description": "列出指定目录下的所有文件",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "相对路径，留空表示当前目录"}
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "读取文件内容，可指定起止位置",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "文件相对路径"},
                            "start": {"type": "integer", "description": "起始位置（可选）"},
                            "end": {"type": "integer", "description": "结束位置（可选）"}
                        },
                        "required": ["file_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_keyword",
                    "description": "在文件中搜索关键词，返回匹配位置上下文",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "文件相对路径"},
                            "keyword": {"type": "string", "description": "要搜索的关键词"}
                        },
                        "required": ["file_path", "keyword"]
                    }
                }
            }
        ]

    def execute_tool_call(self, tool_name: str, arguments: Dict) -> Dict:
        """执行具体工具调用"""
        try:
            if tool_name == "list_files":
                files = self.list_files(arguments.get("path", ""))
                return {"result": files}
            elif tool_name == "read_file":
                content = self.read_file_content(
                    arguments["file_path"],
                    arguments.get("start"),
                    arguments.get("end")
                )
                return {"result": content}
            elif tool_name == "search_keyword":
                results = self.search_keyword(arguments["file_path"], arguments["keyword"])
                return {"result": results}
            else:
                return {"error": f"未知工具: {tool_name}"}
        except Exception as e:
            return {"error": str(e)}

    def chat_with_tools(self, messages: List[Dict]) -> str:
        """
        与大模型对话，自动处理工具调用循环
        """
        if self.llm_client is None:
            raise ValueError("LLM client not initialized")

        tools = self.get_tool_definitions()
        current_messages = messages.copy()

        while True:
            # 调用大模型
            response = self.llm_client.chat_completion(current_messages, tools=tools)
            
            # 检查是否包含工具调用
            if self.llm_client.is_tool_call(response):
                tool_calls = self.llm_client.extract_tool_calls(response)
                tool_results = []

                # 执行所有工具调用
                for call in tool_calls:
                    func_name = call["function"]["name"]
                    args = json.loads(call["function"]["arguments"])
                    result = self.execute_tool_call(func_name, args)
                    
                    # 添加工具结果到消息历史
                    current_messages.append({
                        "role": "tool",
                        "tool_call_id": call["id"],
                        "name": func_name,
                        "content": json.dumps(result, ensure_ascii=False)
                    })
                    tool_results.append(result)
                
                # 继续下一轮调用（模型会基于工具结果生成最终回复）
                continue
            else:
                # 无工具调用，返回最终内容
                return self.llm_client.extract_content(response)