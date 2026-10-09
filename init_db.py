import sqlite3

conn = sqlite3.connect("settlement.db")
c = conn.cursor()
c.execute("""
CREATE TABLE cpa_orders (
    order_id    TEXT PRIMARY KEY,
    merchant_id TEXT,
    action_time TEXT,          -- 转化(成交)时间
    confirm_time TEXT,         -- 确认/收货时间, 未收货为 NULL
    gmv         REAL,
    commission  REAL,
    status      TEXT           -- completed / pending / refunded
)
""")

# 15条数据: 大部分正常, 故意埋5类问题
orders = [
    ("A001","M01","2026-09-01","2026-09-03",100.0,5.0,"completed"),
    ("A002","M01","2026-09-01","2026-09-10",200.0,10.0,"completed"),  # 超7天收货
    ("A003","M02","2026-09-02",None,150.0,None,"pending"),             # 未确认+佣金缺失
    ("A004","M02","2026-09-03","2026-09-02",300.0,15.0,"completed"),  # 确认早于成交
    ("A005","M03","2026-09-04","2026-09-05",-50.0,-2.5,"completed"),   # 负GMV
    ("A006","M03","2026-09-05","2026-09-06",0.0,0.0,"completed"),      # GMV为0
    ("A007","M01","2026-09-06","2026-09-07",100.0,100.0,"completed"),  # 佣金>=GMV
    ("A008",None ,"2026-09-07","2026-09-08",80.0,4.0,"completed"),     # 商家为空
    ("A009","M02","2026-09-08","2026-09-09",99.999,5.0,"completed"),   # 金额超2位小数
    ("A010","M03","2026-09-09","2026-09-10",120.0,6.0,"unknown"),      # 非法状态
    ("A011","M01","2026-09-10","2026-09-11",100.0,5.0,"completed"),
    ("A012","M02","2026-09-11","2026-09-12",100.0,5.0,"completed"),
]
c.executemany("INSERT INTO cpa_orders VALUES (?,?,?,?,?,?,?)", orders)
conn.commit()
conn.close()
print("settlement.db 就绪")