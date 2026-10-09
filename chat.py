import os
from openai import OpenAI
from dotenv import load_dotenv

# 1. 加载环境变量
load_dotenv()

# 2. 初始化客户端
client = OpenAI(
    # 注意这里：括号里的名字必须和 .env 文件里的名字一模一样！
    api_key=os.getenv("LLM_API_KEY"),       # 对应 .env 里的 LLM_API_KEY
    base_url=os.getenv("LLM_BASE_URL")      # 对应 .env 里的 LLM_BASE_URL
)

def chat_with_agent(user_input):
    # 3. 发送请求
    response = client.chat.completions.create(
        # 直接从 .env 里读取模型名字，避免写死。前提是 .env 里写了 LLM_MODEL=qwen-plus
        model=os.getenv("LLM_MODEL"),
        messages=[
            {"role": "system", "content": "你是一个乐于助人的 AI 助手。"},
            {"role": "user", "content": user_input}
        ]
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    print("🤖 Agent 已启动（输入 'quit' 退出）")
    while True:
        user_input = input("\n你: ")
        if user_input.lower() in ['quit', 'exit']:
            break

        print("Agent 思考中...")
        reply = chat_with_agent(user_input)
        print(f"AI: {reply}")