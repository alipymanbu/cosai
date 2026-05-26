def generate_parameter_suggestions(selected_tool, description, parameters, analysis_report, chat_model, HumanMessage):
    """
    基于工具信息和分析报告生成参数建议（严格按参数顺序+值组合去重）
    """
    prompt = f"""请根据以下信息为用户生成参数建议：

工具名称：{selected_tool}
工具描述：{description}
所需参数：{parameters}
数据报告：{analysis_report}

请基于数据报告中的信息，为每个参数提供多个具体的建议值，并以JSON格式返回。请考虑以下可能的数据不达标情况：
1. 数据量不足，样本数量过少
2. 数据中存在缺失值
3. 数据类型不符合要求（如需要数值型数据但提供了文本数据）
4. 数据分布异常，存在极端值
5. 自变量之间存在多重共线性
6. 因变量与自变量之间不存在线性关系

注意：
1. 所有建议都合并到suggestions字段中，每个建议包含场景描述和参数配置。
2. 不同场景的参数配置不要重复。
3. data_eligibility字段只能生成数据不达标的具体原因。
4. 参数值只能使用数据报告中提到的表头名称，不要使用其他名称。
5. 参数名称必须是函数参数的名称，不能是其他名称。
6. 每个建议的参数配置必须是唯一的，不能重复。
JSON应包含以下字段：
{{
  "suggestions": [
    {{
      "scenario": "默认场景",
      "parameters": [
        {{
          "name": "参数名称",
          "value": "建议值",
          "reason": "建议理由"
        }}
      ]
    }},
    {{
      "scenario": "其他场景",
      "parameters": [
        {{
          "name": "参数名称",
          "value": "建议值",
          "reason": "建议理由"
        }}
      ]
    }}
  ],

  "data_eligibility": {{
    "eligible": false,
    "reasons": [
      "数据不达标的原因1",
      "数据不达标的原因2"
    ]
  }},
  "summary": "参数建议总结"
}}

请确保返回的是有效的JSON格式，不要包含其他解释性文字。"""
            
    # 调用大模型生成参数建议
    response = chat_model.invoke([HumanMessage(content=prompt)], temperature=0)
    parameter_suggestions = response.content.strip()

    # ====================== 核心：严格按参数顺序+值去重 ======================
    import json
    res_json = json.loads(parameter_suggestions)
    suggestions = res_json.get("suggestions", [])
    
    if suggestions:
        seen = set()
        unique_list = []
        
        for item in suggestions:
            # 1. 提取当前项的参数列表
            params = item.get("parameters", [])
            
            # 2. 生成“参数指纹”：不排序！严格按原顺序拼接
            # 格式：name1=value1||name2=value2
            fp_items = [f"{p.get('name','')}={p.get('value','')}" for p in params]
            fingerprint = "||".join(fp_items)
            
            # 3. 没见过就保留
            if fingerprint not in seen:
                seen.add(fingerprint)
                unique_list.append(item)
        
        res_json["suggestions"] = unique_list

    final_result = json.dumps(res_json, ensure_ascii=False, indent=2)
    return final_result