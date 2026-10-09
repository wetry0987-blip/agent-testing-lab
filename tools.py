import ast, operator, sqlite3
from langchain_core.tools import tool

@tool
def get_schema() -> str:
    """查询 cpa_orders 表的表结构(字段名和类型), 在写SQL前必须先调用"""
    conn = sqlite3.connect("settlement.db")
    cols = conn.execute("PRAGMA table_info(cpa_orders)").fetchall()
    conn.close()
    return "\n".join(f"{c[1]} {c[2]}" for c in cols)

@tool
def run_sql(sql: str) -> str:
    """在只读模式下执行 SELECT 查询并返回结果, 用于校验结算规则"""
    banned = ("drop", "delete", "update", "insert", "alter", "pragma")
    if any(w in sql.lower() for w in banned):
        return "ERROR: 只允许 SELECT 查询"
    conn = sqlite3.connect("settlement.db")
    try:
        rows = conn.execute(sql).fetchall()
        cols = [d[0] for d in conn.execute(sql).description]
        return f"columns={cols}\nrows={rows}" if rows else "查询成功, 0行结果(说明没有违规数据)"
    except Exception as e:
        return f"SQL执行错误: {e}"
    finally:
        conn.close()

_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.USub: operator.neg}

def _safe_eval(node):
    if isinstance(node, ast.Num):  # python<3.8
        return node.n
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError("不支持的表达式")

@tool
def calculator(expression: str) -> str:
    """安全地计算数学表达式, 例如 '(100 - 5) / 100'"""
    try:
        return str(_safe_eval(ast.parse(expression, mode="eval").body))
    except Exception as e:
        return f"计算错误: {e}"