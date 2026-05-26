import json
from operator import le
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph
from llm_chat import create_chat_model
from get_tools import get_available_tools, extract_method_name, get_tool_description, analyze_user_parameters
from __init__ import State
from llm_code import generate_tool_code, check_and_generate_tool
from Ai_advice import generate_parameter_suggestions


# 创建 ChatTongyi 模型实例
chat_model = create_chat_model()


# 基本分析
# analysis_report = analyze_milk_tea_orders()

# 用户输入
# user_input = "帮我进行信效度检验"

# 定义判断用户需求类型的函数
def classify_user_intent(chat_model, user_input):
    prompt = f"""请判断用户输入的需求类型：

        类型定义：
        类型 1（用户指定特定分析）：用户明确要求执行某一项具体的数据分析操作，需指定具体分析动作（如"计算用户年龄均值""绘制月度销售额折线图""筛选大于 100 的订单数据"）。
        类型 2（整体数据整体分析）：用户要求对数据集进行全面、系统的分析，未指定具体操作，需智能体自动生成分析优先级并执行（如"帮我全面分析这份销售数据"）。
        类型 3（用户询问数据问题）：用户单纯提问数据相关概念、原因、逻辑，不要求执行任何分析操作，仅需纯对话式回答（如"什么是数据相关性？""销售额下降的可能原因有哪些？""均值和中位数的区别是什么？"）。包括用户要求解释或简化之前回答的情况（如"再简单点""还是不懂"等）。
        类型 4（用户要求其他问题）：用户要求执行其他操作，如"请生成一个随机数""请发送邮件""今天天气怎么样啊""你好"等，不涉及数据相关概念的询问。

        示例：
        用户输入："帮我计算年龄的平均值" -> 1
        用户输入："筛选出订单金额大于 100 的数据" -> 1
        用户输入："帮我进行信效度检验" -> 1
        用户输入："对数据进行标准化处理" -> 1
        用户输入："帮我全面分析这份销售数据" -> 2
        用户输入："整体解读这个数据集" -> 3
        用户输入："对这个数据集进行完整的探索性分析" -> 1
        用户输入："什么是数据相关性？" -> 3
        用户输入："销售额下降的可能原因有哪些？" -> 3
        用户输入："均值和中位数的区别是什么？" -> 3
        用户输入："再简单点解释" -> 3
        用户输入："还是不懂，能说得更通俗吗" -> 3
        用户输入："今天天气怎么样" -> 4
        用户输入："请生成一个随机数" -> 4
        用户输入："帮我写一封邮件" -> 4
        用户输入："你好" -> 4
        用户输入：{user_input}
        
        请仅返回类型编号（1、2、3 或 4），不要返回其他内容!!!!!!"""
    # 固定温度为 0，确保分类结果稳定
    intent_type = chat_model.invoke([HumanMessage(content=prompt)], temperature=0).content.strip()
    print(intent_type)
    return intent_type
def process_specific_analysis_request(chat_model, user_input):
    tool_name = extract_method_name(chat_model, user_input, get_available_tools())
    # print(get_available_tools())
    # print(tool_name)
    if len(tool_name) > 1:
        # print("用户输入中包含多个工具名称，无法确定具体操作。")
        return [tool_name, 1]
    elif len(tool_name) == 0:
        return [tool_name, 2]
#         # 未提取到工具名称，分析用户输入需要什么分析
#         print("未提取到工具名称，分析用户输入需要什么分析...")
        
#         # 让 AI 分析用户输入需要什么分析
#         prompt = f"""请分析用户输入的内容，判断用户可能需要什么类型的数据分析：

# 用户输入：{user_input}

# 请基于用户的输入，分析他们可能需要的数据分析类型，并以 JSON 格式返回。JSON 应包含以下字段：
# {{
# "analysis_needs": [
# {{
#     "type": "分析类型",
#     "description": "分析类型的描述",
#     "reason": "为什么用户可能需要这种分析"
# }}
# ]
# }}

# 请确保返回的是有效的 JSON 格式，不要包含其他解释性文字。"""
        
#         # 调用大模型分析用户需求
#         response = chat_model.invoke([HumanMessage(content=prompt)], temperature=0)
#         analysis_result = response.content.strip()
        
#         # 解析 JSON
#         needs_analysis = json.loads(analysis_result)
#         # 打印分析结果
#         print("用户需求分析结果:")
#         print(json.dumps(needs_analysis, ensure_ascii=False, indent=2))
        
#         # 让用户选择分析类型
#         selected_analysis = None
#         if len(needs_analysis["analysis_needs"]) > 1:
#             i = input("请选择你需要的分析类型（输入序号）：")
#             selected_analysis = needs_analysis["analysis_needs"][int(i)-1]
#             print("你选择了的分析类型:", selected_analysis["type"])
#         elif len(needs_analysis["analysis_needs"]) == 1:
#             selected_analysis = needs_analysis["analysis_needs"][0]
#             print("自动选择分析类型:", selected_analysis["type"])
    else:
        return [tool_name, 3]
    
#             # 如果用户选择了分析类型，生成代码
#             if selected_analysis:
#                 print("\n正在生成代码...")
                
#                 # 让 AI 生成代码，格式要和 linear_regression_tools.py 中的函数一样
#                 prompt = f"""请根据以下分析需求生成 Python 代码，格式要和 linear_regression_tools.py 中的函数一样：

# 分析类型：{selected_analysis["type"]}
# 分析描述：{selected_analysis["description"]}
# 需求原因：{selected_analysis["reason"]}

# 请生成完整的 Python 函数代码，包括函数定义、参数、返回值和必要的注释。"""
                
#                 # 调用大模型生成代码
#                 response = chat_model.invoke([HumanMessage(content=prompt)], temperature=0.7)
#                 generated_code = response.content.strip()
                
#                 # 打印生成的代码
#                 print("生成的代码:")
#                 print(generated_code)
                
#                 # 将生成的代码写入文件
#                 with open("generated_code.py", "w", encoding="utf-8") as f:
#                     f.write(generated_code)
                
#                 print("代码已写入 generated_code.py 文件")
    
#     return tool_name
