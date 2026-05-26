import os
import pandas as pd
import pandasai as pai
from pandasai_litellm.litellm import LiteLLM
import matplotlib.pyplot as plt
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from langchain_litellm import ChatLiteLLM
from pydantic import BaseModel, Field
from enum import Enum

plt.rcParams['font.sans-serif'] = ['SimHei']

class IntentEnum(str, Enum):
    MODIFY = "modify"
    REPORT = "report"
    QUESTION = "question"

class IntentResponse(BaseModel):
    intent: IntentEnum = Field(description="用户意图：modify(修改数据), report(生成报告), question(询问问题)")
    confidence: float = Field(description="置信度，0-1 之间", ge=0, le=1)
    reason: str = Field(description="判断理由，简短说明")

def detect_user_intent(user_query, llm_model, api_key, api_base):
    """
    调用大模型判断用户意图
    返回：'modify' (修改数据), 'report' (生成报告), 或 'question' (询问问题)
    """
    lc_llm = ChatLiteLLM(
        model=llm_model,
        api_key=api_key,
        api_base=api_base,
        temperature=0.1
    )
    
    parser = PydanticOutputParser(pydantic_object=IntentResponse)
    
    prompt = ChatPromptTemplate.from_template("""
请分析用户的以下指令，判断用户的主要意图：

用户指令：{user_query}

判断标准：
- 如果用户明确要求删除、修改、更新、清洗数据等操作，返回 'modify'
- 如果用户要求分析、报告、图表、统计等结果，返回 'report'
- 如果用户在询问概念、定义、方法、为什么等问题，返回 'question'

{format_instructions}
    """)
    
    prompt = prompt.partial(format_instructions=parser.get_format_instructions())
    
    chain = prompt | lc_llm | parser
    
    try:
        response = chain.invoke({"user_query": user_query})
        print(f"意图识别结果：{response.intent.value} (置信度：{response.confidence:.2f})")
        print(f"判断理由：{response.reason}")
        return response.intent.value
    except Exception as e:
        print(f"意图识别失败：{e}，默认使用 'question'")
        return 'question'

# 1. 创建目录
os.makedirs("exports/charts", exist_ok=True)
os.makedirs("exports/data", exist_ok=True)
os.makedirs("exports/logs", exist_ok=True)

# 2. 阿里云模型
llm = LiteLLM(
    model="openai/qwen3.5-plus-2026-02-15",
    api_key="sk-d16cf6ba5aca4cea881c7259a417710b",
    api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
    temperature=0.1
)

# 3. 读取数据
df = pd.read_csv("奶茶店每日订单.csv")

# 4. 关闭 SQL！这是修复关键！
pai.config.set({
    "llm": llm,
    "save_logs": False,
    "verbose": False,
    "save_charts": True,
    "save_charts_path": "exports/charts",
    "open_charts": True,
    "enable_cache": True,
    "max_retries": 3,
    "direct_sql": True, 
})

pai_df = pai.DataFrame(df, name="milk_tea_orders")

# 5. 用户指令
user_query = "帮我删除里面的重复值和缺失值还有问题值"

# 6. 检测用户意图
print("正在分析用户意图...")
intent = detect_user_intent(user_query, "openai/qwen3.5-plus-2026-02-15", "sk-d16cf6ba5aca4cea881c7259a417710b", "https://dashscope.aliyuncs.com/compatible-mode/v1")
print(f"用户意图:{'修改数据' if intent == 'modify' else '生成报告' if intent == 'report' else '询问问题'}")

# 7. 根据意图执行不同操作
if intent == 'modify':
    print("正在处理数据...")
    # 设置pandas显示选项
    
    
    # 调用pandasai处理查询
    ans = pai_df.chat(user_query + "\n返回数据时要生成能被pandas读取的格式")
    
    # if str(ans)[-3:] == "png":
    #     print(f"图表已保存：{ans}")
    # else:
    #     print(f"处理结果：{ans}")
    

elif intent == 'report':
    print("正在生成分析报告...")
    ans = pai_df.chat(user_query + "\n返回数据时要生成能被pandas读取的格式")
    
    # if str(ans)[-3:] == "png":
    #     print(f"图表已保存：{ans}")
    # else:
    #     print(f"分析结果：{ans}")
    
else:
    print("正在回答问题...")

    
    lc_llm = ChatLiteLLM(
        model="openai/qwen3.5-plus-2026-02-15",
        api_key="sk-d16cf6ba5aca4cea881c7259a417710b",
        api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
        temperature=0.1
    )
    
    prompt = ChatPromptTemplate.from_template("""
请回答用户的问题：

用户问题：{user_query}

请提供清晰、准确的回答。
    """)
    
    output_parser = StrOutputParser()
    chain = prompt | lc_llm | output_parser
    ans = chain.invoke({"user_query": user_query})


print(ans)
    
# if intent in ['modify', 'report']:
#     lc_llm = ChatLiteLLM(
#         model="openai/qwen3.5-plus-2026-02-15",
#         api_key="sk-d16cf6ba5aca4cea881c7259a417710b",
#         api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
#         temperature=0.1
#     )
#     code = ans.last_code_executed
#     print("@@@___", code)

#     explain_prompt = ChatPromptTemplate.from_template("""
# 请分析以下Python代码完成的数据处理操作，不需要提及具体代码实现，只需说明：

# 1. 这段代码的整体作用是什么？
# 2. 它对哪些列（字段）进行了操作？
# 3. 每个操作的具体含义是什么？

# 请用自然语言回答，不要出现任何代码片段以及代码相关的内容。

# {code}
# """)
#     output_parser = StrOutputParser()
#     explain_chain = explain_prompt | lc_llm | output_parser
#     explanation = explain_chain.invoke({"code": code})
#     print("=== 代码解释 ===")
#     print(explanation)
