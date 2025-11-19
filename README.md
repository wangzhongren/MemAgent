# MemAgent: AI-Powered File Navigator with Persistent Memory

**MemAgent** is an open-source multi-agent system that lets you interact with your file system through natural language. Powered by large language models (LLMs), it automatically executes file operations (read, search, list) and builds a persistent memory of solutions to recurring questions — all through an intuitive web interface.

> 🌟 **Key Innovation**: Unlike rigid command parsers, MemAgent uses LLMs to *autonomously decide* when to call tools, enabling fluid, human-like problem solving over your codebase or documents.

---

## ✨ Core Features

### Triple-Agent Architecture
| Agent | Responsibility |
|-------|----------------|
| **Main Agent** | Orchestrates LLM interactions, executes file operations (`list_files`, `read_file`, `search_keyword`), and handles multi-turn tool calling |
| **Memory Agent** | Summarizes key Q&A pairs into persistent memory (e.g., *"How to debug auth errors? → Check logs/auth.log line 150"*) |
| **Context Agent** | Injects relevant memories into prompts so the AI "remembers" past solutions |

### Intelligent File Operations
- **Browse directories**: `list_files src/`
- **Precise file reading**: `read_file config.yaml start=20 end=50`
- **Contextual keyword search**: `search_keyword app.py keyword="timeout"` → Returns matches with **200-char context before/after**

### Universal LLM Compatibility
Works with any OpenAI-compatible API:
- **Local**: [Ollama](https://ollama.com/) (Llama 3, Qwen, Mistral)
- **Cloud**: OpenAI GPT-4, Azure OpenAI, DeepSeek, etc.

### Web UI Included
- Real-time chat interface
- Memory bank visualization
- One-click model configuration

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- [Ollama](https://ollama.com/) (recommended for local/offline use) **OR** OpenAI API key

### Installation
```bash
# Clone the repo
git clone https://github.com/your-username/memagent.git
cd memagent

# Install dependencies
pip install flask requests

# Start the server
python server.py
```

### Usage
1. Open [http://localhost:8000](http://localhost:8000)
2. Configure your LLM:
   - **LLM Base URL**: `http://localhost:11434/v1` (Ollama default)
   - **Model Name**: `qwen:7b` (or any installed model)
   - **API Key**: Leave empty for Ollama
3. Ask natural language questions like:
   > *"Show me the error handling in main.py"*  
   > *"What did I ask about file reading yesterday?"*

---

## 🧠 How It Works

### System Architecture
```
User Query
    │
    ▼
Web UI (Browser)
    │
    ▼
Flask Server
    ├── Context Agent → Retrieves relevant memories from memory.json
    ├── Main Agent → Communicates with LLM + executes file operations
    └── Memory Agent → Saves new Q&A pairs to memory.json
                │
                ▼
            File System (Your project files)
```

### Workflow
1. User asks a question in natural language
2. System retrieves relevant memories as context
3. LLM decides whether to call tools (e.g., read a file)
4. Tools execute and return results to the LLM
5. LLM generates a final human-readable answer
6. Key insights are saved to `memory.json` for future use

---

## 🛠️ Customize & Extend

### Add New Tools
1. Implement a method in `agents/main_agent.py` (e.g., `def analyze_log(self, path): ...`)
2. Register it in `get_tool_definitions()` with OpenAI function schema
3. Map the function name in `execute_tool_call()`

### Enhance Memory
- Replace keyword matching in `agents/context_agent.py` with vector similarity (e.g., using Sentence Transformers)
- Add memory expiration based on usage frequency

---

## 📜 License
Distributed under the MIT License. See [LICENSE](LICENSE) for details.

---

## 💬 Example Interactions

**User**:  
> List Python files in the agents directory

**MemAgent**:  
> Found 4 files:  
> - main_agent.py  
> - memory_agent.py  
> - context_agent.py  
> - llm_client.py  

**User**:  
> Find where 'search_keyword' is defined in main_agent.py

**MemAgent**:  
> Located at lines 45-62:  
> ```python
> def search_keyword(self, file_path: str, keyword: str) -> List[Dict]:
>     """Searches for keyword in file, returns context around matches"""
>     # Implementation...
> ```

---

> 💡 **Pro Tip**: Pair with [Ollama](https://ollama.com/library) for free, offline, private AI assistance! No API costs or data leaks.