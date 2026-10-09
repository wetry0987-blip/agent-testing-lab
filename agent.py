from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from tools import get_schema, run_sql, calculator
import os
from dotenv import load_dotenv
load_dotenv()

tools = [get_schema, run_sql, calculator]


llm = ChatOpenAI(
    model=os.getenv("LLM_MODEL"),
    temperature=0,
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
).bind_tools(tools)

SYSTEM = """你是结算规则验证专家。严格遵守以下流程:
1. 必须先调用 get_schema 了解表结构
2. 必须调用 run_sql 执行查询找出违规数据, 不允许仅凭推理给出结论
3. 需要计算时调用 calculator
4. 只有执行过 run_sql 之后, 才能输出最终JSON结论:
{"pass": true/false, "violations": 违规数量, "evidence": "关键证据", "sql": "你执行的核心SQL"}
禁止输出任何与工具调用无关的中间说明文字。"""

def call_model(state: MessagesState):
    msgs = [{"role": "system", "content": SYSTEM}] + state["messages"]
    return {"messages": [llm.invoke(msgs)]}

def should_continue(state: MessagesState) -> str:
    if state["messages"][-1].tool_calls:
        return "tools"
    return END

builder = StateGraph(MessagesState)
builder.add_node("agent", call_model)
builder.add_node("tools", ToolNode(tools))
builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
builder.add_edge("tools", "agent")

app = builder.compile(
    checkpointer=MemorySaver(),
    interrupt_before=["tools"],   # ★ 新增: 每次执行工具前暂停, 等人工确认
)