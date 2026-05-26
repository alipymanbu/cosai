from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
from llm_chat import create_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from tongyi_chat import classify_user_intent, process_specific_analysis_request
from get_tools import get_tool_description, get_tool_docstring
import json
import pandas as pd
import sqlite3
import uuid
from data_descriptive import analyze_orders
from Ai_advice import generate_parameter_suggestions
import os
import inspect
import importlib.util



# 你要批量导入的文件夹路径
FOLDER_PATH = r"E:\cos0.3\Ai\tools"

# 存储所有导入的函数（白名单，安全可用）
ALL_FUNCTIONS = {}

# 👇 自动遍历文件夹，导入所有 .py 文件里的所有函数
for filename in os.listdir(FOLDER_PATH):
    # 只处理 .py 文件
    if filename.endswith(".py") and filename != "__init__.py":
        file_path = os.path.join(FOLDER_PATH, filename)
        module_name = filename[:-3]  # 去掉 .py 后缀

        # 动态加载模块
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # 把模块里的所有函数加入字典
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            # 只导入函数，排除内置属性
            if callable(attr) and not attr_name.startswith("__"):
                ALL_FUNCTIONS[attr_name] = attr
# 初始化数据库
def init_db():
    conn = sqlite3.connect('chat_history.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()

# 初始化数据库
init_db()

# 保存聊天记录
def save_chat_history(session_id: str, role: str, content: str):
    conn = sqlite3.connect('chat_history.db')
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO chat_history (session_id, role, content) VALUES (?, ?, ?)',
        (session_id, role, content)
    )
    conn.commit()
    conn.close()

# 加载聊天历史
def load_chat_history(session_id: str, limit: int = 10):
    conn = sqlite3.connect('chat_history.db')
    cursor = conn.cursor()
    cursor.execute(
        'SELECT role, content FROM chat_history WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?',
        (session_id, limit)
    )
    history = cursor.fetchall()
    conn.close()
    # 反转历史记录，使最早的消息在前面
    return history[::-1]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

class ScenarioRequest(BaseModel):
    tool: str
    scenario: dict
df = None
@app.post("/api/post-data")
async def post_data(data: Dict[str, str]):
    global df
    df = data
    print("接收到前端数据:", df)
    
    return {"status": "success", "message": "数据已接收"}
@app.post("/api/chat")
async def chat(request: ChatRequest):
    print(request.message)
    chat_model = create_chat_model()
    intent_type = classify_user_intent(chat_model, request.message)
    print("intent_type:", intent_type[0])

    # 使用固定的session_id，确保上下文记忆
    session_id = "default_session"
    
    if str(intent_type.strip()) == "1":
        tool_name = process_specific_analysis_request(chat_model, request.message)
        print('@@@@',tool_name)
        if tool_name[1] == 1:
            return ChatResponse(response=json.dumps({'tools': tool_name[0], 'type': 1}, ensure_ascii=False))
        elif tool_name[1] == 2:
            return ChatResponse(response=json.dumps({'tools': ['抱歉没有找到相应的工具'], 'type': 2}, ensure_ascii=False))
        elif tool_name[1] == 3:
            return ChatResponse(response=json.dumps({'tools': tool_name[0], 'type': 3}, ensure_ascii=False))
    elif str(intent_type.strip()) == "3" or str(intent_type.strip()) == "2":
        chat_model = create_chat_model()
        analysis_report = analyze_orders(df)
        print(analysis_report)
        # 加载历史聊天记录
        history = load_chat_history(session_id)
        
        # 构建历史上下文
        history_context = ""
        if history:
            history_context = "\n\n历史聊天记录：\n"
            for role, content in history:
                if role == "user":
                    history_context += f"用户：{content}\n"
                else:
                    history_context += f"助手：{content}\n"
        
        # 直接调用大模型回答用户问题
        prompt = f"""你是一个专业的数据分析师助手，请根据以下数据报告和历史聊天记录回答用户问题。

数据报告：
{analysis_report}{history_context}

用户问题：{request.message}

请按照以下要求回答：
1. 使用 Markdown 格式，让内容更美观易读
2. 使用标题（#、##）来组织内容结构
3. 使用列表（- 或 1.）来列举要点
4. 使用代码块（```）来展示代码或数据
5. 使用表格来展示数据对比
6. 使用加粗（**文本**）来突出重点
7. 使用引用（>）来强调重要信息
8. 保持适当的段落间距
9. 用中文回答，保持专业但亲切的语气
10. 如果数据报告中没有相关信息，请如实告知用户

请确保回答内容结构清晰、排版美观、易于阅读。"""
     
        response = chat_model.invoke([HumanMessage(content=prompt)], temperature=0.7)
        answer = response.content.strip()
        # print(answer)
        
        # 只保存用户问题到数据库
        save_chat_history(session_id, "user", request.message)
        
        return ChatResponse(response=json.dumps({'content': answer, 'type': 31}, ensure_ascii=False))
    elif str(intent_type.strip()) == "4":
        # print("我进来了")
        return ChatResponse(response=json.dumps({'content': '你好！我是你的cos数据分析助手。我可以帮你分析数据。请问我数据相关的问题吧！', 'type': 41}, ensure_ascii=False))
    
