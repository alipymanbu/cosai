import pandas as pd

def to_dataframe(data):
    """
    将前端传来的数据字典转换为DataFrame
    参数格式: {"row-col": "value", ...} 如 {"1-1": "A1", "1-2": "B1"}
    """
    if data is None or len(data) == 0:
        return pd.DataFrame()
    
    # 确定实际需要的行列数
    max_row = 0
    max_col = 0
    for k in data.keys():
        row, col = map(int, k.split('-'))
        max_row = max(max_row, row)
        max_col = max(max_col, col)
    
    # 创建正好大小的DataFrame
    df = pd.DataFrame(index=range(max_row), columns=range(max_col))
    for k, y in data.items():
        row, col = map(int, k.split('-'))
        df.iloc[row-1, col-1] = y
    
    # 删除全为空的行和列
    df = df.dropna(how='all', axis=0)
    df = df.dropna(how='all', axis=1)
    
    return df
