from langchain_core.tools import Tool
from typing import Dict, Any, Optional, List
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.impute import SimpleImputer
from sklearn.feature_selection import SelectKBest, f_regression
from sklearn.model_selection import train_test_split

def standard_scaling(data: List[str]) -> Dict[str, Any]:
    """执行数据标准化
    
    Args:
        data: 需要标准化的列名列表
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典：
            - scaled_data: 标准化后的数据
            - mean: 每个特征的均值
            - std: 每个特征的标准差
            - method: 使用的方法名称
    """
    data = pd.read_csv(r"Ai\奶茶店每日订单.csv")[data]
    
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(data)
    
    return {
        "scaled_data": scaled_data.tolist(),
        "mean": scaler.mean_.tolist(),
        "std": scaler.scale_.tolist(),
        "method": "standard_scaling"
    }

def minmax_scaling(data: List[str], feature_range: List[float] = [0, 1]) -> Dict[str, Any]:
    """执行数据归一化
    
    Args:
        data: 需要归一化的列名列表
        feature_range: 归一化的范围，默认为[0, 1]
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典：
            - scaled_data: 归一化后的数据
            - min: 每个特征的最小值
            - max: 每个特征的最大值
            - feature_range: 归一化的范围
            - method: 使用的方法名称
    """
    data = pd.read_csv(r"Ai\奶茶店每日订单.csv")[data]
    feature_range = tuple(feature_range)
    
    scaler = MinMaxScaler(feature_range=feature_range)
    scaled_data = scaler.fit_transform(data)
    
    return {
        "scaled_data": scaled_data.tolist(),
        "min": scaler.data_min_.tolist(),
        "max": scaler.data_max_.tolist(),
        "feature_range": feature_range,
        "method": "minmax_scaling"
    }   

def impute_missing_values(data: List[str], strategy: str = "mean", fill_value: Optional[float] = None) -> Dict[str, Any]:
    """处理缺失值
    
    Args:
        data: 包含缺失值的列名列表
        strategy: 填充策略，可选值：mean, median, most_frequent, constant
        fill_value: 当strategy为constant时的填充值
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典：
            - imputed_data: 填充缺失值后的数据
            - strategy: 使用的填充策略
            - fill_value: 当strategy为constant时的填充值
            - method: 使用的方法名称
    """
    data = pd.read_csv(r"Ai\奶茶店每日订单.csv")[data]
    
    if strategy == "constant" and fill_value is not None:
        imputer = SimpleImputer(strategy=strategy, fill_value=fill_value)
    else:
        imputer = SimpleImputer(strategy=strategy)
    
    imputed_data = imputer.fit_transform(data)
    
    return {
        "imputed_data": imputed_data.tolist(),
        "strategy": strategy,
        "fill_value": fill_value,
        "method": "impute_missing_values"
    }
    
def feature_selection(X: List[str], y: str, k: int) -> Dict[str, Any]:
    """执行特征选择
    
    Args:
        X: 特征列名列表
        y: 目标变量列名
        k: 选择的特征数量
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典：
            - selected_features: 选择的特征数据
            - selected_indices: 选中的特征索引
            - feature_scores: 每个特征的得分
            - k: 选择的特征数量
            - method: 使用的方法名称
    """
    X = pd.read_csv(r"Ai\奶茶店每日订单.csv")[X]
    y = pd.read_csv(r"Ai\奶茶店每日订单.csv")[y]
    
    selector = SelectKBest(score_func=f_regression, k=k)
    X_new = selector.fit_transform(X, y)
    
    # 获取选中的特征索引
    selected_indices = selector.get_support(indices=True).tolist()
    # 获取特征得分
    feature_scores = selector.scores_.tolist()
    
    return {
        "selected_features": X_new.tolist(),
        "selected_indices": selected_indices,
        "feature_scores": feature_scores,
        "k": k,
        "method": "feature_selection"
    }

def train_test_split_data(X: List[str], y: str, test_size: float = 0.2, random_state: Optional[int] = None) -> Dict[str, Any]:
    """执行训练集和测试集分割
    
    Args:
        X: 特征列名列表
        y: 目标变量列名
        test_size: 测试集大小，默认为0.2
        random_state: 随机种子
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典：
            - X_train: 训练集特征数据
            - X_test: 测试集特征数据
            - y_train: 训练集目标变量
            - y_test: 测试集目标变量
            - test_size: 测试集大小
            - random_state: 随机种子
            - method: 使用的方法名称
    """
    X = pd.read_csv(r"Ai\奶茶店每日订单.csv")[X]
    y = pd.read_csv(r"Ai\奶茶店每日订单.csv")[y]
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )
    
    return {
        "X_train": X_train.values.tolist(),
        "X_test": X_test.values.tolist(),
        "y_train": y_train.values.tolist(),
        "y_test": y_test.values.tolist(),
        "test_size": test_size,
        "random_state": random_state,
        "method": "train_test_split"
    }

