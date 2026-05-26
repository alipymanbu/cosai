from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import pandas as pd
import numpy as np
import pandasai as pai  
from pandasai_litellm.litellm import LiteLLM
import matplotlib.pyplot as plt
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from langchain_litellm import ChatLiteLLM
from pydantic import BaseModel, Field
from enum import Enum
import io
# pd.set_option('display.max_rows', None)
# pd.set_option('display.max_columns', None)
plt.rcParams['font.sans-serif'] = ['SimHei']

class IntentEnum(str, Enum):
    MODIFY = "modify"
    REPORT = "report"
    QUESTION = "question"

class IntentResponse(BaseModel):
    intent: IntentEnum = Field(description="用户意图：modify(修改数据), report(生成报告), question(询问问题)")
    confidence: float = Field(description="置信度，0-1 之间", ge=0, le=1)
    reason: str = Field(description="判断理由，简短说明")



class APIResponse(BaseModel):
    intent: str
    message: str
    explanation: str = None
    code: str = None
    chart_url: str = None


app = FastAPI(
    title="数据处理API",
    version="1.0.0",
)

# 挂载图表目录为静态文件服务
app.mount("/charts", StaticFiles(directory="exports/charts"), name="charts")

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量存储数据
df = pd.DataFrame()


# 初始化配置
def init_config():
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
    
    # 4. 配置 pandasai
    pai.config.set({
        "llm": llm,
        "save_logs": False,
        "verbose": True,
        "save_charts": True,
        "save_charts_path": "exports/charts",
        "open_charts": True,
        "enable_cache": True,
        "max_retries": 3,
        "direct_sql": True, 
    })
    
    return llm

# 加载配置
llm = init_config()
df = pd.DataFrame()
def to_dataframe(data):
    if data is None or len(data) == 0:
        return pd.DataFrame()
    
    max_row = 0
    max_col = 0
    print(data)
    for k in data.keys():
        row, col = map(int, k.split('-'))
        max_row = max(max_row, row)
        max_col = max(max_col, col)

    # 提取第1行作为列名
    columns = []
    for col in range(1, max_col + 1):
        key = f"1-{col}"
        col_name = data.get(key, f"col_{col}")
        # 跳过空的列名
        if col_name.strip() != "":
            columns.append(col_name)

    # 创建DataFrame，从第2行开始是数据
    data_rows = []

    # 重新遍历列，只保留非空列名的索引
    valid_col_indices = []
    for col in range(1, max_col + 1):
        key = f"1-{col}"
        col_name = data.get(key, f"col_{col}")
        if col_name.strip() != "":
            valid_col_indices.append(col)

    for row in range(2, max_row + 1):
        row_data = []
        for col in valid_col_indices:
            key = f"{row}-{col}"
            row_data.append(data.get(key, ''))
        data_rows.append(row_data)
        

    df = pd.DataFrame(data_rows, columns=columns)
    
    # 生成每列的类型信息


    # print(df)
    df.replace(" ", np.nan, inplace=True)

    # 在最后一列添加idchen列，数值从1开始递增
    df['idchen'] = range(2, len(df) + 2)
    
    return df

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
        return response.intent.value
    except Exception as e:
        return 'question'

@app.post("/api/post-data")
async def post_data(data: dict):

    """接收前端传来的单元格数据"""
    global df
    df = to_dataframe(data)
    print(f"---接收到数据: {len(data)} 个单元格")
    print(f"数据形状: {df.shape}")
    return {"success": True, "message": "数据已接收", "rows": len(df), "cols": len(df.columns)}

@app.get("/api/get-data")
async def get_data():
    """返回当前数据"""
    global df
    df_clean = df.replace({np.nan: ''})
    return df_clean.to_dict()

class ProcessRequest(BaseModel):
    query: str

@app.post("/process", response_model=APIResponse)
async def process_query(request: ProcessRequest):

    print(request.query)
    # """
    # 处理用户查询并返回结果
    # """

    global df
    
    # 检查数据是否为空
    # if df.empty:
    #     raise HTTPException(status_code=400, detail="请先上传数据")
    
    import os
    
    # 确保历史记录目录存在
    history_dir = "./pandasai_history"
    if not os.path.exists(history_dir):
        os.makedirs(history_dir)
    
    # 创建pandasai DataFrame并启用历史记录
    pai_df = pai.DataFrame(df, name="milk_tea_orders", history_dir=history_dir)
    
    # # 检测用户意图
    # intent = detect_user_intent(
    #     request.query, 
    #     "openai/qwen3.5-plus-2026-02-15", 
    #     "sk-d16cf6ba5aca4cea881c7259a417710b", 
    #     "https://dashscope.aliyuncs.com/compatible-mode/v1"
    # )
    
    intent = 'modify'
    if intent == 'modify':
   
        # 处理数据或生成报告
        ans = pai_df.chat(request.query + "\n不要修改数据数据类型\n去重的时候idchen不要参与运算\n保存到本地文件，文件名：milk.csv")
       
        code = ans.last_code_executed
        print("====================")
        print(code)
        print(ans)

        df = pd.read_csv("milk.csv", dtype=str)
        df.fillna("", inplace=True)
        
        sep = "chen"
        result = []
        result.append(sep.join(df.columns))
        for _, row in df.iterrows():
            
            result.append(sep.join(map(str, row)))
        str_result = "\n".join(result)
        

        return APIResponse(
            intent="modify",
            message="处理完成",
            explanation=str_result,
            code=code
        )
    elif intent == 'report':
        # 生成报告
        # ans = pai_df.chat(request.query + "\n保存到本地文件，文件名：baogao.csv。还要进行画图操作")
        # code = ans.last_code_executed
        print("====================")
        # print(ans)
        
        df = pd.read_csv("milk.csv", dtype=str)
        df.fillna("", inplace=True)
        
        sep = "chen"
        result = []
        result.append(sep.join(df.columns))
        for _, row in df.iterrows():
            
            result.append(sep.join(map(str, row)))
        str_result = "\n".join(result)

        # 图表文件名（根据实际情况动态获取）
        chart_filename = "temp_chart_e52b2605-4118-420a-80d0-ef0992a30719.png"
        
        return APIResponse(
            intent="report",
            message="报告已生成",
            explanation=str_result,
            code="1",
            chart_url=r"E:\cosai\exports\charts\temp_chart_adfd5cd0-3244-4e31-94b2-180a01cacdf5.png"
        )

#     else:  # question
        # 回答问题
#         lc_llm = ChatLiteLLM(
#             model="openai/tongyi-xiaomi-analysis-flash",
#             api_key="sk-d16cf6ba5aca4cea881c7259a417710b",
#             api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
#             temperature=0.1
#         )
        
#         prompt = ChatPromptTemplate.from_template("""
# 请回答用户的问题：

# 用户问题：{user_query}

# 请提供清晰、准确的回答。
# """)
        
#         output_parser = StrOutputParser()
#         chain = prompt | lc_llm | output_parser
#         ans = chain.invoke({"user_query": request.query})
        
#         return APIResponse(
#             intent=intent,
#             message=ans
#         )
            


@app.get("/")
async def root():
    """
    根路径
    """
    return {"message": "Welcome to the API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8001, reload=True)