@app.post("/api/select")
async def select(request: ChatRequest):
    print(request.message)
    parameters = get_tool_docstring(request.message)
    description = get_tool_description(request.message)
    analysis_report = analyze_orders(df)
    chat_model = create_chat_model()
    prompt = generate_parameter_suggestions(request.message, description, parameters, analysis_report, chat_model, HumanMessage)
    
    print(prompt)
    
    # 解析prompt中的JSON字符串，然后重新序列化为JSON字符串
    parsed_data = json.loads(prompt)
    # 将parameters添加到解析后的数据中
    parsed_data['parameters'] = parameters
    return ChatResponse(response=json.dumps(parsed_data, ensure_ascii=False))

@app.post("/api/confirm-scenario")
async def confirm_scenario(request: ScenarioRequest):
    print("收到场景确认请求:")
    print(f"工具: {request.tool}")
    print(f"场景: {request.scenario}")
    analysis_report = analyze_orders(df)
    data = {'tool': request.tool, 'scenario': request.scenario}
    
    # 让AI判断是否需要前置条件（预处理）
    chat_model = create_chat_model()
    tool = request.tool
    scenario = request.scenario
    
    # 构建判断是否需要预处理的prompt
    preprocess_prompt = f"你是一个数据处理专家，需要判断以下分析场景是否需要前置条件（预处理）。\n"
    preprocess_prompt += f"工具：{tool}\n"
    preprocess_prompt += f"场景：{scenario}\n"
    preprocess_prompt += f"分析报告：{analysis_report}\n"
    preprocess_prompt += "请判断这个分析场景是否需要前置条件（预处理）。\n"
    preprocess_prompt += "如果需要，请返回JSON格式：{\"need_preprocess\": 1, \"preprocess_steps\": [\"步骤1\", \"步骤2\", ...]}\n"
    preprocess_prompt += "如果不需要，请返回JSON格式：{\"need_preprocess\": -1, \"preprocess_steps\": []}\n"
    preprocess_prompt += "注意：只返回JSON格式，不要返回其他内容。"
    preprocess_prompt += "请严格按照JSON格式返回，不要包含任何额外的内容。"

    
    # 调用AI进行判断
    
    preprocess_decision = chat_model.invoke([HumanMessage(content=preprocess_prompt)])
    print(f"AI判断结果：@@@@{preprocess_decision.content}")
    preprocess_decision.content = """{"need_preprocess": 1, "preprocess_steps": ["将天气分类变量转换为数值型（如多云=3, 阴=2, 雪=1, 雨=0, 晴=1）", "检查并处理数据中的异常值（如销量中的-1.0异常值）", "验证数据分布是否符合线性回归假设（如正态性、同方差性等）", "检查自相关性和多重共线性（虽然主要变量较少，但仍可检查）", "进行数据标准化或归一化（如果变量量纲差异较大）"]}
    """
    # 解析AI返回的结果
    json_start_idx = preprocess_decision.content.strip().find("{")
    clean_json = preprocess_decision.content.strip()[json_start_idx:]
    try:
        result = json.loads(clean_json)
        need_preprocess = result.get('need_preprocess', -1)
        preprocess_steps = result.get('preprocess_steps', [])
    except json.JSONDecodeError as e:
        result = json.loads(clean_json[:-1])
        need_preprocess = result.get('need_preprocess', -1)
        preprocess_steps = result.get('preprocess_steps', [])



    if need_preprocess == 1:
        for step in preprocess_steps:

            tool_name = process_specific_analysis_request(chat_model, step)
            print(tool_name)
            if len(tool_name[0]) == 0:
                data.update({'data': step})
            else:
                tool_list = list(tool_name)
                tool_list.append(str(step))   
                description = get_tool_description(tool_list[0][0])
                docstring = get_tool_docstring(tool_list[0][0])
                re_parameters = get_tool_docstring(tool)
                print("11")
                # 构建预处理提示词
                preprocess_prompt = (
                    f"你是一个数据处理专家，需要为特定分析场景准备数据预处理参数\n"
                    f"=====================================\n"
                    f"分析场景信息：\n"
                    f"工具：{tool}\n"
                    f"参数：{re_parameters}\n"
                    f"场景：{scenario}\n"
                    f"分析报告：{analysis_report}\n"
                    f"=====================================\n"
                    f"预处理工具信息：\n"
                    f"工具名称：{tool_list[0][0]}\n"
                    f"工具描述和返回值说明和参数说明：{description}\n"
                    f"工具文档：{docstring}\n"
                    f"=====================================\n"
                    f"任务：\n"
                    f"请根据分析场景和数据情况，为上述预处理工具生成正确的参数值\n"
                    f"1. data参数：可以是单个列名(如\"销量\")或多个列名的列表(如[\"销量\", \"客单价\"])\n"
                    f"2. 选择合适的处理方法和参数值\n"
                    f"3. 明确指定需要使用的返回值字段\n"
                    f"=====================================\n"
                    f"返回值说明：\n"
                    f"handle_outliers函数返回以下字段：\n"
                    f"- processed_data：处理极端值后的数据（列表格式）\n"
                    f"- method：使用的极端值处理方法\n"
                    f"- threshold：处理阈值（仅适用于iqr和zscore方法）\n"
                    f"- lower_quantile：下分位数（仅适用于winsorize和truncate方法）\n"
                    f"- upper_quantile：上分位数（仅适用于winsorize和truncate方法）\n"
                    f"=====================================\n"
                    f"输出格式：\n"
                    f"请返回JSON格式的参数对象，包含以下内容：\n"
                    f"- function_name字段：指定函数名称，如\"handle_outliers\"\n"
                    f"- 工具所需的所有参数\n"
                    f"- return_value字段：指定需要使用的返回值字段，如\"processed_data\"\n"
                    f"\n"
                    f"示例1（单个列）：\n"
                    f"{{\"function_name\": \"handle_outliers\", \"data\": \"销量\", \"method\": \"iqr\", \"threshold\": 1.5, \"return_value\": \"processed_data\"}}\n"
                    f"\n"
                    f"示例2（多个列）：\n"
                    f"{{\"function_name\": \"handle_outliers\", \"data\": [\"销量\", \"客单价\"], \"method\": \"truncate\", \"lower_quantile\": 0.05, \"upper_quantile\": 0.95, \"return_value\": \"processed_data\"}}\n"
                    f"\n"
                    f"注意：\n"
                    f"- 列名必须出现在数据中\n"
                    f"- 只返回JSON，不要返回其他内容\n"
                    f"- 请确保JSON格式正确，包含function_name字段\n"
                    f"=====================================\n"
                )
                preprocess_decision = chat_model.invoke([HumanMessage(content=preprocess_prompt)])
                data[step] = json.loads(preprocess_decision.content.strip())
                
    # 构建去重提示词
    deduplicate_prompt = "你是一个专业的数据分析师，擅长数据预处理和分析任务\n"
    deduplicate_prompt += "=====================================\n"
    deduplicate_prompt += "任务：\n"
    deduplicate_prompt += "请分析以下JSON数据，判断其中是否存在重复的分析步骤\n"
    deduplicate_prompt += "如果存在重复项，请删除重复的内容，只保留一个实例\n"
    deduplicate_prompt += "=====================================\n"
    deduplicate_prompt += "处理规则：\n"
    deduplicate_prompt += "1. 保持原始JSON格式不变\n"
    deduplicate_prompt += "2. 只删除重复的分析步骤，不要修改其他内容\n"
    deduplicate_prompt += "3. 删除时确保完整删除，不要留下部分内容\n"
    deduplicate_prompt += "4. 请返回处理后的完整JSON数据\n"
    deduplicate_prompt += "=====================================\n"
    deduplicate_prompt += "原始数据：\n"
    deduplicate_prompt += json.dumps(data, ensure_ascii=False) + "\n"
    
    # 调用大模型进行去重处理
    deduplicate_result = chat_model.invoke([HumanMessage(content=deduplicate_prompt)])
    print(f"去重结果：{deduplicate_result.content}")
    
    # 解析去重后的结果
    try:
        deduplicated_data = json.loads(deduplicate_result.content.strip())
        data = deduplicated_data
    except:
        print("去重失败，使用原始数据")
        pass




    # 返回判断结果
    print(data)
    print(json.dumps(data))
    return ChatResponse(response=json.dumps({"status": "success", "need_preprocess": 1, "preprocess_steps": 1, "message": "场景确认成功", "data": json.dumps(data, ensure_ascii=False)}))   
