import importlib.util
import os
from typing import List
from langchain_core.messages import HumanMessage
from llm_chat import create_chat_model

TOOLS_DIR = r"Ai\tools"


def get_available_tools():
    """获取当前可用的工具列表"""
    # 构建工具列表
    tools = []
    
    # 遍历tools目录下的所有Python文件
    for file_name in os.listdir(TOOLS_DIR):
        if file_name.endswith('.py') and not file_name.startswith('__'):
            file_path = os.path.join(TOOLS_DIR, file_name)
            module_name = os.path.splitext(file_name)[0]
            
            # 导入模块
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 查找模块中的工具列表
            for attr_name in dir(module):
                attr_value = getattr(module, attr_name)
                # 检查是否是工具列表
                if isinstance(attr_value, list) and len(attr_value) > 0 and hasattr(attr_value[0], 'name') and hasattr(attr_value[0], 'description'):
                    for tool in attr_value:
                        tools.append({"name": tool.name, "description": tool.description})
    
    return tools

def check_tool_exists(method_name: str) -> bool:
    """检查指定工具是否存在"""
    available_tools = get_available_tools()
    return any(tool["name"] == method_name for tool in available_tools)

def extract_method_name(chat_model, user_input: str, available_tools: List[dict]) -> List[str]:    
    """从用户输入中提取工具名称"""
    if not available_tools:
        return []
    
    # 准备工具列表和描述
    tool_list_with_description = "\n".join([f"- {tool['name']}: {tool['description']}" for tool in available_tools])
    
    # 使用大模型从用户输入中提取工具名称
    prompt = f"""从用户输入中提取数据分析工具需求，并从可用工具列表中选择所有匹配的工具。

            用户输入：{user_input}

            可用工具列表：
{tool_list_with_description}

            注意：请根据用户的需求和工具的描述，选择所有匹配的工具名称，仅返回工具名称本身，不要返回其他内容，有多个工具请用回车隔开。
            
            重要：如果没有任何工具与用户需求匹配，请返回空字符串，不要返回任何不相关的工具名称。
            示例：
            用户输入："帮我计算年龄的平均值" -> "DescriptiveAnalysis"
            用户输入："绘制月度销售额折线图" -> "TimeSeriesAnalysis"
            用户输入："帮我进行信效度检验" -> "ConfidenceIntervalAnalysis"
            用户输入："帮我进行相关性分析" -> "CorrelationAnalysis\nSimpleLinearRegression"
            """
    
    # 固定温度为0，确保结果稳定
    response = chat_model.invoke([HumanMessage(content=prompt)], temperature=0)
    print(response.content)
    extracted_tools = response.content.strip().split('\n')
    # 验证提取的工具是否在可用列表中，并去重
    valid_tools = []
    seen = set()
    for tool_name in extracted_tools:
        tool_name = tool_name.strip()
        # 检查工具名称是否在可用列表中
        is_valid = any(tool["name"] == tool_name for tool in available_tools)
        if tool_name and tool_name not in seen and is_valid:
            valid_tools.append(tool_name)
            seen.add(tool_name)
    
    # 如果没有匹配的工具，使用规则匹配
    # if not valid_tools:
    #     valid_tools = rule_based_tool_matching(user_input, available_tools)
    
    return valid_tools
    # except Exception as e:
    #     print(f"大模型调用失败，使用规则匹配：{str(e)}")
    #     # 降级到规则匹配
    #     return rule_based_tool_matching(user_input, available_tools)

# def rule_based_tool_matching(user_input: str, available_tools: List[str]) -> str:
#     """基于规则的工具匹配"""
#     # 工具名称与关键词映射
#     tool_keywords = {
#         "SimpleLinearRegression": ["线性回归", "回归分析", "linear", "regression"],
#         "KMeansClustering": ["聚类", "k-means", "clustering", "cluster"],
#         "DescriptiveAnalysis": ["描述性", "统计", "描述", "descriptive"],
#         "CorrelationAnalysis": ["相关性", "相关分析", "correlation", "correl"],
#         "TimeSeriesAnalysis": ["时间序列", "时序", "time series", "trend"]
#     }
    
#     # 转换为小写便于匹配
#     user_input_lower = user_input.lower()
    
#     # 计算每个工具的匹配得分
#     scores = {}
#     for tool in available_tools:
#         score = 0
#         keywords = tool_keywords.get(tool, [])
#         for keyword in keywords:
#             if keyword.lower() in user_input_lower:
#                 score += 1
#         scores[tool] = score
    
#     # 返回得分最高的工具
#     if scores:
#         best_tool = max(scores, key=scores.get)
#         if scores[best_tool] > 0:
#             return best_tool
    
#     # 如果没有匹配的工具，返回第一个工具作为默认
#     return available_tools[0] if available_tools else ""


def get_tool_description(tool_name: str) -> str:
    """获取指定工具的描述信息"""
    available_tools = get_available_tools()
    if not any(tool["name"] == tool_name for tool in available_tools):
        return ""
    
    # 遍历tools目录下的所有Python文件
    for file_name in os.listdir(TOOLS_DIR):
        if file_name.endswith('.py') and not file_name.startswith('__'):
            file_path = os.path.join(TOOLS_DIR, file_name)
            module_name = os.path.splitext(file_name)[0]
            
            # 导入模块
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 查找模块中的工具列表
            for attr_name in dir(module):
                attr_value = getattr(module, attr_name)
                # 检查是否是工具列表
                if isinstance(attr_value, list) and len(attr_value) > 0 and hasattr(attr_value[0], 'name') and hasattr(attr_value[0], 'description'):
                    for tool in attr_value:
                        if tool.name == tool_name:
                            return tool.description
    return ""

