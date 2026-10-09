from agent import app

config = {"configurable": {"thread_id": "demo-1"}}
state = app.invoke(
    {"messages": [("user", "验证规则: CPA订单成交后必须在7天内确认收货")]},
    config=config,
)

while "__interrupt__" in state:
    print("=== 待执行的tool_calls ===")
    print(state["messages"][-1].tool_calls)
    input("检查无误后回车继续...")
    state = app.invoke(None, config=config)

# 跑完后打印完整消息流(调试必备, 以后排查问题就靠它)
for m in state["messages"]:
    print(f"\n[{m.type}] {str(m.content)[:200]}")

print("\n===== 最终结论 =====")
print(state["messages"][-1].content)