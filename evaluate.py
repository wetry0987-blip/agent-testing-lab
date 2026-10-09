import json, re, time
from agent import app

# (编号, 规则描述, 预期是否通过)
RULES = [
    ("R01", "CPA订单成交后必须在7天内确认收货", False),
    ("R02", "所有订单必须有确认时间(不允许为NULL)", False),
    ("R03", "GMV必须大于0", False),
    ("R04", "佣金必须小于GMV", False),
    ("R05", "确认时间不得早于成交时间", False),
    ("R06", "商家ID不能为空", False),
    ("R07", "订单状态必须是completed/pending/refunded之一", False),
    ("R08", "GMV和佣金金额必须最多保留两位小数", False),
    ("R09", "order_id不能为空且必须唯一", True),
    ("R10", "佣金必须等于GMV的5%", False),
]

MAX_TURNS = 10  # 防死循环保险丝

def run_rule(rule_text: str):
    """跑一条规则, 返回(最终输出文本, 工具调用日志)"""
    config = {"configurable": {"thread_id": f"eval-{time.time_ns()}"}}
    state = app.invoke(
        {"messages": [("user", f"验证规则: {rule_text}")]},
        config=config,
    )
    tool_log = []
    turns = 0
    # 每次interrupt后自动续跑, 直到图走完
    while "__interrupt__" in state and turns < MAX_TURNS:
        tool_log.extend(state["messages"][-1].tool_calls)
        state = app.invoke(None, config=config)
        turns += 1
    return state["messages"][-1].content, tool_log

def parse_verdict(text: str) -> dict | None:
    """从模型输出里抠出JSON结论(容忍markdown代码块)"""
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None

def main():
    report = []
    for rid, rule, expected in RULES:
        output, tool_log = run_rule(rule)
        verdict = parse_verdict(output)
        actual = verdict.get("pass") if verdict else None
        correct = (actual == expected)
        report.append({
            "rule_id": rid,
            "rule": rule,
            "expected_pass": expected,
            "actual_pass": actual,
            "correct": correct,
            "violations": verdict.get("violations") if verdict else None,
            "tool_calls": [t["name"] for t in tool_log],
            "raw_output": output[:500],
        })
        status = "✓" if correct else "✗"
        print(f"{status} {rid} 预期={expected} 实际={actual} "
              f"工具调用={[t['name'] for t in tool_log]}")

    passed = sum(1 for r in report if r["correct"])
    accuracy = passed / len(report)
    print(f"\n===== 端到端通过率: {passed}/{len(report)} = {accuracy:.0%} =====")

    with open("eval_report.json", "w", encoding="utf-8") as f:
        json.dump({"accuracy": accuracy, "results": report}, f,
                  ensure_ascii=False, indent=2)
    print("详细报告已写入 eval_report.json")

if __name__ == "__main__":
    main()