def handle_outliers(data: List[str], method: str, threshold: float = 1.5, lower_quantile: float = 0.05, upper_quantile: float = 0.95) -> Dict[str, Any]:
    """处理极端值
    
    Args:
        data: 需要处理极端值的列名列表
        method: 极端值处理方法，可选值：iqr, zscore, winsorize, truncate
        threshold: 处理阈值，IQR方法使用1.5，Z-score方法使用3.0
        lower_quantile: 缩尾和截断方法的下分位数，默认为0.05
        upper_quantile: 缩尾和截断方法的上分位数，默认为0.95
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典：
            - processed_data: 处理极端值后的数据
            - method: 使用的极端值处理方法
            - threshold: 处理阈值（仅适用于iqr和zscore方法）
            - lower_quantile: 下分位数（仅适用于winsorize和truncate方法）
            - upper_quantile: 上分位数（仅适用于winsorize和truncate方法）
    """
    # 读取完整数据
    full_data = pd.read_csv(r"Ai\奶茶店每日订单.csv")
    # 提取需要处理的列
    data_subset = full_data[data]
    
    if method == "iqr":
        # 使用IQR方法处理极端值
        Q1 = np.percentile(data_subset, 25, axis=0)
        Q3 = np.percentile(data_subset, 75, axis=0)
        IQR = Q3 - Q1
        lower_bound = Q1 - threshold * IQR
        upper_bound = Q3 + threshold * IQR
        
        # 缩尾处理
        data_processed = np.clip(data_subset, lower_bound, upper_bound)
        # 将处理后的数据放回完整数据中
        full_data[data] = data_processed
        
    elif method == "zscore":
        # 使用Z-score方法处理极端值
        mean = np.mean(data_subset, axis=0)
        std = np.std(data_subset, axis=0)
        z_scores = np.abs((data_subset - mean) / std)
        
        # 缩尾处理
        data_processed = np.copy(data_subset)
        outlier_mask = z_scores > threshold
        
        # 只处理有极端值的情况
        if np.any(outlier_mask):
            data_processed[outlier_mask] = np.where(
                data_subset[outlier_mask] > mean,
                mean + threshold * std,
                mean - threshold * std
            )
        # 将处理后的数据放回完整数据中
        full_data[data] = data_processed
        
    elif method == "winsorize":
        # 使用缩尾方法处理极端值
        lower_bounds = np.percentile(data_subset, lower_quantile * 100, axis=0)
        upper_bounds = np.percentile(data_subset, upper_quantile * 100, axis=0)
        data_processed = np.clip(data_subset, lower_bounds, upper_bounds)
        # 将处理后的数据放回完整数据中
        full_data[data] = data_processed
        
    elif method == "truncate":
        # 使用截断方法处理极端值
        lower_bounds = np.percentile(data_subset, lower_quantile * 100, axis=0)
        upper_bounds = np.percentile(data_subset, upper_quantile * 100, axis=0)
        
        # 找出非极端值的索引
        mask = np.all((data_subset >= lower_bounds) & (data_subset <= upper_bounds), axis=1)
        # 保留非极端值的完整数据
        full_data = full_data[mask]
        
    else:
        raise ValueError("不支持的极端值处理方法，请选择：iqr, zscore, winsorize, truncate")
    
    return {
        "processed_data": full_data.values.tolist(),
        "columns": full_data.columns.tolist(),
        "method": method,
        "threshold": threshold if method in ["iqr", "zscore"] else None,
        "lower_quantile": lower_quantile if method in ["winsorize", "truncate"] else None,
        "upper_quantile": upper_quantile if method in ["winsorize", "truncate"] else None
    }

data_preprocessing_tools = [
    Tool(
        name="standard_scaling",
        func=standard_scaling,
        description="执行数据标准化，将数据转换为均值为0，标准差为1的分布"
    ),
    Tool(
        name="minmax_scaling",
        func=minmax_scaling,
        description="执行数据归一化，将数据缩放到指定范围，默认为[0, 1]"
    ),
    Tool(
        name="impute_missing_values",
        func=impute_missing_values,
        description="处理数据中的缺失值，支持多种填充策略"
    ),
    Tool(
        name="feature_selection",
        func=feature_selection,
        description="基于F检验执行特征选择，选择与目标变量相关性最高的k个特征"
    ),
    Tool(
        name="train_test_split_data",
        func=train_test_split_data,
        description="将数据集分割为训练集和测试集"
    ),
    Tool(
        name="handle_outliers",
        func=handle_outliers,
        description="处理数据中的极端值，支持IQR、Z-score、缩尾和截断方法"
    )
]

if __name__ == "__main__":
    # 测试标准化
    scaling_result = standard_scaling(data=["销量", "客单价"])
    print("Standard Scaling Result:")
    print(scaling_result)
    
    # 测试归一化
    minmax_result = minmax_scaling(data=["销量", "客单价"], feature_range=[-1, 1])
    print("\nMinMax Scaling Result:")
    print(minmax_result)
    
    # 测试缺失值处理
    impute_result = impute_missing_values(data=["销量", "客单价"], strategy="mean")
    print("\nImpute Missing Values Result:")
    print(impute_result)
    
    # 测试特征选择
    feature_result = feature_selection(X=["促销活动", "天气", "周末"], y="销量", k=2)
    print("\nFeature Selection Result:")
    print(feature_result)
    
    # 测试数据分割
    split_result = train_test_split_data(X=["促销活动", "天气", "周末"], y="销量", test_size=0.2, random_state=42)
    print("\nTrain Test Split Result:")
    print(split_result)
    
    # 测试极端值处理 - IQR方法
    outlier_result = handle_outliers(data=["销量", "客单价"], method="iqr", threshold=1.5)
    print("\nOutlier Handling Result (IQR):")
    print(outlier_result)
    
    # 测试极端值处理 - Z-score方法
    zscore_result = handle_outliers(data=["销量", "客单价"], method="zscore", threshold=3.0)
    print("\nOutlier Handling Result (Z-score):")
    print(zscore_result)
    
    # 测试极端值处理 - 缩尾方法
    winsorize_result = handle_outliers(data=["销量", "客单价"], method="winsorize", lower_quantile=0.1, upper_quantile=0.9)
    print("\nOutlier Handling Result (Winsorize):")
    print(winsorize_result)
    
    # 测试极端值处理 - 截断方法
    truncate_result = handle_outliers(data=["销量", "客单价"], method="truncate", lower_quantile=0.1, upper_quantile=0.9)
    print("\nOutlier Handling Result (Truncate):")
    print(truncate_result)