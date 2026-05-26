from langchain_core.messages import HumanMessage
from __init__ import State
from get_tools import get_available_tools, extract_method_name
from llm_chat import create_chat_model
from get_tools import check_tool_exists
def generate_tool_code(chat_model, method_name: str, method_description: str) -> str:
    """使用 AI 生成新工具的代码"""
    prompt = f"""请为以下分析方法生成 Python 代码，要求：
1. 使用 langchain_core.tools.Tool 封装
2. 使用 pydantic 定义输入模型
3. 返回 Dict[str, Any] 类型的结果
4. 代码要完整可运行

方法名称：{method_name}
方法描述：{method_description}

请只返回代码，不要有其他说明。代码格式参考：
from langchain_core.tools import Tool
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import numpy as np

class MethodNameInput(BaseModel):
    # 定义输入参数

def method_name(input_data: MethodNameInput) -> Dict[str, Any]:
    # 实现方法逻辑
    return {{...}}
"""
    
    response = chat_model.invoke([HumanMessage(content=prompt)])
    return response.content

def check_and_generate_tool(chat_model, state: State) -> State:

    requested_method = state.get('requested_method', '')
    user_input = state.get('user_input', '')
    
    # 如果用户没有指定工具，直接返回 True
    if not requested_method:
        state['tool_available'] = True
        return state
    
    # 获取当前可用的工具列表
    available_tools = get_available_tools()
    
    # 从用户输入中提取工具名称
    actual_method_name = extract_method_name(chat_model, user_input, available_tools)

    # 更新状态中的工具名称
    state['requested_method'] = actual_method_name
    
    # 如果工具名称，检查工具是否存在
    if actual_method_name and not check_tool_exists(actual_method_name):
        print(f"工具 '{actual_method_name}' 不存在，正在生成代码...")
        
        generated_code = generate_tool_code(
            chat_model,        
            actual_method_name, 
            f"用户请求的{actual_method_name}分析方法"
        )
        
        state['tool_available'] = False
        state['generated_code'] = generated_code
        print(f"已生成 {actual_method_name} 的代码")
    else:
        state['tool_available'] = True
    
    return state

if __name__ == "__main__":
    chat_model = create_chat_model()
    # print(generate_tool_code("k-means", "分类模型"))
    state = State(
        messages=[],
        analysis_report="",
        requested_method="k-means",
        user_input="请你使用k-means分析一下这个数据",
        tool_available=True,
        generated_code=""
    )

    print(check_and_generate_tool(chat_model, state))