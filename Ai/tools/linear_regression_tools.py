from langchain_core.tools import Tool
from typing import Dict, Any
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score

def simple_linear_regression(x: str, y: str) -> Dict[str, Any]:
    """执行简单线性回归
    
    Args:
        x: 自变量列名
        y: 因变量列名
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典：
            - coefficients: 回归系数
            - intercept: 截距
            - mse: 均方误差
            - r2: R²值
            - model_type: 模型类型
    """
    # 从CSV文件读取数据
    data = pd.read_csv(r"Ai\奶茶店每日订单.csv")
    x_data = np.array(data[x]).reshape(-1, 1)
    y_data = np.array(data[y])
    
    model = LinearRegression()
    model.fit(x_data, y_data)
    
    predictions = model.predict(x_data)
    mse = mean_squared_error(y_data, predictions)
    r2 = r2_score(y_data, predictions)
    
    return {
        "coefficients": model.coef_.tolist(),
        "intercept": model.intercept_,
        "mse": mse,
        "r2": r2,
        "model_type": "simple_linear_regression"
    }

def multiple_linear_regression(x: list, y: str) -> Dict[str, Any]:
    """执行多元线性回归
    
    Args:
        x: 自变量列名列表
        y: 因变量列名
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典：
            - coefficients: 回归系数
            - intercept: 截距
            - mse: 均方误差
            - r2: R²值
            - model_type: 模型类型
    """
    # 从CSV文件读取数据
    data = pd.read_csv(r"Ai\奶茶店每日订单.csv")
    x_data = np.array(data[x])
    y_data = np.array(data[y])
    
    model = LinearRegression()
    model.fit(x_data, y_data)
    
    predictions = model.predict(x_data)
    mse = mean_squared_error(y_data, predictions)
    r2 = r2_score(y_data, predictions)
    
    return {
        "coefficients": model.coef_.tolist(),
        "intercept": model.intercept_,
        "mse": mse,
        "r2": r2,
        "model_type": "multiple_linear_regression"
    }

linear_regression_tools = [
    Tool(
        name="SimpleLinearRegression",
        func=simple_linear_regression,
        description="执行简单线性回归，输入自变量和因变量数据，返回回归系数、截距、均方误差和R²值"
    ),
    Tool(
        name="MultipleLinearRegression",
        func=multiple_linear_regression,
        description="执行多元线性回归，输入多个自变量和因变量数据，返回回归系数、截距、均方误差和R²值"
    )
]

if __name__ == "__main__":
    # 测试简单线性回归
    result = simple_linear_regression(x="促销活动", y="销量")
    print("Simple Linear Regression Result:")
    print(result)
    
    # 测试多元线性回归
    multiple_result = multiple_linear_regression(x=["促销活动", "天气", "周末"], y="销量")
    print("\nMultiple Linear Regression Result:")
    print(multiple_result)
