from langchain_ollama import ChatOllama
from langchain_deepseek import ChatDeepSeek
from langchain_openai import ChatOpenAI

model = ChatOllama(
    base_url="http://localhost:11434",
    model="gpt-oss:20b",
    disable_streaming=False
)

# model = ChatOllama(
#     base_url="http://192.168.10.24:11434",
#     model="qwen3:8b",
#     disable_streaming=False
# )

DEEP_SEEK_API_KEY = "sk-1c7757989d8f4689a80923e69484975b"

deepseek = ChatDeepSeek(
    base_url="https://api.deepseek.com",
    api_key=DEEP_SEEK_API_KEY,
    model="deepseek-chat"
)

QWEN_API_KEY = "sk-8e8db79b2a674c13865028a046988791"

qwen = ChatOpenAI(
    model="qwen3-235b-a22b-instruct-2507",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key=QWEN_API_KEY,
)