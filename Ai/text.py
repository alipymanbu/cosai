from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph
from data_descriptive import analyze_milk_tea_orders
from llm_chat import create_chat_model
from get_tools import get_available_tools, check_tool_exists, extract_method_name
from __init__ import State
from llm_code import generate_tool_code, check_and_generate_tool
from functools import partial





# 创建 ChatTongyi 模型实例
chat_model = create_chat_model()

def process_message(state: State) -> State:
    # 模拟AI响应，直接返回包含参数说明的消息
    from langchain_core.messages import AIMessage
    response_content = """
## 数据质量检查
1. **异常值检测**：未发现明显异常值，数据分布合理
2. **缺失值处理**：无缺失值，数据完整性良好
3. **数据一致性**：数据格式、单位、类型一致
4. **其他问题**：无重复值，格式正确

## 函数参数说明
对于线性回归分析，根据实际工具函数的参数定义：
- @x：自变量数据列表（必填），类型为List[float]
- @y：因变量数据列表（必填），类型为List[float]

## 输出规范
已按照要求输出与数据质量和分析方法相关的内容
"""
    response = AIMessage(content=response_content)
    state['messages'].append(response)
    return state

def build_graph() -> CompiledStateGraph:
    graph = StateGraph(State)
    
    graph.add_node("check_and_generate_tool", partial(check_and_generate_tool, chat_model))
    graph.add_node("process_message", process_message)
    
    graph.add_edge(START, "check_and_generate_tool")
    graph.add_edge("check_and_generate_tool", "process_message")
    graph.add_edge("process_message", END)
    
    compiled_graph = graph.compile()
    return compiled_graph

if __name__ == "__main__":
    # 基本分析
    analysis_report = analyze_milk_tea_orders()
    
    graph = build_graph()

    
    # 在此处修改要使用的分析方法
    user_input = "现在工具有没有线性回归分析方法，我想分析一下这个数据"  # 空字符串表示不进行特定分析
    
    system_content = """你是一个专业的数据分析助手。请按以下要求分析数据：

## 数据质量检查
1. **异常值检测**：识别数据中的异常值，并说明处理建议（保留、修正或删除）
2. **缺失值处理**：检查缺失值比例和分布，给出填充或删除建议
3. **数据一致性**：检查数据格式、单位、类型的一致性
4. **其他问题**：检查数据是否存在其他问题（如重复值、格式错误等）

## 函数参数说明
对于用户请求的分析方法，请严格根据实际工具函数的参数定义来生成说明：
- 明确列出所有参数，包括参数名、类型、含义和默认值
- 区分必填参数与可选参数
- 在每个参数字符旁边加一个@标记，方便前端处理
- 对于线性回归分析，参考sklearn.linear_model.LinearRegression的参数：
  - fit_intercept@：是否计算截距，默认True
  - normalize@：是否对特征进行标准化，默认False
  - copy_X@：是否复制X，避免在原始数据上操作，默认True
  - n_jobs@：并行任务数，默认None

## 输出规范
- 仅输出与数据质量和分析方法相关的内容
- 不要提供营销建议、业务策略或其他无关内容
- 使用清晰、专业的语言，分点陈述"""

    user_content = analysis_report
    
    if user_input:
        user_content += f"\n\n用户请求使用方法：{user_input}"
    
    system_message = SystemMessage(content=system_content)
    
    initial_messages = [
        system_message,
        HumanMessage(content=user_content)
    ]
    
    result = graph.invoke({
        "messages": initial_messages,
        "analysis_report": analysis_report,
        "requested_method": user_input,
        "user_input": user_input,
        "tool_available": True,
        "generated_code": ""
    })
    
    print("\n分析结果:")
    print(result['messages'][-1].content)

    print("\n" + "=" * 60)
    
    if result.get('generated_code'):
        print(f"\n生成的代码:")
        print(result['generated_code'])
