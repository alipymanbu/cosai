import os
import pandas as pd
from pandasai import SmartDataframe
from pandasai.config import Config  # 关键！
from pandasai_litellm.litellm import LiteLLM

# 1. 创建目录
os.makedirs("exports/charts", exist_ok=True)

# 2. 你的阿里云 LLM
llm = LiteLLM(
    model="openai/tongyi-xiaomi-analysis-flash",
    api_key="sk-d16cf6ba5aca4cea881c7259a417710b",
    api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
    temperature=0.1
)

# 3. 数据（必须用 pd.DataFrame）
df = pd.read_csv("奶茶店每日订单.csv")

## ======================================================================
# ✅ 正确配置：全部放进 Config() 里！（完全匹配你给的源码）
# ======================================================================
config = Config(
    llm=llm,
    save_logs=True,
    verbose=False,
    save_charts=True,
    save_charts_path="exports/charts",
    open_charts=True,
    enable_cache=False,
    max_retries=3,
    security="none",       # 关闭安全检查，解决 SQL 报错
    direct_sql=False       # 禁用 SQL，根治报错
)

# ======================================================================
# ✅ 正确初始化（只传 df 和 config！）
# ======================================================================
sdf = SmartDataframe(df, config=config)

# 4. 正常聊天！
ans = sdf.chat("帮我做一个线性回归，并且画图给我")
print("@@@", ans)
print("@@@@@#", sdf._agent.last_code_executed) 