def get_tool_docstring(tool_name: str) -> str:
    """获取指定工具函数的文档字符串"""
    available_tools = get_available_tools()
    if not any(tool["name"] == tool_name for tool in available_tools):
        return ""
    
    # 遍历tools目录下的所有Python文件
    for file_name in os.listdir(TOOLS_DIR):
        if file_name.endswith('.py') and not file_name.startswith('__'):
            file_path = os.path.join(TOOLS_DIR, file_name)
            module_name = os.path.splitext(file_name)[0]
            
            # 导入模块
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 查找模块中的工具列表
            for attr_name in dir(module):
                attr_value = getattr(module, attr_name)
                # 检查是否是工具列表
                if isinstance(attr_value, list) and len(attr_value) > 0 and hasattr(attr_value[0], 'name') and hasattr(attr_value[0], 'description'):
                    for tool in attr_value:
                        if tool.name == tool_name:
                            # 提取工具函数的文档字符串
                            func = tool.func
                            if func.__doc__:
                                return func.__doc__
    return ""

def analyze_user_parameters(chat_model, user_input: str, data_columns: List[str]) -> dict:
    """分析用户输入中的参数，并检查是否存在于数据中"""
    # try:
    prompt = f"""请分析用户输入中的参数信息，并检查这些参数是否存在于提供的数据列中。

用户输入：{user_input}

数据列列表：{data_columns}

请按以下格式返回分析结果：
{{
  "extracted_parameters": [
    {{
      "name": "参数名称",
      "value": "参数值（如果提供）",
      "exists_in_data": true/false,
      "suggestion": "可能的正确拼写（如果存在）"
    }}
  ],
  "missing_parameters": ["缺失的参数名称"],
  "suggestions": {{"输入参数": "可能的正确拼写"}},
  "summary": "分析总结"
}}

请确保返回的是有效的JSON格式，不要包含其他解释性文字。"""
        
    # 固定温度为0，确保结果稳定
    response = chat_model.invoke([HumanMessage(content=prompt)], temperature=0)
    result = response.content.strip()
        
    # 解析JSON结果
    import json
    return json.loads(result)
    # except Exception as e:
    #     print(f"AI分析失败，使用简单规则分析：{str(e)}")
    #     # 降级到简单规则分析
    #     return enhanced_parameter_analysis(user_input, data_columns)

# def enhanced_parameter_analysis(user_input: str, data_columns: List[str]) -> dict:
#     """增强的参数分析（降级方案）"""
#     # 提取可能的参数名称
#     import re
#     from difflib import SequenceMatcher
    
#     # 匹配类似 "x是..." 或 "y是..." 的模式
#     param_patterns = re.findall(r'(\w+)\s*是\s*(\S+)', user_input)
    
#     extracted_parameters = []
#     missing_parameters = []
#     suggestions = {}
    
#     for param_name, param_value in param_patterns:
#         exists = False
#         best_match = None
#         best_score = 0
        
#         # 检查参数是否存在于数据列中
#         for col in data_columns:
#             # 检查精确匹配
#             if param_value.lower() in col.lower():
#                 exists = True
#                 break
#             # 检查相似度
#             score = SequenceMatcher(None, param_value.lower(), col.lower()).ratio()
#             if score > best_score and score > 0.6:  # 相似度阈值
#                 best_score = score
#                 best_match = col
        
#         extracted_parameters.append({
#             "name": param_name,
#             "value": param_value,
#             "exists_in_data": exists,
#             "suggestion": best_match if not exists and best_match else None
#         })
        
#         if not exists:
#             missing_parameters.append(param_value)
#             if best_match:
#                 suggestions[param_value] = best_match
    
#     # 生成总结
#     if missing_parameters:
#         summary = f"从用户输入中提取了{len(extracted_parameters)}个参数，其中{len(missing_parameters)}个在数据中不存在"
#         if suggestions:
#             summary += "\n\n可能的拼写错误："
#             for param, suggestion in suggestions.items():
#                 summary += f"\n- '{param}' 可能是 '{suggestion}'"
#     else:
#         summary = f"从用户输入中提取了{len(extracted_parameters)}个参数，所有参数都存在于数据中"
    
#     return {
#         "extracted_parameters": extracted_parameters,
#         "missing_parameters": missing_parameters,
#         "suggestions": suggestions,
#         "summary": summary
#     }

# def simple_parameter_analysis(user_input: str, data_columns: List[str]) -> dict:
#     """简单的参数分析（降级方案）"""
#     # 提取可能的参数名称
#     import re
#     # 匹配类似 "x是..." 或 "y是..." 的模式
#     param_patterns = re.findall(r'(\w+)\s*是\s*(\S+)', user_input)
    
#     extracted_parameters = []
#     missing_parameters = []
    
#     for param_name, param_value in param_patterns:
#         exists = any(param_name.lower() in col.lower() for col in data_columns)
#         extracted_parameters.append({
#             "name": param_name,
#             "value": param_value,
#             "exists_in_data": exists
#         })
#         if not exists:
#             missing_parameters.append(param_name)
    
#     summary = f"从用户输入中提取了{len(extracted_parameters)}个参数，其中{len(missing_parameters)}个在数据中不存在"
    
#     return {
#         "extracted_parameters": extracted_parameters,
#         "missing_parameters": missing_parameters,
#         "summary": summary
#     }



if __name__ == "__main__":
    # 打印可用工具列表
    print("可用工具列表:")
    available_tools = get_available_tools()
    get_tool_description("SimpleLinearRegression")
    print(get_tool_description("SimpleLinearRegression"))
   
   