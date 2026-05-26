import pandas as pd
from to_dataframe import to_dataframe
def analyze_orders(data):
    """分析奶茶店订单数据并生成报告"""
    file_path = "Ai\奶茶店每日订单.csv"
    df = pd.read_csv(file_path)
    
    basic_info = {
        "数据量": len(df),
        "列数": len(df.columns),
        "列名": list(df.columns)
    }
    
    numeric_stats = df.describe().to_dict()
    
    categorical_stats = {}
    for col in df.select_dtypes(include=['object']).columns:
        categorical_stats[col] = {
            "唯一值数量": df[col].nunique(),
            "前5个最常见值": df[col].value_counts().head(5).to_dict()
        }
    
    missing_values = df.isnull().sum().to_dict()
    
    analysis_report = f"""奶茶店每日订单数据分析报告：

1. 基本信息
数据量: {basic_info['数据量']}条记录
列数: {basic_info['列数']}列
列名: {basic_info['列名']}

2. 数值型数据统计
{numeric_stats}

3. 分类数据统计
{categorical_stats}

4. 缺失值情况
{missing_values}    

上面是数据的基本信息"""
    
    return analysis_report

if __name__ == "__main__":
    df = []
    analysis_report = analyze_orders(df)
    print(analysis_report)