@app.post("/api/run-description")
async def run_description(request: Request):
    data = await request.json()
    for key in list(data.keys())[2:]:
        # func = data.get(key, None)
        # print(func["function_name"])
        # print(func["data"])
        # return_value = func["return_value"]
        # 前端传来的函数名和参数
        # ifunc_name = func["function_name"]
        
        # args = []
        # for arg in list(func.keys())[1:]:
        #     arg = func.get(arg, None)
        #     args.append(arg)

           

        # 直接调用
        # print(args)
        # # print(help(func_name))
        # if len(ifunc_name.split("_")) >= 2:
           
        #     class_name = ""
        #     for i in ifunc_name.split("_"):
        #         class_name += i[0].upper() + i[1:]
        #     func_name = class_name
        # else:
        #     class_name = ifunc_name
        #     func_name = ""
        #     uppercase_positions = [(i, char) for i, char in enumerate(ifunc_name) if char.isupper()]
        #     last_pos = 0
        #     for pos, char in uppercase_positions:
        #         if pos > 0:
        #             func_name += ifunc_name[last_pos:pos].lower() + "_"
        #         last_pos = pos
        #     func_name += ifunc_name[last_pos:].lower()
        # print(class_name)
        # funct =  ALL_FUNCTIONS[ifunc_name](*args)
        # print(funct)
        # result = ALL_FUNCTIONS[func_name](classfunct_args)
        # result = result[return_value]
        # print(result)  # 30
        df = pd.read_csv(r"Ai\奶茶店每日订单.csv")
        df = df.describe().to_csv(sep='\t')
        df = [i.split("\r") for i in df.split("\t")]
        table_df = []
        for i in df:
            for j in i:
                table_df.append(j)
        columns = []
        processed_data = []
        row = []
        for t in table_df:
            
            if t[:1] == "\n":
                processed_data.append(row)
                row = []
                row.append(t[1:])
                continue
            row.append(t)
        columns = processed_data[0]
        processed_data = processed_data[1:]
        data = {
            "columns": columns,
            'processed_data': processed_data
        }

    return ChatResponse(response=json.dumps({"status": "success", "message": "运行成功", "data": json.dumps(data, ensure_ascii=False)}))

if __name__ == "__main__":
    import uvicorn
    # host=0.0.0.0：允许局域网/外网访问；port=8001：后端端口
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)