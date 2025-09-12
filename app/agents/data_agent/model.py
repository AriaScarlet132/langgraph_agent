from langchain_ollama import ChatOllama

model = ChatOllama(
    base_url="http://192.168.10.21:11434",
    model="gpt-oss:20b",
    disable_streaming=False
)

# model = ChatOllama(
#     base_url="http://192.168.10.24:11434",
#     model="qwen3:8b",
#     disable_streaming=False
# )
